#include <Arduino.h>
#include <esp_arduino_version.h>

// Atlas 6.0 Stage 4-R
// ESP32 DEVKIT_C + HW-095/L298N + two DC motors
// This firmware is only for short, wheel-suspended bench tests.

// Locked GPIO map
constexpr uint8_t PIN_ENA = 13;
constexpr uint8_t PIN_IN1 = 14;
constexpr uint8_t PIN_IN2 = 4;
constexpr uint8_t PIN_IN3 = 32;
constexpr uint8_t PIN_IN4 = 23;
constexpr uint8_t PIN_ENB = 33;

// PWM configuration
constexpr uint32_t PWM_FREQUENCY_HZ = 5000;
constexpr uint8_t PWM_RESOLUTION_BITS = 8;
constexpr uint8_t PWM_CHANNEL_A = 0;  // Used by Arduino-ESP32 2.x
constexpr uint8_t PWM_CHANNEL_B = 1;  // Used by Arduino-ESP32 2.x
constexpr int PWM_LIMIT = 220;

// Every motion command must end within this time.
constexpr uint32_t MIN_ACTION_MS = 50;
constexpr uint32_t MAX_ACTION_MS = 500;
constexpr uint32_t COMMAND_WATCHDOG_MS = 550;

// Begin with both set to false for the individual channel tests.
// After both motors work, change only the motor whose chassis-forward
// direction is reversed, then upload the complete program again.
constexpr bool LEFT_INVERTED = false;
constexpr bool RIGHT_INVERTED = false;

bool armed = false;
bool moving = false;
uint32_t motionDeadlineMs = 0;
uint32_t lastMotionCommandMs = 0;
String activeCommand = "NONE";
String serialLine;

void writePwm(uint8_t pin, uint8_t channel, uint8_t duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, duty);
#else
  ledcWrite(channel, duty);
#endif
}

bool attachPwm() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  const bool aOk = ledcAttach(PIN_ENA, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  const bool bOk = ledcAttach(PIN_ENB, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  return aOk && bOk;
#else
  ledcSetup(PWM_CHANNEL_A, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  ledcSetup(PWM_CHANNEL_B, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  ledcAttachPin(PIN_ENA, PWM_CHANNEL_A);
  ledcAttachPin(PIN_ENB, PWM_CHANNEL_B);
  return true;
#endif
}

void setBridgeA(int signedPwm) {
  signedPwm = constrain(signedPwm, -PWM_LIMIT, PWM_LIMIT);
  writePwm(PIN_ENA, PWM_CHANNEL_A, 0);

  if (signedPwm > 0) {
    digitalWrite(PIN_IN1, HIGH);
    digitalWrite(PIN_IN2, LOW);
  } else if (signedPwm < 0) {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, HIGH);
  } else {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);
  }

  writePwm(PIN_ENA, PWM_CHANNEL_A, abs(signedPwm));
}

void setBridgeB(int signedPwm) {
  signedPwm = constrain(signedPwm, -PWM_LIMIT, PWM_LIMIT);
  writePwm(PIN_ENB, PWM_CHANNEL_B, 0);

  if (signedPwm > 0) {
    digitalWrite(PIN_IN3, HIGH);
    digitalWrite(PIN_IN4, LOW);
  } else if (signedPwm < 0) {
    digitalWrite(PIN_IN3, LOW);
    digitalWrite(PIN_IN4, HIGH);
  } else {
    digitalWrite(PIN_IN3, LOW);
    digitalWrite(PIN_IN4, LOW);
  }

  writePwm(PIN_ENB, PWM_CHANNEL_B, abs(signedPwm));
}

void stopMotors(const char *reason, bool disarmNow) {
  // Disable both bridges first, then clear all direction inputs.
  writePwm(PIN_ENA, PWM_CHANNEL_A, 0);
  writePwm(PIN_ENB, PWM_CHANNEL_B, 0);
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);

  moving = false;
  activeCommand = "NONE";
  if (disarmNow) {
    armed = false;
  }

  Serial.printf(
      "STOPPED;REASON=%s;ARMED=%s\n",
      reason,
      armed ? "YES" : "NO");
}

int withDirectionCorrection(int value, bool inverted) {
  return inverted ? -value : value;
}

void startMotion(
    const String &command,
    int leftPwm,
    int rightPwm,
    uint32_t durationMs) {
  if (!armed) {
    stopMotors("NOT_ARMED", true);
    return;
  }

  if (durationMs < MIN_ACTION_MS || durationMs > MAX_ACTION_MS ||
      abs(leftPwm) > PWM_LIMIT || abs(rightPwm) > PWM_LIMIT ||
      (leftPwm == 0 && rightPwm == 0)) {
    stopMotors("OUT_OF_RANGE", true);
    return;
  }

  const int correctedLeft =
      withDirectionCorrection(leftPwm, LEFT_INVERTED);
  const int correctedRight =
      withDirectionCorrection(rightPwm, RIGHT_INVERTED);

  setBridgeA(correctedLeft);
  setBridgeB(correctedRight);

  moving = true;
  activeCommand = command;
  lastMotionCommandMs = millis();
  motionDeadlineMs = lastMotionCommandMs + durationMs;

  Serial.printf(
      "RUN;CMD=%s;LEFT=%d;RIGHT=%d;DURATION_MS=%lu;ARMED=YES\n",
      command.c_str(),
      correctedLeft,
      correctedRight,
      static_cast<unsigned long>(durationMs));
}

