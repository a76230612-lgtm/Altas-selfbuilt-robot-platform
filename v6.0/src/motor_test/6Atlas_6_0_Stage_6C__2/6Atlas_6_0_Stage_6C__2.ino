#include <Arduino.h>
#include <math.h>
#include <stdlib.h>

// ============================================================
// Atlas 6.0 Stage 6C
// ESP32 DEVKIT_C + L298N + 双编码器
//
// 目标：
// 1. 保留 Stage 6A 的全部安全、定时运动和编码器功能。
// 2. 按当前真实接线，显示“物理左轮 / 物理右轮”编码器计数。
// 3. 支持单轮目标脉冲停车和双轮按距离自动停车。
// 4. 左右轮独立到达、独立停止。
// 5. 提供 700 ms 堵转保护、12 s 总超时和异常脉冲保护。
//
// 当前已锁定的编码器映射（信号组保持交换状态）：
//   物理右轮编码器 -> GPIO18 / GPIO19 -> 原始计数 RAW_18_19
//   物理左轮编码器 -> GPIO25 / GPIO26 -> 原始计数 RAW_25_26
//
// 最新带电实测：两个物理轮前进时原始计数均为负数，所以：
//   PHYSICAL_LEFT_PULSES  = -RAW_25_26
//   PHYSICAL_RIGHT_PULSES = -RAW_18_19
//
// 注意：不要再交换编码器线，也不要用 abs() 隐藏方向错误。
// ============================================================

// -------------------- L298N 接线 --------------------
// 物理左电机（L298N A通道）
constexpr uint8_t PIN_ENA = 13;
constexpr uint8_t PIN_IN1 = 14;
constexpr uint8_t PIN_IN2 = 4;

// 物理右电机（L298N B通道）
constexpr uint8_t PIN_ENB = 33;
constexpr uint8_t PIN_IN3 = 32;
constexpr uint8_t PIN_IN4 = 23;

// 当前电机线序已经验证为正确，不反转电机输出。
constexpr bool LEFT_MOTOR_INVERTED  = false;
constexpr bool RIGHT_MOTOR_INVERTED = false;

// -------------------- 编码器接线 --------------------
// 物理右轮编码器信号组
constexpr uint8_t PIN_RAW_18_19_A = 18;
constexpr uint8_t PIN_RAW_18_19_B = 19;

// 物理左轮编码器信号组
constexpr uint8_t PIN_RAW_25_26_A = 25;
constexpr uint8_t PIN_RAW_25_26_B = 26;

// -------------------- Stage 6C 标定参数 --------------------
// 这里的 6.10 cm 必须是轮胎沿地面滚动一整圈的距离，不是轮子直径。
constexpr float WHEEL_CIRCUMFERENCE_CM = 6.10f;
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

// 运行中若计数超过“目标 + max(100, 目标的20%)”，判为异常脉冲。
// 正常情况下，控制循环会在达到目标后的几个脉冲内关断电机。
constexpr int32_t MIN_SPIKE_MARGIN_PULSES = 100;

// -------------------- 运行状态 --------------------
enum class MotionMode : uint8_t {
  NONE,
  TIMED,
  TARGET
};

String serialLine = "";
String activeCommand = "NONE";

bool armed = false;
bool moving = false;
MotionMode motionMode = MotionMode::NONE;

unsigned long timedStopDeadline = 0;
unsigned long targetStartMs = 0;

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

  // 当前硬件实测映射：前进统一显示为正数。
  physicalLeft  = -raw25_26;
  physicalRight = -raw18_19;
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

  Serial.print("ENCODER;CMD=");
  Serial.print(command);
  Serial.print(";PHYSICAL_LEFT_PULSES=");
  Serial.print(physicalLeft);
  Serial.print(";PHYSICAL_RIGHT_PULSES=");
  Serial.print(physicalRight);
  Serial.print(";RAW_18_19=");
  Serial.print(raw18_19);
  Serial.print(";RAW_25_26=");
  Serial.println(raw25_26);
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
  applyOneMotor(
      speed,
      PIN_ENA,
      PIN_IN1,
      PIN_IN2,
      LEFT_MOTOR_INVERTED);
}

