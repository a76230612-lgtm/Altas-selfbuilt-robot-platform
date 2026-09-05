#include <Arduino.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

// ============================================================
// Atlas 6.0 Stage 8A Sensor Safety V1
// ESP32 DEVKIT_C + L298N + 双编码器 + US-100
//
// 目标：
// 1. 完整保留 Stage 6C V4 的电机、编码器、目标停车和安全功能。
// 2. 加入 US-100 前向距离安全门：无效数据立即停车，近障碍禁止前进。
// 3. 25 cm 以下 FORCE_STOP；25–50 cm CAUTION；50 cm 以上 CLEAR。
// 4. 从 CAUTION 恢复到 CLEAR 时使用 55 cm 释放线，避免临界点反复切换。
// 5. CAUTION 状态把向前方向的 PWM 限制到 100；恢复后不会自动提速。
// 6. 安全状态恢复后必须重新 ARM，绝不自动继续之前的运动。
// 7. 本 Stage 8A 文件强制关闭真实电机输出，仅用于无动力软件整合测试。
//
// 当前已锁定的编码器映射（信号组保持交换状态）：
//   物理右轮编码器 -> GPIO18 / GPIO19 -> 原始计数 RAW_18_19
//   物理左轮编码器 -> GPIO25 / GPIO26 -> 原始计数 RAW_25_26
//
// Stage 8A 仍保留 V4 的编码器前进符号自动学习。真实电机测试版本必须先执行：
//   arm -> check left
//   arm -> check right
// 程序依据真实短测结果分别学习符号。目标运动不会使用 abs() 隐藏反向错误。
// 不要交换电机线或编码器线。
// ============================================================

// Stage 8A 安全锁：false 表示所有 L298N 输出始终保持 LOW / PWM 0。
// 只有完成本文件的软件安全验收后，才创建新的 Stage 8B 文件启用电机。
constexpr bool MOTOR_OUTPUTS_ENABLED = false;

// -------------------- L298N 接线 --------------------
// 物理左电机（L298N A通道）
constexpr uint8_t PIN_ENA = 13;
constexpr uint8_t PIN_IN1 = 14;
constexpr uint8_t PIN_IN2 = 4;

// 物理右电机（L298N B通道）
constexpr uint8_t PIN_ENB = 33;
constexpr uint8_t PIN_IN3 = 32;
constexpr uint8_t PIN_IN4 = 23;

// 2026-08-07 实测：TESTL 100 只驱动物理左轮，但左轮向后转。
// 保持所有接线不变，仅在软件中反转左电机输出；右电机保持原极性。
constexpr bool LEFT_MOTOR_INVERTED  = true;
constexpr bool RIGHT_MOTOR_INVERTED = false;

// -------------------- 编码器接线 --------------------
// 物理右轮编码器信号组
constexpr uint8_t PIN_RAW_18_19_A = 18;
constexpr uint8_t PIN_RAW_18_19_B = 19;

// 物理左轮编码器信号组
constexpr uint8_t PIN_RAW_25_26_A = 25;
constexpr uint8_t PIN_RAW_25_26_B = 26;

// -------------------- US-100 接线 --------------------
// 工作模式：Trigger / Echo；模块背面串口模式跳帽已取下。
// 当前底盘测试映射：Trig/TX -> GPIO27，Echo/RX -> GPIO34。
constexpr uint8_t PIN_US100_TRIG = 27;
constexpr uint8_t PIN_US100_ECHO = 34;

constexpr unsigned long US100_SAMPLE_INTERVAL_MS = 60;
constexpr unsigned long US100_ECHO_TIMEOUT_US = 25000;
constexpr float US100_MIN_VALID_CM = 2.0f;
constexpr float US100_MAX_VALID_CM = 400.0f;
constexpr uint8_t US100_VALID_SAMPLES_REQUIRED = 3;

constexpr float FORCE_STOP_ENTER_CM = 25.0f;
constexpr float FORCE_STOP_RELEASE_CM = 28.0f;
constexpr float CAUTION_ENTER_CM = 50.0f;
constexpr float CLEAR_RELEASE_CM = 55.0f;
constexpr int CAUTION_FORWARD_PWM = 100;

// -------------------- Stage 6C 标定参数 --------------------
// 2026-08-08 实测并确认：轮胎沿地面滚动一整圈的距离为 21.40 cm。
// 这是实际滚动周长，不是轮子直径。本版本只更新此标定值和版本标识。
constexpr float WHEEL_CIRCUMFERENCE_CM = 21.40f;
constexpr float LEFT_PULSES_PER_REV     = 632.05f;
constexpr float RIGHT_PULSES_PER_REV    = 634.17f;

// 6C 第一轮基准测试固定使用 160 / 160；先不要在同一轮测试中改 PWM。
constexpr int LEFT_TARGET_PWM  = 160;
constexpr int RIGHT_TARGET_PWM = 160;

// -------------------- 安全限制 --------------------
constexpr int MIN_PWM = 80;
constexpr int MAX_PWM = 220;

// 保留旧的定时运动命令范围。
constexpr unsigned long MIN_DURATION_MS = 100;
constexpr unsigned long MAX_DURATION_MS = 1000;

// Stage 6C 目标运动范围。
constexpr float MIN_DISTANCE_CM = 1.0f;
constexpr float MAX_DISTANCE_CM = 30.0f;
constexpr long MIN_TEST_PULSES  = 20;
constexpr long MAX_TEST_PULSES  = 3000;

constexpr unsigned long STALL_TIMEOUT_MS        = 700;
constexpr unsigned long TARGET_TOTAL_TIMEOUT_MS = 12000;
constexpr unsigned long FINAL_SETTLE_MS         = 300;

// 每次编码器方向检查只让一个轮子悬空向前转 400 ms。
constexpr unsigned long ENCODER_CHECK_DURATION_MS = 400;
constexpr int ENCODER_CHECK_PWM = 160;
constexpr int32_t MIN_ENCODER_CHECK_PULSES = 10;

// 运行中若计数超过“目标 + max(100, 目标的20%)”，判为异常脉冲。
// 正常情况下，控制循环会在达到目标后的几个脉冲内关断电机。
constexpr int32_t MIN_SPIKE_MARGIN_PULSES = 100;

// -------------------- 运行状态 --------------------
enum class MotionMode : uint8_t {
  NONE,
  TIMED,
  TARGET,
  ENCODER_CHECK
};

enum class CheckWheel : uint8_t {
  NONE,
  LEFT,
  RIGHT
};

enum class SensorSafetyState : uint8_t {
  STARTUP_STOP,
  SENSOR_INVALID_STOP,
  FORCE_STOP,
  CAUTION,
  CLEAR
};

String serialLine = "";
String activeCommand = "NONE";

bool armed = false;
bool moving = false;
MotionMode motionMode = MotionMode::NONE;

unsigned long timedStopDeadline = 0;
unsigned long targetStartMs = 0;

CheckWheel activeCheckWheel = CheckWheel::NONE;

// 0 = 尚未检查；+1 / -1 = 原始计数转换为前进正脉冲时使用的乘数。
// 每次 ESP32 重启后都重新检查，避免旧假设掩盖当前硬件方向。
int8_t leftEncoderForwardSign = 0;
int8_t rightEncoderForwardSign = 0;

int32_t leftTargetPulses = 0;
int32_t rightTargetPulses = 0;

bool leftTargetActive = false;
bool rightTargetActive = false;
bool leftTargetDone = false;
bool rightTargetDone = false;

int32_t leftBestProgress = 0;
int32_t rightBestProgress = 0;
unsigned long leftLastProgressMs = 0;
unsigned long rightLastProgressMs = 0;

// 最近一次交给电机底层的逻辑速度。即使 Stage 8A 禁用真实输出，也保留这些值供安全逻辑验证。
int commandedLeftSpeed = 0;
int commandedRightSpeed = 0;

