#include <Arduino.h>
#include <WiFi.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

// ============================================================
// Atlas 6.0 Stage 8C Practical Avoidance V1
// ESP32 DEVKIT_C + L298N + two quadrature encoders + US-100
//
// Production scope:
//   - Wi-Fi TCP and USB command control.
//   - One ARM authorizes one bounded action.
//   - TCP heartbeat loss stops motion.
//   - Encoder-assisted timed forward drive (no centimetre target).
//   - US-100 fail-safe stop and one bounded avoidance manoeuvre.
//   - Exact-distance FDS is deliberately deferred.
//
// Locked hardware mapping from the passed Atlas 6.0 tests:
//   Left motor : ENA 13, IN1 14, IN2 4, software-inverted.
//   Right motor: ENB 33, IN3 32, IN4 23, normal polarity.
//   Left encoder : GPIO25 / GPIO26.
//   Right encoder: GPIO18 / GPIO19.
//   US-100 Trigger/Echo: GPIO27 / GPIO34.
// ============================================================

// -------------------- Wi-Fi TCP --------------------
constexpr char WIFI_AP_SSID[] = "ATLAS_6_0";
constexpr char WIFI_AP_PASSWORD[] = "Atlas6Stage7";
constexpr uint16_t WIFI_TCP_PORT = 3333;
constexpr uint8_t WIFI_MAX_CLIENTS = 1;
constexpr unsigned long TCP_HEARTBEAT_TIMEOUT_MS = 350;
constexpr size_t INPUT_LINE_MAX_LENGTH = 95;

WiFiServer tcpServer(WIFI_TCP_PORT);
WiFiClient tcpClient;
bool tcpClientActive = false;

class MirroredConsole : public Print {
 public:
  size_t write(uint8_t value) override {
    Serial.write(value);
    if (tcpClientActive && tcpClient.connected()) {
      tcpClient.write(value);
    }
    return 1;
  }

  size_t write(const uint8_t* buffer, size_t size) override {
    Serial.write(buffer, size);
    if (tcpClientActive && tcpClient.connected()) {
      tcpClient.write(buffer, size);
    }
    return size;
  }
};

MirroredConsole console;

// -------------------- L298N --------------------
constexpr uint8_t PIN_ENA = 13;
constexpr uint8_t PIN_IN1 = 14;
constexpr uint8_t PIN_IN2 = 4;
constexpr uint8_t PIN_ENB = 33;
constexpr uint8_t PIN_IN3 = 32;
constexpr uint8_t PIN_IN4 = 23;

constexpr bool LEFT_MOTOR_INVERTED = true;
constexpr bool RIGHT_MOTOR_INVERTED = false;

// -------------------- Encoders --------------------
constexpr uint8_t PIN_RIGHT_ENCODER_A = 18;
constexpr uint8_t PIN_RIGHT_ENCODER_B = 19;
constexpr uint8_t PIN_LEFT_ENCODER_A = 25;
constexpr uint8_t PIN_LEFT_ENCODER_B = 26;

constexpr float WHEEL_CIRCUMFERENCE_CM = 21.40f;
constexpr float LEFT_PULSES_PER_REV = 632.05f;
constexpr float RIGHT_PULSES_PER_REV = 634.17f;

// -------------------- US-100 --------------------
constexpr uint8_t PIN_US100_TRIG = 27;
constexpr uint8_t PIN_US100_ECHO = 34;
constexpr unsigned long SENSOR_SAMPLE_INTERVAL_MS = 60;
constexpr unsigned long SENSOR_ECHO_TIMEOUT_US = 25000;
constexpr float SENSOR_MIN_VALID_CM = 2.0f;
constexpr float SENSOR_MAX_VALID_CM = 400.0f;
constexpr uint8_t SENSOR_VALID_SAMPLES_REQUIRED = 3;

constexpr float FORCE_STOP_ENTER_CM = 25.0f;
constexpr float FORCE_STOP_RELEASE_CM = 28.0f;
constexpr float CAUTION_ENTER_CM = 50.0f;
constexpr float CLEAR_RELEASE_CM = 55.0f;

// -------------------- Practical mobility --------------------
constexpr int MIN_PWM = 80;
constexpr int MAX_PWM = 180;
constexpr unsigned long MIN_DRIVE_DURATION_MS = 100;
constexpr unsigned long MAX_DRIVE_DURATION_MS = 1000;

constexpr int START_BOOST_MIN_PWM = 100;
constexpr unsigned long START_BOOST_DURATION_MS = 150;

constexpr unsigned long DRIVE_CONTROL_INTERVAL_MS = 50;
constexpr unsigned long DRIVE_REPORT_INTERVAL_MS = 200;
constexpr float DRIVE_DEADBAND_EQUIV_PULSES = 3.0f;
constexpr float DRIVE_KP_PWM_PER_EQUIV_PULSE = 0.15f;
constexpr int DRIVE_MAX_BOOST_PWM = 8;
constexpr int DRIVE_MAX_PWM_STEP = 1;
constexpr int32_t DRIVE_REVERSE_LIMIT_PULSES = 20;
constexpr unsigned long DRIVE_STALL_TIMEOUT_MS = 700;

constexpr unsigned long ENCODER_CHECK_DURATION_MS = 400;
constexpr int ENCODER_CHECK_PWM = 160;
constexpr int32_t MIN_ENCODER_CHECK_PULSES = 10;
constexpr int32_t MAX_INACTIVE_CHECK_PULSES = 3;

// -------------------- Avoidance --------------------
constexpr unsigned long AVOID_DEFAULT_TIMEOUT_MS = 3000;
constexpr unsigned long AVOID_MIN_TIMEOUT_MS = 1000;
constexpr unsigned long AVOID_MAX_TIMEOUT_MS = 10000;
constexpr int AVOID_BASE_PWM = 80;
constexpr int AVOID_TURN_PWM = 100;
constexpr unsigned long AVOID_STOP_SETTLE_MS = 200;
constexpr unsigned long AVOID_RIGHT_TURN_MS = 300;
constexpr unsigned long AVOID_LEFT_SCAN_TURN_MS = 600;
constexpr uint8_t AVOID_MAX_OBSTACLE_CYCLES = 1;

// -------------------- General safety --------------------
constexpr unsigned long FINAL_SETTLE_MS = 150;

enum class CommandSource : uint8_t {
  USB_SERIAL,
  TCP
};

enum class MotionMode : uint8_t {
  NONE,
  TIMED,
  DRIVE_ASSIST,
  ENCODER_CHECK,
  AVOID
};

enum class CheckWheel : uint8_t {
  NONE,
  LEFT,
  RIGHT
};

enum class SensorState : uint8_t {
  STARTUP_STOP,
  INVALID_STOP,
  FORCE_STOP,
  CAUTION,
  CLEAR
};

enum class AvoidState : uint8_t {
  NONE,
  FORWARD,
  WAIT_BEFORE_RIGHT,
  TURN_RIGHT,
  WAIT_AFTER_RIGHT,
  SAMPLE_AFTER_RIGHT,
  TURN_LEFT_SCAN,
  WAIT_AFTER_LEFT,
  SAMPLE_AFTER_LEFT
};

// -------------------- Command and safety state --------------------
String serialLine = "";
String tcpLine = "";
String activeCommand = "NONE";

CommandSource currentCommandSource = CommandSource::USB_SERIAL;
CommandSource armedCommandSource = CommandSource::USB_SERIAL;
CommandSource activeMotionSource = CommandSource::USB_SERIAL;
bool armedCommandSourceValid = false;
unsigned long lastTcpHeartbeatMs = 0;

bool armed = false;
bool moving = false;
MotionMode motionMode = MotionMode::NONE;
CheckWheel activeCheckWheel = CheckWheel::NONE;

unsigned long motionStartMs = 0;
unsigned long motionDeadlineMs = 0;

