/*
  Atlas 6.0 - Stage 4
  ESP32 DevKit_C + TB6612FNG dual motor driver
  Safe suspended-wheel bench-test firmware

  IMPORTANT:
  1. Keep both drive wheels suspended above the table.
  2. Use the 2 A blade fuse and the NC contact of the latching E-stop
     in series with the 6 V motor-supply positive wire.
  3. ESP32 GND, TB6612 GND, and battery negative must share a common ground.
  4. TB6612 VCC goes to ESP32 3V3. TB6612 VM goes to switched/fused 6 V.
  5. This firmware intentionally does NOT use encoders, ROS 2, US-100,
     Atlas head servos, LEDs, or OLED.
  6. Maximum allowed PWM is 70/255.

  TB6612 -> ESP32 GPIO map:
    PWMA -> GPIO13   Left motor PWM
    AIN1 -> GPIO14   Left motor direction 1
    AIN2 -> GPIO4    Left motor direction 2
    STBY -> GPIO23   Driver enable; LOW is hardware-safe standby
    BIN1 -> GPIO32   Right motor direction 1
    BIN2 -> GPIO15   Right motor direction 2
    PWMB -> GPIO33   Right motor PWM

  Reserved Atlas 5.0 GPIOs, deliberately not used here:
    Pan 18, Tilt 19, OLED 21/22, LEDs 25/26/27.

  GPIO16/17 are deliberately not used because ESP32-DevKitC boards fitted
  with an ESP32-WROVER module reserve those pins for PSRAM.

  Serial Monitor:
    Baud: 115200
    Line ending: Newline

  Safe command sequence:
    ARM
    LF 40 300

  Every motion is time-limited to 100..500 ms and automatically:
    STOP -> STBY LOW -> DISARM
*/

#include <Arduino.h>

#if __has_include(<esp_arduino_version.h>)
  #include <esp_arduino_version.h>
#endif

#ifndef ESP_ARDUINO_VERSION_MAJOR
  // Older Arduino-ESP32 releases may not expose the version macro.
  #define ESP_ARDUINO_VERSION_MAJOR 2
#endif

// ---------------------------------------------------------------------------
// Locked Stage 4 GPIO assignment
// ---------------------------------------------------------------------------
constexpr uint8_t PIN_PWMA = 13;
constexpr uint8_t PIN_AIN1 = 14;
constexpr uint8_t PIN_AIN2 = 4;
constexpr uint8_t PIN_STBY = 23;
constexpr uint8_t PIN_BIN1 = 32;
constexpr uint8_t PIN_BIN2 = 15;
constexpr uint8_t PIN_PWMB = 33;

// ---------------------------------------------------------------------------
// Safety limits
// ---------------------------------------------------------------------------
constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint32_t PWM_FREQUENCY_HZ = 20000;
constexpr uint8_t PWM_RESOLUTION_BITS = 8;

constexpr uint8_t DEFAULT_PWM = 40;
constexpr uint8_t MAX_PWM = 70;
constexpr uint16_t DEFAULT_DURATION_MS = 300;
constexpr uint16_t MIN_DURATION_MS = 100;
constexpr uint16_t MAX_DURATION_MS = 500;
constexpr uint32_t ACTIVE_COMMAND_WATCHDOG_MS = 650;

// If a wheel spins opposite to the intended logical direction, do not change
// wiring while powered. Set only that wheel's value to true, re-upload, and
// retest with the wheels suspended.
constexpr bool LEFT_FORWARD_INVERTED = false;
constexpr bool RIGHT_FORWARD_INVERTED = false;

#if ESP_ARDUINO_VERSION_MAJOR < 3
constexpr uint8_t PWM_CHANNEL_A = 0;
constexpr uint8_t PWM_CHANNEL_B = 1;
#endif

enum class Motion : uint8_t {
  STOPPED,
  LEFT_FORWARD,
  LEFT_REVERSE,
  RIGHT_FORWARD,
  RIGHT_REVERSE,
  BOTH_FORWARD,
  BOTH_REVERSE
};