// -------------------- US-100 运行状态 --------------------
SensorSafetyState sensorSafetyState = SensorSafetyState::STARTUP_STOP;
float lastDistanceCm = NAN;
unsigned long lastEchoDurationUs = 0;
unsigned long lastSensorSampleMs = 0;
uint8_t consecutiveValidSensorSamples = 0;
unsigned long totalValidSensorSamples = 0;
unsigned long totalInvalidSensorSamples = 0;

float distanceWindow[3] = {0.0f, 0.0f, 0.0f};
uint8_t distanceWindowCount = 0;
uint8_t distanceWindowIndex = 0;

// -------------------- 编码器原始状态 --------------------
volatile int32_t rawCount18_19 = 0;
volatile int32_t rawCount25_26 = 0;

portMUX_TYPE encoderMux = portMUX_INITIALIZER_UNLOCKED;

// ============================================================
// 编码器中断：A 相上升沿 1X 计数，B 相判断方向
// ============================================================

void IRAM_ATTR onRaw18_19A() {
  const int delta =
      (digitalRead(PIN_RAW_18_19_B) == HIGH) ? 1 : -1;

  portENTER_CRITICAL_ISR(&encoderMux);
  rawCount18_19 += delta;
  portEXIT_CRITICAL_ISR(&encoderMux);
}

void IRAM_ATTR onRaw25_26A() {
  const int delta =
      (digitalRead(PIN_RAW_25_26_B) == HIGH) ? 1 : -1;

  portENTER_CRITICAL_ISR(&encoderMux);
  rawCount25_26 += delta;
  portEXIT_CRITICAL_ISR(&encoderMux);
}

// ============================================================
// 编码器辅助函数
// ============================================================

void resetEncoderCounts() {
  portENTER_CRITICAL(&encoderMux);
  rawCount18_19 = 0;
  rawCount25_26 = 0;
  portEXIT_CRITICAL(&encoderMux);
}

void readRawEncoderCounts(int32_t& raw18_19, int32_t& raw25_26) {
  portENTER_CRITICAL(&encoderMux);
  raw18_19 = rawCount18_19;
  raw25_26 = rawCount25_26;
  portEXIT_CRITICAL(&encoderMux);
}

void readPhysicalEncoderCounts(
    int32_t& physicalLeft,
    int32_t& physicalRight,
    int32_t& raw18_19,
    int32_t& raw25_26) {

  readRawEncoderCounts(raw18_19, raw25_26);

  physicalLeft = (leftEncoderForwardSign == 0)
      ? 0
      : raw25_26 * leftEncoderForwardSign;

  physicalRight = (rightEncoderForwardSign == 0)
      ? 0
      : raw18_19 * rightEncoderForwardSign;
}

void readPhysicalEncoderCounts(
    int32_t& physicalLeft,
    int32_t& physicalRight) {

  int32_t raw18_19;
  int32_t raw25_26;
  readPhysicalEncoderCounts(
      physicalLeft,
      physicalRight,
      raw18_19,
      raw25_26);
}

void printEncoderReport(const String& command) {
  int32_t physicalLeft;
  int32_t physicalRight;
  int32_t raw18_19;
  int32_t raw25_26;

  readPhysicalEncoderCounts(
      physicalLeft,
      physicalRight,
      raw18_19,
      raw25_26);

  String displayCommand = command;
  displayCommand.toLowerCase();

  Serial.println();
  Serial.println("[Encoder reading]");
  Serial.print("source command : ");
  Serial.println(displayCommand);

  Serial.print("left raw       : ");
  Serial.print(raw25_26);
  Serial.print(" pulses (gpio 25/26)");
  if (leftEncoderForwardSign == 0) {
    Serial.println("; forward sign not checked");
  } else {
    Serial.print("; forward pulses = ");
    Serial.println(physicalLeft);
  }

  Serial.print("right raw      : ");
  Serial.print(raw18_19);
  Serial.print(" pulses (gpio 18/19)");
  if (rightEncoderForwardSign == 0) {
    Serial.println("; forward sign not checked");
  } else {
    Serial.print("; forward pulses = ");
    Serial.println(physicalRight);
  }
}

// ============================================================
// 电机底层控制
// ============================================================

void applyOneMotor(
    int requestedSpeed,
    uint8_t pinEnable,
    uint8_t pinA,
    uint8_t pinB,
    bool inverted) {

  int actualSpeed = inverted ? -requestedSpeed : requestedSpeed;

  // 改变方向前先关 PWM。
  analogWrite(pinEnable, 0);

  // Stage 8A 软件整合版本：即使收到运动请求，真实 L298N 输出也始终保持关闭。
  if (!MOTOR_OUTPUTS_ENABLED) {
    digitalWrite(pinA, LOW);
    digitalWrite(pinB, LOW);
    analogWrite(pinEnable, 0);
    return;
  }

  if (actualSpeed > 0) {
    digitalWrite(pinA, HIGH);
    digitalWrite(pinB, LOW);
    analogWrite(pinEnable, actualSpeed);

  } else if (actualSpeed < 0) {
    digitalWrite(pinA, LOW);
    digitalWrite(pinB, HIGH);
    analogWrite(pinEnable, -actualSpeed);

  } else {
    digitalWrite(pinA, LOW);
    digitalWrite(pinB, LOW);
    analogWrite(pinEnable, 0);
  }
}

void setLeftMotor(int speed) {
  commandedLeftSpeed = speed;
  applyOneMotor(
      speed,
      PIN_ENA,
      PIN_IN1,
      PIN_IN2,
      LEFT_MOTOR_INVERTED);
}

void setRightMotor(int speed) {
  commandedRightSpeed = speed;
  applyOneMotor(
      speed,
      PIN_ENB,
      PIN_IN3,
      PIN_IN4,
      RIGHT_MOTOR_INVERTED);
}

void driveMotors(int leftSpeed, int rightSpeed) {
  setLeftMotor(leftSpeed);
  setRightMotor(rightSpeed);
}

void stopMotorOutputsImmediately() {
  driveMotors(0, 0);
}

// ============================================================
// US-100 距离安全状态
// ============================================================

const char* sensorSafetyStateName(SensorSafetyState state) {
  if (state == SensorSafetyState::SENSOR_INVALID_STOP) {
    return "SENSOR_INVALID_STOP";
  }
  if (state == SensorSafetyState::FORCE_STOP) {
    return "FORCE_STOP";
  }
  if (state == SensorSafetyState::CAUTION) {
    return "CAUTION";
  }
  if (state == SensorSafetyState::CLEAR) {
    return "CLEAR";
  }
  return "STARTUP_STOP";
}

bool sensorDataIsOperational() {
  return sensorSafetyState == SensorSafetyState::FORCE_STOP ||
         sensorSafetyState == SensorSafetyState::CAUTION ||
         sensorSafetyState == SensorSafetyState::CLEAR;
}

float medianOfThree(float a, float b, float c) {
  if (a > b) {
    const float temporary = a;
    a = b;
    b = temporary;
  }
  if (b > c) {
    const float temporary = b;
    b = c;
    c = temporary;
  }
  if (a > b) {
    const float temporary = a;
    a = b;
    b = temporary;
  }
  return b;
}

float filteredDistanceCm() {
  if (distanceWindowCount < 3) {
    return lastDistanceCm;
  }
  return medianOfThree(
      distanceWindow[0],
      distanceWindow[1],
      distanceWindow[2]);
}