// -------------------- Motor state --------------------
int commandedLeftSpeed = 0;
int commandedRightSpeed = 0;
int lastLeftLogicalSpeed = 0;
int lastRightLogicalSpeed = 0;

// -------------------- Encoder state --------------------
volatile int32_t rawRightEncoder = 0;
volatile int32_t rawLeftEncoder = 0;
portMUX_TYPE encoderMux = portMUX_INITIALIZER_UNLOCKED;

int8_t leftEncoderForwardSign = 0;
int8_t rightEncoderForwardSign = 0;

int driveBasePwm = 0;
int driveLeftPwm = 0;
int driveRightPwm = 0;
unsigned long driveNextControlMs = 0;
unsigned long driveNextReportMs = 0;
unsigned long drivePhaseStartMs = 0;
bool driveStartBoostActive = false;
int32_t driveLeftBestProgress = 0;
int32_t driveRightBestProgress = 0;
unsigned long driveLeftLastProgressMs = 0;
unsigned long driveRightLastProgressMs = 0;

// -------------------- Sensor state --------------------
SensorState sensorState = SensorState::STARTUP_STOP;
float lastDistanceCm = NAN;
unsigned long lastEchoDurationUs = 0;
unsigned long lastSensorSampleMs = 0;
uint8_t consecutiveValidSensorSamples = 0;
unsigned long totalValidSensorSamples = 0;
unsigned long totalInvalidSensorSamples = 0;
float distanceWindow[3] = {0.0f, 0.0f, 0.0f};
uint8_t distanceWindowCount = 0;
uint8_t distanceWindowIndex = 0;

// -------------------- Avoidance state --------------------
AvoidState avoidState = AvoidState::NONE;
unsigned long avoidSessionDeadlineMs = 0;
unsigned long avoidStateDeadlineMs = 0;
uint8_t avoidFreshValidSamples = 0;
uint8_t avoidObstacleCycles = 0;

// ============================================================
// Small helpers
// ============================================================

int clampInt(int value, int minimum, int maximum) {
  if (value < minimum) {
    return minimum;
  }
  if (value > maximum) {
    return maximum;
  }
  return value;
}

int moveIntToward(int current, int target, int maximumStep) {
  if (current < target) {
    const int difference = target - current;
    return current + (difference > maximumStep ? maximumStep : difference);
  }
  if (current > target) {
    const int difference = current - target;
    return current - (difference > maximumStep ? maximumStep : difference);
  }
  return current;
}

const char* commandSourceName(CommandSource source) {
  return source == CommandSource::TCP ? "wifi tcp" : "usb serial";
}

const char* sensorStateName(SensorState state) {
  if (state == SensorState::STARTUP_STOP) return "STARTUP_STOP";
  if (state == SensorState::INVALID_STOP) return "SENSOR_INVALID_STOP";
  if (state == SensorState::FORCE_STOP) return "FORCE_STOP";
  if (state == SensorState::CAUTION) return "CAUTION";
  return "CLEAR";
}

const char* motionModeName(MotionMode mode) {
  if (mode == MotionMode::TIMED) return "timed motion";
  if (mode == MotionMode::DRIVE_ASSIST) return "encoder-assisted timed drive";
  if (mode == MotionMode::ENCODER_CHECK) return "encoder check";
  if (mode == MotionMode::AVOID) return "bounded obstacle avoidance";
  return "none";
}

const char* avoidStateName(AvoidState state) {
  if (state == AvoidState::FORWARD) return "FORWARD";
  if (state == AvoidState::WAIT_BEFORE_RIGHT) return "WAIT_BEFORE_RIGHT";
  if (state == AvoidState::TURN_RIGHT) return "TURN_RIGHT";
  if (state == AvoidState::WAIT_AFTER_RIGHT) return "WAIT_AFTER_RIGHT";
  if (state == AvoidState::SAMPLE_AFTER_RIGHT) return "SAMPLE_AFTER_RIGHT";
  if (state == AvoidState::TURN_LEFT_SCAN) return "TURN_LEFT_SCAN";
  if (state == AvoidState::WAIT_AFTER_LEFT) return "WAIT_AFTER_LEFT";
  if (state == AvoidState::SAMPLE_AFTER_LEFT) return "SAMPLE_AFTER_LEFT";
  return "NONE";
}

// ============================================================
// Encoder interrupts and readings
// ============================================================

void IRAM_ATTR onRightEncoderA() {
  const int delta = digitalRead(PIN_RIGHT_ENCODER_B) == HIGH ? 1 : -1;
  portENTER_CRITICAL_ISR(&encoderMux);
  rawRightEncoder += delta;
  portEXIT_CRITICAL_ISR(&encoderMux);
}

void IRAM_ATTR onLeftEncoderA() {
  const int delta = digitalRead(PIN_LEFT_ENCODER_B) == HIGH ? 1 : -1;
  portENTER_CRITICAL_ISR(&encoderMux);
  rawLeftEncoder += delta;
  portEXIT_CRITICAL_ISR(&encoderMux);
}

void resetEncoderCounts() {
  portENTER_CRITICAL(&encoderMux);
  rawRightEncoder = 0;
  rawLeftEncoder = 0;
  portEXIT_CRITICAL(&encoderMux);
}

void readRawEncoderCounts(int32_t& rawLeft, int32_t& rawRight) {
  portENTER_CRITICAL(&encoderMux);
  rawLeft = rawLeftEncoder;
  rawRight = rawRightEncoder;
  portEXIT_CRITICAL(&encoderMux);
}

void readForwardEncoderCounts(int32_t& leftForward, int32_t& rightForward) {
  int32_t rawLeft;
  int32_t rawRight;
  readRawEncoderCounts(rawLeft, rawRight);
  leftForward = leftEncoderForwardSign == 0
      ? 0
      : rawLeft * leftEncoderForwardSign;
  rightForward = rightEncoderForwardSign == 0
      ? 0
      : rawRight * rightEncoderForwardSign;
}

float normalizedEquivalentPulses(int32_t pulses, float pulsesPerRev) {
  const float averagePpr =
      (LEFT_PULSES_PER_REV + RIGHT_PULSES_PER_REV) * 0.5f;
  return static_cast<float>(pulses) / pulsesPerRev * averagePpr;
}

void printEncoderReport(const char* source) {
  int32_t rawLeft;
  int32_t rawRight;
  readRawEncoderCounts(rawLeft, rawRight);

  const int32_t leftForward = leftEncoderForwardSign == 0
      ? 0
      : rawLeft * leftEncoderForwardSign;
  const int32_t rightForward = rightEncoderForwardSign == 0
      ? 0
      : rawRight * rightEncoderForwardSign;

  console.println();
  console.println("[Encoder reading]");
  console.print("source command  : ");
  console.println(source);
  console.print("left raw        : ");
  console.print(rawLeft);
  console.print(" pulses (gpio 25/26)");
  if (leftEncoderForwardSign == 0) {
    console.println("; forward sign not checked");
  } else {
    console.print("; forward pulses = ");
    console.println(leftForward);
  }
  console.print("right raw       : ");
  console.print(rawRight);
  console.print(" pulses (gpio 18/19)");
  if (rightEncoderForwardSign == 0) {
    console.println("; forward sign not checked");
  } else {
    console.print("; forward pulses = ");
    console.println(rightForward);
  }
}

// ============================================================
// Motor control
// ============================================================

