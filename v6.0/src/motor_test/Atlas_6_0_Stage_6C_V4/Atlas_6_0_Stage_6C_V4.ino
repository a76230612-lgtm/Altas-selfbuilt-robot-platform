#include <Arduino.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

// ============================================================
// Atlas 6.0 Stage 6C V4
// ESP32 DEVKIT_C + L298N + 双编码器
//
// 目标：
// 1. 保留 Stage 6A 的全部安全、定时运动和编码器功能。
// 2. 按当前真实接线，显示“物理左轮 / 物理右轮”编码器计数。
// 3. 支持单轮目标脉冲停车和双轮按距离自动停车。
// 4. 左右轮独立到达、独立停止。
// 5. 先用短时悬空检查自动学习两个编码器的前进符号，再允许目标运动。
// 6. 提供 700 ms 堵转保护、12 s 总超时和异常脉冲保护。
//
// 当前已锁定的编码器映射（信号组保持交换状态）：
//   物理右轮编码器 -> GPIO18 / GPIO19 -> 原始计数 RAW_18_19
//   物理左轮编码器 -> GPIO25 / GPIO26 -> 原始计数 RAW_25_26
//
// V4 保留 V3 的编码器前进符号自动学习。必须先执行：
//   arm -> check left
//   arm -> check right
// 程序依据真实短测结果分别学习符号。目标运动不会使用 abs() 隐藏反向错误。
// 不要交换电机线或编码器线。
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

// 2026-08-07 实测：TESTL 100 只驱动物理左轮，但左轮向后转。
// 保持所有接线不变，仅在软件中反转左电机输出；右电机保持原极性。
constexpr bool LEFT_MOTOR_INVERTED = true;
constexpr bool RIGHT_MOTOR_INVERTED = false;

// -------------------- 编码器接线 --------------------
// 物理右轮编码器信号组
constexpr uint8_t PIN_RAW_18_19_A = 18;
constexpr uint8_t PIN_RAW_18_19_B = 19;

// 物理左轮编码器信号组
constexpr uint8_t PIN_RAW_25_26_A = 25;
constexpr uint8_t PIN_RAW_25_26_B = 26;

// -------------------- Stage 6C 标定参数 --------------------
// 2026-08-08 实测并确认：轮胎沿地面滚动一整圈的距离为 21.40 cm。
// 这是实际滚动周长，不是轮子直径。本版本只更新此标定值和版本标识。
constexpr float WHEEL_CIRCUMFERENCE_CM = 21.40f;
constexpr float LEFT_PULSES_PER_REV = 632.05f;
constexpr float RIGHT_PULSES_PER_REV = 634.17f;

// 6C 第一轮基准测试固定使用 160 / 160；先不要在同一轮测试中改 PWM。
constexpr int LEFT_TARGET_PWM = 160;
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
constexpr long MIN_TEST_PULSES = 20;
constexpr long MAX_TEST_PULSES = 3000;

constexpr unsigned long STALL_TIMEOUT_MS = 700;
constexpr unsigned long TARGET_TOTAL_TIMEOUT_MS = 12000;
constexpr unsigned long FINAL_SETTLE_MS = 300;

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
  return "Motion stopped by a safety or command rule.";
}

const char* resultForReason(const char* reason) {
  if (strcmp(reason, "TARGET_COMPLETE") == 0 || strcmp(reason, "ACTION_COMPLETE") == 0) {
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
      100.0f * static_cast<float>(leftError) / static_cast<float>(leftTarget);

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
      100.0f * static_cast<float>(rightError) / static_cast<float>(rightTarget);

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

  if (strcmp(reason, "STALL_LEFT") == 0 || strcmp(reason, "STALL_RIGHT") == 0) {
    Serial.println("next            : stop target tests; run the encoder check again");
  } else if (strcmp(reason, "TARGET_COMPLETE") == 0) {
    Serial.println("next            : record the result; arm again before another motion");
  } else if (strcmp(reason, "USER_STOP") == 0) {
    Serial.println("next            : arm again only if another test is needed");
  }
  Serial.println("========================================");

  clearMotionState();
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
  Serial.println("version         : Atlas 6C v4 distance-calibrated");
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
  Serial.println();
  Serial.println("Required checks after every restart:");
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
  return command == "F" || command == "B" || command == "TL" || command == "TR" || command == "LF" || command == "LB" || command == "RF" || command == "RB";
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

  if (durationMs < MIN_DURATION_MS || durationMs > MAX_DURATION_MS) {
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
  if (!motionStartAllowed()) {
    return;
  }

  resetEncoderCounts();

  activeCheckWheel = wheel;
  activeCommand = (wheel == CheckWheel::LEFT) ? "check left" : "check right";
  motionMode = MotionMode::ENCODER_CHECK;
  moving = true;
  timedStopDeadline = millis() + ENCODER_CHECK_DURATION_MS;

  if (wheel == CheckWheel::LEFT) {
    driveMotors(ENCODER_CHECK_PWM, 0);
  } else {
    driveMotors(0, ENCODER_CHECK_PWM);
  }

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
    Serial.println(LEFT_TARGET_PWM);
  } else {
    Serial.println("not used");
  }
  Serial.print("right target    : ");
  if (rightTargetActive) {
    Serial.print(rightTargetPulses);
    Serial.print(" pulses at PWM ");
    Serial.println(RIGHT_TARGET_PWM);
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
  if (leftTargetActive && !leftTargetDone && pulseCountIsImplausible(physicalLeft, leftTargetPulses)) {
    finishMotion("ENCODER_SPIKE_LEFT", true);
    return;
  }

  if (rightTargetActive && !rightTargetDone && pulseCountIsImplausible(physicalRight, rightTargetPulses)) {
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

    stopMotorOutputsImmediately();
    clearMotionState();
    armed = true;
    Serial.println();
    Serial.println("[Ready]");
    Serial.println("safety          : armed for one limited motion");
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

  char commandBuffer[12] = { 0 };
  char argument1[24] = { 0 };
  char argument2[24] = { 0 };
  char extraBuffer[12] = { 0 };

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

    if (!parseLongStrict(argument1, pwmLong) || !parseLongStrict(argument2, durationLong) || pwmLong < 0 || durationLong < 0) {
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
    if (!parseLongStrict(argument1, targetLong) || targetLong < MIN_TEST_PULSES || targetLong > MAX_TEST_PULSES) {
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
    if (!parseFloatStrict(argument1, distanceCm) || distanceCm < MIN_DISTANCE_CM || distanceCm > MAX_DISTANCE_CM) {
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
  clearMotionState();

  Serial.println();
  Serial.println("========================================");
  Serial.println("Atlas 6C v4 is ready");
  Serial.println("motors          : stopped");
  Serial.println("safety          : disarmed");
  Serial.println("encoder mode    : A rising edge, 1x count");
  Serial.println("left mapping    : gpio 25/26");
  Serial.println("right mapping   : gpio 18/19");
  Serial.println("encoder signs   : not checked after this restart");
  Serial.println("next            : send 'config', then follow the encoder checks");
  Serial.println("help            : send 'help'");
  Serial.println("========================================");
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
        Serial.println("Error: the serial line was too long. The system is disarmed.");
      }
    }
  }

  if (moving && motionMode == MotionMode::TIMED && static_cast<int32_t>(millis() - timedStopDeadline) >= 0) {
    finishMotion("ACTION_COMPLETE", true);
  }

  if (moving && motionMode == MotionMode::ENCODER_CHECK && static_cast<int32_t>(millis() - timedStopDeadline) >= 0) {
    finishEncoderCheck();
  }

  monitorTargetMotion();
}
