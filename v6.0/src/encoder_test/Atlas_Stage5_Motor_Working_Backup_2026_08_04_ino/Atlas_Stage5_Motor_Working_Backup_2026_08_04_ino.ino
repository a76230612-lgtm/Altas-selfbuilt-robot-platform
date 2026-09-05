#include <Arduino.h>

// ============================================================
// Atlas 6.0 Stage 6A
// ESP32 + L298N + 双编码器安全测试程序
//
// 控制命令：
// ARM
// STOP
// STATUS
// HELP
//
// F  PWM TIME
// B  PWM TIME
// TL PWM TIME
// TR PWM TIME
// LF PWM TIME
// LB PWM TIME
// RF PWM TIME
// RB PWM TIME
//
// 编码器命令：
// ZERO   左右编码器计数清零
// ENC    显示当前左右编码器计数
//
// 每次运动开始时自动清零编码器。
// 每次运动结束后自动显示左右脉冲。
// ============================================================

// -------------------- L298N接线 --------------------

constexpr uint8_t PIN_ENA = 13;
constexpr uint8_t PIN_IN1 = 14;
constexpr uint8_t PIN_IN2 = 4;

constexpr uint8_t PIN_ENB = 33;
constexpr uint8_t PIN_IN3 = 32;
constexpr uint8_t PIN_IN4 = 23;

constexpr bool LEFT_INVERTED  = false;
constexpr bool RIGHT_INVERTED = false;

// -------------------- 编码器接线 --------------------
//
// 左编码器A -> GPIO18
// 左编码器B -> GPIO19
// 右编码器A -> GPIO25
// 右编码器B -> GPIO26
// 编码器VCC -> ESP32 3V3
// 编码器GND -> ESP32 GND
//
// 本程序在编码器A相上升沿计数，B相用于判断方向。

constexpr uint8_t PIN_LEFT_ENCODER_A  = 18;
constexpr uint8_t PIN_LEFT_ENCODER_B  = 19;
constexpr uint8_t PIN_RIGHT_ENCODER_A = 25;
constexpr uint8_t PIN_RIGHT_ENCODER_B = 26;

// 初始阶段保持false。
// 如果之后需要统一前进时的正负方向，再根据真实数据修改。
constexpr bool LEFT_ENCODER_INVERTED  = false;
constexpr bool RIGHT_ENCODER_INVERTED = false;

// -------------------- 安全限制 --------------------

constexpr int MIN_PWM = 80;
constexpr int MAX_PWM = 220;

constexpr unsigned long MIN_DURATION_MS = 100;
constexpr unsigned long MAX_DURATION_MS = 1000;

// -------------------- 运行状态 --------------------

String serialLine = "";
String activeCommand = "NONE";

bool armed = false;
bool moving = false;

unsigned long stopDeadline = 0;

// -------------------- 编码器状态 --------------------

volatile int32_t leftEncoderCount = 0;
volatile int32_t rightEncoderCount = 0;

portMUX_TYPE encoderMux = portMUX_INITIALIZER_UNLOCKED;

// ============================================================
// 编码器中断
// ============================================================

void IRAM_ATTR onLeftEncoderA() {
  int delta;

  if (digitalRead(PIN_LEFT_ENCODER_B) == HIGH) {
    delta = 1;
  } else {
    delta = -1;
  }

  portENTER_CRITICAL_ISR(&encoderMux);
  leftEncoderCount += delta;
  portEXIT_CRITICAL_ISR(&encoderMux);
}

void IRAM_ATTR onRightEncoderA() {
  int delta;

  if (digitalRead(PIN_RIGHT_ENCODER_B) == HIGH) {
    delta = 1;
  } else {
    delta = -1;
  }

  portENTER_CRITICAL_ISR(&encoderMux);
  rightEncoderCount += delta;
  portEXIT_CRITICAL_ISR(&encoderMux);
}

// ============================================================
// 编码器辅助函数
// ============================================================

void resetEncoderCounts() {
  portENTER_CRITICAL(&encoderMux);

  leftEncoderCount = 0;
  rightEncoderCount = 0;

  portEXIT_CRITICAL(&encoderMux);
}

void readEncoderCounts(int32_t& leftCount, int32_t& rightCount) {
  portENTER_CRITICAL(&encoderMux);

  leftCount = leftEncoderCount;
  rightCount = rightEncoderCount;

  portEXIT_CRITICAL(&encoderMux);

  if (LEFT_ENCODER_INVERTED) {
    leftCount = -leftCount;
  }

  if (RIGHT_ENCODER_INVERTED) {
    rightCount = -rightCount;
  }
}

