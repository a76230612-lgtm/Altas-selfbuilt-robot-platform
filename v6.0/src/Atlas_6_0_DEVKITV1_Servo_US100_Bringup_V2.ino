#include <Arduino.h>

// Atlas 6.0 DEVKITV1 Servo + US-100 Bring-Up V2
// Servo Signal -> GPIO21
// Servo VCC -> 5V
// Servo GND -> GND
// US-100 TRIG -> GPIO27
// US-100 ECHO -> GPIO34
// Serial Monitor -> 115200

static const uint8_t SERVO_PIN = 21;
static const uint8_t TRIG_PIN = 27;
static const uint8_t ECHO_PIN = 34;

static const int ANGLE_LEFT = 60;
static const int ANGLE_CENTER = 90;
static const int ANGLE_RIGHT = 120;

static const uint16_t SERVO_PERIOD_US = 20000;
static const uint16_t SERVO_MIN_US = 1000;
static const uint16_t SERVO_MAX_US = 2000;

uint16_t angleToPulse(int angle) {
  angle = constrain(angle, 0, 180);
  return map(angle, 0, 180, SERVO_MIN_US, SERVO_MAX_US);
}

void moveServo(int angle) {
  uint16_t pulse = angleToPulse(angle);
  uint32_t cycles = 35; // ~700 ms

  for (uint32_t i = 0; i < cycles; ++i) {
    digitalWrite(SERVO_PIN, HIGH);
    delayMicroseconds(pulse);
    digitalWrite(SERVO_PIN, LOW);
    delayMicroseconds(SERVO_PERIOD_US - pulse);
  }
  delay(250);
}

float readOnceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(3);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long us = pulseIn(ECHO_PIN, HIGH, 30000UL);
  if (us == 0) return NAN;

  float cm = us * 0.0343f / 2.0f;
  if (cm < 2.0f || cm > 400.0f) return NAN;
  return cm;
}

void sortFloats(float *a, int n) {
  for (int i = 0; i < n; ++i) {
    for (int j = i + 1; j < n; ++j) {
      if (a[j] < a[i]) {
        float t = a[i]; a[i] = a[j]; a[j] = t;
      }
    }
  }
}

float median5() {
  float v[5];
  int n = 0;

  for (int i = 0; i < 5; ++i) {
    float cm = readOnceCm();
    Serial.print("US,SAMPLE,");
    Serial.print(i + 1);
    Serial.print(",");
    if (isnan(cm)) {
      Serial.println("INVALID");
    } else {
      Serial.print(cm, 1);
      Serial.println(",CM");
      v[n++] = cm;
    }
    delay(70);
  }

  if (n < 3) {
    Serial.println("US,RESULT,UNKNOWN");
    return NAN;
  }

  sortFloats(v, n);
  float m = (n % 2) ? v[n/2] : (v[n/2 - 1] + v[n/2]) / 2.0f;
  Serial.print("US,RESULT,MEDIAN_CM,");
  Serial.println(m, 1);
  return m;
}

const char* stateOf(float cm) {
  if (isnan(cm)) return "UNKNOWN";
  if (cm <= 30.0f) return "BLOCKED";
  if (cm <= 45.0f) return "CAUTION";
  return "CLEAR";
}

void scanOne(const char* name, int angle) {
  Serial.print("SCAN,START,");
  Serial.println(name);
  moveServo(angle);
  float cm = median5();
  Serial.print("SCAN,RESULT,");
  Serial.print(name);
  Serial.print(",");
  if (isnan(cm)) {
    Serial.println("UNKNOWN");
  } else {
    Serial.print(cm, 1);
    Serial.print(",CM,");
    Serial.println(stateOf(cm));
  }
}

void fullScan() {
  scanOne("LEFT", ANGLE_LEFT);
  scanOne("CENTER", ANGLE_CENTER);
  scanOne("RIGHT", ANGLE_RIGHT);
  moveServo(ANGLE_CENTER);
  Serial.println("SCAN,DONE,CENTERED");
}

void stability() {
  Serial.println("SERVO_STABILITY_TEST_BEGIN");
  for (int i = 1; i <= 10; ++i) {
    Serial.print("CYCLE,"); Serial.println(i);
    moveServo(ANGLE_LEFT);
    moveServo(ANGLE_CENTER);
    moveServo(ANGLE_RIGHT);
    moveServo(ANGLE_CENTER);
  }
  Serial.println("SERVO_STABILITY_TEST_END");
}

void help() {
  Serial.println("H=help C=center L=left R=right S=fullscan T=servo_stability M=measure");
}

void setup() {
  Serial.begin(115200);
  pinMode(SERVO_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(SERVO_PIN, LOW);
  digitalWrite(TRIG_PIN, LOW);

  delay(1000);
  moveServo(ANGLE_CENTER);
  Serial.println("ATLAS 6.0 DEVKITV1 SERVO+US100 V2 READY");
  Serial.println("SERVO=21 TRIG=27 ECHO=34");
  help();
}

void loop() {
  if (!Serial.available()) {
    delay(5);
    return;
  }

  char c = toupper((char)Serial.read());
  if (c == '\r' || c == '\n' || c == ' ') return;

  switch (c) {
    case 'H': help(); break;
    case 'C': scanOne("CENTER", ANGLE_CENTER); break;
    case 'L': scanOne("LEFT", ANGLE_LEFT); break;
    case 'R': scanOne("RIGHT", ANGLE_RIGHT); break;
    case 'S': fullScan(); break;
    case 'T': stability(); break;
    case 'M': median5(); break;
    default:
      Serial.print("ERROR,UNKNOWN_COMMAND,");
      Serial.println(c);
  }
}