void printSensorStateChange(
    SensorSafetyState previousState,
    SensorSafetyState newState) {

  if (previousState == newState) {
    return;
  }

  Serial.println();
  Serial.println("[US-100 safety state changed]");
  Serial.print("previous        : ");
  Serial.println(sensorSafetyStateName(previousState));
  Serial.print("current         : ");
  Serial.println(sensorSafetyStateName(newState));
  Serial.print("distance        : ");
  if (isfinite(lastDistanceCm)) {
    Serial.print(lastDistanceCm, 2);
    Serial.println(" cm");
  } else {
    Serial.println("invalid");
  }
  Serial.print("motor action    : ");
  if (newState == SensorSafetyState::SENSOR_INVALID_STOP ||
      newState == SensorSafetyState::STARTUP_STOP) {
    Serial.println("all motion blocked");
  } else if (newState == SensorSafetyState::FORCE_STOP) {
    Serial.println("forward blocked");
  } else if (newState == SensorSafetyState::CAUTION) {
    Serial.println("forward PWM limited to 100");
  } else {
    Serial.println("normal limited motion allowed after ARM");
  }
}

bool updateUs100Safety(bool forceSample) {
  const unsigned long now = millis();
  if (!forceSample &&
      now - lastSensorSampleMs < US100_SAMPLE_INTERVAL_MS) {
    return false;
  }
  lastSensorSampleMs = now;

  digitalWrite(PIN_US100_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_US100_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_US100_TRIG, LOW);

  const unsigned long durationUs = pulseIn(
      PIN_US100_ECHO,
      HIGH,
      US100_ECHO_TIMEOUT_US);

  lastEchoDurationUs = durationUs;
  const float measuredDistanceCm =
      static_cast<float>(durationUs) * 0.0343f * 0.5f;

  const bool valid =
      durationUs > 0 &&
      measuredDistanceCm >= US100_MIN_VALID_CM &&
      measuredDistanceCm <= US100_MAX_VALID_CM;

  const SensorSafetyState previousState = sensorSafetyState;

  if (!valid) {
    lastDistanceCm = NAN;
    consecutiveValidSensorSamples = 0;
    distanceWindowCount = 0;
    distanceWindowIndex = 0;
    ++totalInvalidSensorSamples;
    sensorSafetyState = SensorSafetyState::SENSOR_INVALID_STOP;
    printSensorStateChange(previousState, sensorSafetyState);
    return true;
  }

  lastDistanceCm = measuredDistanceCm;
  ++totalValidSensorSamples;
  if (consecutiveValidSensorSamples < 255) {
    ++consecutiveValidSensorSamples;
  }

  distanceWindow[distanceWindowIndex] = measuredDistanceCm;
  distanceWindowIndex = (distanceWindowIndex + 1) % 3;
  if (distanceWindowCount < 3) {
    ++distanceWindowCount;
  }

  // 单次可靠近距数据立即进入 FORCE_STOP，不等待滤波窗口填满。
  if (measuredDistanceCm < FORCE_STOP_ENTER_CM) {
    sensorSafetyState = SensorSafetyState::FORCE_STOP;
    printSensorStateChange(previousState, sensorSafetyState);
    return true;
  }

  // 无效数据恢复后必须重新获得连续3次有效读数。
  if (consecutiveValidSensorSamples < US100_VALID_SAMPLES_REQUIRED ||
      distanceWindowCount < 3) {
    sensorSafetyState = SensorSafetyState::STARTUP_STOP;
    printSensorStateChange(previousState, sensorSafetyState);
    return true;
  }

  const float filteredCm = filteredDistanceCm();

  if (previousState == SensorSafetyState::FORCE_STOP) {
    if (filteredCm < FORCE_STOP_RELEASE_CM) {
      sensorSafetyState = SensorSafetyState::FORCE_STOP;
    } else if (filteredCm <= CAUTION_ENTER_CM) {
      sensorSafetyState = SensorSafetyState::CAUTION;
    } else {
      sensorSafetyState = SensorSafetyState::CLEAR;
    }

  } else if (previousState == SensorSafetyState::CAUTION) {
    if (filteredCm < FORCE_STOP_ENTER_CM) {
      sensorSafetyState = SensorSafetyState::FORCE_STOP;
    } else if (filteredCm < CLEAR_RELEASE_CM) {
      sensorSafetyState = SensorSafetyState::CAUTION;
    } else {
      sensorSafetyState = SensorSafetyState::CLEAR;
    }

  } else {
    sensorSafetyState =
        (filteredCm <= CAUTION_ENTER_CM)
            ? SensorSafetyState::CAUTION
            : SensorSafetyState::CLEAR;
  }

  printSensorStateChange(previousState, sensorSafetyState);
  return true;
}

void printDistanceReport() {
  Serial.println();
  Serial.println("[US-100 distance report]");
  Serial.print("state           : ");
  Serial.println(sensorSafetyStateName(sensorSafetyState));
  Serial.print("latest          : ");
  if (isfinite(lastDistanceCm)) {
    Serial.print(lastDistanceCm, 2);
    Serial.println(" cm");
  } else {
    Serial.println("invalid");
  }
  Serial.print("filtered        : ");
  if (distanceWindowCount > 0 && isfinite(filteredDistanceCm())) {
    Serial.print(filteredDistanceCm(), 2);
    Serial.println(" cm");
  } else {
    Serial.println("unavailable");
  }
  Serial.print("echo duration   : ");
  Serial.print(lastEchoDurationUs);
  Serial.println(" us");
  Serial.print("valid total     : ");
  Serial.println(totalValidSensorSamples);
  Serial.print("invalid total   : ");
  Serial.println(totalInvalidSensorSamples);
  Serial.print("consecutive valid: ");
  Serial.println(consecutiveValidSensorSamples);
}

// ============================================================
// 状态和报告
// ============================================================

const char* motionModeName(MotionMode mode) {
  if (mode == MotionMode::TIMED) {
    return "timed motion";
  }

  if (mode == MotionMode::TARGET) {
    return "target motion";
  }

  if (mode == MotionMode::ENCODER_CHECK) {
    return "encoder check";
  }

  return "none";
}

void clearMotionState() {
  moving = false;
  motionMode = MotionMode::NONE;
  activeCommand = "NONE";
  timedStopDeadline = 0;
  targetStartMs = 0;
  activeCheckWheel = CheckWheel::NONE;

  leftTargetPulses = 0;
  rightTargetPulses = 0;
  leftTargetActive = false;
  rightTargetActive = false;
  leftTargetDone = false;
  rightTargetDone = false;

  leftBestProgress = 0;
  rightBestProgress = 0;
  leftLastProgressMs = 0;
  rightLastProgressMs = 0;
}

const char* friendlyStopReason(const char* reason) {
  if (strcmp(reason, "TARGET_COMPLETE") == 0) {
    return "Target reached normally.";
  }
  if (strcmp(reason, "ACTION_COMPLETE") == 0) {
    return "Timed motion finished normally.";
  }
  if (strcmp(reason, "USER_STOP") == 0) {
    return "Stopped by the user.";
  }
  if (strcmp(reason, "STALL_LEFT") == 0) {
    return "Left forward pulse count did not increase for 700 ms.";
  }
  if (strcmp(reason, "STALL_RIGHT") == 0) {
    return "Right forward pulse count did not increase for 700 ms.";
  }
  if (strcmp(reason, "ENCODER_SPIKE_LEFT") == 0) {
    return "Left encoder count changed beyond the safe limit.";
  }
  if (strcmp(reason, "ENCODER_SPIKE_RIGHT") == 0) {
    return "Right encoder count changed beyond the safe limit.";
  }
  if (strcmp(reason, "TARGET_TIMEOUT") == 0) {
    return "The target was not completed within 12 seconds.";
  }
  if (strcmp(reason, "BOOT_DEFAULT") == 0) {
    return "Safe stop after startup.";
  }
  if (strcmp(reason, "SENSOR_INVALID_STOP") == 0) {
    return "US-100 data became invalid; all motion was stopped.";
  }
  if (strcmp(reason, "SENSOR_STARTUP_STOP") == 0) {
    return "US-100 has not produced three consecutive valid readings.";
  }
  if (strcmp(reason, "OBSTACLE_FORCE_STOP") == 0) {
    return "The forward obstacle distance entered FORCE_STOP.";
  }
  return "Motion stopped by a safety or command rule.";
}