void applyOneMotor(
    int requestedSpeed,
    uint8_t pinEnable,
    uint8_t pinA,
    uint8_t pinB,
    bool inverted,
    int& lastLogicalSpeed) {

  requestedSpeed = clampInt(requestedSpeed, -255, 255);
  const int previousDirection =
      lastLogicalSpeed > 0 ? 1 : (lastLogicalSpeed < 0 ? -1 : 0);
  const int requestedDirection =
      requestedSpeed > 0 ? 1 : (requestedSpeed < 0 ? -1 : 0);

  const int actualSpeed = inverted ? -requestedSpeed : requestedSpeed;

  // Only interrupt PWM when direction actually changes. Duty-only updates
  // during encoder correction do not insert a repeated zero-output gap.
  if (requestedDirection != previousDirection) {
    analogWrite(pinEnable, 0);
  }

  if (actualSpeed > 0) {
    if (requestedDirection != previousDirection) {
      digitalWrite(pinA, HIGH);
      digitalWrite(pinB, LOW);
    }
    analogWrite(pinEnable, actualSpeed);
  } else if (actualSpeed < 0) {
    if (requestedDirection != previousDirection) {
      digitalWrite(pinA, LOW);
      digitalWrite(pinB, HIGH);
    }
    analogWrite(pinEnable, -actualSpeed);
  } else {
    digitalWrite(pinA, LOW);
    digitalWrite(pinB, LOW);
    analogWrite(pinEnable, 0);
  }

  lastLogicalSpeed = requestedSpeed;
}

void setLeftMotor(int speed) {
  applyOneMotor(
      speed,
      PIN_ENA,
      PIN_IN1,
      PIN_IN2,
      LEFT_MOTOR_INVERTED,
      lastLeftLogicalSpeed);
  commandedLeftSpeed = speed;
}

void setRightMotor(int speed) {
  applyOneMotor(
      speed,
      PIN_ENB,
      PIN_IN3,
      PIN_IN4,
      RIGHT_MOTOR_INVERTED,
      lastRightLogicalSpeed);
  commandedRightSpeed = speed;
}

void driveMotors(int leftSpeed, int rightSpeed) {
  setLeftMotor(leftSpeed);
  setRightMotor(rightSpeed);
}

void stopMotorsImmediately() {
  driveMotors(0, 0);
}

bool hasForwardComponent() {
  return commandedLeftSpeed > 0 || commandedRightSpeed > 0;
}

// ============================================================
// US-100 sampling and state transitions
// ============================================================

float medianOfThree(float a, float b, float c) {
  if (a > b) { const float temporary = a; a = b; b = temporary; }
  if (b > c) { const float temporary = b; b = c; c = temporary; }
  if (a > b) { const float temporary = a; a = b; b = temporary; }
  return b;
}

float filteredDistanceCm() {
  if (distanceWindowCount < 3) {
    return NAN;
  }
  return medianOfThree(
      distanceWindow[0],
      distanceWindow[1],
      distanceWindow[2]);
}

void resetSensorFilter() {
  consecutiveValidSensorSamples = 0;
  distanceWindowCount = 0;
  distanceWindowIndex = 0;
}

bool sampleUs100(bool forceSample) {
  const unsigned long now = millis();
  if (!forceSample &&
      now - lastSensorSampleMs < SENSOR_SAMPLE_INTERVAL_MS) {
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
      SENSOR_ECHO_TIMEOUT_US);
  lastEchoDurationUs = durationUs;

  const float measuredCm =
      static_cast<float>(durationUs) * 0.0343f * 0.5f;
  const bool valid =
      durationUs > 0 &&
      measuredCm >= SENSOR_MIN_VALID_CM &&
      measuredCm <= SENSOR_MAX_VALID_CM;

  if (!valid) {
    ++totalInvalidSensorSamples;
    lastDistanceCm = NAN;
    sensorState = SensorState::INVALID_STOP;
    resetSensorFilter();
    return true;
  }

  ++totalValidSensorSamples;
  lastDistanceCm = measuredCm;
  if (consecutiveValidSensorSamples < 255) {
    ++consecutiveValidSensorSamples;
  }
  if (motionMode == MotionMode::AVOID && avoidFreshValidSamples < 255) {
    ++avoidFreshValidSamples;
  }

  distanceWindow[distanceWindowIndex] = measuredCm;
  distanceWindowIndex = (distanceWindowIndex + 1) % 3;
  if (distanceWindowCount < 3) {
    ++distanceWindowCount;
  }

  // One reliable near reading is enough for an immediate emergency stop.
  if (measuredCm < FORCE_STOP_ENTER_CM) {
    sensorState = SensorState::FORCE_STOP;
    return true;
  }

  if (consecutiveValidSensorSamples < SENSOR_VALID_SAMPLES_REQUIRED ||
      distanceWindowCount < 3) {
    sensorState = SensorState::STARTUP_STOP;
    return true;
  }

  const float filteredCm = filteredDistanceCm();
  const SensorState previousState = sensorState;

  if (previousState == SensorState::FORCE_STOP) {
    if (filteredCm < FORCE_STOP_RELEASE_CM) {
      sensorState = SensorState::FORCE_STOP;
    } else if (filteredCm <= CAUTION_ENTER_CM) {
      sensorState = SensorState::CAUTION;
    } else {
      sensorState = SensorState::CLEAR;
    }
  } else if (previousState == SensorState::CAUTION) {
    if (filteredCm < FORCE_STOP_ENTER_CM) {
      sensorState = SensorState::FORCE_STOP;
    } else if (filteredCm < CLEAR_RELEASE_CM) {
      sensorState = SensorState::CAUTION;
    } else {
      sensorState = SensorState::CLEAR;
    }
  } else {
    sensorState = filteredCm <= CAUTION_ENTER_CM
        ? SensorState::CAUTION
        : SensorState::CLEAR;
  }

  return true;
}

void printSensorReport() {
  console.println();
  console.println("[US-100 distance report]");
  console.print("state           : ");
  console.println(sensorStateName(sensorState));
  console.print("last distance   : ");
  if (isfinite(lastDistanceCm)) {
    console.print(lastDistanceCm, 2);
    console.println(" cm");
  } else {
    console.println("invalid");
  }
  console.print("filtered        : ");
  const float filtered = filteredDistanceCm();
  if (isfinite(filtered)) {
    console.print(filtered, 2);
    console.println(" cm");
  } else {
    console.println("not ready");
  }
  console.print("valid / invalid : ");
  console.print(totalValidSensorSamples);
  console.print(" / ");
  console.println(totalInvalidSensorSamples);
}

// ============================================================
// Motion lifecycle
// ============================================================

void clearMotionState() {
  moving = false;
  motionMode = MotionMode::NONE;
  activeCommand = "NONE";
  activeCheckWheel = CheckWheel::NONE;
  activeMotionSource = CommandSource::USB_SERIAL;
  motionStartMs = 0;
  motionDeadlineMs = 0;

  driveBasePwm = 0;
  driveLeftPwm = 0;
  driveRightPwm = 0;
  driveNextControlMs = 0;
  driveNextReportMs = 0;
  drivePhaseStartMs = 0;
  driveStartBoostActive = false;
  driveLeftBestProgress = 0;
  driveRightBestProgress = 0;
  driveLeftLastProgressMs = 0;
  driveRightLastProgressMs = 0;

  avoidState = AvoidState::NONE;
  avoidSessionDeadlineMs = 0;
  avoidStateDeadlineMs = 0;
  avoidFreshValidSamples = 0;
  avoidObstacleCycles = 0;
}