void printStatus() {
  Serial.printf(
      "STATUS;ARMED=%s;MOVING=%s;ACTIVE=%s;PWM_LIMIT=%d;"
      "MAX_ACTION_MS=%lu;LEFT_INVERTED=%s;RIGHT_INVERTED=%s\n",
      armed ? "YES" : "NO",
      moving ? "YES" : "NO",
      activeCommand.c_str(),
      PWM_LIMIT,
      static_cast<unsigned long>(MAX_ACTION_MS),
      LEFT_INVERTED ? "YES" : "NO",
      RIGHT_INVERTED ? "YES" : "NO");
}

void printHelp() {
  Serial.println("COMMANDS:");
  Serial.println("  ARM");
  Serial.println("  STOP");
  Serial.println("  DISARM");
  Serial.println("  STATUS");
  Serial.println("  HELP");
  Serial.println("  LF <PWM> <MS>   left motor forward");
  Serial.println("  LB <PWM> <MS>   left motor backward");
  Serial.println("  RF <PWM> <MS>   right motor forward");
  Serial.println("  RB <PWM> <MS>   right motor backward");
  Serial.println("  F  <PWM> <MS>   both forward");
  Serial.println("  B  <PWM> <MS>   both backward");
  Serial.println("  TL <PWM> <MS>   turn left in place");
  Serial.println("  TR <PWM> <MS>   turn right in place");
  Serial.printf(
      "LIMITS: PWM=1..%d, duration=%lu..%lu ms\n",
      PWM_LIMIT,
      static_cast<unsigned long>(MIN_ACTION_MS),
      static_cast<unsigned long>(MAX_ACTION_MS));
}

void processCommand(String line) {
  line.trim();
  line.toUpperCase();

  if (line.length() == 0) {
    return;
  }

  Serial.printf("RECEIVED;%s\n", line.c_str());

  if (line == "ARM") {
    stopMotors("ARM_REQUEST", false);
    armed = true;
    Serial.println("ARMED;WAITING_FOR_TIME_LIMITED_COMMAND");
    return;
  }

  if (line == "STOP") {
    stopMotors("USER_STOP", true);
    return;
  }

  if (line == "DISARM") {
    stopMotors("USER_DISARM", true);
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

  char operation[8] = {0};
  int pwm = 0;
  unsigned long durationMs = 0;
  char extra = '\0';

  // The fourth conversion catches unwanted extra text.
  const int parsed = sscanf(
      line.c_str(),
      "%7s %d %lu %c",
      operation,
      &pwm,
      &durationMs,
      &extra);

  if (parsed != 3 || pwm < 1 || pwm > PWM_LIMIT ||
      durationMs < MIN_ACTION_MS || durationMs > MAX_ACTION_MS) {
    stopMotors("INVALID_COMMAND", true);
    return;
  }

  if (strcmp(operation, "LF") == 0) {
    startMotion("LF", pwm, 0, durationMs);
  } else if (strcmp(operation, "LB") == 0) {
    startMotion("LB", -pwm, 0, durationMs);
  } else if (strcmp(operation, "RF") == 0) {
    startMotion("RF", 0, pwm, durationMs);
  } else if (strcmp(operation, "RB") == 0) {
    startMotion("RB", 0, -pwm, durationMs);
  } else if (strcmp(operation, "F") == 0) {
    startMotion("F", pwm, pwm, durationMs);
  } else if (strcmp(operation, "B") == 0) {
    startMotion("B", -pwm, -pwm, durationMs);
  } else if (strcmp(operation, "TL") == 0) {
    startMotion("TL", -pwm, pwm, durationMs);
  } else if (strcmp(operation, "TR") == 0) {
    startMotion("TR", pwm, -pwm, durationMs);
  } else {
    stopMotors("UNKNOWN_COMMAND", true);
  }
}

void setup() {
  // Set direction and enable pins low before PWM is attached.
  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_ENB, OUTPUT);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);

  digitalWrite(PIN_ENA, LOW);
  digitalWrite(PIN_ENB, LOW);
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);

  Serial.begin(115200);
  delay(300);

  if (!attachPwm()) {
    Serial.println("FATAL;PWM_ATTACH_FAILED");
    while (true) {
      digitalWrite(PIN_ENA, LOW);
      digitalWrite(PIN_ENB, LOW);
      delay(100);
    }
  }

  stopMotors("BOOT_DEFAULT", true);
  Serial.println("ATLAS_STAGE4R_READY");
  printStatus();
  printHelp();
}

void loop() {
  while (Serial.available() > 0) {
    const char incoming = static_cast<char>(Serial.read());

    if (incoming == '\n' || incoming == '\r') {
      if (serialLine.length() > 0) {
        processCommand(serialLine);
        serialLine = "";
      }
    } else if (serialLine.length() < 79) {
      serialLine += incoming;
    } else {
      serialLine = "";
      stopMotors("SERIAL_LINE_TOO_LONG", true);
    }
  }

  if (moving) {
    const uint32_t now = millis();

    if (static_cast<int32_t>(now - motionDeadlineMs) >= 0) {
      stopMotors("ACTION_COMPLETE", false);
    } else if (now - lastMotionCommandMs > COMMAND_WATCHDOG_MS) {
      stopMotors("COMMAND_TIMEOUT", true);
    }
  }
}