const char* resultForReason(const char* reason) {
  if (!MOTOR_OUTPUTS_ENABLED &&
      strcmp(reason, "ACTION_COMPLETE") == 0) {
    return "logic completed; motor outputs disabled";
  }
  if (strcmp(reason, "TARGET_COMPLETE") == 0 ||
      strcmp(reason, "ACTION_COMPLETE") == 0) {
    return "passed";
  }
  if (strcmp(reason, "USER_STOP") == 0) {
    return "stopped by user";
  }
  return "not passed";
}

void printTargetResult(
    const String& command,
    int32_t leftTarget,
    int32_t rightTarget,
    int32_t finalLeft,
    int32_t finalRight) {

  String displayCommand = command;
  displayCommand.toLowerCase();

  Serial.println();
  Serial.println("[Target result]");
  Serial.print("command         : ");
  Serial.println(displayCommand);

  if (leftTarget > 0) {
    const int32_t leftError = finalLeft - leftTarget;
    const float leftErrorPercent =
        100.0f * static_cast<float>(leftError) /
        static_cast<float>(leftTarget);

    Serial.print("left progress   : ");
    Serial.print(finalLeft);
    Serial.print(" / ");
    Serial.print(leftTarget);
    Serial.println(" pulses");
    Serial.print("left error      : ");
    Serial.print(leftError);
    Serial.print(" pulses (");
    Serial.print(leftErrorPercent, 2);
    Serial.println("%)");
  }

  if (rightTarget > 0) {
    const int32_t rightError = finalRight - rightTarget;
    const float rightErrorPercent =
        100.0f * static_cast<float>(rightError) /
        static_cast<float>(rightTarget);

    Serial.print("right progress  : ");
    Serial.print(finalRight);
    Serial.print(" / ");
    Serial.print(rightTarget);
    Serial.println(" pulses");
    Serial.print("right error     : ");
    Serial.print(rightError);
    Serial.print(" pulses (");
    Serial.print(rightErrorPercent, 2);
    Serial.println("%)");
  }
}

void finishMotion(const char* reason, bool disarmSystem) {
  const bool wasMoving = moving;
  const String finishedCommand = activeCommand;
  const MotionMode finishedMode = motionMode;
  const int32_t finishedLeftTarget = leftTargetPulses;
  const int32_t finishedRightTarget = rightTargetPulses;

  // 安全动作的第一步永远是立即关闭两个电机。
  stopMotorOutputsImmediately();
  moving = false;

  // 电机已经关闭；等待是为了把惯性滑行计入最终脉冲。
  if (wasMoving) {
    delay(FINAL_SETTLE_MS);
  }

  if (disarmSystem) {
    armed = false;
  }

  int32_t finalLeft;
  int32_t finalRight;
  readPhysicalEncoderCounts(finalLeft, finalRight);

  String reasonCode = String(reason);
  reasonCode.toLowerCase();

  String displayCommand = finishedCommand;
  displayCommand.toLowerCase();

  Serial.println();
  Serial.println("========================================");
  Serial.println("[Motion finished]");
  Serial.print("result          : ");
  Serial.println(resultForReason(reason));
  Serial.print("reason          : ");
  Serial.println(friendlyStopReason(reason));
  Serial.print("reason code     : ");
  Serial.println(reasonCode);
  Serial.print("command         : ");
  Serial.println(displayCommand);
  Serial.print("safety          : ");
  Serial.println(armed ? "armed" : "disarmed");

  if (wasMoving) {
    printEncoderReport(finishedCommand);

    if (finishedMode == MotionMode::TARGET) {
      printTargetResult(
          finishedCommand,
          finishedLeftTarget,
          finishedRightTarget,
          finalLeft,
          finalRight);
    }
  }

  if (strcmp(reason, "STALL_LEFT") == 0 ||
      strcmp(reason, "STALL_RIGHT") == 0) {
    Serial.println("next            : stop target tests; run the encoder check again");
  } else if (strcmp(reason, "TARGET_COMPLETE") == 0) {
    Serial.println("next            : record the result; arm again before another motion");
  } else if (strcmp(reason, "USER_STOP") == 0) {
    Serial.println("next            : arm again only if another test is needed");
  }
  Serial.println("========================================");

  clearMotionState();
}

bool hasForwardComponent(int leftSpeed, int rightSpeed) {
  return leftSpeed > 0 || rightSpeed > 0;
}

void blockNewMotionForSensor(const char* reason) {
  stopMotorOutputsImmediately();
  armed = false;
  clearMotionState();

  Serial.println();
  Serial.println("[Motion blocked by US-100]");
  Serial.print("reason code     : ");
  String reasonCode = String(reason);
  reasonCode.toLowerCase();
  Serial.println(reasonCode);
  Serial.print("sensor state    : ");
  Serial.println(sensorSafetyStateName(sensorSafetyState));
  Serial.print("distance        : ");
  if (isfinite(lastDistanceCm)) {
    Serial.print(lastDistanceCm, 2);
    Serial.println(" cm");
  } else {
    Serial.println("invalid");
  }
  Serial.println("safety          : disarmed");
  Serial.println("next            : restore a safe valid reading, then send 'arm' again");
}

bool prepareRequestedMotion(
    int& leftSpeed,
    int& rightSpeed) {

  updateUs100Safety(true);

  if (sensorSafetyState == SensorSafetyState::SENSOR_INVALID_STOP) {
    blockNewMotionForSensor("SENSOR_INVALID_STOP");
    return false;
  }

  if (sensorSafetyState == SensorSafetyState::STARTUP_STOP) {
    blockNewMotionForSensor("SENSOR_STARTUP_STOP");
    return false;
  }

  if (hasForwardComponent(leftSpeed, rightSpeed) &&
      sensorSafetyState == SensorSafetyState::FORCE_STOP) {
    blockNewMotionForSensor("OBSTACLE_FORCE_STOP");
    return false;
  }

  if (hasForwardComponent(leftSpeed, rightSpeed) &&
      sensorSafetyState == SensorSafetyState::CAUTION) {
    if (leftSpeed > CAUTION_FORWARD_PWM) {
      leftSpeed = CAUTION_FORWARD_PWM;
    }
    if (rightSpeed > CAUTION_FORWARD_PWM) {
      rightSpeed = CAUTION_FORWARD_PWM;
    }
    Serial.println();
    Serial.println("[US-100 caution speed limit]");
    Serial.println("forward PWM     : limited to 100");
    Serial.println("automatic speed-up after recovery: disabled");
  }

  return true;
}

void enforceSensorSafetyDuringMotion() {
  if (!moving) {
    return;
  }

  if (sensorSafetyState == SensorSafetyState::SENSOR_INVALID_STOP) {
    finishMotion("SENSOR_INVALID_STOP", true);
    return;
  }

  if (sensorSafetyState == SensorSafetyState::STARTUP_STOP) {
    finishMotion("SENSOR_STARTUP_STOP", true);
    return;
  }

  if (sensorSafetyState == SensorSafetyState::FORCE_STOP &&
      hasForwardComponent(commandedLeftSpeed, commandedRightSpeed)) {
    finishMotion("OBSTACLE_FORCE_STOP", true);
    return;
  }

  if (sensorSafetyState == SensorSafetyState::CAUTION &&
      hasForwardComponent(commandedLeftSpeed, commandedRightSpeed)) {
    int safeLeft = commandedLeftSpeed;
    int safeRight = commandedRightSpeed;

    if (safeLeft > CAUTION_FORWARD_PWM) {
      safeLeft = CAUTION_FORWARD_PWM;
    }
    if (safeRight > CAUTION_FORWARD_PWM) {
      safeRight = CAUTION_FORWARD_PWM;
    }

    if (safeLeft != commandedLeftSpeed ||
        safeRight != commandedRightSpeed) {
      driveMotors(safeLeft, safeRight);
      Serial.println();
      Serial.println("[US-100 runtime slowdown]");
      Serial.println("reason          : obstacle entered CAUTION range");
      Serial.println("forward PWM     : limited to 100");
      Serial.println("speed recovery  : requires a new command after this motion");
    }
  }
}