const char* friendlyReason(const char* reason) {
  if (strcmp(reason, "ACTION_COMPLETE") == 0)
    return "Timed motion finished normally.";
  if (strcmp(reason, "DRIVE_COMPLETE") == 0)
    return "Encoder-assisted timed drive finished normally.";
  if (strcmp(reason, "AVOID_SESSION_COMPLETE") == 0)
    return "The bounded avoidance session reached its safe time limit.";
  if (strcmp(reason, "USER_STOP") == 0)
    return "Stopped by the user.";
  if (strcmp(reason, "TCP_DISCONNECT") == 0)
    return "The Wi-Fi TCP client disconnected.";
  if (strcmp(reason, "TCP_HEARTBEAT_TIMEOUT") == 0)
    return "The Wi-Fi TCP heartbeat timed out.";
  if (strcmp(reason, "STALL_LEFT") == 0)
    return "Left forward encoder made no progress for 700 ms.";
  if (strcmp(reason, "STALL_RIGHT") == 0)
    return "Right forward encoder made no progress for 700 ms.";
  if (strcmp(reason, "REVERSE_LEFT") == 0)
    return "Left forward count became negative beyond the safe limit.";
  if (strcmp(reason, "REVERSE_RIGHT") == 0)
    return "Right forward count became negative beyond the safe limit.";
  if (strcmp(reason, "SENSOR_INVALID_STOP") == 0)
    return "US-100 returned an invalid reading; fail-safe stop applied.";
  if (strcmp(reason, "OBSTACLE_FORCE_STOP") == 0)
    return "Obstacle entered the FORCE_STOP range.";
  if (strcmp(reason, "OBSTACLE_CAUTION_STOP") == 0)
    return "Obstacle entered the CAUTION range during timed drive.";
  if (strcmp(reason, "NO_CLEAR_PATH") == 0)
    return "No clear path was found after the bounded right/left scan.";
  if (strcmp(reason, "SECOND_OBSTACLE_STOP") == 0)
    return "A second obstacle was detected; the one-cycle avoider stopped safely.";
  return "Motion stopped by a safety or command rule.";
}

bool reasonPassed(const char* reason) {
  return strcmp(reason, "ACTION_COMPLETE") == 0 ||
      strcmp(reason, "DRIVE_COMPLETE") == 0 ||
      strcmp(reason, "AVOID_SESSION_COMPLETE") == 0;
}

void finishMotion(const char* reason) {
  const bool wasMoving = moving;
  const String finishedCommand = activeCommand;
  const MotionMode finishedMode = motionMode;
  const AvoidState finishedAvoidState = avoidState;
  const unsigned long elapsed = motionStartMs > 0
      ? millis() - motionStartMs
      : 0;

  stopMotorsImmediately();
  moving = false;
  if (wasMoving) {
    delay(FINAL_SETTLE_MS);
  }

  armed = false;
  armedCommandSourceValid = false;

  String reasonCode = String(reason);
  reasonCode.toLowerCase();
  String displayCommand = finishedCommand;
  displayCommand.toLowerCase();

  console.println();
  console.println("========================================");
  console.println("[Motion finished]");
  console.print("result          : ");
  console.println(reasonPassed(reason) ? "passed" : "not passed");
  console.print("reason          : ");
  console.println(friendlyReason(reason));
  console.print("reason code     : ");
  console.println(reasonCode);
  console.print("command         : ");
  console.println(displayCommand);
  console.print("elapsed         : ");
  console.print(elapsed);
  console.println(" ms");
  console.println("safety          : disarmed");

  if (wasMoving) {
    printEncoderReport(finishedCommand.c_str());
  }
  if (finishedMode == MotionMode::DRIVE_ASSIST ||
      finishedMode == MotionMode::AVOID) {
    console.println();
    console.println("[Practical controller report]");
    console.print("base PWM        : ");
    console.println(driveBasePwm);
    console.print("final PWM       : ");
    console.print(driveLeftPwm);
    console.print(" / ");
    console.println(driveRightPwm);
    console.print("avoid state     : ");
    console.println(avoidStateName(finishedAvoidState));
    console.println("distance target : not used");
  }

  console.println("next            : inspect the result; send arm before another action");
  console.println("========================================");
  clearMotionState();
}

bool motionStartAllowed() {
  if (moving) {
    finishMotion("NEW_ACTION_DURING_MOTION");
    return false;
  }
  if (!armed) {
    console.println();
    console.println("[Command rejected]");
    console.println("reason code     : not_armed");
    console.println("next            : send arm, then one motion command");
    return false;
  }
  if (!armedCommandSourceValid || armedCommandSource != currentCommandSource) {
    stopMotorsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    console.println();
    console.println("[Command rejected]");
    console.println("reason code     : arm_source_mismatch");
    console.println("next            : arm and action must use the same USB or TCP link");
    return false;
  }
  return true;
}

bool encoderChecksPassed() {
  if (leftEncoderForwardSign == 0 || rightEncoderForwardSign == 0) {
    stopMotorsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    console.println();
    console.println("[Command rejected]");
    console.println("reason code     : encoder_checks_required");
    console.println("next            : arm + check left, then arm + check right");
    return false;
  }
  return true;
}

bool forwardSensorAllowsStart() {
  if (sensorState != SensorState::CLEAR) {
    stopMotorsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    console.println();
    console.println("[Command rejected]");
    console.print("sensor state    : ");
    console.println(sensorStateName(sensorState));
    console.println("reason code     : forward_not_clear");
    console.println("next            : restore a valid distance above 55 cm, then arm again");
    return false;
  }
  return true;
}

// ============================================================
// Encoder check
// ============================================================

void startEncoderCheck(CheckWheel wheel) {
  if (!motionStartAllowed()) {
    return;
  }

  resetEncoderCounts();
  activeCheckWheel = wheel;
  activeCommand = wheel == CheckWheel::LEFT
      ? "CHECK LEFT"
      : "CHECK RIGHT";
  motionMode = MotionMode::ENCODER_CHECK;
  moving = true;
  activeMotionSource = currentCommandSource;
  motionStartMs = millis();
  motionDeadlineMs = motionStartMs + ENCODER_CHECK_DURATION_MS;

  if (wheel == CheckWheel::LEFT) {
    driveMotors(ENCODER_CHECK_PWM, 0);
  } else {
    driveMotors(0, ENCODER_CHECK_PWM);
  }

  console.println();
  console.println("[Encoder check started]");
  console.print("wheel           : ");
  console.println(wheel == CheckWheel::LEFT ? "left" : "right");
  console.println("required setup  : both wheels at least 2 cm above the surface");
  console.println("visual check    : active wheel must rotate forward");
}

void finishEncoderCheck() {
  const CheckWheel checkedWheel = activeCheckWheel;
  stopMotorsImmediately();
  moving = false;
  delay(FINAL_SETTLE_MS);

  int32_t rawLeft;
  int32_t rawRight;
  readRawEncoderCounts(rawLeft, rawRight);
  const int32_t activeRaw = checkedWheel == CheckWheel::LEFT
      ? rawLeft
      : rawRight;
  const int32_t inactiveRaw = checkedWheel == CheckWheel::LEFT
      ? rawRight
      : rawLeft;

  const bool enoughPulses = labs(activeRaw) >= MIN_ENCODER_CHECK_PULSES;
  const bool inactiveQuiet = labs(inactiveRaw) <= MAX_INACTIVE_CHECK_PULSES;
  const bool passed = enoughPulses && inactiveQuiet;

  if (passed) {
    const int8_t learnedSign = activeRaw >= 0 ? 1 : -1;
    if (checkedWheel == CheckWheel::LEFT) {
      leftEncoderForwardSign = learnedSign;
    } else {
      rightEncoderForwardSign = learnedSign;
    }
  }

  armed = false;
  armedCommandSourceValid = false;

  console.println();
  console.println("========================================");
  console.println("[Encoder check finished]");
  console.print("wheel           : ");
  console.println(checkedWheel == CheckWheel::LEFT ? "left" : "right");
  console.print("active raw      : ");
  console.println(activeRaw);
  console.print("other raw       : ");
  console.println(inactiveRaw);
  console.print("result          : ");
  console.println(passed ? "pulse check passed" : "pulse check not passed");
  if (passed) {
    console.println("visual decision : continue only if the active wheel moved forward");
    console.println("next            : arm and check the other wheel, or begin final testing");
  } else {
    console.println("next            : stop and inspect encoder power/signal wiring");
  }
  console.println("safety          : disarmed");
  console.println("========================================");
  clearMotionState();
}

// ============================================================
// Encoder-assisted timed forward drive
// ============================================================

