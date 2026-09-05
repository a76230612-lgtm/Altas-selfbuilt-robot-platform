#include <Arduino.h>

// ============================================================
// Atlas 6.0 Stage 8
// US-100 Component Test
//
// 安全边界：
// 1. 电机电源必须物理断开。
// 2. 不运行任何运动命令。
// 3. GPIO27 / GPIO34仅用于本次临时单部件测试。
// 4. US-100使用3.3V供电。
// 5. US-100背面模式跳帽必须拔掉。
// ============================================================

// -------------------- US-100临时测试引脚 --------------------
constexpr uint8_t PIN_US100_TRIG = 27;
constexpr uint8_t PIN_US100_ECHO = 34;

// -------------------- 当前L298N引脚 --------------------
// 测试程序只把这些引脚保持LOW，绝不驱动电机。
constexpr uint8_t PIN_ENA = 13;
constexpr uint8_t PIN_IN1 = 14;
constexpr uint8_t PIN_IN2 = 4;

constexpr uint8_t PIN_ENB = 33;
constexpr uint8_t PIN_IN3 = 32;
constexpr uint8_t PIN_IN4 = 23;

// -------------------- 测量参数 --------------------
constexpr float MIN_VALID_DISTANCE_CM = 2.0f;
constexpr float MAX_VALID_DISTANCE_CM = 400.0f;

constexpr float FORCE_STOP_THRESHOLD_CM = 25.0f;
constexpr float CLEAR_THRESHOLD_CM = 50.0f;

constexpr unsigned long ECHO_TIMEOUT_US = 30000UL;
constexpr unsigned long BETWEEN_PINGS_MS = 70UL;

constexpr uint8_t BATCH_SAMPLE_COUNT = 10;

struct DistanceReading {
  bool valid;
  float distanceCm;
  unsigned long durationUs;
};

// ============================================================
// 安全：保持全部电机控制引脚LOW
// ============================================================

void holdAllMotorPinsLow() {
  const uint8_t motorPins[] = {
    PIN_ENA,
    PIN_IN1,
    PIN_IN2,
    PIN_ENB,
    PIN_IN3,
    PIN_IN4
  };

  for (uint8_t i = 0; i < sizeof(motorPins); i++) {
    pinMode(motorPins[i], OUTPUT);
    digitalWrite(motorPins[i], LOW);
  }
}

// ============================================================
// US-100单次测量
// ============================================================

DistanceReading readUS100Once() {
  digitalWrite(PIN_US100_TRIG, LOW);
  delayMicroseconds(3);

  digitalWrite(PIN_US100_TRIG, HIGH);
  delayMicroseconds(10);

  digitalWrite(PIN_US100_TRIG, LOW);

  const unsigned long durationUs =
      pulseIn(PIN_US100_ECHO, HIGH, ECHO_TIMEOUT_US);

  if (durationUs == 0) {
    return {
      false,
      0.0f,
      0UL
    };
  }

  const float distanceCm =
      static_cast<float>(durationUs) * 0.0343f / 2.0f;

  const bool valid =
      distanceCm >= MIN_VALID_DISTANCE_CM &&
      distanceCm <= MAX_VALID_DISTANCE_CM;

  return {
    valid,
    distanceCm,
    durationUs
  };
}

// ============================================================
// 数值排序和中位数
// ============================================================

void sortValues(float values[], uint8_t count) {
  for (uint8_t i = 0; i < count; i++) {
    for (uint8_t j = i + 1; j < count; j++) {
      if (values[j] < values[i]) {
        const float temporary = values[i];
        values[i] = values[j];
        values[j] = temporary;
      }
    }
  }
}

float calculateMedian(const float values[], uint8_t count) {
  if (count == 0) {
    return 0.0f;
  }

  if (count % 2 == 1) {
    return values[count / 2];
  }

  return (
      values[count / 2 - 1] +
      values[count / 2]
  ) / 2.0f;
}

// ============================================================
// 安全状态
// ============================================================

const char* classifyDistance(
    float medianDistanceCm,
    uint8_t invalidCount) {

  // 最终安全策略：只要本批次出现无效数据，就不能认为道路安全。
  if (invalidCount > 0) {
    return "SENSOR_INVALID_STOP";
  }

  if (medianDistanceCm < FORCE_STOP_THRESHOLD_CM) {
    return "FORCE_STOP";
  }

  if (medianDistanceCm <= CLEAR_THRESHOLD_CM) {
    return "CAUTION";
  }

  return "CLEAR";
}

const char* allowedActionForState(const char* state) {
  if (strcmp(state, "CLEAR") == 0) {
    return "FORWARD_ALLOWED";
  }

  if (strcmp(state, "CAUTION") == 0) {
    return "SLOW_OR_WARN";
  }

  return "STOP";
}

// ============================================================
// 单次读取输出
// ============================================================

