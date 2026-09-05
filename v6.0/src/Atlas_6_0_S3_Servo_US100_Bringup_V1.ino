#include <Arduino.h>

static const uint8_t SERVO_PIN = 21;
static const uint8_t US_TRIG_PIN = 14;
static const uint8_t US_ECHO_PIN = 15;

static const uint32_t SERVO_FREQ_HZ = 50;
static const uint8_t SERVO_RES_BITS = 14;
static const uint32_t SERVO_MAX_DUTY = (1UL << SERVO_RES_BITS) - 1UL;

static const uint16_t SERVO_MIN_US = 1000;
static const uint16_t SERVO_MAX_US = 2000;

static const int ANGLE_LEFT = 60;
static const int ANGLE_CENTER = 90;
static const int ANGLE_RIGHT = 120;

static const uint32_t SERVO_SETTLE_MS = 350;
static const uint32_t ECHO_TIMEOUT_US = 30000UL;
static const uint8_t DISTANCE_SAMPLES = 5;
static const uint8_t MIN_VALID_SAMPLES = 3;

int currentAngle = ANGLE_CENTER;

uint32_t pulseUsToDuty(uint16_t pulseUs) {
  const uint32_t periodUs = 1000000UL / SERVO_FREQ_HZ;
  return (uint32_t)((uint64_t)pulseUs * SERVO_MAX_DUTY / periodUs);
}

uint16_t angleToPulseUs(int angle) {
  angle = constrain(angle, 0, 180);
  return (uint16_t)map(angle, 0, 180, SERVO_MIN_US, SERVO_MAX_US);
}