void initializeDriveController(int basePwm) {
  resetEncoderCounts();
  driveBasePwm = basePwm;
  const int startPwm = basePwm < START_BOOST_MIN_PWM
      ? START_BOOST_MIN_PWM
      : basePwm;
  driveLeftPwm = startPwm;
  driveRightPwm = startPwm;
  const unsigned long now = millis();
  drivePhaseStartMs = now;
  driveStartBoostActive = basePwm < START_BOOST_MIN_PWM;
  driveNextControlMs = now + DRIVE_CONTROL_INTERVAL_MS;
  driveNextReportMs = now + DRIVE_REPORT_INTERVAL_MS;
  driveLeftBestProgress = 0;
  driveRightBestProgress = 0;
  driveLeftLastProgressMs = now;
  driveRightLastProgressMs = now;
  driveMotors(driveLeftPwm, driveRightPwm);
}

void startDriveAssist(int basePwm, unsigned long durationMs) {
  if (!motionStartAllowed() ||
      !encoderChecksPassed() ||
      !forwardSensorAllowsStart()) {
    return;
  }
  if (basePwm < MIN_PWM || basePwm > MAX_PWM) {
    stopMotorsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    console.println("Error: DRIVE PWM must be between 80 and 180.");
    return;
  }
  if (durationMs < MIN_DRIVE_DURATION_MS ||
      durationMs > MAX_DRIVE_DURATION_MS) {
    stopMotorsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    console.println("Error: DRIVE duration must be between 100 and 1000 ms.");
    return;
  }

  activeCommand = "DRIVE";
  motionMode = MotionMode::DRIVE_ASSIST;
  moving = true;
  activeMotionSource = currentCommandSource;
  motionStartMs = millis();
  motionDeadlineMs = motionStartMs + durationMs;
  initializeDriveController(basePwm);

  console.println();
  console.println("[Encoder-assisted drive started]");
  console.print("base PWM        : ");
  console.println(basePwm);
  console.print("start PWM       : ");
  console.println(driveLeftPwm);
  console.print("start boost     : ");
  console.print(START_BOOST_DURATION_MS);
  console.println(" ms");
  console.print("duration        : ");
  console.print(durationMs);
  console.println(" ms");
  console.println("distance target : not used");
}

bool monitorForwardEncoderController(const char* reportPrefix) {
  const unsigned long now = millis();
  int32_t leftForward;
  int32_t rightForward;
  readForwardEncoderCounts(leftForward, rightForward);

  if (leftForward < -DRIVE_REVERSE_LIMIT_PULSES) {
    finishMotion("REVERSE_LEFT");
    return false;
  }
  if (rightForward < -DRIVE_REVERSE_LIMIT_PULSES) {
    finishMotion("REVERSE_RIGHT");
    return false;
  }

  if (leftForward > driveLeftBestProgress) {
    driveLeftBestProgress = leftForward;
    driveLeftLastProgressMs = now;
  }
  if (rightForward > driveRightBestProgress) {
    driveRightBestProgress = rightForward;
    driveRightLastProgressMs = now;
  }

  if (now - driveLeftLastProgressMs >= DRIVE_STALL_TIMEOUT_MS) {
    finishMotion("STALL_LEFT");
    return false;
  }
  if (now - driveRightLastProgressMs >= DRIVE_STALL_TIMEOUT_MS) {
    finishMotion("STALL_RIGHT");
    return false;
  }

  if (static_cast<int32_t>(now - driveNextControlMs) < 0) {
    return true;
  }
  do {
    driveNextControlMs += DRIVE_CONTROL_INTERVAL_MS;
  } while (static_cast<int32_t>(now - driveNextControlMs) >= 0);

  int targetLeftPwm = driveBasePwm;
  int targetRightPwm = driveBasePwm;

  if (now - drivePhaseStartMs < START_BOOST_DURATION_MS) {
    targetLeftPwm = driveBasePwm < START_BOOST_MIN_PWM
        ? START_BOOST_MIN_PWM
        : driveBasePwm;
    targetRightPwm = targetLeftPwm;
  } else {
    // End the short static-friction boost in one duty update. Subsequent
    // encoder corrections still change by at most one PWM per control step.
    if (driveStartBoostActive) {
      driveStartBoostActive = false;
      driveLeftPwm = driveBasePwm;
      driveRightPwm = driveBasePwm;
      driveMotors(driveLeftPwm, driveRightPwm);
    }

    const float leftEquivalent = normalizedEquivalentPulses(
        leftForward,
        LEFT_PULSES_PER_REV);
    const float rightEquivalent = normalizedEquivalentPulses(
        rightForward,
        RIGHT_PULSES_PER_REV);
    const float error = leftEquivalent - rightEquivalent;

    if (error > DRIVE_DEADBAND_EQUIV_PULSES) {
      int boost = static_cast<int>(lroundf(
          (error - DRIVE_DEADBAND_EQUIV_PULSES) *
          DRIVE_KP_PWM_PER_EQUIV_PULSE));
      boost = clampInt(boost < 1 ? 1 : boost, 1, DRIVE_MAX_BOOST_PWM);
      targetRightPwm = driveBasePwm + boost;
    } else if (error < -DRIVE_DEADBAND_EQUIV_PULSES) {
      int boost = static_cast<int>(lroundf(
          (-error - DRIVE_DEADBAND_EQUIV_PULSES) *
          DRIVE_KP_PWM_PER_EQUIV_PULSE));
      boost = clampInt(boost < 1 ? 1 : boost, 1, DRIVE_MAX_BOOST_PWM);
      targetLeftPwm = driveBasePwm + boost;
    }
  }

  targetLeftPwm = clampInt(targetLeftPwm, MIN_PWM, MAX_PWM);
  targetRightPwm = clampInt(targetRightPwm, MIN_PWM, MAX_PWM);
  driveLeftPwm = moveIntToward(
      driveLeftPwm,
      targetLeftPwm,
      DRIVE_MAX_PWM_STEP);
  driveRightPwm = moveIntToward(
      driveRightPwm,
      targetRightPwm,
      DRIVE_MAX_PWM_STEP);
  driveMotors(driveLeftPwm, driveRightPwm);

  if (static_cast<int32_t>(now - driveNextReportMs) >= 0) {
    driveNextReportMs = now + DRIVE_REPORT_INTERVAL_MS;
    console.print(reportPrefix);
    console.print(" t=");
    console.print(now - motionStartMs);
    console.print(" ms; L=");
    console.print(leftForward);
    console.print("; R=");
    console.print(rightForward);
    console.print("; PWM=");
    console.print(driveLeftPwm);
    console.print("/");
    console.println(driveRightPwm);
  }

  return true;
}

void monitorDriveAssist() {
  if (!moving || motionMode != MotionMode::DRIVE_ASSIST) {
    return;
  }

  if (sensorState == SensorState::INVALID_STOP ||
      sensorState == SensorState::STARTUP_STOP) {
    finishMotion("SENSOR_INVALID_STOP");
    return;
  }
  if (sensorState == SensorState::FORCE_STOP) {
    finishMotion("OBSTACLE_FORCE_STOP");
    return;
  }
  if (sensorState == SensorState::CAUTION) {
    finishMotion("OBSTACLE_CAUTION_STOP");
    return;
  }
  if (static_cast<int32_t>(millis() - motionDeadlineMs) >= 0) {
    finishMotion("DRIVE_COMPLETE");
    return;
  }
  monitorForwardEncoderController("DRIVE");
}

// ============================================================
// Other bounded timed actions
// ============================================================

bool isOtherTimedCommand(const String& command) {
  return command == "B" || command == "TL" || command == "TR" ||
      command == "LF" || command == "LB" ||
      command == "RF" || command == "RB";
}