void printStatus() {
  int32_t physicalLeft;
  int32_t physicalRight;
  readPhysicalEncoderCounts(physicalLeft, physicalRight);

  String displayCommand = activeCommand;
  displayCommand.toLowerCase();

  Serial.println();
  Serial.println("[Current status]");
  Serial.print("safety          : ");
  Serial.println(armed ? "armed" : "disarmed");
  Serial.print("motors          : ");
  Serial.println(moving ? "moving" : "stopped");
  Serial.print("mode            : ");
  Serial.println(motionModeName(motionMode));
  Serial.print("active command  : ");
  Serial.println(displayCommand);
  Serial.print("motor outputs   : ");
  Serial.println(MOTOR_OUTPUTS_ENABLED ? "enabled" : "DISABLED (Stage 8A safe mode)");
  Serial.print("requested speed : left ");
  Serial.print(commandedLeftSpeed);
  Serial.print(", right ");
  Serial.println(commandedRightSpeed);
  Serial.print("US-100 state    : ");
  Serial.println(sensorSafetyStateName(sensorSafetyState));
  Serial.print("US-100 distance : ");
  if (isfinite(lastDistanceCm)) {
    Serial.print(lastDistanceCm, 2);
    Serial.println(" cm");
  } else {
    Serial.println("invalid");
  }
  Serial.print("left check      : ");
  Serial.println(leftEncoderForwardSign == 0 ? "not completed" : "completed");
  Serial.print("right check     : ");
  Serial.println(rightEncoderForwardSign == 0 ? "not completed" : "completed");
  Serial.print("target commands : ");
  Serial.println(
      leftEncoderForwardSign != 0 && rightEncoderForwardSign != 0
          ? "ready"
          : "locked until required encoder checks pass");
}

void printConfig() {
  Serial.println();
  Serial.println("[Configuration]");
  Serial.println("version         : Atlas 8A sensor safety v1");
  Serial.print("motor outputs   : ");
  Serial.println(MOTOR_OUTPUTS_ENABLED ? "enabled" : "disabled for software integration");
  Serial.print("wheel distance  : ");
  Serial.print(WHEEL_CIRCUMFERENCE_CM, 2);
  Serial.println(" cm per revolution");
  Serial.print("left PPR        : ");
  Serial.println(LEFT_PULSES_PER_REV, 2);
  Serial.print("right PPR       : ");
  Serial.println(RIGHT_PULSES_PER_REV, 2);
  Serial.print("target PWM      : left ");
  Serial.print(LEFT_TARGET_PWM);
  Serial.print(", right ");
  Serial.println(RIGHT_TARGET_PWM);
  Serial.println("motor direction : left inverted, right normal");
  Serial.println("encoder mapping : left gpio 25/26, right gpio 18/19");
  Serial.println("US-100 mapping  : trig gpio 27, echo gpio 34");
  Serial.println("US-100 thresholds: <25 stop, 25-50 caution, >50 clear");
  Serial.println("clear hysteresis: caution -> clear at 55 cm");
  Serial.println("caution PWM cap : 100 forward");
  Serial.print("left sign       : ");
  if (leftEncoderForwardSign == 0) {
    Serial.println("not checked");
  } else {
    Serial.println(leftEncoderForwardSign);
  }
  Serial.print("right sign      : ");
  if (rightEncoderForwardSign == 0) {
    Serial.println("not checked");
  } else {
    Serial.println(rightEncoderForwardSign);
  }
  Serial.print("stall timeout   : ");
  Serial.print(STALL_TIMEOUT_MS);
  Serial.println(" ms");
  Serial.print("total timeout   : ");
  Serial.print(TARGET_TOTAL_TIMEOUT_MS);
  Serial.println(" ms");
}

void printHelp() {
  Serial.println();
  Serial.println("[Command guide]");
  Serial.println("Safety and information:");
  Serial.println("  arm                 allow one limited motion");
  Serial.println("  stop                stop immediately and disarm");
  Serial.println("  status              show current state");
  Serial.println("  config              show parameters and learned signs");
  Serial.println("  help                show this guide");
  Serial.println("  zero                reset encoder counts");
  Serial.println("  enc                 show readable encoder values");
  Serial.println("  uncal               clear learned encoder signs");
  Serial.println("  dist                show US-100 state and readings");
  Serial.println();
  Serial.println("Stage 8A software test (motor outputs are disabled):");
  Serial.println("  wait for CLEAR/CAUTION, then use arm + f 160 1000");
  Serial.println("  move an object into CAUTION/FORCE_STOP while the timer is active");
  Serial.println();
  Serial.println("Required checks in the later motor-enabled Stage 8B file:");
  Serial.println("  arm  then  check left");
  Serial.println("  arm  then  check right");
  Serial.println();
  Serial.println("Target motion, only after the required checks:");
  Serial.println("  arm  then  testl 100");
  Serial.println("  arm  then  testr 100");
  Serial.println("  arm  then  fd 5");
  Serial.println();
  Serial.println("Short timed motion:");
  Serial.println("  f / b / tl / tr / lf / lb / rf / rb  PWM  time_ms");
  Serial.println("  example: arm  then  lf 160 200");
  Serial.println();
  Serial.println("Input is not case-sensitive. Lowercase is recommended.");
}

// ============================================================
// 参数解析
// ============================================================

bool parseLongStrict(const char* text, long& value) {
  if (text == nullptr || *text == '\0') {
    return false;
  }

  char* endPointer = nullptr;
  const long parsed = strtol(text, &endPointer, 10);

  if (endPointer == text || *endPointer != '\0') {
    return false;
  }

  value = parsed;
  return true;
}

bool parseFloatStrict(const char* text, float& value) {
  if (text == nullptr || *text == '\0') {
    return false;
  }

  char* endPointer = nullptr;
  const float parsed = strtof(text, &endPointer);

  if (endPointer == text || *endPointer != '\0' || !isfinite(parsed)) {
    return false;
  }

  value = parsed;
  return true;
}

bool isTimedMotionCommand(const String& command) {
  return command == "F"  ||
         command == "B"  ||
         command == "TL" ||
         command == "TR" ||
         command == "LF" ||
         command == "LB" ||
         command == "RF" ||
         command == "RB";
}

bool motionStartAllowed() {
  if (moving) {
    finishMotion("MOTION_ALREADY_ACTIVE", true);
    Serial.println("Error: another motion was already active. The system is now disarmed.");
    return false;
  }

  if (!armed) {
    stopMotorOutputsImmediately();
    Serial.println();
    Serial.println("[Command blocked]");
    Serial.println("reason          : the system is not armed");
    Serial.println("next            : send 'arm', wait for Ready, then send one motion command");
    return false;
  }

  return true;
}

// ============================================================
// 运动启动函数
// ============================================================