bool setServoAngle(int angle) {
  angle = constrain(angle, 0, 180);
  uint16_t pulseUs = angleToPulseUs(angle);
  uint32_t duty = pulseUsToDuty(pulseUs);
  bool ok = ledcWrite(SERVO_PIN, duty);
  if (!ok) {
    Serial.println("ERROR,SERVO_PWM_WRITE_FAILED");
    return false;
  }
  currentAngle = angle;
  Serial.print("SERVO,ANGLE,");
  Serial.print(angle);
  Serial.print(",PULSE_US,");
  Serial.println(pulseUs);
  delay(SERVO_SETTLE_MS);
  return true;
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

void sortFloatArray(float *a, uint8_t n) {
  for (uint8_t i = 0; i < n; i++) {
    for (uint8_t j = i + 1; j < n; j++) {
      if (a[j] < a[i]) {
        float t = a[i];
        a[i] = a[j];
        a[j] = t;
      }
    }
  }
}

float readMedianDistanceCm(bool verbose = true) {
  float valid[DISTANCE_SAMPLES];
  uint8_t validCount = 0;

  for (uint8_t i = 0; i < DISTANCE_SAMPLES; i++) {
    float cm = readDistanceOnceCm();

    if (verbose) {
      Serial.print("US,SAMPLE,");
      Serial.print(i + 1);
      Serial.print(",");
      if (isnan(cm)) {
        Serial.println("INVALID");
      } else {
        Serial.print(cm, 1);
        Serial.println(",CM");
      }
    }

    if (!isnan(cm)) valid[validCount++] = cm;
    delay(70);
  }

  if (validCount < MIN_VALID_SAMPLES) {
    Serial.print("US,RESULT,UNKNOWN,VALID_COUNT,");
    Serial.println(validCount);
    return NAN;
  }

  sortFloatArray(valid, validCount);

  float median;
  if (validCount % 2 == 1) {
    median = valid[validCount / 2];
  } else {
    median = (valid[validCount / 2 - 1] + valid[validCount / 2]) / 2.0f;
  }

  Serial.print("US,RESULT,MEDIAN_CM,");
  Serial.print(median, 1);
  Serial.print(",VALID_COUNT,");
  Serial.println(validCount);

  return median;
}

const char* classifyDistance(float cm) {
  if (isnan(cm)) return "UNKNOWN";
  if (cm <= 30.0f) return "BLOCKED";
  if (cm <= 45.0f) return "CAUTION";
  return "CLEAR";
}

float measureAtAngle(const char *label, int angle) {
  Serial.println();
  Serial.print("SCAN,START,");
  Serial.println(label);

  if (!setServoAngle(angle)) return NAN;

  float cm = readMedianDistanceCm(true);

  Serial.print("SCAN,RESULT,");
  Serial.print(label);
  Serial.print(",");
  if (isnan(cm)) {
    Serial.println("UNKNOWN");
  } else {
    Serial.print(cm, 1);
    Serial.print(",CM,");
    Serial.println(classifyDistance(cm));
  }

  return cm;
}

void fullScan() {
  Serial.println();
  Serial.println("ATLAS_US_SERVO_SCAN_BEGIN");

  float leftCm = measureAtAngle("LEFT", ANGLE_LEFT);
  float centerCm = measureAtAngle("CENTER", ANGLE_CENTER);
  float rightCm = measureAtAngle("RIGHT", ANGLE_RIGHT);

  setServoAngle(ANGLE_CENTER);

  Serial.println("SCAN_SUMMARY");

  Serial.print("LEFT,");
  if (isnan(leftCm)) Serial.println("UNKNOWN");
  else {
    Serial.print(leftCm, 1);
    Serial.print(",CM,");
    Serial.println(classifyDistance(leftCm));
  }

  Serial.print("CENTER,");
  if (isnan(centerCm)) Serial.println("UNKNOWN");
  else {
    Serial.print(centerCm, 1);
    Serial.print(",CM,");
    Serial.println(classifyDistance(centerCm));
  }

  Serial.print("RIGHT,");
  if (isnan(rightCm)) Serial.println("UNKNOWN");
  else {
    Serial.print(rightCm, 1);
    Serial.print(",CM,");
    Serial.println(classifyDistance(rightCm));
  }

  Serial.println("ATLAS_US_SERVO_SCAN_END");
}

void servoStabilityTest() {
  Serial.println();
  Serial.println("SERVO_STABILITY_TEST_BEGIN");

  for (int cycle = 1; cycle <= 10; cycle++) {
    Serial.print("CYCLE,");
    Serial.println(cycle);

    if (!setServoAngle(ANGLE_LEFT)) return;
    delay(250);

    if (!setServoAngle(ANGLE_CENTER)) return;
    delay(250);

    if (!setServoAngle(ANGLE_RIGHT)) return;
    delay(250);

    if (!setServoAngle(ANGLE_CENTER)) return;
    delay(500);
  }

  Serial.println("SERVO_STABILITY_TEST_END");
  Serial.println("RESULT,IF_NO_RESET_OR_USB_DROP,PASS");
}

void printHelp() {
  Serial.println("H : Help");
  Serial.println("C : CENTER + measure");
  Serial.println("L : LEFT + measure");
  Serial.println("R : RIGHT + measure");
  Serial.println("S : Full LEFT/CENTER/RIGHT scan");
  Serial.println("T : Servo 10-cycle stability test");
  Serial.println("M : Measure 5 samples at current angle");
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(US_TRIG_PIN, OUTPUT);
  pinMode(US_ECHO_PIN, INPUT);
  digitalWrite(US_TRIG_PIN, LOW);

  Serial.println("ATLAS 6.0 S3 SERVO + US100 BRING-UP");

  bool pwmOk = ledcAttach(SERVO_PIN, SERVO_FREQ_HZ, SERVO_RES_BITS);
  if (!pwmOk) {
    Serial.println("FATAL,SERVO_PWM_ATTACH_FAILED");
    while (true) delay(1000);
  }

  Serial.println("SERVO_PWM_ATTACH,PASS");
  Serial.println("US100_GPIO_INIT,PASS");

  setServoAngle(ANGLE_CENTER);

  Serial.println("STATUS,READY");
  printHelp();
}

void loop() {
  if (Serial.available() <= 0) {
    delay(10);
    return;
  }

  char c = Serial.read();
  if (c == '\r' || c == '\n') return;

  c = toupper(c);

  switch (c) {
    case 'H': printHelp(); break;
    case 'C': measureAtAngle("CENTER", ANGLE_CENTER); break;
    case 'L': measureAtAngle("LEFT", ANGLE_LEFT); break;
    case 'R': measureAtAngle("RIGHT", ANGLE_RIGHT); break;
    case 'S': fullScan(); break;
    case 'T': servoStabilityTest(); break;
    case 'M':
      Serial.print("CURRENT_ANGLE,");
      Serial.println(currentAngle);
      readMedianDistanceCm(true);
      break;
    default:
      Serial.print("ERROR,UNKNOWN_COMMAND,");
      Serial.println(c);
      break;
  }
}