void startOtherTimedMotion(
    const String& command,
    int pwm,
    unsigned long durationMs) {

  if (!motionStartAllowed()) {
    return;
  }
  if (pwm < MIN_PWM || pwm > MAX_PWM ||
      durationMs < MIN_DRIVE_DURATION_MS ||
      durationMs > MAX_DRIVE_DURATION_MS) {
    stopMotorsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    console.println("Error: PWM 80-180; duration 100-1000 ms.");
    return;
  }

  int leftSpeed = 0;
  int rightSpeed = 0;
  if (command == "B") { leftSpeed = -pwm; rightSpeed = -pwm; }
  else if (command == "TL") { leftSpeed = -pwm; rightSpeed = pwm; }
  else if (command == "TR") { leftSpeed = pwm; rightSpeed = -pwm; }
  else if (command == "LF") { leftSpeed = pwm; }
  else if (command == "LB") { leftSpeed = -pwm; }
  else if (command == "RF") { rightSpeed = pwm; }
  else if (command == "RB") { rightSpeed = -pwm; }

  activeCommand = command;
  motionMode = MotionMode::TIMED;
  moving = true;
  activeMotionSource = currentCommandSource;
  motionStartMs = millis();
  motionDeadlineMs = motionStartMs + durationMs;
  resetEncoderCounts();
  driveMotors(leftSpeed, rightSpeed);

  console.println();
  console.println("[Bounded timed motion started]");
  console.print("command         : ");
  console.println(command);
  console.print("PWM / duration  : ");
  console.print(pwm);
  console.print(" / ");
  console.print(durationMs);
  console.println(" ms");
}

// ============================================================
// Bounded obstacle avoidance
// ============================================================

void beginAvoidForward() {
  avoidState = AvoidState::FORWARD;
  initializeDriveController(AVOID_BASE_PWM);
  console.println();
  console.println("[Avoidance state]");
  console.println("state           : FORWARD");
  console.println("controller      : encoder-assisted timed drive");
}

void beginAvoidWait(AvoidState state, unsigned long waitMs) {
  stopMotorsImmediately();
  avoidState = state;
  avoidStateDeadlineMs = millis() + waitMs;
  avoidFreshValidSamples = 0;
}

void beginAvoidTurn(AvoidState state, int leftSpeed, int rightSpeed,
                    unsigned long durationMs) {
  resetEncoderCounts();
  avoidState = state;
  avoidStateDeadlineMs = millis() + durationMs;
  driveMotors(leftSpeed, rightSpeed);
  console.println();
  console.println("[Avoidance state]");
  console.print("state           : ");
  console.println(avoidStateName(state));
  console.print("PWM / duration  : ");
  console.print(AVOID_TURN_PWM);
  console.print(" / ");
  console.print(durationMs);
  console.println(" ms");
}

void startAvoidance(unsigned long sessionDurationMs) {
  if (!motionStartAllowed() || !encoderChecksPassed()) {
    return;
  }
  if (sessionDurationMs < AVOID_MIN_TIMEOUT_MS ||
      sessionDurationMs > AVOID_MAX_TIMEOUT_MS) {
    stopMotorsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    console.println();
    console.println("[Command rejected]");
    console.println("reason code     : invalid_avoid_duration");
    console.println("allowed         : 1000 to 10000 ms");
    return;
  }
  if (sensorState == SensorState::INVALID_STOP ||
      sensorState == SensorState::STARTUP_STOP ||
      sensorState == SensorState::FORCE_STOP) {
    stopMotorsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    console.println();
    console.println("[Command rejected]");
    console.print("sensor state    : ");
    console.println(sensorStateName(sensorState));
    console.println("reason code     : avoid_start_not_safe");
    console.println("next            : restore a valid distance of at least 25 cm");
    return;
  }

  activeCommand = "AVOID";
  motionMode = MotionMode::AVOID;
  moving = true;
  activeMotionSource = currentCommandSource;
  motionStartMs = millis();
  avoidSessionDeadlineMs = motionStartMs + sessionDurationMs;
  avoidObstacleCycles = 0;

  console.println();
  console.println("[Bounded avoidance started]");
  console.print("session timeout : ");
  console.print(sessionDurationMs);
  console.println(" ms");
  console.println("reverse motion  : disabled; no rear sensor is installed");

  if (sensorState == SensorState::CLEAR) {
    beginAvoidForward();
  } else {
    avoidObstacleCycles = 1;
    beginAvoidWait(AvoidState::WAIT_BEFORE_RIGHT, AVOID_STOP_SETTLE_MS);
    console.println("initial state   : CAUTION; preparing right scan");
  }
}

void monitorAvoidance() {
  if (!moving || motionMode != MotionMode::AVOID) {
    return;
  }

  const unsigned long now = millis();
  if (static_cast<int32_t>(now - avoidSessionDeadlineMs) >= 0) {
    finishMotion("AVOID_SESSION_COMPLETE");
    return;
  }
  if (sensorState == SensorState::INVALID_STOP) {
    finishMotion("SENSOR_INVALID_STOP");
    return;
  }
  const bool rebuildingSensorWindow =
      avoidState == AvoidState::SAMPLE_AFTER_RIGHT ||
      avoidState == AvoidState::SAMPLE_AFTER_LEFT;
  if (sensorState == SensorState::STARTUP_STOP &&
      !rebuildingSensorWindow) {
    finishMotion("SENSOR_INVALID_STOP");
    return;
  }
  if (sensorState == SensorState::FORCE_STOP) {
    finishMotion("OBSTACLE_FORCE_STOP");
    return;
  }

  if (avoidState == AvoidState::FORWARD) {
    if (sensorState == SensorState::CAUTION) {
      if (avoidObstacleCycles >= AVOID_MAX_OBSTACLE_CYCLES) {
        finishMotion("SECOND_OBSTACLE_STOP");
        return;
      }
      ++avoidObstacleCycles;
      beginAvoidWait(AvoidState::WAIT_BEFORE_RIGHT, AVOID_STOP_SETTLE_MS);
      console.println();
      console.println("[Avoidance state]");
      console.println("state           : CAUTION_STOP");
      console.println("next            : bounded right scan");
      return;
    }
    monitorForwardEncoderController("AVOID");
    return;
  }

  if (avoidState == AvoidState::WAIT_BEFORE_RIGHT &&
      static_cast<int32_t>(now - avoidStateDeadlineMs) >= 0) {
    beginAvoidTurn(
        AvoidState::TURN_RIGHT,
        AVOID_TURN_PWM,
        -AVOID_TURN_PWM,
        AVOID_RIGHT_TURN_MS);
    return;
  }

  if (avoidState == AvoidState::TURN_RIGHT &&
      static_cast<int32_t>(now - avoidStateDeadlineMs) >= 0) {
    beginAvoidWait(AvoidState::WAIT_AFTER_RIGHT, AVOID_STOP_SETTLE_MS);
    return;
  }

  if (avoidState == AvoidState::WAIT_AFTER_RIGHT &&
      static_cast<int32_t>(now - avoidStateDeadlineMs) >= 0) {
    avoidState = AvoidState::SAMPLE_AFTER_RIGHT;
    avoidFreshValidSamples = 0;
    resetSensorFilter();
    return;
  }

  if (avoidState == AvoidState::SAMPLE_AFTER_RIGHT &&
      avoidFreshValidSamples >= SENSOR_VALID_SAMPLES_REQUIRED) {
    if (sensorState == SensorState::CLEAR) {
      beginAvoidForward();
    } else {
      beginAvoidTurn(
          AvoidState::TURN_LEFT_SCAN,
          -AVOID_TURN_PWM,
          AVOID_TURN_PWM,
          AVOID_LEFT_SCAN_TURN_MS);
    }
    return;
  }

  if (avoidState == AvoidState::TURN_LEFT_SCAN &&
      static_cast<int32_t>(now - avoidStateDeadlineMs) >= 0) {
    beginAvoidWait(AvoidState::WAIT_AFTER_LEFT, AVOID_STOP_SETTLE_MS);
    return;
  }

  if (avoidState == AvoidState::WAIT_AFTER_LEFT &&
      static_cast<int32_t>(now - avoidStateDeadlineMs) >= 0) {
    avoidState = AvoidState::SAMPLE_AFTER_LEFT;
    avoidFreshValidSamples = 0;
    resetSensorFilter();
    return;
  }

  if (avoidState == AvoidState::SAMPLE_AFTER_LEFT &&
      avoidFreshValidSamples >= SENSOR_VALID_SAMPLES_REQUIRED) {
    if (sensorState == SensorState::CLEAR) {
      beginAvoidForward();
    } else {
      finishMotion("NO_CLEAR_PATH");
    }
  }
}

