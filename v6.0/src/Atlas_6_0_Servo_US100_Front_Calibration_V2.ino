/*
  Atlas 6.0 - Servo + US-100 Front Calibration V2
  ------------------------------------------------
  Target:
    ESP32 DEVKIT V1 first (known-good board)
    Also portable to ESP32-S3 because it uses basic GPIO timing.

  Wiring:
    Servo Signal -> GPIO21
    Servo VCC    -> ESP32 5V
    Servo GND    -> ESP32 GND


    US-100 TRIG  -> GPIO14
    US-100 ECHO  -> GPIO15
    US-100 VCC   -> 3V3
    US-100 GND   -> GND

  Serial Monitor:
    115200 baud

  Commands:
    A = current angle - 5 deg
    D = current angle + 5 deg
    F = save CURRENT angle as physical FRONT/CENTER
    V = invert LEFT/RIGHT direction and save
    C = move to calibrated CENTER and measure
    L = move to calibrated LEFT and measure
    R = move to calibrated RIGHT and measure
    S = full LEFT -> CENTER -> RIGHT -> CENTER scan
    M = measure at current angle
    P = print calibration
    X = reset calibration to defaults
    H = help
*/

#include <Arduino.h>
#include <Preferences.h>

static const uint8_t SERVO_PIN = 21;
static const uint8_t US_TRIG_PIN = 14;
static const uint8_t US_ECHO_PIN = 15;

static const uint16_t SERVO_PERIOD_US = 20000;
static const uint16_t SERVO_MIN_PULSE_US = 1000;
static const uint16_t SERVO_MAX_PULSE_US = 2000;

static const int SERVO_MIN_ANGLE = 5;
static const int SERVO_MAX_ANGLE = 175;
static const int CAL_STEP_DEG = 5;
static const int SCAN_OFFSET_DEG = 30;

static const uint32_t SERVO_MOVE_HOLD_MS = 650;
static const uint32_t SERVO_SETTLE_AFTER_MOVE_MS = 180;

static const uint32_t ECHO_TIMEOUT_US = 30000UL;
static const int US_SAMPLES = 5;
static const int US_MIN_VALID = 3;

Preferences prefs;

int currentAngle = 90;
int centerAngle = 90;
int leftDirectionSign = +1;

uint16_t angleToPulseUs(int angle) {
  angle = constrain(angle, 0, 180);
  return (uint16_t)map(angle, 0, 180, SERVO_MIN_PULSE_US, SERVO_MAX_PULSE_US);
}

void holdServoAtAngle(int angle, uint32_t durationMs) {
  angle = constrain(angle, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE);
  currentAngle = angle;

  const uint16_t pulseUs = angleToPulseUs(angle);
  const uint32_t cycles = max((uint32_t)1, durationMs / 20);

  for (uint32_t i = 0; i < cycles; i++) {
    digitalWrite(SERVO_PIN, HIGH);
    delayMicroseconds(pulseUs);
    digitalWrite(SERVO_PIN, LOW);
    delayMicroseconds(SERVO_PERIOD_US - pulseUs);
  }

  digitalWrite(SERVO_PIN, LOW);
}

void moveServo(int angle) {
  angle = constrain(angle, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE);

  Serial.print("SERVO,MOVE_FROM,");
  Serial.print(currentAngle);
  Serial.print(",TO,");
  Serial.println(angle);

  holdServoAtAngle(angle, SERVO_MOVE_HOLD_MS);
  delay(SERVO_SETTLE_AFTER_MOVE_MS);
}