bool armed = false;
bool motionActive = false;
bool pwmReady = false;
Motion currentMotion = Motion::STOPPED;
uint8_t currentPwm = 0;
uint32_t motionStartedAtMs = 0;
uint32_t motionEndsAtMs = 0;

constexpr size_t SERIAL_BUFFER_SIZE = 64;
char serialBuffer[SERIAL_BUFFER_SIZE] = {};
size_t serialLength = 0;

// ---------------------------------------------------------------------------
// PWM compatibility layer: Arduino-ESP32 2.x and 3.x
// ---------------------------------------------------------------------------
bool setupMotorPwm() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  const bool aOk = ledcAttach(PIN_PWMA, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  const bool bOk = ledcAttach(PIN_PWMB, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  return aOk && bOk;
#else
  const double aFrequency =
      ledcSetup(PWM_CHANNEL_A, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  const double bFrequency =
      ledcSetup(PWM_CHANNEL_B, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  ledcAttachPin(PIN_PWMA, PWM_CHANNEL_A);
  ledcAttachPin(PIN_PWMB, PWM_CHANNEL_B);
  return aFrequency > 0.0 && bFrequency > 0.0;
#endif
}

void writePwmA(uint8_t duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(PIN_PWMA, duty);
#else
  ledcWrite(PWM_CHANNEL_A, duty);
#endif
}

void writePwmB(uint8_t duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(PIN_PWMB, duty);
#else
  ledcWrite(PWM_CHANNEL_B, duty);
#endif
}

// ---------------------------------------------------------------------------
// Motor output helpers
// ---------------------------------------------------------------------------
void setLeftDirection(bool forward) {
  const bool actualForward = forward ^ LEFT_FORWARD_INVERTED;
  digitalWrite(PIN_AIN1, actualForward ? HIGH : LOW);
  digitalWrite(PIN_AIN2, actualForward ? LOW : HIGH);
}

void setRightDirection(bool forward) {
  const bool actualForward = forward ^ RIGHT_FORWARD_INVERTED;
  digitalWrite(PIN_BIN1, actualForward ? HIGH : LOW);
  digitalWrite(PIN_BIN2, actualForward ? LOW : HIGH);
}

void setLeftCoast() {
  digitalWrite(PIN_AIN1, LOW);
  digitalWrite(PIN_AIN2, LOW);
}

void setRightCoast() {
  digitalWrite(PIN_BIN1, LOW);
  digitalWrite(PIN_BIN2, LOW);
}

void safeStop(const char *reason, bool printMessage = true) {
  // Disable the driver first, before changing any other motor signal.
  digitalWrite(PIN_STBY, LOW);

  if (pwmReady) {
    writePwmA(0);
    writePwmB(0);
  }

  setLeftCoast();
  setRightCoast();

  motionActive = false;
  currentMotion = Motion::STOPPED;
  currentPwm = 0;
  motionStartedAtMs = 0;
  motionEndsAtMs = 0;

  if (printMessage) {
    Serial.print(F("OK:STOPPED;STBY=LOW;REASON="));
    Serial.println(reason);
  }
}

void safeStopAndDisarm(const char *reason) {
  safeStop(reason);
  armed = false;
  Serial.println(F("OK:DISARMED"));
}

const char *motionName(Motion motion) {
  switch (motion) {
    case Motion::LEFT_FORWARD:  return "LEFT_FORWARD";
    case Motion::LEFT_REVERSE:  return "LEFT_REVERSE";
    case Motion::RIGHT_FORWARD: return "RIGHT_FORWARD";
    case Motion::RIGHT_REVERSE: return "RIGHT_REVERSE";
    case Motion::BOTH_FORWARD:  return "BOTH_FORWARD";
    case Motion::BOTH_REVERSE:  return "BOTH_REVERSE";
    default:                    return "STOPPED";
  }
}

bool startMotion(Motion motion, uint8_t pwm, uint16_t durationMs) {
  if (!armed) {
    safeStop("NOT_ARMED");
    Serial.println(F("ERR:Send ARM before any motion command."));
    return false;
  }

  if (!pwmReady) {
    safeStopAndDisarm("PWM_NOT_READY");
    Serial.println(F("ERR:PWM initialization failed. Do not power the motors."));
    return false;
  }

  if (motionActive) {
    safeStopAndDisarm("MOTION_ALREADY_ACTIVE");
    Serial.println(F("ERR:Motion command rejected while another motion is active."));
    return false;
  }

  if (pwm == 0 || pwm > MAX_PWM) {
    safeStopAndDisarm("PWM_OUT_OF_RANGE");
    Serial.print(F("ERR:PWM must be 1.."));
    Serial.println(MAX_PWM);
    return false;
  }

  if (durationMs < MIN_DURATION_MS || durationMs > MAX_DURATION_MS) {
    safeStopAndDisarm("DURATION_OUT_OF_RANGE");
    Serial.print(F("ERR:Duration must be "));
    Serial.print(MIN_DURATION_MS);
    Serial.print(F(".."));
    Serial.print(MAX_DURATION_MS);
    Serial.println(F(" ms."));
    return false;
  }

  // Keep STBY low while direction and PWM are prepared.
  digitalWrite(PIN_STBY, LOW);
  writePwmA(0);
  writePwmB(0);
  setLeftCoast();
  setRightCoast();

  switch (motion) {
    case Motion::LEFT_FORWARD:
      setLeftDirection(true);
      writePwmA(pwm);
      break;
    case Motion::LEFT_REVERSE:
      setLeftDirection(false);
      writePwmA(pwm);
      break;
    case Motion::RIGHT_FORWARD:
      setRightDirection(true);
      writePwmB(pwm);
      break;
    case Motion::RIGHT_REVERSE:
      setRightDirection(false);
      writePwmB(pwm);
      break;
    case Motion::BOTH_FORWARD:
      setLeftDirection(true);
      setRightDirection(true);
      writePwmA(pwm);
      writePwmB(pwm);
      break;
    case Motion::BOTH_REVERSE:
      setLeftDirection(false);
      setRightDirection(false);
      writePwmA(pwm);
      writePwmB(pwm);
      break;
    default:
      safeStopAndDisarm("INVALID_MOTION");
      return false;
  }

  currentMotion = motion;
  currentPwm = pwm;
  motionStartedAtMs = millis();
  motionEndsAtMs = motionStartedAtMs + durationMs;
  motionActive = true;

  // STBY goes HIGH last. Motor power is enabled only after all signals are ready.
  digitalWrite(PIN_STBY, HIGH);

  Serial.print(F("OK:MOTION_STARTED;TYPE="));
  Serial.print(motionName(motion));
  Serial.print(F(";PWM="));
  Serial.print(pwm);
  Serial.print(F(";MS="));
  Serial.println(durationMs);
  return true;
}

// ---------------------------------------------------------------------------
// Serial command handling
// ---------------------------------------------------------------------------
void printHelp() {
  Serial.println(F("=== Atlas 6.0 Stage 4 Safe Test ==="));
  Serial.println(F("Set Serial Monitor: 115200 baud, Newline."));
  Serial.println(F("Commands:"));
  Serial.println(F("  HELP"));
  Serial.println(F("  STATUS"));
  Serial.println(F("  ARM"));
  Serial.println(F("  STOP"));
  Serial.println(F("  DISARM"));
  Serial.println(F("  LF [PWM] [MS]  left motor forward"));
  Serial.println(F("  LR [PWM] [MS]  left motor reverse"));
  Serial.println(F("  RF [PWM] [MS]  right motor forward"));
  Serial.println(F("  RR [PWM] [MS]  right motor reverse"));
  Serial.println(F("  BF [PWM] [MS]  both motors forward"));
  Serial.println(F("  BR [PWM] [MS]  both motors reverse"));
  Serial.println(F("Defaults: PWM=40, MS=300."));
  Serial.println(F("Limits: PWM=1..70, MS=100..500."));
  Serial.println(F("Each motion stops and DISARMS automatically."));
}

void printStatus() {
  Serial.print(F("STATUS:ARMED="));
  Serial.print(armed ? F("YES") : F("NO"));
  Serial.print(F(";ACTIVE="));
  Serial.print(motionActive ? F("YES") : F("NO"));
  Serial.print(F(";MOTION="));
  Serial.print(motionName(currentMotion));
  Serial.print(F(";PWM="));
  Serial.print(currentPwm);
  Serial.print(F(";STBY="));
  Serial.print(digitalRead(PIN_STBY) == HIGH ? F("HIGH") : F("LOW"));
  Serial.print(F(";PWM_READY="));
  Serial.println(pwmReady ? F("YES") : F("NO"));
}

void uppercaseInPlace(char *text) {
  for (size_t i = 0; text[i] != '\0'; ++i) {
    if (text[i] >= 'a' && text[i] <= 'z') {
      text[i] = static_cast<char>(text[i] - 'a' + 'A');
    }
  }
}

void trimInPlace(char *text) {
  size_t start = 0;
  while (text[start] == ' ' || text[start] == '\t') {
    ++start;
  }

  if (start > 0) {
    size_t destination = 0;
    while (text[start] != '\0') {
      text[destination++] = text[start++];
    }
    text[destination] = '\0';
  }

  size_t length = strlen(text);
  while (length > 0 &&
         (text[length - 1] == ' ' || text[length - 1] == '\t')) {
    text[--length] = '\0';
  }
}

bool parseUnsignedLongStrict(const char *text, unsigned long &value) {
  if (text == nullptr || text[0] == '\0') {
    return false;
  }

  char *endPointer = nullptr;
  value = strtoul(text, &endPointer, 10);
  return endPointer != text && *endPointer == '\0';
}

bool decodeMotionCommand(const char *command, Motion &motion) {
  if (strcmp(command, "LF") == 0) {
    motion = Motion::LEFT_FORWARD;
  } else if (strcmp(command, "LR") == 0) {
    motion = Motion::LEFT_REVERSE;
  } else if (strcmp(command, "RF") == 0) {
    motion = Motion::RIGHT_FORWARD;
  } else if (strcmp(command, "RR") == 0) {
    motion = Motion::RIGHT_REVERSE;
  } else if (strcmp(command, "BF") == 0) {
    motion = Motion::BOTH_FORWARD;
  } else if (strcmp(command, "BR") == 0) {
    motion = Motion::BOTH_REVERSE;
  } else {
    return false;
  }
  return true;
}

void processCommand(char *line) {
  trimInPlace(line);
  uppercaseInPlace(line);

  if (line[0] == '\0') {
    return;
  }

  char *savePointer = nullptr;
  char *command = strtok_r(line, " \t", &savePointer);
  char *pwmText = strtok_r(nullptr, " \t", &savePointer);
  char *durationText = strtok_r(nullptr, " \t", &savePointer);
  char *extraText = strtok_r(nullptr, " \t", &savePointer);

  if (extraText != nullptr) {
    safeStopAndDisarm("TOO_MANY_ARGUMENTS");
    Serial.println(F("ERR:Too many command arguments."));
    return;
  }

  if (strcmp(command, "HELP") == 0) {
    printHelp();
    return;
  }

  if (strcmp(command, "STATUS") == 0) {
    printStatus();
    return;
  }

  if (strcmp(command, "STOP") == 0 || strcmp(command, "DISARM") == 0) {
    safeStopAndDisarm(command);
    return;
  }

  if (strcmp(command, "ARM") == 0) {
    safeStop("ARM_PRECHECK");
    if (!pwmReady) {
      armed = false;
      Serial.println(F("ERR:Cannot ARM because PWM initialization failed."));
      return;
    }
    armed = true;
    Serial.println(F("OK:ARMED;MOTORS=STOPPED;STBY=LOW"));
    return;
  }

  Motion requestedMotion = Motion::STOPPED;
  if (!decodeMotionCommand(command, requestedMotion)) {
    safeStopAndDisarm("UNKNOWN_COMMAND");
    Serial.println(F("ERR:Unknown command. Send HELP."));
    return;
  }

  unsigned long parsedPwm = DEFAULT_PWM;
  unsigned long parsedDuration = DEFAULT_DURATION_MS;

  if (pwmText != nullptr && !parseUnsignedLongStrict(pwmText, parsedPwm)) {
    safeStopAndDisarm("INVALID_PWM_TEXT");
    Serial.println(F("ERR:PWM must be an integer."));
    return;
  }

  if (durationText != nullptr &&
      !parseUnsignedLongStrict(durationText, parsedDuration)) {
    safeStopAndDisarm("INVALID_DURATION_TEXT");
    Serial.println(F("ERR:Duration must be an integer."));
    return;
  }

  if (parsedPwm > 255UL || parsedDuration > 65535UL) {
    safeStopAndDisarm("NUMBER_TOO_LARGE");
    Serial.println(F("ERR:Numeric argument is too large."));
    return;
  }

  startMotion(
      requestedMotion,
      static_cast<uint8_t>(parsedPwm),
      static_cast<uint16_t>(parsedDuration));
}

void serviceSerial() {
  while (Serial.available() > 0) {
    const char incoming = static_cast<char>(Serial.read());

    if (incoming == '\n' || incoming == '\r') {
      if (serialLength > 0) {
        serialBuffer[serialLength] = '\0';
        processCommand(serialBuffer);
        serialLength = 0;
        serialBuffer[0] = '\0';
      }
      continue;
    }

    if (serialLength < SERIAL_BUFFER_SIZE - 1) {
      serialBuffer[serialLength++] = incoming;
    } else {
      serialLength = 0;
      serialBuffer[0] = '\0';
      safeStopAndDisarm("SERIAL_LINE_TOO_LONG");
      Serial.println(F("ERR:Serial command was too long."));
    }
  }
}

void serviceMotionSafety() {
  if (!motionActive) {
    return;
  }

  const uint32_t now = millis();

  if (static_cast<int32_t>(now - motionEndsAtMs) >= 0) {
    safeStopAndDisarm("ACTION_COMPLETE");
    return;
  }

  if (now - motionStartedAtMs > ACTIVE_COMMAND_WATCHDOG_MS) {
    safeStopAndDisarm("WATCHDOG_TIMEOUT");
  }
}

// ---------------------------------------------------------------------------
// Arduino entry points
// ---------------------------------------------------------------------------
void setup() {
  // Load LOW into each output latch before changing the pin to OUTPUT.
  digitalWrite(PIN_STBY, LOW);
  digitalWrite(PIN_AIN1, LOW);
  digitalWrite(PIN_AIN2, LOW);
  digitalWrite(PIN_BIN1, LOW);
  digitalWrite(PIN_BIN2, LOW);
  digitalWrite(PIN_PWMA, LOW);
  digitalWrite(PIN_PWMB, LOW);

  pinMode(PIN_STBY, OUTPUT);
  pinMode(PIN_AIN1, OUTPUT);
  pinMode(PIN_AIN2, OUTPUT);
  pinMode(PIN_BIN1, OUTPUT);
  pinMode(PIN_BIN2, OUTPUT);
  pinMode(PIN_PWMA, OUTPUT);
  pinMode(PIN_PWMB, OUTPUT);

  // STBY remains LOW throughout PWM initialization.
  pwmReady = setupMotorPwm();
  safeStop("BOOT_SAFE", false);
  armed = false;

  Serial.begin(SERIAL_BAUD);
  delay(250);

  Serial.println();
  Serial.println(F("Atlas 6.0 Stage 4 safe motor test firmware started."));
  Serial.println(F("BOOT STATE: STOPPED + DISARMED + STBY LOW"));
  Serial.print(F("Arduino-ESP32 major version detected: "));
  Serial.println(ESP_ARDUINO_VERSION_MAJOR);

  if (!pwmReady) {
    Serial.println(F("FATAL:PWM initialization failed. Keep motor battery OFF."));
  } else {
    Serial.println(F("PWM initialization: OK"));
  }

  printHelp();
}

void loop() {
  serviceSerial();
  serviceMotionSafety();
  delay(1);
}