void startTimedMotion(
    const String& command,
    int pwm,
    unsigned long durationMs) {

  if (!motionStartAllowed()) {
    return;
  }

  if (pwm < MIN_PWM || pwm > MAX_PWM) {
    finishMotion("INVALID_PWM", true);
    Serial.print("Error: PWM must be between ");
    Serial.print(MIN_PWM);
    Serial.print(" and ");
    Serial.println(MAX_PWM);
    return;
  }

  if (durationMs < MIN_DURATION_MS ||
      durationMs > MAX_DURATION_MS) {
    finishMotion("INVALID_DURATION", true);
    Serial.print("Error: duration must be between ");
    Serial.print(MIN_DURATION_MS);
    Serial.print(" and ");
    Serial.print(MAX_DURATION_MS);
    Serial.println(" ms");
    return;
  }

  int leftSpeed = 0;
  int rightSpeed = 0;

  if (command == "F") {
    leftSpeed = pwm;
    rightSpeed = pwm;
  } else if (command == "B") {
    leftSpeed = -pwm;
    rightSpeed = -pwm;
  } else if (command == "TL") {
    leftSpeed = -pwm;
    rightSpeed = pwm;
  } else if (command == "TR") {
    leftSpeed = pwm;
    rightSpeed = -pwm;
  } else if (command == "LF") {
    leftSpeed = pwm;
  } else if (command == "LB") {
    leftSpeed = -pwm;
  } else if (command == "RF") {
    rightSpeed = pwm;
  } else if (command == "RB") {
    rightSpeed = -pwm;
  }

  if (!prepareRequestedMotion(leftSpeed, rightSpeed)) {
    return;
  }

  resetEncoderCounts();

  activeCommand = command;
  motionMode = MotionMode::TIMED;
  moving = true;
  timedStopDeadline = millis() + durationMs;

  driveMotors(leftSpeed, rightSpeed);

  String displayCommand = command;
  displayCommand.toLowerCase();

  Serial.println();
  Serial.println("[Motion started]");
  Serial.println("mode            : timed motion");
  Serial.print("command         : ");
  Serial.println(displayCommand);
  Serial.print("motor command   : left ");
  Serial.print(leftSpeed);
  Serial.print(", right ");
  Serial.println(rightSpeed);
  Serial.print("duration        : ");
  Serial.print(durationMs);
  Serial.println(" ms");
}

void startEncoderCheck(CheckWheel wheel) {
  if (!MOTOR_OUTPUTS_ENABLED) {
    stopMotorOutputsImmediately();
    armed = false;
    Serial.println();
    Serial.println("[Encoder check blocked]");
    Serial.println("reason          : Stage 8A motor outputs are intentionally disabled");
    Serial.println("next            : use Stage 8A timed commands only for safety-logic testing");
    return;
  }

  if (!motionStartAllowed()) {
    return;
  }

  int requestedLeftSpeed =
      (wheel == CheckWheel::LEFT) ? ENCODER_CHECK_PWM : 0;
  int requestedRightSpeed =
      (wheel == CheckWheel::RIGHT) ? ENCODER_CHECK_PWM : 0;

  if (!prepareRequestedMotion(requestedLeftSpeed, requestedRightSpeed)) {
    return;
  }

  resetEncoderCounts();

  activeCheckWheel = wheel;
  activeCommand = (wheel == CheckWheel::LEFT) ? "check left" : "check right";
  motionMode = MotionMode::ENCODER_CHECK;
  moving = true;
  timedStopDeadline = millis() + ENCODER_CHECK_DURATION_MS;

  driveMotors(requestedLeftSpeed, requestedRightSpeed);

  Serial.println();
  Serial.println("[Encoder check started]");
  Serial.print("wheel           : ");
  Serial.println(wheel == CheckWheel::LEFT ? "left" : "right");
  Serial.print("duration        : ");
  Serial.print(ENCODER_CHECK_DURATION_MS);
  Serial.println(" ms");
  Serial.println("watch           : this wheel must move toward the robot's front");
}

void finishEncoderCheck() {
  const CheckWheel checkedWheel = activeCheckWheel;

  stopMotorOutputsImmediately();
  moving = false;
  delay(100);
  armed = false;

  int32_t raw18_19;
  int32_t raw25_26;
  readRawEncoderCounts(raw18_19, raw25_26);

  const int32_t activeRaw =
      (checkedWheel == CheckWheel::LEFT) ? raw25_26 : raw18_19;
  const int32_t inactiveRaw =
      (checkedWheel == CheckWheel::LEFT) ? raw18_19 : raw25_26;

  const int32_t activeMagnitude = labs(activeRaw);
  const int32_t inactiveMagnitude = labs(inactiveRaw);
  const int32_t inactiveLimit =
      (activeMagnitude / 5 > 10) ? activeMagnitude / 5 : 10;

  const bool enoughPulses = activeMagnitude >= MIN_ENCODER_CHECK_PULSES;
  const bool inactiveIsQuiet = inactiveMagnitude <= inactiveLimit;
  const bool checkPassed = enoughPulses && inactiveIsQuiet;

  if (checkPassed) {
    const int8_t learnedSign = (activeRaw > 0) ? 1 : -1;
    if (checkedWheel == CheckWheel::LEFT) {
      leftEncoderForwardSign = learnedSign;
    } else {
      rightEncoderForwardSign = learnedSign;
    }
  } else {
    if (checkedWheel == CheckWheel::LEFT) {
      leftEncoderForwardSign = 0;
    } else {
      rightEncoderForwardSign = 0;
    }
  }

  Serial.println();
  Serial.println("========================================");
  Serial.println("[Encoder check finished]");
  Serial.print("wheel           : ");
  Serial.println(checkedWheel == CheckWheel::LEFT ? "left" : "right");
  Serial.print("result          : ");
  Serial.println(checkPassed ? "pulse check passed" : "pulse check not passed");
  Serial.print("active raw      : ");
  Serial.print(activeRaw);
  Serial.println(" pulses");
  Serial.print("other raw       : ");
  Serial.print(inactiveRaw);
  Serial.println(" pulses");

  if (checkPassed) {
    Serial.print("learned sign    : ");
    Serial.println(activeRaw > 0 ? "+1" : "-1");
    Serial.println("visual decision : continue only if this wheel moved forward");
    Serial.println("next            : arm and check the other wheel");
  } else if (!enoughPulses) {
    Serial.println("reason          : too few pulses from the active encoder");
    Serial.println("next            : stop testing and inspect encoder power/signal connections");
  } else {
    Serial.println("reason          : the inactive encoder also changed too much");
    Serial.println("next            : stop testing and inspect mapping or electrical noise");
  }

  Serial.println("safety          : disarmed");
  Serial.println("========================================");
  clearMotionState();
}

void startTargetMotion(
    const String& command,
    int32_t requestedLeftTarget,
    int32_t requestedRightTarget) {

  if (!MOTOR_OUTPUTS_ENABLED) {
    stopMotorOutputsImmediately();
    armed = false;
    Serial.println();
    Serial.println("[Target motion blocked]");
    Serial.println("reason          : Stage 8A motor outputs are intentionally disabled");
    Serial.println("next            : validate US-100 logic with timed commands first");
    return;
  }

  if (!motionStartAllowed()) {
    return;
  }

  if (requestedLeftTarget <= 0 && requestedRightTarget <= 0) {
    finishMotion("INVALID_TARGET", true);
    Serial.println("Error: at least one target must be positive.");
    return;
  }

  if (requestedLeftTarget > 0 && leftEncoderForwardSign == 0) {
    stopMotorOutputsImmediately();
    armed = false;
    Serial.println();
    Serial.println("[Target command blocked]");
    Serial.println("reason          : left encoder sign has not been checked");
    Serial.println("next            : arm, then send 'check left'");
    return;
  }

  if (requestedRightTarget > 0 && rightEncoderForwardSign == 0) {
    stopMotorOutputsImmediately();
    armed = false;
    Serial.println();
    Serial.println("[Target command blocked]");
    Serial.println("reason          : right encoder sign has not been checked");
    Serial.println("next            : arm, then send 'check right'");
    return;
  }

  int requestedLeftSpeed =
      requestedLeftTarget > 0 ? LEFT_TARGET_PWM : 0;
  int requestedRightSpeed =
      requestedRightTarget > 0 ? RIGHT_TARGET_PWM : 0;

  if (!prepareRequestedMotion(requestedLeftSpeed, requestedRightSpeed)) {
    return;
  }

  resetEncoderCounts();

  const unsigned long now = millis();

  activeCommand = command;
  motionMode = MotionMode::TARGET;
  moving = true;
  targetStartMs = now;

  leftTargetPulses = requestedLeftTarget;
  rightTargetPulses = requestedRightTarget;

  leftTargetActive = requestedLeftTarget > 0;
  rightTargetActive = requestedRightTarget > 0;
  leftTargetDone = !leftTargetActive;
  rightTargetDone = !rightTargetActive;

  leftBestProgress = 0;
  rightBestProgress = 0;
  leftLastProgressMs = now;
  rightLastProgressMs = now;

  driveMotors(requestedLeftSpeed, requestedRightSpeed);

  String displayCommand = command;
  displayCommand.toLowerCase();

  Serial.println();
  Serial.println("[Motion started]");
  Serial.println("mode            : target motion");
  Serial.print("command         : ");
  Serial.println(displayCommand);
  Serial.print("left target     : ");
  if (leftTargetActive) {
    Serial.print(leftTargetPulses);
    Serial.print(" pulses at PWM ");
    Serial.println(requestedLeftSpeed);
  } else {
    Serial.println("not used");
  }
  Serial.print("right target    : ");
  if (rightTargetActive) {
    Serial.print(rightTargetPulses);
    Serial.print(" pulses at PWM ");
    Serial.println(requestedRightSpeed);
  } else {
    Serial.println("not used");
  }
}