void printEncoderReport(const String& command) {
  int32_t leftCount;
  int32_t rightCount;

  readEncoderCounts(leftCount, rightCount);

  Serial.print("ENCODER;CMD=");
  Serial.print(command);
  Serial.print(";LEFT_PULSES=");
  Serial.print(leftCount);
  Serial.print(";RIGHT_PULSES=");
  Serial.println(rightCount);
}

// ============================================================
// 电机底层控制
// ============================================================

void rawStopMotors() {
  analogWrite(PIN_ENA, 0);
  analogWrite(PIN_ENB, 0);

  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);

  moving = false;
  activeCommand = "NONE";
}

void stopWithReason(const char* reason, bool disarmSystem) {
  bool wasMoving = moving;
  String finishedCommand = activeCommand;

  // 先立即停止电机
  rawStopMotors();

  // 等待极短时间，记录停车前后的最后几个编码器脉冲
  if (wasMoving) {
    delay(20);
  }

  if (disarmSystem) {
    armed = false;
  }

  Serial.print("STOPPED;REASON=");
  Serial.print(reason);
  Serial.print(";ARMED=");
  Serial.println(armed ? "YES" : "NO");

  if (wasMoving) {
    printEncoderReport(finishedCommand);
  }
}

void applyOneMotor(
    int requestedSpeed,
    uint8_t pinEnable,
    uint8_t pinA,
    uint8_t pinB,
    bool inverted) {

  int actualSpeed = requestedSpeed;

  if (inverted) {
    actualSpeed = -actualSpeed;
  }

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

void driveMotors(int leftSpeed, int rightSpeed) {
  applyOneMotor(
      leftSpeed,
      PIN_ENA,
      PIN_IN1,
      PIN_IN2,
      LEFT_INVERTED);

  applyOneMotor(
      rightSpeed,
      PIN_ENB,
      PIN_IN3,
      PIN_IN4,
      RIGHT_INVERTED);
}

// ============================================================
// 状态与帮助信息
// ============================================================

void printStatus() {
  int32_t leftCount;
  int32_t rightCount;

  readEncoderCounts(leftCount, rightCount);

  Serial.print("STATUS;ARMED=");
  Serial.print(armed ? "YES" : "NO");
  Serial.print(";MOVING=");
  Serial.print(moving ? "YES" : "NO");
  Serial.print(";ACTIVE_COMMAND=");
  Serial.print(activeCommand);
  Serial.print(";LEFT_PULSES=");
  Serial.print(leftCount);
  Serial.print(";RIGHT_PULSES=");
  Serial.println(rightCount);
}

void printHelp() {
  Serial.println("COMMANDS:");
  Serial.println("  ARM");
  Serial.println("  STOP");
  Serial.println("  STATUS");
  Serial.println("  HELP");
  Serial.println("  ZERO");
  Serial.println("  ENC");
  Serial.println("  F  PWM TIME");
  Serial.println("  B  PWM TIME");
  Serial.println("  TL PWM TIME");
  Serial.println("  TR PWM TIME");
  Serial.println("  LF PWM TIME");
  Serial.println("  LB PWM TIME");
  Serial.println("  RF PWM TIME");
  Serial.println("  RB PWM TIME");
  Serial.println("EXAMPLE: F 160 300");
  Serial.println("PWM_RANGE=80_TO_220");
  Serial.println("TIME_RANGE_MS=100_TO_1000");
  Serial.println("ARM_REQUIRED_BEFORE_EACH_MOTION");
  Serial.println("ENCODER_COUNT_MODE=A_RISING_1X");
}

// ============================================================
// 命令处理
// ============================================================

bool isMotionCommand(const String& command) {
  return command == "F"  ||
         command == "B"  ||
         command == "TL" ||
         command == "TR" ||
         command == "LF" ||
         command == "LB" ||
         command == "RF" ||
         command == "RB";
}

void startMotion(
    const String& command,
    int pwm,
    unsigned long durationMs) {

  if (moving) {
    stopWithReason("MOTION_ALREADY_ACTIVE", true);
    Serial.println("ERROR:MOTION_ALREADY_ACTIVE");
    return;
  }

  if (!armed) {
    stopWithReason("NOT_ARMED", true);
    Serial.println("ERROR:NOT_ARMED;SEND_ARM_FIRST");
    return;
  }

  if (pwm < MIN_PWM || pwm > MAX_PWM) {
    stopWithReason("INVALID_PWM", true);

    Serial.print("ERROR:INVALID_PWM;ALLOWED=");
    Serial.print(MIN_PWM);
    Serial.print("_TO_");
    Serial.println(MAX_PWM);
    return;
  }

  if (durationMs < MIN_DURATION_MS ||
      durationMs > MAX_DURATION_MS) {

    stopWithReason("INVALID_DURATION", true);

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
    rightSpeed = 0;

  } else if (command == "LB") {
    leftSpeed = -pwm;
    rightSpeed = 0;

  } else if (command == "RF") {
    leftSpeed = 0;
    rightSpeed = pwm;

  } else if (command == "RB") {
    leftSpeed = 0;
    rightSpeed = -pwm;
  }

  // 每次动作开始前清零左右编码器
  resetEncoderCounts();

  activeCommand = command;
  moving = true;
  stopDeadline = millis() + durationMs;

  driveMotors(leftSpeed, rightSpeed);

  Serial.print("RUN;CMD=");
  Serial.print(command);
  Serial.print(";LEFT=");
  Serial.print(leftSpeed);
  Serial.print(";RIGHT=");
  Serial.print(rightSpeed);
  Serial.print(";PWM=");
  Serial.print(pwm);
  Serial.print(";DURATION_MS=");
  Serial.print(durationMs);
  Serial.println(";ARMED=YES");
}

void processCommand(String line) {
  line.trim();
  line.toUpperCase();

  if (line.length() == 0) {
    return;
  }

  Serial.print("RECEIVED;");
  Serial.println(line);

  if (line == "STOP") {
    stopWithReason("USER_STOP", true);
    return;
  }

  if (line == "ARM") {
    if (moving) {
      stopWithReason("ARM_RECEIVED_DURING_MOTION", true);
    } else {
      rawStopMotors();
    }

    armed = true;
    Serial.println("ARMED;READY_FOR_ONE_TIME_LIMITED_COMMAND");
    return;
  }

  if (line == "STATUS") {
    printStatus();
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

  char commandBuffer[8] = {0};
  char extraBuffer[8] = {0};

  int pwm = 0;
  unsigned long durationMs = 0;

  int fieldCount = sscanf(
      line.c_str(),
      "%7s %d %lu %7s",
      commandBuffer,
      &pwm,
      &durationMs,
      extraBuffer);

  String motionCommand = String(commandBuffer);
  motionCommand.toUpperCase();

  if (!isMotionCommand(motionCommand)) {
    stopWithReason("UNKNOWN_COMMAND", true);

    Serial.print("ERROR:UNKNOWN_COMMAND;");
    Serial.println(line);
    Serial.println("SEND_HELP_TO_VIEW_SUPPORTED_COMMANDS");
    return;
  }

  if (fieldCount != 3) {
    stopWithReason("INVALID_FORMAT", true);
    Serial.println("ERROR:INVALID_FORMAT");
    Serial.println("EXPECTED_FORMAT: F 160 300");
    return;
  }

  startMotion(motionCommand, pwm, durationMs);
}

// ============================================================
// Arduino主程序
// ============================================================

void setup() {
  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);

  pinMode(PIN_ENB, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);

  rawStopMotors();

  pinMode(PIN_LEFT_ENCODER_A, INPUT_PULLUP);
  pinMode(PIN_LEFT_ENCODER_B, INPUT_PULLUP);
  pinMode(PIN_RIGHT_ENCODER_A, INPUT_PULLUP);
  pinMode(PIN_RIGHT_ENCODER_B, INPUT_PULLUP);

  resetEncoderCounts();

  attachInterrupt(
      digitalPinToInterrupt(PIN_LEFT_ENCODER_A),
      onLeftEncoderA,
      RISING);

  attachInterrupt(
      digitalPinToInterrupt(PIN_RIGHT_ENCODER_A),
      onRightEncoderA,
      RISING);

  Serial.begin(115200);
  delay(500);

  armed = false;
  moving = false;

  Serial.println();
  Serial.println("ATLAS_STAGE6A_ENCODER_TEST_V1_READY");
  Serial.println("STOPPED;REASON=BOOT_DEFAULT;ARMED=NO");
  Serial.println("ENCODER_COUNT_MODE=A_RISING_1X");
  Serial.println("SEND_HELP_TO_VIEW_COMMANDS");
}

void loop() {
  while (Serial.available() > 0) {
    char incoming = static_cast<char>(Serial.read());

    if (incoming == '\n' || incoming == '\r') {
      if (serialLine.length() > 0) {
        processCommand(serialLine);
        serialLine = "";
      }

    } else if (incoming >= 32 && incoming <= 126) {
      if (serialLine.length() < 63) {
        serialLine += incoming;

      } else {
        serialLine = "";
        stopWithReason("SERIAL_LINE_TOO_LONG", true);
        Serial.println("ERROR:SERIAL_LINE_TOO_LONG");
      }
    }
  }

  if (moving &&
      static_cast<int32_t>(millis() - stopDeadline) >= 0) {

    stopWithReason("ACTION_COMPLETE", true);
  }
}