void setRightMotor(int speed) {
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
// 状态和报告
// ============================================================

const char* motionModeName(MotionMode mode) {
  if (mode == MotionMode::TIMED) {
    return "TIMED";
  }

  if (mode == MotionMode::TARGET) {
    return "TARGET";
  }

  return "NONE";
}

void clearMotionState() {
  moving = false;
  motionMode = MotionMode::NONE;
  activeCommand = "NONE";
  timedStopDeadline = 0;
  targetStartMs = 0;

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

void printTargetResult(
    const String& command,
    int32_t leftTarget,
    int32_t rightTarget,
    int32_t finalLeft,
    int32_t finalRight) {

  Serial.print("TARGET_RESULT;CMD=");
  Serial.print(command);

  if (leftTarget > 0) {
    const int32_t leftError = finalLeft - leftTarget;
    const float leftErrorPercent =
        100.0f * static_cast<float>(leftError) /
        static_cast<float>(leftTarget);

    Serial.print(";LEFT_TARGET=");
    Serial.print(leftTarget);
    Serial.print(";LEFT_FINAL=");
    Serial.print(finalLeft);
    Serial.print(";LEFT_ERROR=");
    Serial.print(leftError);
    Serial.print(";LEFT_ERROR_PERCENT=");
    Serial.print(leftErrorPercent, 2);
  } else {
    Serial.print(";LEFT_TARGET=NA;LEFT_FINAL=");
    Serial.print(finalLeft);
  }

  if (rightTarget > 0) {
    const int32_t rightError = finalRight - rightTarget;
    const float rightErrorPercent =
        100.0f * static_cast<float>(rightError) /
        static_cast<float>(rightTarget);

    Serial.print(";RIGHT_TARGET=");
    Serial.print(rightTarget);
    Serial.print(";RIGHT_FINAL=");
    Serial.print(finalRight);
    Serial.print(";RIGHT_ERROR=");
    Serial.print(rightError);
    Serial.print(";RIGHT_ERROR_PERCENT=");
    Serial.print(rightErrorPercent, 2);
  } else {
    Serial.print(";RIGHT_TARGET=NA;RIGHT_FINAL=");
    Serial.print(finalRight);
  }

  Serial.println();
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

  Serial.print("STOPPED;REASON=");
  Serial.print(reason);
  Serial.print(";ARMED=");
  Serial.println(armed ? "YES" : "NO");

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

  clearMotionState();
}

void printStatus() {
  int32_t physicalLeft;
  int32_t physicalRight;
  readPhysicalEncoderCounts(physicalLeft, physicalRight);

  Serial.print("STATUS;ARMED=");
  Serial.print(armed ? "YES" : "NO");
  Serial.print(";MOVING=");
  Serial.print(moving ? "YES" : "NO");
  Serial.print(";MODE=");
  Serial.print(motionModeName(motionMode));
  Serial.print(";ACTIVE_COMMAND=");
  Serial.print(activeCommand);
  Serial.print(";PHYSICAL_LEFT_PULSES=");
  Serial.print(physicalLeft);
  Serial.print(";PHYSICAL_RIGHT_PULSES=");
  Serial.print(physicalRight);
  Serial.print(";LEFT_TARGET=");
  Serial.print(leftTargetPulses);
  Serial.print(";RIGHT_TARGET=");
  Serial.println(rightTargetPulses);
}

void printConfig() {
  Serial.println("CONFIG;VERSION=ATLAS_STAGE6C_V1");
  Serial.print("CONFIG;WHEEL_CIRCUMFERENCE_CM=");
  Serial.println(WHEEL_CIRCUMFERENCE_CM, 2);
  Serial.print("CONFIG;LEFT_PPR=");
  Serial.print(LEFT_PULSES_PER_REV, 2);
  Serial.print(";RIGHT_PPR=");
  Serial.println(RIGHT_PULSES_PER_REV, 2);
  Serial.print("CONFIG;LEFT_TARGET_PWM=");
  Serial.print(LEFT_TARGET_PWM);
  Serial.print(";RIGHT_TARGET_PWM=");
  Serial.println(RIGHT_TARGET_PWM);
  Serial.println("CONFIG;PHYSICAL_LEFT=-RAW_25_26");
  Serial.println("CONFIG;PHYSICAL_RIGHT=-RAW_18_19");
  Serial.print("CONFIG;STALL_TIMEOUT_MS=");
  Serial.print(STALL_TIMEOUT_MS);
  Serial.print(";TOTAL_TIMEOUT_MS=");
  Serial.println(TARGET_TOTAL_TIMEOUT_MS);
}

void printHelp() {
  Serial.println("COMMANDS:");
  Serial.println("  ARM");
  Serial.println("  STOP");
  Serial.println("  STATUS");
  Serial.println("  CONFIG");
  Serial.println("  HELP");
  Serial.println("  ZERO");
  Serial.println("  ENC");
  Serial.println("  F  PWM TIME_MS");
  Serial.println("  B  PWM TIME_MS");
  Serial.println("  TL PWM TIME_MS");
  Serial.println("  TR PWM TIME_MS");
  Serial.println("  LF PWM TIME_MS");
  Serial.println("  LB PWM TIME_MS");
  Serial.println("  RF PWM TIME_MS");
  Serial.println("  RB PWM TIME_MS");
  Serial.println("  TESTL TARGET_PULSES");
  Serial.println("  TESTR TARGET_PULSES");
  Serial.println("  FD DISTANCE_CM");
  Serial.println("EXAMPLES:");
  Serial.println("  ARM  then  F 160 1000");
  Serial.println("  ARM  then  TESTL 100");
  Serial.println("  ARM  then  TESTR 100");
  Serial.println("  ARM  then  FD 6.1");
  Serial.println("  ARM  then  FD 20");
  Serial.println("PWM_RANGE=80_TO_220");
  Serial.println("TIMED_RANGE_MS=100_TO_1000");
  Serial.println("FD_RANGE_CM=1.0_TO_30.0");
  Serial.println("TEST_PULSE_RANGE=20_TO_3000");
  Serial.println("ARM_REQUIRED_BEFORE_EACH_MOTION");
  Serial.println("ENCODER_COUNT_MODE=A_RISING_1X");
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
    Serial.println("ERROR:MOTION_ALREADY_ACTIVE;SYSTEM_DISARMED");
    return false;
  }

  if (!armed) {
    stopMotorOutputsImmediately();
    Serial.println("ERROR:NOT_ARMED;SEND_ARM_FIRST");
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
    Serial.print("ERROR:INVALID_PWM;ALLOWED=");
    Serial.print(MIN_PWM);
    Serial.print("_TO_");
    Serial.println(MAX_PWM);
    return;
  }

  if (durationMs < MIN_DURATION_MS ||
      durationMs > MAX_DURATION_MS) {
    finishMotion("INVALID_DURATION", true);
    Serial.print("ERROR:INVALID_DURATION;ALLOWED_MS=");
    Serial.print(MIN_DURATION_MS);
    Serial.print("_TO_");
    Serial.println(MAX_DURATION_MS);
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

  resetEncoderCounts();

  activeCommand = command;
  motionMode = MotionMode::TIMED;
  moving = true;
  timedStopDeadline = millis() + durationMs;

  driveMotors(leftSpeed, rightSpeed);

  Serial.print("RUN;MODE=TIMED;CMD=");
  Serial.print(command);
  Serial.print(";LEFT_SPEED=");
  Serial.print(leftSpeed);
  Serial.print(";RIGHT_SPEED=");
  Serial.print(rightSpeed);
  Serial.print(";PWM=");
  Serial.print(pwm);
  Serial.print(";DURATION_MS=");
  Serial.print(durationMs);
  Serial.println(";ARMED=YES");
}

void startTargetMotion(
    const String& command,
    int32_t requestedLeftTarget,
    int32_t requestedRightTarget) {

  if (!motionStartAllowed()) {
    return;
  }

  if (requestedLeftTarget <= 0 && requestedRightTarget <= 0) {
    finishMotion("INVALID_TARGET", true);
    Serial.println("ERROR:AT_LEAST_ONE_TARGET_MUST_BE_POSITIVE");
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

  driveMotors(
      leftTargetActive ? LEFT_TARGET_PWM : 0,
      rightTargetActive ? RIGHT_TARGET_PWM : 0);

  Serial.print("RUN;MODE=TARGET;CMD=");
  Serial.print(command);
  Serial.print(";LEFT_TARGET=");
  Serial.print(leftTargetPulses);
  Serial.print(";RIGHT_TARGET=");
  Serial.print(rightTargetPulses);
  Serial.print(";LEFT_PWM=");
  Serial.print(leftTargetActive ? LEFT_TARGET_PWM : 0);
  Serial.print(";RIGHT_PWM=");
  Serial.print(rightTargetActive ? RIGHT_TARGET_PWM : 0);
  Serial.println(";ARMED=YES");
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
      Serial.print("WHEEL_TARGET_REACHED;WHEEL=LEFT;TARGET=");
      Serial.print(leftTargetPulses);
      Serial.print(";COUNT_AT_STOP=");
      Serial.println(physicalLeft);

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
      Serial.print("WHEEL_TARGET_REACHED;WHEEL=RIGHT;TARGET=");
      Serial.print(rightTargetPulses);
      Serial.print(";COUNT_AT_STOP=");
      Serial.println(physicalRight);

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

  Serial.print("ERROR:");
  Serial.print(reason);
  Serial.print(";INPUT=");
  Serial.println(line);
  Serial.println("SEND_HELP_TO_VIEW_SUPPORTED_COMMANDS");
}

void processCommand(String line) {
  line.trim();
  line.toUpperCase();

  if (line.length() == 0) {
    return;
  }

  Serial.print("RECEIVED;");
  Serial.println(line);

  // STOP 始终具有最高优先级。
  if (line == "STOP") {
    finishMotion("USER_STOP", true);
    return;
  }

  if (line == "ARM") {
    if (moving) {
      finishMotion("ARM_DURING_MOTION", true);
      Serial.println("ERROR:ARM_DURING_MOTION;SEND_ARM_AGAIN");
      return;
    }

    stopMotorOutputsImmediately();
    clearMotionState();
    armed = true;
    Serial.println("ARMED;READY_FOR_ONE_LIMITED_MOTION");
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
    printEncoderReport("MANUAL");
    return;
  }

  if (line == "ZERO") {
    if (moving) {
      Serial.println("ERROR:CANNOT_ZERO_WHILE_MOVING");
      return;
    }

    resetEncoderCounts();
    Serial.println("ENCODER_COUNTS_RESET_TO_ZERO");
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

  if (isTimedMotionCommand(command)) {
    if (fieldCount != 3) {
      rejectCommand("INVALID_TIMED_FORMAT", line);
      Serial.println("EXPECTED_FORMAT:F 160 1000");
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
      Serial.println("EXPECTED_FORMAT:TESTL 100");
      return;
    }

    long targetLong;
    if (!parseLongStrict(argument1, targetLong) ||
        targetLong < MIN_TEST_PULSES ||
        targetLong > MAX_TEST_PULSES) {
      rejectCommand("INVALID_TEST_TARGET", line);
      Serial.print("ALLOWED_TEST_PULSES=");
      Serial.print(MIN_TEST_PULSES);
      Serial.print("_TO_");
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
      Serial.println("EXPECTED_FORMAT:FD 20");
      return;
    }

    float distanceCm;
    if (!parseFloatStrict(argument1, distanceCm) ||
        distanceCm < MIN_DISTANCE_CM ||
        distanceCm > MAX_DISTANCE_CM) {
      rejectCommand("INVALID_DISTANCE", line);
      Serial.print("ALLOWED_DISTANCE_CM=");
      Serial.print(MIN_DISTANCE_CM, 1);
      Serial.print("_TO_");
      Serial.println(MAX_DISTANCE_CM, 1);
      return;
    }

    const int32_t calculatedLeftTarget = static_cast<int32_t>(lroundf(
        distanceCm / WHEEL_CIRCUMFERENCE_CM * LEFT_PULSES_PER_REV));

    const int32_t calculatedRightTarget = static_cast<int32_t>(lroundf(
        distanceCm / WHEEL_CIRCUMFERENCE_CM * RIGHT_PULSES_PER_REV));

    Serial.print("DISTANCE_PLAN;CM=");
    Serial.print(distanceCm, 2);
    Serial.print(";LEFT_TARGET=");
    Serial.print(calculatedLeftTarget);
    Serial.print(";RIGHT_TARGET=");
    Serial.println(calculatedRightTarget);

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
  clearMotionState();

  Serial.println();
  Serial.println("ATLAS_STAGE6C_V1_READY");
  Serial.println("STOPPED;REASON=BOOT_DEFAULT;ARMED=NO");
  Serial.println("ENCODER_COUNT_MODE=A_RISING_1X");
  Serial.println("MAPPING;PHYSICAL_LEFT=-RAW_25_26;PHYSICAL_RIGHT=-RAW_18_19");
  Serial.println("SEND_CONFIG_TO_VERIFY_PARAMETERS");
  Serial.println("SEND_HELP_TO_VIEW_COMMANDS");
}

void loop() {
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
        Serial.println("ERROR:SERIAL_LINE_TOO_LONG;SYSTEM_DISARMED");
      }
    }
  }

  if (moving && motionMode == MotionMode::TIMED &&
      static_cast<int32_t>(millis() - timedStopDeadline) >= 0) {
    finishMotion("ACTION_COMPLETE", true);
  }

  monitorTargetMotion();
}