// ============================================================
// Stage 6C 目标运动监控
// ============================================================

int32_t spikeMarginForTarget(int32_t target) {
  const int32_t twentyPercent = target / 5;
  return (twentyPercent > MIN_SPIKE_MARGIN_PULSES)
      ? twentyPercent
      : MIN_SPIKE_MARGIN_PULSES;
}

bool pulseCountIsImplausible(int32_t count, int32_t target) {
  const int32_t limit = target + spikeMarginForTarget(target);
  return count > limit || count < -limit;
}

void monitorTargetMotion() {
  if (!moving || motionMode != MotionMode::TARGET) {
    return;
  }

  const unsigned long now = millis();
  int32_t physicalLeft;
  int32_t physicalRight;
  readPhysicalEncoderCounts(physicalLeft, physicalRight);

  // 先检查异常脉冲，再检查是否到达目标，避免假脉冲被误判为完成。
  if (leftTargetActive && !leftTargetDone &&
      pulseCountIsImplausible(physicalLeft, leftTargetPulses)) {
    finishMotion("ENCODER_SPIKE_LEFT", true);
    return;
  }

  if (rightTargetActive && !rightTargetDone &&
      pulseCountIsImplausible(physicalRight, rightTargetPulses)) {
    finishMotion("ENCODER_SPIKE_RIGHT", true);
    return;
  }

  if (leftTargetActive && !leftTargetDone) {
    if (physicalLeft >= leftTargetPulses) {
      setLeftMotor(0);
      leftTargetDone = true;
      Serial.println();
      Serial.println("[Wheel target reached]");
      Serial.println("wheel           : left");
      Serial.print("count at stop   : ");
      Serial.print(physicalLeft);
      Serial.print(" / ");
      Serial.println(leftTargetPulses);

    } else {
      if (physicalLeft > leftBestProgress) {
        leftBestProgress = physicalLeft;
        leftLastProgressMs = now;
      }

      if (now - leftLastProgressMs >= STALL_TIMEOUT_MS) {
        finishMotion("STALL_LEFT", true);
        return;
      }
    }
  }

  if (rightTargetActive && !rightTargetDone) {
    if (physicalRight >= rightTargetPulses) {
      setRightMotor(0);
      rightTargetDone = true;
      Serial.println();
      Serial.println("[Wheel target reached]");
      Serial.println("wheel           : right");
      Serial.print("count at stop   : ");
      Serial.print(physicalRight);
      Serial.print(" / ");
      Serial.println(rightTargetPulses);

    } else {
      if (physicalRight > rightBestProgress) {
        rightBestProgress = physicalRight;
        rightLastProgressMs = now;
      }

      if (now - rightLastProgressMs >= STALL_TIMEOUT_MS) {
        finishMotion("STALL_RIGHT", true);
        return;
      }
    }
  }

  if (leftTargetDone && rightTargetDone) {
    finishMotion("TARGET_COMPLETE", true);
    return;
  }

  if (now - targetStartMs >= TARGET_TOTAL_TIMEOUT_MS) {
    finishMotion("TARGET_TIMEOUT", true);
  }
}

// ============================================================
// 命令处理
// ============================================================

void rejectCommand(const char* reason, const String& line) {
  if (moving) {
    finishMotion(reason, true);
  } else {
    stopMotorOutputsImmediately();
    armed = false;
  }

  String reasonCode = String(reason);
  reasonCode.toLowerCase();
  String displayInput = line;
  displayInput.toLowerCase();

  Serial.println();
  Serial.println("[Command rejected]");
  Serial.print("reason code     : ");
  Serial.println(reasonCode);
  Serial.print("input           : ");
  Serial.println(displayInput);
  Serial.println("next            : send 'help' to view the command guide");
}