float readDistanceOnceCm() {
  digitalWrite(US_TRIG_PIN, LOW);
  delayMicroseconds(3);
  digitalWrite(US_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(US_TRIG_PIN, LOW);

  uint32_t durationUs = pulseIn(US_ECHO_PIN, HIGH, ECHO_TIMEOUT_US);
  if (durationUs == 0) return NAN;

  float cm = durationUs * 0.0343f / 2.0f;
  if (cm < 2.0f || cm > 400.0f) return NAN;

  return cm;
}

void sortFloats(float *a, int n) {
  for (int i = 0; i < n; i++) {
    for (int j = i + 1; j < n; j++) {
      if (a[j] < a[i]) {
        float t = a[i];
        a[i] = a[j];
        a[j] = t;
      }
    }
  }
}

float readMedianDistanceCm() {
  float valid[US_SAMPLES];
  int count = 0;

  for (int i = 0; i < US_SAMPLES; i++) {
    float cm = readDistanceOnceCm();

    Serial.print("US,SAMPLE,");
    Serial.print(i + 1);
    Serial.print(",");

    if (isnan(cm)) {
      Serial.println("INVALID");
    } else {
      Serial.print(cm, 1);
      Serial.println(",CM");
      valid[count++] = cm;
    }

    delay(70);
  }

  if (count < US_MIN_VALID) {
    Serial.print("US,RESULT,UNKNOWN,VALID_COUNT,");
    Serial.println(count);
    return NAN;
  }

  sortFloats(valid, count);

  float median;
  if (count % 2 == 1) {
    median = valid[count / 2];
  } else {
    median = (valid[count / 2 - 1] + valid[count / 2]) / 2.0f;
  }

  Serial.print("US,RESULT,MEDIAN_CM,");
  Serial.print(median, 1);
  Serial.print(",VALID_COUNT,");
  Serial.println(count);

  return median;
}

const char* distanceState(float cm) {
  if (isnan(cm)) return "UNKNOWN";
  if (cm <= 30.0f) return "BLOCKED";
  if (cm <= 45.0f) return "CAUTION";
  return "CLEAR";
}

int leftAngle() {
  return centerAngle + leftDirectionSign * SCAN_OFFSET_DEG;
}

int rightAngle() {
  return centerAngle - leftDirectionSign * SCAN_OFFSET_DEG;
}

bool scanAnglesValid() {
  int l = leftAngle();
  int r = rightAngle();

  return (
    l >= SERVO_MIN_ANGLE &&
    l <= SERVO_MAX_ANGLE &&
    r >= SERVO_MIN_ANGLE &&
    r <= SERVO_MAX_ANGLE
  );
}

void printCalibration() {
  Serial.println();
  Serial.println("========== ATLAS SERVO CALIBRATION ==========");
  Serial.print("CURRENT ANGLE : ");
  Serial.println(currentAngle);

  Serial.print("CENTER ANGLE  : ");
  Serial.println(centerAngle);

  Serial.print("LEFT SIGN     : ");
  Serial.println(leftDirectionSign);

  Serial.print("LEFT ANGLE    : ");
  Serial.println(leftAngle());

  Serial.print("RIGHT ANGLE   : ");
  Serial.println(rightAngle());

  Serial.print("SCAN VALID    : ");
  Serial.println(scanAnglesValid() ? "YES" : "NO");

  if (!scanAnglesValid()) {
    Serial.println("WARNING: CENTER too close to servo end-stop for +/-30 deg scan.");
    Serial.println("Re-seat horn mechanically or choose a safer CENTER angle.");
  }

  Serial.println("=============================================");
  Serial.println();
}

float moveAndMeasure(const char* label, int angle) {
  if (
    angle < SERVO_MIN_ANGLE ||
    angle > SERVO_MAX_ANGLE
  ) {
    Serial.print("ERROR,ANGLE_OUT_OF_RANGE,");
    Serial.print(label);
    Serial.print(",");
    Serial.println(angle);
    return NAN;
  }

  Serial.println();
  Serial.print("SCAN,");
  Serial.print(label);
  Serial.print(",ANGLE,");
  Serial.println(angle);

  moveServo(angle);

  float cm = readMedianDistanceCm();

  Serial.print("SCAN_RESULT,");
  Serial.print(label);
  Serial.print(",");

  if (isnan(cm)) {
    Serial.println("UNKNOWN");
  } else {
    Serial.print(cm, 1);
    Serial.print(",CM,");
    Serial.println(distanceState(cm));
  }

  return cm;
}

void saveCenter() {
  centerAngle = currentAngle;
  prefs.putInt("center", centerAngle);

  Serial.print("CALIBRATION,SAVED_CENTER,");
  Serial.println(centerAngle);

  printCalibration();
}

void invertDirection() {
  leftDirectionSign *= -1;
  prefs.putInt("leftSign", leftDirectionSign);

  Serial.print("CALIBRATION,LEFT_RIGHT_INVERTED,SIGN,");
  Serial.println(leftDirectionSign);

  printCalibration();
}

void fullScan() {
  if (!scanAnglesValid()) {
    Serial.println("SCAN,ABORTED,ANGLES_OUT_OF_SAFE_RANGE");
    printCalibration();
    return;
  }

  Serial.println();
  Serial.println("========== FULL SCAN BEGIN ==========");

  float l = moveAndMeasure("LEFT", leftAngle());
  float c = moveAndMeasure("CENTER", centerAngle);
  float r = moveAndMeasure("RIGHT", rightAngle());

  moveServo(centerAngle);

  Serial.println();
  Serial.println("========== SCAN SUMMARY ==========");

  Serial.print("LEFT,");
  if (isnan(l)) Serial.println("UNKNOWN");
  else {
    Serial.print(l, 1);
    Serial.print(",CM,");
    Serial.println(distanceState(l));
  }

  Serial.print("CENTER,");
  if (isnan(c)) Serial.println("UNKNOWN");
  else {
    Serial.print(c, 1);
    Serial.print(",CM,");
    Serial.println(distanceState(c));
  }

  Serial.print("RIGHT,");
  if (isnan(r)) Serial.println("UNKNOWN");
  else {
    Serial.print(r, 1);
    Serial.print(",CM,");
    Serial.println(distanceState(r));
  }

  Serial.println("=========== FULL SCAN END ===========");
}

void resetCalibration() {
  centerAngle = 90;
  currentAngle = 90;
  leftDirectionSign = +1;

  prefs.putInt("center", centerAngle);
  prefs.putInt("leftSign", leftDirectionSign);

  moveServo(centerAngle);

  Serial.println("CALIBRATION,RESET_TO_DEFAULT");
  printCalibration();
}

void printHelp() {
  Serial.println();
  Serial.println("=============== COMMANDS ===============");
  Serial.println("A : servo angle -5 deg");
  Serial.println("D : servo angle +5 deg");
  Serial.println("F : save CURRENT angle as FRONT/CENTER");
  Serial.println("V : invert physical LEFT/RIGHT direction");
  Serial.println("C : go CENTER + measure");
  Serial.println("L : go LEFT + measure");
  Serial.println("R : go RIGHT + measure");
  Serial.println("S : full LEFT/CENTER/RIGHT scan");
  Serial.println("M : measure at current angle");
  Serial.println("P : print calibration");
  Serial.println("X : reset calibration to defaults");
  Serial.println("H : help");
  Serial.println("========================================");
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(SERVO_PIN, OUTPUT);
  digitalWrite(SERVO_PIN, LOW);

  pinMode(US_TRIG_PIN, OUTPUT);
  pinMode(US_ECHO_PIN, INPUT);
  digitalWrite(US_TRIG_PIN, LOW);

  prefs.begin("atlasServo", false);

  centerAngle = prefs.getInt("center", 90);
  leftDirectionSign = prefs.getInt("leftSign", +1);

  if (leftDirectionSign != +1 && leftDirectionSign != -1) {
    leftDirectionSign = +1;
  }

  currentAngle = centerAngle;

  Serial.println();
  Serial.println("ATLAS 6.0 SERVO + US100 FRONT CALIBRATION V2");
  Serial.println("STATUS,READY");

  moveServo(centerAngle);

  printCalibration();
  printHelp();
}

void loop() {
  if (Serial.available() <= 0) {
    delay(5);
    return;
  }

  char c = (char)Serial.read();

  if (c == '\r' || c == '\n' || c == ' ') {
    return;
  }

  c = toupper(c);

  switch (c) {
    case 'A':
      moveServo(currentAngle - CAL_STEP_DEG);
      break;

    case 'D':
      moveServo(currentAngle + CAL_STEP_DEG);
      break;

    case 'F':
      saveCenter();
      break;

    case 'V':
      invertDirection();
      break;

    case 'C':
      moveAndMeasure("CENTER", centerAngle);
      break;

    case 'L':
      moveAndMeasure("LEFT", leftAngle());
      break;

    case 'R':
      moveAndMeasure("RIGHT", rightAngle());
      break;

    case 'S':
      fullScan();
      break;

    case 'M': {
      float cm = readMedianDistanceCm();
      Serial.print("MEASURE_CURRENT_ANGLE,");
      Serial.print(currentAngle);
      Serial.print(",");
      if (isnan(cm)) {
        Serial.println("UNKNOWN");
      } else {
        Serial.print(cm, 1);
        Serial.print(",CM,");
        Serial.println(distanceState(cm));
      }
      break;
    }

    case 'P':
      printCalibration();
      break;

    case 'X':
      resetCalibration();
      break;

    case 'H':
      printHelp();
      break;

    default:
      Serial.print("ERROR,UNKNOWN_COMMAND,");
      Serial.println(c);
      break;
  }
}
