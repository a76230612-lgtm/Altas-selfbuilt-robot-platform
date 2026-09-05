#include <Arduino.h>

// ============================================================
// Atlas 6.0 Stage 4-R
// ESP32 + L298N 双电机安全测试程序
//
// 支持命令：
// ARM
// STOP
// STATUS
// HELP
//
// F  PWM TIME   双电机前进
// B  PWM TIME   双电机后退
// TL PWM TIME   原地左转
// TR PWM TIME   原地右转
//
// LF PWM TIME   仅左电机正向
// LB PWM TIME   仅左电机反向
// RF PWM TIME   仅右电机正向
// RB PWM TIME   仅右电机反向
//
// 示例：F 160 300
// ============================================================

// -------------------- L298N接线 --------------------

constexpr uint8_t PIN_ENA = 13;
constexpr uint8_t PIN_IN1 = 14;
constexpr uint8_t PIN_IN2 = 4;

constexpr uint8_t PIN_ENB = 33;
constexpr uint8_t PIN_IN3 = 32;
constexpr uint8_t PIN_IN4 = 23;

// 如果F命令被接受，但某一侧实际方向相反，暂时不要自己修改。
// 记录左右轮方向后，再根据实际结果生成最终版本。
constexpr bool LEFT_INVERTED  = false;
constexpr bool RIGHT_INVERTED = false;

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

// ============================================================
// 电机底层控制
// ============================================================

void rawStopMotors() {
  // 先关闭PWM，再把方向引脚全部拉低
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
  rawStopMotors();

  if (disarmSystem) {
    armed = false;
  }

  Serial.print("STOPPED;REASON=");
  Serial.print(reason);
  Serial.print(";ARMED=");
  Serial.println(armed ? "YES" : "NO");
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

  // 改变方向前先关闭PWM
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
  Serial.print("STATUS;ARMED=");
  Serial.print(armed ? "YES" : "NO");
  Serial.print(";MOVING=");
  Serial.print(moving ? "YES" : "NO");
  Serial.print(";ACTIVE_COMMAND=");
  Serial.println(activeCommand);
}

void printHelp() {
  Serial.println("COMMANDS:");
  Serial.println("  ARM");
  Serial.println("  STOP");
  Serial.println("  STATUS");
  Serial.println("  HELP");
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

  // 无参数命令
  if (line == "STOP") {
    stopWithReason("USER_STOP", true);
    return;
  }

  if (line == "ARM") {
    rawStopMotors();
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

  // 解析三段式运动命令，例如：F 160 300
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

  Serial.begin(115200);
  delay(500);

  armed = false;
  moving = false;

  Serial.println();
  Serial.println("ATLAS_STAGE4R_DUAL_MOTOR_V2_READY");
  Serial.println("STOPPED;REASON=BOOT_DEFAULT;ARMED=NO");
  Serial.println("SEND_HELP_TO_VIEW_COMMANDS");
}

void loop() {
  // 非阻塞串口接收，因此运动时仍然可以收到STOP
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

  // 到达规定时间后自动停车，并自动解除ARM
  if (moving &&
      static_cast<int32_t>(millis() - stopDeadline) >= 0) {

    stopWithReason("ACTION_COMPLETE", true);
  }
}