// ============================================================
// Status, config, help
// ============================================================

void printStatus() {
  int32_t leftForward;
  int32_t rightForward;
  readForwardEncoderCounts(leftForward, rightForward);

  console.println();
  console.println("[Current status]");
  console.print("safety          : ");
  console.println(armed ? "armed" : "disarmed");
  console.print("motors          : ");
  console.println(moving ? "moving" : "stopped");
  console.print("mode            : ");
  console.println(motionModeName(motionMode));
  console.print("active command  : ");
  console.println(activeCommand);
  console.print("control source  : ");
  if (moving) console.println(commandSourceName(activeMotionSource));
  else if (armed && armedCommandSourceValid)
    console.println(commandSourceName(armedCommandSource));
  else console.println("none");
  console.print("sensor state    : ");
  console.println(sensorStateName(sensorState));
  console.print("distance        : ");
  if (isfinite(lastDistanceCm)) {
    console.print(lastDistanceCm, 2);
    console.println(" cm");
  } else {
    console.println("invalid");
  }
  console.print("encoder checks  : left ");
  console.print(leftEncoderForwardSign == 0 ? "required" : "passed");
  console.print(", right ");
  console.println(rightEncoderForwardSign == 0 ? "required" : "passed");
  console.print("forward pulses  : ");
  console.print(leftForward);
  console.print(" / ");
  console.println(rightForward);
  console.print("wifi AP         : ");
  console.println(WIFI_AP_SSID);
  console.print("wifi IP         : ");
  console.println(WiFi.softAPIP());
  console.print("tcp client      : ");
  console.println(tcpClientActive && tcpClient.connected()
      ? "connected"
      : "not connected");
}

void printConfig() {
  console.println();
  console.println("[Atlas 6.0 Stage 8C configuration]");
  console.println("distance FDS    : deferred / disabled");
  console.print("wheel circle    : ");
  console.print(WHEEL_CIRCUMFERENCE_CM, 2);
  console.println(" cm");
  console.print("PPR left/right  : ");
  console.print(LEFT_PULSES_PER_REV, 2);
  console.print(" / ");
  console.println(RIGHT_PULSES_PER_REV, 2);
  console.print("start boost     : PWM ");
  console.print(START_BOOST_MIN_PWM);
  console.print(" for ");
  console.print(START_BOOST_DURATION_MS);
  console.println(" ms");
  console.print("drive correction: every ");
  console.print(DRIVE_CONTROL_INTERVAL_MS);
  console.print(" ms, max +");
  console.println(DRIVE_MAX_BOOST_PWM);
  console.print("stall stop      : ");
  console.print(DRIVE_STALL_TIMEOUT_MS);
  console.println(" ms no progress");
  console.print("sensor limits   : FORCE <");
  console.print(FORCE_STOP_ENTER_CM, 0);
  console.print("; CAUTION <=");
  console.print(CAUTION_ENTER_CM, 0);
  console.print("; resume >");
  console.print(CLEAR_RELEASE_CM, 0);
  console.println(" cm");
  console.print("heartbeat stop  : ");
  console.print(TCP_HEARTBEAT_TIMEOUT_MS);
  console.println(" ms");
}

void printHelp() {
  console.println();
  console.println("[Command guide]");
  console.println("Information and safety:");
  console.println("  status              show state and current distance");
  console.println("  sensor              force a US-100 report");
  console.println("  enc                 show encoder counts");
  console.println("  config              show locked parameters");
  console.println("  help                show this guide");
  console.println("  arm                 authorize one bounded action");
  console.println("  stop                stop immediately and disarm");
  console.println();
  console.println("After every ESP32 restart, wheels suspended:");
  console.println("  arm  then  check left");
  console.println("  arm  then  check right");
  console.println();
  console.println("Production ground drive, sensor must be CLEAR:");
  console.println("  arm  then  drive 80 1000");
  console.println("  f 80 1000 is a compatible alias for DRIVE");
  console.println();
  console.println("Bounded obstacle avoidance:");
  console.println("  arm  then  avoid 3000");
  console.println("  avoid without a number also uses 3000 ms");
  console.println();
  console.println("Other bounded manual motions:");
  console.println("  b / tl / tr / lf / lb / rf / rb  PWM  time_ms");
  console.println();
  console.println("Exact-distance commands FD/FDS are disabled by design.");
}

// ============================================================
// Parsing and commands
// ============================================================

bool parseLongStrict(const char* text, long& value) {
  if (text == nullptr || *text == '\0') {
    return false;
  }
  char* endPointer = nullptr;
  value = strtol(text, &endPointer, 10);
  return endPointer != text && *endPointer == '\0';
}

void rejectCommand(const char* reason, const String& input) {
  stopMotorsImmediately();
  armed = false;
  armedCommandSourceValid = false;
  String reasonCode = String(reason);
  reasonCode.toLowerCase();
  console.println();
  console.println("[Command rejected]");
  console.print("reason code     : ");
  console.println(reasonCode);
  console.print("input           : ");
  console.println(input);
  console.println("next            : send help to view the command guide");
}

void processCommand(String line, CommandSource source) {
  line.trim();
  if (line.length() == 0) {
    return;
  }

  String receivedLine = line;
  line.toUpperCase();
  currentCommandSource = source;

  if (line == "PING") {
    if (source == CommandSource::TCP) {
      lastTcpHeartbeatMs = millis();
    }
    if (source == CommandSource::TCP &&
        tcpClientActive && tcpClient.connected()) {
      tcpClient.println("PONG");
    } else {
      console.println("PONG");
    }
    return;
  }

  console.println();
  console.print("Received        : ");
  console.println(receivedLine);

  if (line == "STOP") {
    finishMotion("USER_STOP");
    return;
  }

  if (line == "ARM") {
    if (moving) {
      finishMotion("ARM_DURING_MOTION");
      console.println("Send arm again after the motors stop.");
      return;
    }
    stopMotorsImmediately();
    clearMotionState();
    armed = true;
    armedCommandSource = source;
    armedCommandSourceValid = true;
    console.println();
    console.println("[Ready]");
    console.println("safety          : armed for one bounded action");
    console.println("next            : send one motion command");
    return;
  }

  if (line == "STATUS") { printStatus(); return; }
  if (line == "CONFIG") { printConfig(); return; }
  if (line == "HELP") { printHelp(); return; }
  if (line == "ENC") { printEncoderReport("manual request"); return; }
  if (line == "SENSOR") {
    sampleUs100(true);
    printSensorReport();
    return;
  }
  char commandBuffer[16] = {0};
  char argument1[24] = {0};
  char argument2[24] = {0};
  char extraBuffer[16] = {0};
  const int fieldCount = sscanf(
      line.c_str(),
      "%15s %23s %23s %15s",
      commandBuffer,
      argument1,
      argument2,
      extraBuffer);

  String command = String(commandBuffer);
  command.toUpperCase();

  if (command == "AVOID") {
    if (fieldCount != 1 && fieldCount != 2) {
      rejectCommand("INVALID_AVOID_FORMAT", receivedLine);
      console.println("Expected format : avoid 3000");
      return;
    }
    unsigned long durationMs = AVOID_DEFAULT_TIMEOUT_MS;
    if (fieldCount == 2) {
      long durationLong;
      if (!parseLongStrict(argument1, durationLong) || durationLong < 0) {
        rejectCommand("INVALID_AVOID_NUMBER", receivedLine);
        return;
      }
      durationMs = static_cast<unsigned long>(durationLong);
    }
    startAvoidance(durationMs);
    return;
  }

  if (command == "CHECK") {
    if (fieldCount != 2) {
      rejectCommand("INVALID_CHECK_FORMAT", receivedLine);
      console.println("Expected format : check left OR check right");
      return;
    }
    String wheel = String(argument1);
    wheel.toUpperCase();
    if (wheel == "LEFT") startEncoderCheck(CheckWheel::LEFT);
    else if (wheel == "RIGHT") startEncoderCheck(CheckWheel::RIGHT);
    else rejectCommand("INVALID_CHECK_WHEEL", receivedLine);
    return;
  }

  if (command == "FD" || command == "FDS") {
    rejectCommand("FEATURE_DEFERRED", receivedLine);
    console.println("reason          : exact-distance driving is not required for Atlas 6.0");
    console.println("next            : use drive PWM time_ms or avoid");
    return;
  }

  if (command == "DRIVE" || command == "F") {
    if (fieldCount != 3) {
      rejectCommand("INVALID_DRIVE_FORMAT", receivedLine);
      console.println("Expected format : drive 80 1000");
      return;
    }
    long pwmLong;
    long durationLong;
    if (!parseLongStrict(argument1, pwmLong) ||
        !parseLongStrict(argument2, durationLong) ||
        pwmLong < 0 || durationLong < 0) {
      rejectCommand("INVALID_DRIVE_NUMBER", receivedLine);
      return;
    }
    startDriveAssist(
        static_cast<int>(pwmLong),
        static_cast<unsigned long>(durationLong));
    return;
  }

  if (isOtherTimedCommand(command)) {
    if (fieldCount != 3) {
      rejectCommand("INVALID_TIMED_FORMAT", receivedLine);
      console.println("Expected format : tr 100 300");
      return;
    }
    long pwmLong;
    long durationLong;
    if (!parseLongStrict(argument1, pwmLong) ||
        !parseLongStrict(argument2, durationLong) ||
        pwmLong < 0 || durationLong < 0) {
      rejectCommand("INVALID_TIMED_NUMBER", receivedLine);
      return;
    }
    startOtherTimedMotion(
        command,
        static_cast<int>(pwmLong),
        static_cast<unsigned long>(durationLong));
    return;
  }

  rejectCommand("UNKNOWN_COMMAND", receivedLine);
}