void printSingleReading() {
  const DistanceReading reading = readUS100Once();

  Serial.println();
  Serial.println("[Single US-100 reading]");

  if (!reading.valid) {
    Serial.println("valid           : no");
    Serial.println("distance        : INVALID");
    Serial.println("safety state    : SENSOR_INVALID_STOP");
    Serial.println("allowed action  : STOP");
    return;
  }

  const char* state =
      reading.distanceCm < FORCE_STOP_THRESHOLD_CM
          ? "FORCE_STOP"
          : (
              reading.distanceCm <= CLEAR_THRESHOLD_CM
                  ? "CAUTION"
                  : "CLEAR"
            );

  Serial.println("valid           : yes");

  Serial.print("duration        : ");
  Serial.print(reading.durationUs);
  Serial.println(" us");

  Serial.print("distance        : ");
  Serial.print(reading.distanceCm, 2);
  Serial.println(" cm");

  Serial.print("safety state    : ");
  Serial.println(state);

  Serial.print("allowed action  : ");
  Serial.println(allowedActionForState(state));
}

// ============================================================
// 10次批量测试
// ============================================================

void runBatchTest() {
  float validDistances[BATCH_SAMPLE_COUNT];

  uint8_t validCount = 0;
  uint8_t invalidCount = 0;

  Serial.println();
  Serial.println("========================================");
  Serial.println("[US-100 batch test]");
  Serial.println("samples         : 10");
  Serial.println("motor power     : must be physically disconnected");
  Serial.println("----------------------------------------");

  for (uint8_t i = 0; i < BATCH_SAMPLE_COUNT; i++) {
    const DistanceReading reading = readUS100Once();

    Serial.print("sample ");
    Serial.print(i + 1);
    Serial.print("        : ");

    if (!reading.valid) {
      invalidCount++;
      Serial.println("INVALID");
    } else {
      validDistances[validCount] = reading.distanceCm;
      validCount++;

      Serial.print(reading.distanceCm, 2);
      Serial.print(" cm; duration=");
      Serial.print(reading.durationUs);
      Serial.println(" us");
    }

    delay(BETWEEN_PINGS_MS);
  }

  Serial.println("----------------------------------------");

  Serial.print("valid readings  : ");
  Serial.print(validCount);
  Serial.print(" / ");
  Serial.println(BATCH_SAMPLE_COUNT);

  Serial.print("invalid readings: ");
  Serial.print(invalidCount);
  Serial.print(" / ");
  Serial.println(BATCH_SAMPLE_COUNT);

  if (validCount == 0) {
    Serial.println("median          : unavailable");
    Serial.println("minimum         : unavailable");
    Serial.println("maximum         : unavailable");
    Serial.println("spread          : unavailable");
    Serial.println("safety state    : SENSOR_INVALID_STOP");
    Serial.println("allowed action  : STOP");
    Serial.println("result          : not passed");
    Serial.println("========================================");
    return;
  }

  sortValues(validDistances, validCount);

  const float medianDistance =
      calculateMedian(validDistances, validCount);

  const float minimumDistance =
      validDistances[0];

  const float maximumDistance =
      validDistances[validCount - 1];

  const float spread =
      maximumDistance - minimumDistance;

  const char* safetyState =
      classifyDistance(
          medianDistance,
          invalidCount
      );

  Serial.print("median          : ");
  Serial.print(medianDistance, 2);
  Serial.println(" cm");

  Serial.print("minimum         : ");
  Serial.print(minimumDistance, 2);
  Serial.println(" cm");

  Serial.print("maximum         : ");
  Serial.print(maximumDistance, 2);
  Serial.println(" cm");

  Serial.print("spread          : ");
  Serial.print(spread, 2);
  Serial.println(" cm");

  Serial.print("safety state    : ");
  Serial.println(safetyState);

  Serial.print("allowed action  : ");
  Serial.println(allowedActionForState(safetyState));

  Serial.print("result          : ");
  Serial.println(
      invalidCount == 0
          ? "measurement completed"
          : "sensor data not fully reliable"
  );

  Serial.println("========================================");
}

void printHelp() {
  Serial.println();
  Serial.println("[Stage 8 command guide]");
  Serial.println("  read   : take one distance reading");
  Serial.println("  test   : take 10 readings and print a summary");
  Serial.println("  help   : show this guide");
  Serial.println();
  Serial.println("No command in this program can move a motor.");
}

void processSerialCommand(String command) {
  command.trim();
  command.toLowerCase();

  if (command.length() == 0) {
    return;
  }

  if (command == "read") {
    printSingleReading();
    return;
  }

  if (command == "test") {
    runBatchTest();
    return;
  }

  if (command == "help") {
    printHelp();
    return;
  }

  Serial.println();
  Serial.println("[Command rejected]");
  Serial.println("Allowed commands: read, test, help");
}

// ============================================================
// Arduino setup/loop
// ============================================================

void setup() {
  // 第一动作：保证所有电机控制引脚为LOW。
  holdAllMotorPinsLow();

  pinMode(PIN_US100_TRIG, OUTPUT);
  digitalWrite(PIN_US100_TRIG, LOW);

  // GPIO34是输入专用脚。
  pinMode(PIN_US100_ECHO, INPUT);

  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("========================================");
  Serial.println("Atlas 6.0 Stage 8 US-100 Component Test");
  Serial.println("motor outputs   : LOW");
  Serial.println("motor power     : must be disconnected");
  Serial.println("US-100 mode     : Trigger/Echo; rear jumper removed");
  Serial.println("US-100 power    : 3.3V");
  Serial.println("Trig            : GPIO27");
  Serial.println("Echo            : GPIO34");
  Serial.println("safety          : no motor commands exist");
  Serial.println("========================================");

  printHelp();
}

void loop() {
  holdAllMotorPinsLow();

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    processSerialCommand(command);
  }
}