void processCommand(String line) {
  line.trim();

  if (line.length() == 0) {
    return;
  }

  String receivedLine = line;
  line.toUpperCase();

  Serial.println();
  Serial.print("Received        : ");
  Serial.println(receivedLine);

  // STOP 始终具有最高优先级。
  if (line == "STOP") {
    finishMotion("USER_STOP", true);
    return;
  }

  if (line == "ARM") {
    if (moving) {
      finishMotion("ARM_DURING_MOTION", true);
      Serial.println("Error: 'arm' cannot be sent during motion. Send it again after stopping.");
      return;
    }

    updateUs100Safety(true);
    if (!sensorDataIsOperational()) {
      stopMotorOutputsImmediately();
      armed = false;
      clearMotionState();
      Serial.println();
      Serial.println("[ARM blocked by US-100]");
      Serial.print("sensor state    : ");
      Serial.println(sensorSafetyStateName(sensorSafetyState));
      Serial.println("required        : three consecutive valid readings");
      Serial.println("next            : restore the sensor, wait 1 second, then send 'dist'");
      return;
    }

    stopMotorOutputsImmediately();
    clearMotionState();
    armed = true;
    Serial.println();
    Serial.println("[Ready]");
    Serial.println("safety          : armed for one limited motion");
    Serial.print("sensor state    : ");
    Serial.println(sensorSafetyStateName(sensorSafetyState));
    if (sensorSafetyState == SensorSafetyState::FORCE_STOP) {
      Serial.println("motion limit    : forward blocked; backward-only escape is allowed");
    }
    Serial.println("next            : send one motion command");
    return;
  }

  if (line == "STATUS") {
    printStatus();
    return;
  }

  if (line == "CONFIG") {
    printConfig();
    return;
  }

  if (line == "HELP") {
    printHelp();
    return;
  }

  if (line == "ENC") {
    printEncoderReport("manual request");
    return;
  }

  if (line == "DIST") {
    updateUs100Safety(true);
    printDistanceReport();
    return;
  }

  if (line == "UNCAL") {
    if (moving) {
      Serial.println("Error: learned signs cannot be cleared during motion.");
      return;
    }

    stopMotorOutputsImmediately();
    armed = false;
    leftEncoderForwardSign = 0;
    rightEncoderForwardSign = 0;
    clearMotionState();
    Serial.println();
    Serial.println("[Encoder signs cleared]");
    Serial.println("safety          : disarmed");
    Serial.println("next            : repeat 'arm' + 'check left', then 'arm' + 'check right'");
    return;
  }

  if (line == "ZERO") {
    if (moving) {
      Serial.println("Error: encoder counts cannot be reset during motion.");
      return;
    }

    resetEncoderCounts();
    Serial.println("Encoder counts were reset to zero.");
    return;
  }

  char commandBuffer[12] = {0};
  char argument1[24] = {0};
  char argument2[24] = {0};
  char extraBuffer[12] = {0};

  const int fieldCount = sscanf(
      line.c_str(),
      "%11s %23s %23s %11s",
      commandBuffer,
      argument1,
      argument2,
      extraBuffer);

  String command = String(commandBuffer);
  command.toUpperCase();

  if (command == "CHECK") {
    if (fieldCount != 2) {
      rejectCommand("INVALID_CHECK_FORMAT", line);
      Serial.println("Expected format : check left  OR  check right");
      return;
    }

    String wheelArgument = String(argument1);
    wheelArgument.toUpperCase();

    if (wheelArgument == "LEFT") {
      startEncoderCheck(CheckWheel::LEFT);
    } else if (wheelArgument == "RIGHT") {
      startEncoderCheck(CheckWheel::RIGHT);
    } else {
      rejectCommand("INVALID_CHECK_WHEEL", line);
      Serial.println("Expected wheel  : left or right");
    }
    return;
  }

  if (isTimedMotionCommand(command)) {
    if (fieldCount != 3) {
      rejectCommand("INVALID_TIMED_FORMAT", line);
      Serial.println("Expected format : f 160 1000");
      return;
    }

    long pwmLong;
    long durationLong;

    if (!parseLongStrict(argument1, pwmLong) ||
        !parseLongStrict(argument2, durationLong) ||
        pwmLong < 0 || durationLong < 0) {
      rejectCommand("INVALID_TIMED_NUMBER", line);
      return;
    }

    startTimedMotion(
        command,
        static_cast<int>(pwmLong),
        static_cast<unsigned long>(durationLong));
    return;
  }

  if (command == "TESTL" || command == "TESTR") {
    if (fieldCount != 2) {
      rejectCommand("INVALID_TEST_FORMAT", line);
      Serial.println("Expected format : testl 100");
      return;
    }

    long targetLong;
    if (!parseLongStrict(argument1, targetLong) ||
        targetLong < MIN_TEST_PULSES ||
        targetLong > MAX_TEST_PULSES) {
      rejectCommand("INVALID_TEST_TARGET", line);
      Serial.print("Allowed pulses  : ");
      Serial.print(MIN_TEST_PULSES);
      Serial.print(" to ");
      Serial.println(MAX_TEST_PULSES);
      return;
    }

    if (command == "TESTL") {
      startTargetMotion(command, static_cast<int32_t>(targetLong), 0);
    } else {
      startTargetMotion(command, 0, static_cast<int32_t>(targetLong));
    }
    return;
  }

  if (command == "FD") {
    if (fieldCount != 2) {
      rejectCommand("INVALID_FD_FORMAT", line);
      Serial.println("Expected format : fd 20");
      return;
    }

    float distanceCm;
    if (!parseFloatStrict(argument1, distanceCm) ||
        distanceCm < MIN_DISTANCE_CM ||
        distanceCm > MAX_DISTANCE_CM) {
      rejectCommand("INVALID_DISTANCE", line);
      Serial.print("Allowed distance: ");
      Serial.print(MIN_DISTANCE_CM, 1);
      Serial.print(" to ");
      Serial.print(MAX_DISTANCE_CM, 1);
      Serial.println(" cm");
      return;
    }

    const int32_t calculatedLeftTarget = static_cast<int32_t>(lroundf(
        distanceCm / WHEEL_CIRCUMFERENCE_CM * LEFT_PULSES_PER_REV));

    const int32_t calculatedRightTarget = static_cast<int32_t>(lroundf(
        distanceCm / WHEEL_CIRCUMFERENCE_CM * RIGHT_PULSES_PER_REV));

    Serial.println();
    Serial.println("[Distance plan]");
    Serial.print("distance        : ");
    Serial.print(distanceCm, 2);
    Serial.println(" cm");
    Serial.print("left target     : ");
    Serial.print(calculatedLeftTarget);
    Serial.println(" pulses");
    Serial.print("right target    : ");
    Serial.print(calculatedRightTarget);
    Serial.println(" pulses");

    startTargetMotion(
        command,
        calculatedLeftTarget,
        calculatedRightTarget);
    return;
  }

  rejectCommand("UNKNOWN_COMMAND", line);
}

// ============================================================
// Arduino 主程序
// ============================================================

void setup() {
  pinMode(PIN_US100_TRIG, OUTPUT);
  digitalWrite(PIN_US100_TRIG, LOW);
  pinMode(PIN_US100_ECHO, INPUT);

  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);

  pinMode(PIN_ENB, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);

  stopMotorOutputsImmediately();

  pinMode(PIN_RAW_18_19_A, INPUT_PULLUP);
  pinMode(PIN_RAW_18_19_B, INPUT_PULLUP);
  pinMode(PIN_RAW_25_26_A, INPUT_PULLUP);
  pinMode(PIN_RAW_25_26_B, INPUT_PULLUP);

  resetEncoderCounts();

  attachInterrupt(
      digitalPinToInterrupt(PIN_RAW_18_19_A),
      onRaw18_19A,
      RISING);

  attachInterrupt(
      digitalPinToInterrupt(PIN_RAW_25_26_A),
      onRaw25_26A,
      RISING);

  Serial.begin(115200);
  delay(500);
  serialLine.reserve(96);

  armed = false;
  leftEncoderForwardSign = 0;
  rightEncoderForwardSign = 0;
  sensorSafetyState = SensorSafetyState::STARTUP_STOP;
  lastDistanceCm = NAN;
  lastEchoDurationUs = 0;
  lastSensorSampleMs = 0;
  consecutiveValidSensorSamples = 0;
  totalValidSensorSamples = 0;
  totalInvalidSensorSamples = 0;
  distanceWindowCount = 0;
  distanceWindowIndex = 0;
  clearMotionState();

  Serial.println();
  Serial.println("========================================");
  Serial.println("Atlas 8A sensor safety v1 is ready");
  Serial.println("motors          : stopped");
  Serial.println("motor outputs   : DISABLED by Stage 8A safety lock");
  Serial.println("safety          : disarmed");
  Serial.println("US-100          : trig gpio 27, echo gpio 34");
  Serial.println("sensor startup  : waiting for 3 consecutive valid readings");
  Serial.println("encoder mode    : A rising edge, 1x count");
  Serial.println("left mapping    : gpio 25/26");
  Serial.println("right mapping   : gpio 18/19");
  Serial.println("encoder signs   : not checked after this restart");
  Serial.println("next            : wait 1 second, then send 'dist'");
  Serial.println("help            : send 'help'");
  Serial.println("========================================");
}

void loop() {
  const bool sensorWasSampled = updateUs100Safety(false);
  if (sensorWasSampled) {
    enforceSensorSafetyDuringMotion();
  }

  while (Serial.available() > 0) {
    const char incoming = static_cast<char>(Serial.read());

    if (incoming == '\n' || incoming == '\r') {
      if (serialLine.length() > 0) {
        processCommand(serialLine);
        serialLine = "";
      }

    } else if (incoming >= 32 && incoming <= 126) {
      if (serialLine.length() < 95) {
        serialLine += incoming;

      } else {
        serialLine = "";
        if (moving) {
          finishMotion("SERIAL_LINE_TOO_LONG", true);
        } else {
          stopMotorOutputsImmediately();
          armed = false;
        }
        Serial.println("Error: the serial line was too long. The system is disarmed.");
      }
    }
  }

  if (moving && motionMode == MotionMode::TIMED &&
      static_cast<int32_t>(millis() - timedStopDeadline) >= 0) {
    finishMotion("ACTION_COMPLETE", true);
  }

  if (moving && motionMode == MotionMode::ENCODER_CHECK &&
      static_cast<int32_t>(millis() - timedStopDeadline) >= 0) {
    finishEncoderCheck();
  }

  monitorTargetMotion();
}