void readCommandStream(
    Stream& stream,
    String& lineBuffer,
    CommandSource source) {

  while (stream.available() > 0) {
    const char received = static_cast<char>(stream.read());
    if (received == '\r') {
      continue;
    }
    if (received == '\n') {
      if (lineBuffer.length() > 0) {
        processCommand(lineBuffer, source);
        lineBuffer = "";
      }
      continue;
    }
    if (lineBuffer.length() >= INPUT_LINE_MAX_LENGTH) {
      lineBuffer = "";
      rejectCommand("INPUT_TOO_LONG", "overlength input");
      continue;
    }
    lineBuffer += received;
  }
}

// ============================================================
// TCP connection service
// ============================================================

void serviceTcpConnection() {
  if (tcpClientActive && !tcpClient.connected()) {
    tcpClient.stop();
    tcpClientActive = false;
    tcpLine = "";
    if ((moving && activeMotionSource == CommandSource::TCP) ||
        (armed && armedCommandSourceValid &&
         armedCommandSource == CommandSource::TCP)) {
      finishMotion("TCP_DISCONNECT");
    }
  }

  if (!tcpClientActive) {
    WiFiClient candidate = tcpServer.available();
    if (candidate) {
      tcpClient = candidate;
      tcpClient.setNoDelay(true);
      tcpClientActive = true;
      tcpLine = "";
      lastTcpHeartbeatMs = millis();
      tcpClient.println();
      tcpClient.println("========================================");
      tcpClient.println("ATLAS_6_0_STAGE_8C");
      tcpClient.println("safety          : disarmed");
      tcpClient.println("next            : send status, config, or help");
      tcpClient.println("========================================");
    }
  }

  if (tcpClientActive && tcpClient.connected()) {
    readCommandStream(tcpClient, tcpLine, CommandSource::TCP);
  }

  if (moving && activeMotionSource == CommandSource::TCP &&
      millis() - lastTcpHeartbeatMs > TCP_HEARTBEAT_TIMEOUT_MS) {
    finishMotion("TCP_HEARTBEAT_TIMEOUT");
  }
}

// ============================================================
// Arduino setup / loop
// ============================================================

void setup() {
  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_ENB, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);
  stopMotorsImmediately();

  pinMode(PIN_RIGHT_ENCODER_A, INPUT_PULLUP);
  pinMode(PIN_RIGHT_ENCODER_B, INPUT_PULLUP);
  pinMode(PIN_LEFT_ENCODER_A, INPUT_PULLUP);
  pinMode(PIN_LEFT_ENCODER_B, INPUT_PULLUP);
  resetEncoderCounts();
  attachInterrupt(
      digitalPinToInterrupt(PIN_RIGHT_ENCODER_A),
      onRightEncoderA,
      RISING);
  attachInterrupt(
      digitalPinToInterrupt(PIN_LEFT_ENCODER_A),
      onLeftEncoderA,
      RISING);

  pinMode(PIN_US100_TRIG, OUTPUT);
  pinMode(PIN_US100_ECHO, INPUT);
  digitalWrite(PIN_US100_TRIG, LOW);

  Serial.begin(115200);
  delay(500);
  serialLine.reserve(96);
  tcpLine.reserve(96);

  armed = false;
  armedCommandSourceValid = false;
  leftEncoderForwardSign = 0;
  rightEncoderForwardSign = 0;
  clearMotionState();
  resetSensorFilter();

  WiFi.mode(WIFI_AP);
  const bool accessPointStarted = WiFi.softAP(
      WIFI_AP_SSID,
      WIFI_AP_PASSWORD,
      1,
      0,
      WIFI_MAX_CLIENTS);
  if (accessPointStarted) {
    tcpServer.begin();
  }

  // Collect the initial three samples with all motor outputs disabled.
  for (uint8_t index = 0; index < SENSOR_VALID_SAMPLES_REQUIRED; ++index) {
    sampleUs100(true);
    delay(SENSOR_SAMPLE_INTERVAL_MS);
  }

  console.println();
  console.println("========================================");
  console.println("ATLAS_6_0_STAGE_8C");
  console.println("build           : Practical Avoidance V1");
  console.println("motors          : stopped");
  console.println("safety          : disarmed");
  console.println("distance FDS    : deferred / disabled");
  console.print("sensor state    : ");
  console.println(sensorStateName(sensorState));
  console.print("wifi AP         : ");
  console.println(accessPointStarted ? WIFI_AP_SSID : "START FAILED");
  console.print("wifi IP         : ");
  console.println(WiFi.softAPIP());
  console.print("tcp port        : ");
  console.println(WIFI_TCP_PORT);
  console.println("encoder checks  : required after this restart");
  console.println("next            : keep motor power off; send status and sensor");
  console.println("========================================");
}

void loop() {
  serviceTcpConnection();
  readCommandStream(Serial, serialLine, CommandSource::USB_SERIAL);

  const bool newSensorSample = sampleUs100(false);
  if (newSensorSample && moving && hasForwardComponent()) {
    if (sensorState == SensorState::INVALID_STOP ||
        sensorState == SensorState::STARTUP_STOP) {
      finishMotion("SENSOR_INVALID_STOP");
    } else if (sensorState == SensorState::FORCE_STOP) {
      finishMotion("OBSTACLE_FORCE_STOP");
    }
  }

  if (moving && motionMode == MotionMode::ENCODER_CHECK &&
      static_cast<int32_t>(millis() - motionDeadlineMs) >= 0) {
    finishEncoderCheck();
  }

  if (moving && motionMode == MotionMode::TIMED &&
      static_cast<int32_t>(millis() - motionDeadlineMs) >= 0) {
    finishMotion("ACTION_COMPLETE");
  }

  monitorDriveAssist();
  monitorAvoidance();
}
