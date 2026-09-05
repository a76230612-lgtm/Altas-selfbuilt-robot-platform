#include <Arduino.h>
#include <WiFi.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

// ============================================================
// Atlas 6.0 Stage 7C Wireless Bridge V1
//
// 这一版只增加通信层：
//   USB Serial  <-> 同一套 processCommand()
//   Wi-Fi TCP   <-> 同一套 processCommand()
//
// Stage 7B V5 的电机、编码器、FDS、SYNC 与安全参数保持不变。
// 不要用这一版重新解释或调节落地 FDS；先完成无线通信验收。
// ============================================================

constexpr char WIFI_AP_SSID[] = "ATLAS_6_0";
constexpr char WIFI_AP_PASSWORD[] = "Atlas6Stage7";
constexpr uint16_t WIFI_TCP_PORT = 3333;
constexpr uint8_t WIFI_MAX_CLIENTS = 1;

// TCP运动命令必须持续收到客户端心跳；超时即停止并解除ARM。
constexpr unsigned long TCP_HEARTBEAT_TIMEOUT_MS = 350;
constexpr size_t INPUT_LINE_MAX_LENGTH = 95;

WiFiServer tcpServer(WIFI_TCP_PORT);
WiFiClient tcpClient;
bool tcpClientActive = false;

// 所有运行报告同时发往USB串口和当前TCP客户端。
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

// ============================================================
// Atlas 6.0 Stage 7B Closed-Loop Distance V5
// ESP32 DEVKIT_C + L298N + 双编码器
//
// 目标：
// 1. 完整保留 Stage 6C V4 的安全、定时运动、目标距离和编码器功能。
// 2. 保留 SYNC PWM time_ms：用于轮子离地的 Stage 7A 直行同步验证。
// 3. 每 50 ms 比较按各自 PPR 归一化后的累计进度。
// 4. BASE_PWM=80 已是可靠下限，因此只给落后轮小幅加 PWM，不降低领先轮。
// 5. V2 设 3 等效脉冲死区、最多 +8 PWM、每次最多变化 1 PWM。
//    这会更早修正小误差，同时降低一次补偿过大造成的反向过冲。
// 6. 提供 700 ms 堵转、反向脉冲、串口命令和一次 ARM 一次动作保护。
// 7. 新增 FDS distance_cm：用相同的同步控制低速前进，并让左右轮按
//    各自目标脉冲独立停车。旧 FD 命令仍保持 160 PWM，作为回退基线。
// 8. V3 不再让 FDS 以连续 PWM 冲到目标。实测 PWM 80 / 500 ms 已产生
//    左 402、右 400 pulses，而 5 cm 目标只有约 148 pulses；连续驱动后再刹车
//    必然把大量旋转动能带到终点。
// 9. V3 的 FDS 改为自适应脉冲逼近：短时 PWM 80 -> L298N Fast motor stop
//    -> 输出关闭 -> 等待完全静止 -> 读取实际增量 -> 自动计算下一次短脉冲。
//    左右轮各自估算响应并独立结束，但每一轮尽量同时开始，降低跑偏。
// 10. V4 修复 V3 在 fds 10 的终止逻辑：三次实测中两次已经满足正式精度
//     门槛，却因为仍追逐固定 6-pulse 死区而触发 60-cycle 上限。
// 11. V4 在 60 个常规 cycle 后先检查正式精度；已合格就正常结束。尚未合格
//     时进入最多 40 个追赶 cycle，暂停领先轮，只驱动落后轮，防止差距扩大。
// 12. FDS 只有在每轮最终误差不超过 10%，且左右最终距离差不超过 5% 时
//     才显示 passed。V3 仍保留为回退版本，不要覆盖。
// 13. V5 根据三次 fds 15 实测（86、87、89 cycles）修复 V4 固定 100-cycle
//     上限对更长距离不足的问题。cycle 上限现在按目标脉冲动态计算；5/10 cm
//     仍至少保留 100 cycles，20 cm 约得到 159 cycles，30 cm 约得到 233 cycles。
// 14. 总超时随动态 cycle 上限同步调整，并继续保留反向、无进度、异常脉冲和
//     用户 STOP 保护。V4 仍保留为回退版本，不要覆盖。
// 15. 最终串口报告直接区分：ESP32 重启、进入 accuracy recovery、以及程序
//     主动暂停的领先轮，避免把这三种完全不同的情况混为一谈。
//
// 当前已锁定的编码器映射（信号组保持交换状态）：
//   物理右轮编码器 -> GPIO18 / GPIO19 -> 原始计数 RAW_18_19
//   物理左轮编码器 -> GPIO25 / GPIO26 -> 原始计数 RAW_25_26
//
// V5 保留 V4 的编码器前进符号自动学习。必须先执行：
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
constexpr bool LEFT_MOTOR_INVERTED  = true;
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
constexpr float LEFT_PULSES_PER_REV     = 632.05f;
constexpr float RIGHT_PULSES_PER_REV    = 634.17f;

// 6C 第一轮基准测试固定使用 160 / 160；先不要在同一轮测试中改 PWM。
constexpr int LEFT_TARGET_PWM  = 160;
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
constexpr long MIN_TEST_PULSES  = 20;
constexpr long MAX_TEST_PULSES  = 3000;

constexpr unsigned long STALL_TIMEOUT_MS        = 700;
constexpr unsigned long TARGET_MIN_TOTAL_TIMEOUT_MS = 30000;
constexpr unsigned long TARGET_MAX_TOTAL_TIMEOUT_MS = 65000;
constexpr unsigned long TARGET_APPROACH_CYCLE_BUDGET_MS = 250;
constexpr unsigned long TARGET_APPROACH_TIMEOUT_MARGIN_MS = 5000;
constexpr unsigned long FINAL_SETTLE_MS         = 300;

// L298N Fast motor stop：Enable 为高、两个方向输入相等。
constexpr int TARGET_BRAKE_PWM = 255;
constexpr unsigned long TARGET_BRAKE_HOLD_MS = 80;

// -------------------- Stage 7B V3 脉冲逼近参数 --------------------
// Atlas 已实测最低可靠连续 PWM 为 80；终点低速通过缩短通电时间实现，
// 不能把连续 PWM 降到 80 以下。
constexpr int APPROACH_PWM = 80;
constexpr unsigned long APPROACH_MIN_BURST_MS = 8;
constexpr unsigned long APPROACH_MAX_BURST_MS = 45;
constexpr unsigned long APPROACH_SETTLE_MS = 100;
constexpr int32_t APPROACH_DEADBAND_PULSES = 6;
constexpr int32_t APPROACH_REVERSE_LIMIT_PULSES = 12;
constexpr uint8_t APPROACH_MAX_NO_PROGRESS_CYCLES = 6;
constexpr uint16_t APPROACH_NORMAL_CYCLES = 60;
constexpr uint16_t APPROACH_MIN_MAX_CYCLES = 100;
constexpr uint16_t APPROACH_ABSOLUTE_MAX_CYCLES = 240;
constexpr float APPROACH_MAX_CYCLES_PER_TARGET_PULSE = 0.25f;
constexpr uint16_t APPROACH_MAX_CYCLE_MARGIN = 10;
constexpr float APPROACH_CATCH_UP_THRESHOLD_PERCENT = 2.0f;

// 由 PWM 80 / 500 ms 的实测 402、400 pulses 得到约 0.80 pulse/ms。
// 短脉冲每次都从静止起步，实际速率会更低，所以保守以 0.45 起算；
// 每次静止后用真实增量更新，避免把 500 ms 平均速度直接套到短脉冲。
constexpr float APPROACH_INITIAL_RATE_PULSES_PER_MS = 0.45f;
constexpr float APPROACH_RATE_EWMA_NEW_WEIGHT = 0.35f;
constexpr float APPROACH_DESIRED_REMAINING_FRACTION = 0.35f;

// FDS 的最终精度门槛。安全逻辑完成但超过门槛时，结果必须显示 not passed。
constexpr float FDS_MAX_FINAL_ERROR_PERCENT = 10.0f;
constexpr float FDS_MAX_WHEEL_MISMATCH_PERCENT = 5.0f;

// -------------------- Stage 7 同步控制参数 --------------------
// 2026-08-12 开环实测：f 80 1000，五次均稳定。
// 左轮平均 928.6 pulses，右轮平均 916.6 pulses；按各自 PPR 换算后，
// 左轮平均约领先 1.64%。
// V1 的 sync 80 1000 五次平均绝对误差约 1.268%，相对开环改善约 22.2%；
// 最差误差由约 4.20% 降至 1.59%，控制方向正确，但未达到 30% 改善门槛。
// V2 不添加固定左右偏置，因为 V1 第三次出现右轮领先；继续采用对称自适应补偿。
constexpr unsigned long SYNC_CONTROL_INTERVAL_MS = 50;
constexpr unsigned long SYNC_REPORT_INTERVAL_MS  = 200;
constexpr unsigned long SYNC_START_DELAY_MS      = 100;
constexpr int SYNC_MAX_BASE_PWM                   = 180;
constexpr float SYNC_KP_PWM_PER_EQUIV_PULSE       = 0.15f;
constexpr float SYNC_DEADBAND_EQUIV_PULSES        = 3.0f;
constexpr int SYNC_MAX_BOOST_PWM                  = 8;
constexpr int SYNC_MAX_PWM_STEP                   = 1;
constexpr int32_t SYNC_REVERSE_LIMIT_PULSES       = 20;

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
  SYNC_TIMED,
  TARGET,
  ENCODER_CHECK
};

enum class CheckWheel : uint8_t {
  NONE,
  LEFT,
  RIGHT
};

enum class ApproachWheelState : uint8_t {
  READY,
  DRIVING,
  BRAKING,
  SETTLING,
  DONE
};

enum class CommandSource : uint8_t {
  USB_SERIAL,
  TCP
};

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

unsigned long timedStopDeadline = 0;
unsigned long targetStartMs = 0;

int syncBasePwm = 0;
int syncLeftPwm = 0;
int syncRightPwm = 0;
unsigned long syncStartMs = 0;
unsigned long syncNextControlMs = 0;
unsigned long syncNextReportMs = 0;
int32_t syncLeftBestProgress = 0;
int32_t syncRightBestProgress = 0;
unsigned long syncLeftLastProgressMs = 0;
unsigned long syncRightLastProgressMs = 0;

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
bool targetSyncEnabled = false;
bool targetPulseApproachEnabled = false;

bool leftBrakeActive = false;
bool rightBrakeActive = false;
unsigned long leftBrakeReleaseMs = 0;
unsigned long rightBrakeReleaseMs = 0;
int32_t leftCountAtBrake = 0;
int32_t rightCountAtBrake = 0;

ApproachWheelState leftApproachState = ApproachWheelState::DONE;
ApproachWheelState rightApproachState = ApproachWheelState::DONE;
unsigned long leftApproachDeadlineMs = 0;
unsigned long rightApproachDeadlineMs = 0;
unsigned long leftApproachBurstMs = 0;
unsigned long rightApproachBurstMs = 0;
int32_t leftApproachStartCount = 0;
int32_t rightApproachStartCount = 0;
float leftApproachRate = APPROACH_INITIAL_RATE_PULSES_PER_MS;
float rightApproachRate = APPROACH_INITIAL_RATE_PULSES_PER_MS;
uint8_t leftApproachNoProgress = 0;
uint8_t rightApproachNoProgress = 0;
uint16_t approachCycleCount = 0;
uint16_t activeApproachMaxCycles = APPROACH_MIN_MAX_CYCLES;
unsigned long activeTargetTimeoutMs = TARGET_MIN_TOTAL_TIMEOUT_MS;
bool accuracyRecoveryEntered = false;
bool leftLeadingWheelHeld = false;
bool rightLeadingWheelHeld = false;

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

  console.println();
  console.println("[Encoder reading]");
  console.print("source command : ");
  console.println(displayCommand);

  console.print("left raw       : ");
  console.print(raw25_26);
  console.print(" pulses (gpio 25/26)");
  if (leftEncoderForwardSign == 0) {
    console.println("; forward sign not checked");
  } else {
    console.print("; forward pulses = ");
    console.println(physicalLeft);
  }

  console.print("right raw      : ");
  console.print(raw18_19);
  console.print(" pulses (gpio 18/19)");
  if (rightEncoderForwardSign == 0) {
    console.println("; forward sign not checked");
  } else {
    console.print("; forward pulses = ");
    console.println(physicalRight);
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

void applyDynamicBrake(
    uint8_t pinEnable,
    uint8_t pinA,
    uint8_t pinB) {

  // 先关 EN，确定两个方向输入均为 LOW，再以满占空比短时接通低侧制动。
  // 这不是反转电机，不受 LEFT/RIGHT_MOTOR_INVERTED 影响。
  analogWrite(pinEnable, 0);
  digitalWrite(pinA, LOW);
  digitalWrite(pinB, LOW);
  analogWrite(pinEnable, TARGET_BRAKE_PWM);
}

void startLeftDynamicBrake() {
  applyDynamicBrake(PIN_ENA, PIN_IN1, PIN_IN2);
}

void startRightDynamicBrake() {
  applyDynamicBrake(PIN_ENB, PIN_IN3, PIN_IN4);
}

// ============================================================
// 状态和报告
// ============================================================

const char* motionModeName(MotionMode mode) {
  if (mode == MotionMode::TIMED) {
    return "timed motion";
  }

  if (mode == MotionMode::SYNC_TIMED) {
    return "stage 7 synchronized timed motion";
  }

  if (mode == MotionMode::TARGET) {
    return "target motion";
  }

  if (mode == MotionMode::ENCODER_CHECK) {
    return "encoder check";
  }

  return "none";
}

const char* commandSourceName(CommandSource source) {
  return source == CommandSource::TCP ? "wifi tcp" : "usb serial";
}

void clearMotionState() {
  moving = false;
  motionMode = MotionMode::NONE;
  activeCommand = "NONE";
  activeMotionSource = CommandSource::USB_SERIAL;
  timedStopDeadline = 0;
  targetStartMs = 0;
  activeCheckWheel = CheckWheel::NONE;

  syncBasePwm = 0;
  syncLeftPwm = 0;
  syncRightPwm = 0;
  syncStartMs = 0;
  syncNextControlMs = 0;
  syncNextReportMs = 0;
  syncLeftBestProgress = 0;
  syncRightBestProgress = 0;
  syncLeftLastProgressMs = 0;
  syncRightLastProgressMs = 0;

  leftTargetPulses = 0;
  rightTargetPulses = 0;
  leftTargetActive = false;
  rightTargetActive = false;
  leftTargetDone = false;
  rightTargetDone = false;
  targetSyncEnabled = false;
  targetPulseApproachEnabled = false;

  leftBrakeActive = false;
  rightBrakeActive = false;
  leftBrakeReleaseMs = 0;
  rightBrakeReleaseMs = 0;
  leftCountAtBrake = 0;
  rightCountAtBrake = 0;

  leftApproachState = ApproachWheelState::DONE;
  rightApproachState = ApproachWheelState::DONE;
  leftApproachDeadlineMs = 0;
  rightApproachDeadlineMs = 0;
  leftApproachBurstMs = 0;
  rightApproachBurstMs = 0;
  leftApproachStartCount = 0;
  rightApproachStartCount = 0;
  leftApproachRate = APPROACH_INITIAL_RATE_PULSES_PER_MS;
  rightApproachRate = APPROACH_INITIAL_RATE_PULSES_PER_MS;
  leftApproachNoProgress = 0;
  rightApproachNoProgress = 0;
  approachCycleCount = 0;
  activeApproachMaxCycles = APPROACH_MIN_MAX_CYCLES;
  activeTargetTimeoutMs = TARGET_MIN_TOTAL_TIMEOUT_MS;
  accuracyRecoveryEntered = false;
  leftLeadingWheelHeld = false;
  rightLeadingWheelHeld = false;

  leftBestProgress = 0;
  rightBestProgress = 0;
  leftLastProgressMs = 0;
  rightLastProgressMs = 0;
}

const char* friendlyStopReason(const char* reason) {
  if (strcmp(reason, "TARGET_COMPLETE") == 0) {
    return "Target reached normally.";
  }
  if (strcmp(reason, "TARGET_ACCURACY_FAILED") == 0) {
    return "Target crossing completed, but final distance accuracy exceeded the FDS tolerance.";
  }
  if (strcmp(reason, "ACTION_COMPLETE") == 0) {
    return "Timed motion finished normally.";
  }
  if (strcmp(reason, "SYNC_COMPLETE") == 0) {
    return "Stage 7 synchronized timed motion finished normally.";
  }
  if (strcmp(reason, "USER_STOP") == 0) {
    return "Stopped by the user.";
  }
  if (strcmp(reason, "TCP_DISCONNECT") == 0) {
    return "The Wi-Fi TCP control client disconnected.";
  }
  if (strcmp(reason, "TCP_HEARTBEAT_TIMEOUT") == 0) {
    return "The Wi-Fi TCP heartbeat timed out.";
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
  if (strcmp(reason, "SYNC_REVERSE_LEFT") == 0) {
    return "Left forward count became negative beyond the Stage 7 limit.";
  }
  if (strcmp(reason, "SYNC_REVERSE_RIGHT") == 0) {
    return "Right forward count became negative beyond the Stage 7 limit.";
  }
  if (strcmp(reason, "TARGET_TIMEOUT") == 0) {
    return "The target was not completed within 30 seconds.";
  }
  if (strcmp(reason, "APPROACH_STALL_LEFT") == 0) {
    return "Left wheel produced no usable progress in six pulse-approach cycles.";
  }
  if (strcmp(reason, "APPROACH_STALL_RIGHT") == 0) {
    return "Right wheel produced no usable progress in six pulse-approach cycles.";
  }
  if (strcmp(reason, "APPROACH_REVERSE_LEFT") == 0) {
    return "Left encoder moved backward beyond the pulse-approach safety limit.";
  }
  if (strcmp(reason, "APPROACH_REVERSE_RIGHT") == 0) {
    return "Right encoder moved backward beyond the pulse-approach safety limit.";
  }
  if (strcmp(reason, "APPROACH_CYCLE_LIMIT") == 0) {
    return "Pulse approach exceeded the maximum number of cycles.";
  }
  if (strcmp(reason, "APPROACH_OVERSHOOT_LEFT") == 0) {
    return "Left wheel exceeded the maximum allowed final target error.";
  }
  if (strcmp(reason, "APPROACH_OVERSHOOT_RIGHT") == 0) {
    return "Right wheel exceeded the maximum allowed final target error.";
  }
  if (strcmp(reason, "BOOT_DEFAULT") == 0) {
    return "Safe stop after startup.";
  }
  return "Motion stopped by a safety or command rule.";
}

const char* resultForReason(const char* reason) {
  if (strcmp(reason, "TARGET_COMPLETE") == 0 ||
      strcmp(reason, "SYNC_COMPLETE") == 0 ||
      strcmp(reason, "ACTION_COMPLETE") == 0) {
    return "passed";
  }
  if (strcmp(reason, "USER_STOP") == 0) {
    return "stopped by user";
  }
  return "not passed";
}

float normalizedEquivalentPulses(
    int32_t pulses,
    float pulsesPerRevolution) {

  const float averagePpr =
      (LEFT_PULSES_PER_REV + RIGHT_PULSES_PER_REV) * 0.5f;
  return static_cast<float>(pulses) /
      pulsesPerRevolution * averagePpr;
}

bool fdsFinalAccuracyPassed(
    int32_t leftTarget,
    int32_t rightTarget,
    int32_t finalLeft,
    int32_t finalRight) {

  if (leftTarget <= 0 || rightTarget <= 0) {
    return false;
  }

  const float leftErrorPercent = 100.0f * fabsf(
      static_cast<float>(finalLeft - leftTarget) /
      static_cast<float>(leftTarget));
  const float rightErrorPercent = 100.0f * fabsf(
      static_cast<float>(finalRight - rightTarget) /
      static_cast<float>(rightTarget));

  const float leftDistanceCm =
      static_cast<float>(finalLeft) /
      LEFT_PULSES_PER_REV * WHEEL_CIRCUMFERENCE_CM;
  const float rightDistanceCm =
      static_cast<float>(finalRight) /
      RIGHT_PULSES_PER_REV * WHEEL_CIRCUMFERENCE_CM;
  const float averageDistanceCm =
      (fabsf(leftDistanceCm) + fabsf(rightDistanceCm)) * 0.5f;
  const float mismatchPercent =
      averageDistanceCm > 0.001f
          ? 100.0f * fabsf(leftDistanceCm - rightDistanceCm) /
              averageDistanceCm
          : 1000.0f;

  return leftErrorPercent <= FDS_MAX_FINAL_ERROR_PERCENT &&
      rightErrorPercent <= FDS_MAX_FINAL_ERROR_PERCENT &&
      mismatchPercent <= FDS_MAX_WHEEL_MISMATCH_PERCENT;
}

void printSyncResult(int32_t finalLeft, int32_t finalRight) {
  const float leftEquivalent = normalizedEquivalentPulses(
      finalLeft,
      LEFT_PULSES_PER_REV);
  const float rightEquivalent = normalizedEquivalentPulses(
      finalRight,
      RIGHT_PULSES_PER_REV);
  const float errorEquivalent = leftEquivalent - rightEquivalent;

  const float leftDistanceCm =
      static_cast<float>(finalLeft) /
      LEFT_PULSES_PER_REV * WHEEL_CIRCUMFERENCE_CM;
  const float rightDistanceCm =
      static_cast<float>(finalRight) /
      RIGHT_PULSES_PER_REV * WHEEL_CIRCUMFERENCE_CM;
  const float averageDistanceCm =
      (leftDistanceCm + rightDistanceCm) * 0.5f;
  const float relativeErrorPercent =
      averageDistanceCm > 0.001f
          ? 100.0f * (leftDistanceCm - rightDistanceCm) /
              averageDistanceCm
          : 0.0f;

  console.println();
  console.println("[Stage 7 synchronization result]");
  console.print("left distance   : ");
  console.print(leftDistanceCm, 3);
  console.println(" cm");
  console.print("right distance  : ");
  console.print(rightDistanceCm, 3);
  console.println(" cm");
  console.print("equiv error     : ");
  console.print(errorEquivalent, 2);
  console.println(" pulses (left - right)");
  console.print("distance error  : ");
  console.print(relativeErrorPercent, 2);
  console.println("% (left - right)");
  console.print("final PWM       : left ");
  console.print(syncLeftPwm);
  console.print(", right ");
  console.println(syncRightPwm);
}

void printTargetResult(
    const String& command,
    int32_t leftTarget,
    int32_t rightTarget,
    int32_t finalLeft,
    int32_t finalRight) {

  String displayCommand = command;
  displayCommand.toLowerCase();

  console.println();
  console.println("[Target result]");
  console.print("command         : ");
  console.println(displayCommand);

  if (leftTarget > 0) {
    const int32_t leftError = finalLeft - leftTarget;
    const float leftErrorPercent =
        100.0f * static_cast<float>(leftError) /
        static_cast<float>(leftTarget);

    console.print("left progress   : ");
    console.print(finalLeft);
    console.print(" / ");
    console.print(leftTarget);
    console.println(" pulses");
    console.print("left error      : ");
    console.print(leftError);
    console.print(" pulses (");
    console.print(leftErrorPercent, 2);
    console.println("%)");
  }

  if (rightTarget > 0) {
    const int32_t rightError = finalRight - rightTarget;
    const float rightErrorPercent =
        100.0f * static_cast<float>(rightError) /
        static_cast<float>(rightTarget);

    console.print("right progress  : ");
    console.print(finalRight);
    console.print(" / ");
    console.print(rightTarget);
    console.println(" pulses");
    console.print("right error     : ");
    console.print(rightError);
    console.print(" pulses (");
    console.print(rightErrorPercent, 2);
    console.println("%)");
  }

  if (targetPulseApproachEnabled) {
    console.print("approach PWM    : ");
    console.println(APPROACH_PWM);
  }

  if (displayCommand == "fds" && leftTarget > 0 && rightTarget > 0) {
    const float leftDistanceCm =
        static_cast<float>(finalLeft) /
        LEFT_PULSES_PER_REV * WHEEL_CIRCUMFERENCE_CM;
    const float rightDistanceCm =
        static_cast<float>(finalRight) /
        RIGHT_PULSES_PER_REV * WHEEL_CIRCUMFERENCE_CM;
    const float averageDistanceCm =
        (fabsf(leftDistanceCm) + fabsf(rightDistanceCm)) * 0.5f;
    const float mismatchPercent =
        averageDistanceCm > 0.001f
            ? 100.0f * fabsf(leftDistanceCm - rightDistanceCm) /
                averageDistanceCm
            : 1000.0f;
    const bool accuracyPassed = fdsFinalAccuracyPassed(
        leftTarget,
        rightTarget,
        finalLeft,
        finalRight);

    console.print("left final cm   : ");
    console.println(leftDistanceCm, 3);
    console.print("right final cm  : ");
    console.println(rightDistanceCm, 3);
    console.print("final mismatch  : ");
    console.print(mismatchPercent, 2);
    console.println("%");
    console.print("accuracy limits : each wheel <= ");
    console.print(FDS_MAX_FINAL_ERROR_PERCENT, 1);
    console.print("%, mismatch <= ");
    console.print(FDS_MAX_WHEEL_MISMATCH_PERCENT, 1);
    console.println("%");
    console.print("accuracy result : ");
    console.println(accuracyPassed ? "passed" : "not passed");
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
    armedCommandSourceValid = false;
  }

  int32_t finalLeft;
  int32_t finalRight;
  readPhysicalEncoderCounts(finalLeft, finalRight);

  const bool evaluateFdsAccuracy =
      finishedMode == MotionMode::TARGET &&
      finishedCommand == "FDS" &&
      strcmp(reason, "TARGET_COMPLETE") == 0;
  const bool fdsAccuracyPassed =
      !evaluateFdsAccuracy || fdsFinalAccuracyPassed(
          finishedLeftTarget,
          finishedRightTarget,
          finalLeft,
          finalRight);
  const char* reportedReason =
      fdsAccuracyPassed ? reason : "TARGET_ACCURACY_FAILED";

  String reasonCode = String(reportedReason);
  reasonCode.toLowerCase();

  String displayCommand = finishedCommand;
  displayCommand.toLowerCase();

  console.println();
  console.println("========================================");
  console.println("[Motion finished]");
  console.print("result          : ");
  console.println(resultForReason(reportedReason));
  console.print("reason          : ");
  console.println(friendlyStopReason(reportedReason));
  console.print("reason code     : ");
  console.println(reasonCode);
  console.print("command         : ");
  console.println(displayCommand);
  console.print("safety          : ");
  console.println(armed ? "armed" : "disarmed");

  if (wasMoving) {
    printEncoderReport(finishedCommand);

    if (finishedMode == MotionMode::TARGET) {
      printTargetResult(
          finishedCommand,
          finishedLeftTarget,
          finishedRightTarget,
          finalLeft,
          finalRight);
      if (finishedCommand == "FDS") {
        console.println();
        console.println("[FDS phase report]");
        console.print("final cycle     : ");
        console.print(approachCycleCount);
        console.print(" / dynamic limit ");
        console.println(activeApproachMaxCycles);
        console.print("accuracy recovery entered : ");
        console.println(accuracyRecoveryEntered ? "yes" : "no");
        console.println("recovery meaning: fine-distance correction; NOT an ESP32 reset");
        console.print("program-held leading wheel: ");
        if (leftLeadingWheelHeld && rightLeadingWheelHeld) {
          console.println("both at different cycles");
        } else if (leftLeadingWheelHeld) {
          console.println("left");
        } else if (rightLeadingWheelHeld) {
          console.println("right");
        } else {
          console.println("none");
        }
        console.println("held meaning    : intentionally paused by software; NOT a wheel fault");
        console.println("ESP32 restart   : record YES only if the startup banner reappeared");
      }
    } else if (finishedMode == MotionMode::SYNC_TIMED) {
      printSyncResult(finalLeft, finalRight);
    }
  }

  if (strcmp(reportedReason, "STALL_LEFT") == 0 ||
      strcmp(reportedReason, "STALL_RIGHT") == 0) {
    console.println("next            : stop target tests; run the encoder check again");
  } else if (strcmp(reportedReason, "TARGET_ACCURACY_FAILED") == 0) {
  console.println("next            : stop longer FDS tests; record final pulses and cycle log");
  } else if (strcmp(reportedReason, "TARGET_COMPLETE") == 0 ||
             strcmp(reportedReason, "SYNC_COMPLETE") == 0) {
    console.println("next            : record the result; arm again before another motion");
  } else if (strcmp(reportedReason, "USER_STOP") == 0) {
    console.println("next            : arm again only if another test is needed");
  }
  console.println("========================================");

  clearMotionState();
}

void printStatus() {
  int32_t physicalLeft;
  int32_t physicalRight;
  readPhysicalEncoderCounts(physicalLeft, physicalRight);

  String displayCommand = activeCommand;
  displayCommand.toLowerCase();

  console.println();
  console.println("[Current status]");
  console.print("safety          : ");
  console.println(armed ? "armed" : "disarmed");
  console.print("motors          : ");
  console.println(moving ? "moving" : "stopped");
  console.print("mode            : ");
  console.println(motionModeName(motionMode));
  console.print("active command  : ");
  console.println(displayCommand);
  console.print("control source  : ");
  if (moving) {
    console.println(commandSourceName(activeMotionSource));
  } else if (armed && armedCommandSourceValid) {
    console.println(commandSourceName(armedCommandSource));
  } else {
    console.println("none");
  }
  console.print("wifi AP         : ");
  console.println(WIFI_AP_SSID);
  console.print("wifi IP         : ");
  console.println(WiFi.softAPIP());
  console.print("tcp client      : ");
  console.println(
      tcpClientActive && tcpClient.connected()
          ? "connected"
          : "not connected");
  console.print("left check      : ");
  console.println(leftEncoderForwardSign == 0 ? "not completed" : "completed");
  console.print("right check     : ");
  console.println(rightEncoderForwardSign == 0 ? "not completed" : "completed");
  console.print("target commands : ");
  console.println(
      leftEncoderForwardSign != 0 && rightEncoderForwardSign != 0
          ? "ready"
          : "locked until required encoder checks pass");
}

void printConfig() {
  console.println();
  console.println("[Configuration]");
  console.println("version         : Atlas 7C wireless bridge v1 over Stage 7B V5");
  console.print("wifi SSID       : ");
  console.println(WIFI_AP_SSID);
  console.print("wifi IP / port  : ");
  console.print(WiFi.softAPIP());
  console.print(" / ");
  console.println(WIFI_TCP_PORT);
  console.print("tcp heartbeat   : ");
  console.print(TCP_HEARTBEAT_TIMEOUT_MS);
  console.println(" ms motion timeout");
  console.print("wheel distance  : ");
  console.print(WHEEL_CIRCUMFERENCE_CM, 2);
  console.println(" cm per revolution");
  console.print("left PPR        : ");
  console.println(LEFT_PULSES_PER_REV, 2);
  console.print("right PPR       : ");
  console.println(RIGHT_PULSES_PER_REV, 2);
  console.print("target PWM      : left ");
  console.print(LEFT_TARGET_PWM);
  console.print(", right ");
  console.println(RIGHT_TARGET_PWM);
  console.println("motor direction : left inverted, right normal");
  console.println("encoder mapping : left gpio 25/26, right gpio 18/19");
  console.print("left sign       : ");
  if (leftEncoderForwardSign == 0) {
    console.println("not checked");
  } else {
    console.println(leftEncoderForwardSign);
  }
  console.print("right sign      : ");
  if (rightEncoderForwardSign == 0) {
    console.println("not checked");
  } else {
    console.println(rightEncoderForwardSign);
  }
  console.print("stall timeout   : ");
  console.print(STALL_TIMEOUT_MS);
  console.println(" ms");
  console.print("timeout range   : ");
  console.print(TARGET_MIN_TOTAL_TIMEOUT_MS);
  console.print(" to ");
  console.print(TARGET_MAX_TOTAL_TIMEOUT_MS);
  console.println(" ms; selected from FDS target size");
  console.print("sync interval   : ");
  console.print(SYNC_CONTROL_INTERVAL_MS);
  console.println(" ms");
  console.print("sync deadband   : ");
  console.print(SYNC_DEADBAND_EQUIV_PULSES, 1);
  console.println(" equivalent pulses");
  console.print("sync max boost  : +");
  console.print(SYNC_MAX_BOOST_PWM);
  console.println(" PWM to lagging wheel only");
  console.println("legacy FD       : fixed 160 PWM target-distance fallback");
  console.println("new FDS         : adaptive PWM 80 pulse approach with fast stop");
  console.print("burst range     : ");
  console.print(APPROACH_MIN_BURST_MS);
  console.print(" to ");
  console.print(APPROACH_MAX_BURST_MS);
  console.println(" ms");
  console.print("settle after    : ");
  console.print(APPROACH_SETTLE_MS);
  console.println(" ms after brake release");
  console.print("target deadband : ");
  console.print(APPROACH_DEADBAND_PULSES);
  console.println(" pulses");
  console.print("normal cycles   : ");
  console.println(APPROACH_NORMAL_CYCLES);
  console.print("cycle limit     : ");
  console.print(APPROACH_MIN_MAX_CYCLES);
  console.print(" to ");
  console.print(APPROACH_ABSOLUTE_MAX_CYCLES);
  console.println("; selected from FDS target pulses");
  console.print("catch-up trigger: ");
  console.print(APPROACH_CATCH_UP_THRESHOLD_PERCENT, 1);
  console.println("% normalized progress difference");
  console.print("brake setting   : ");
  console.print(TARGET_BRAKE_PWM);
  console.print(" PWM for ");
  console.print(TARGET_BRAKE_HOLD_MS);
  console.println(" ms");
  console.print("FDS accuracy    : each wheel <= ");
  console.print(FDS_MAX_FINAL_ERROR_PERCENT, 1);
  console.print("%, mismatch <= ");
  console.print(FDS_MAX_WHEEL_MISMATCH_PERCENT, 1);
  console.println("%");
}

void printHelp() {
  console.println();
  console.println("[Command guide]");
  console.println("Wi-Fi control:");
  console.print("  SSID                 ");
  console.println(WIFI_AP_SSID);
  console.print("  TCP                  192.168.4.1:");
  console.println(WIFI_TCP_PORT);
  console.println("  ARM and ACTION must come from the same USB or TCP link");
  console.println("  TCP terminal sends PING automatically; do not type it manually");
  console.println();
  console.println("Safety and information:");
  console.println("  arm                 allow one limited motion");
  console.println("  stop                stop immediately and disarm");
  console.println("  status              show current state");
  console.println("  config              show parameters and learned signs");
  console.println("  help                show this guide");
  console.println("  zero                reset encoder counts");
  console.println("  enc                 show readable encoder values");
  console.println("  uncal               clear learned encoder signs");
  console.println();
  console.println("Required checks after every restart:");
  console.println("  arm  then  check left");
  console.println("  arm  then  check right");
  console.println();
  console.println("Target motion, only after the required checks:");
  console.println("  arm  then  testl 100");
  console.println("  arm  then  testr 100");
  console.println("  arm  then  fd 5");
  console.println("  arm  then  fds 5   (Stage 7B V5 dynamic-limit pulse approach)");
  console.println();
  console.println("Short timed motion:");
  console.println("  f / b / tl / tr / lf / lb / rf / rb  PWM  time_ms");
  console.println("  example: arm  then  lf 160 200");
  console.println();
  console.println("Stage 7 suspended-wheel synchronization test:");
  console.println("  arm  then  sync 80 1000");
  console.println("  SYNC is forward-only and requires both encoder checks");
  console.println("  Use only with both wheels at least 2 cm off the surface");
  console.println();
  console.println("Input is not case-sensitive. Lowercase is recommended.");
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
  return command == "F"  ||
         command == "B"  ||
         command == "TL" ||
         command == "TR" ||
         command == "LF" ||
         command == "LB" ||
         command == "RF" ||
         command == "RB";
}

bool motionStartAllowed() {
  if (moving) {
    finishMotion("MOTION_ALREADY_ACTIVE", true);
    console.println("Error: another motion was already active. The system is now disarmed.");
    return false;
  }

  if (!armed) {
    stopMotorOutputsImmediately();
    console.println();
    console.println("[Command blocked]");
    console.println("reason          : the system is not armed");
    console.println("next            : send 'arm', wait for Ready, then send one motion command");
    return false;
  }

  if (!armedCommandSourceValid ||
      armedCommandSource != currentCommandSource) {
    stopMotorOutputsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    console.println();
    console.println("[Command blocked]");
    console.println("reason          : ARM and ACTION came from different control links");
    console.println("safety          : disarmed");
    console.println("next            : send ARM and the action from the same USB or TCP link");
    return false;
  }

  activeMotionSource = currentCommandSource;

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
    console.print("Error: PWM must be between ");
    console.print(MIN_PWM);
    console.print(" and ");
    console.println(MAX_PWM);
    return;
  }

  if (durationMs < MIN_DURATION_MS ||
      durationMs > MAX_DURATION_MS) {
    finishMotion("INVALID_DURATION", true);
    console.print("Error: duration must be between ");
    console.print(MIN_DURATION_MS);
    console.print(" and ");
    console.print(MAX_DURATION_MS);
    console.println(" ms");
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

  console.println();
  console.println("[Motion started]");
  console.println("mode            : timed motion");
  console.print("command         : ");
  console.println(displayCommand);
  console.print("motor command   : left ");
  console.print(leftSpeed);
  console.print(", right ");
  console.println(rightSpeed);
  console.print("duration        : ");
  console.print(durationMs);
  console.println(" ms");
}

int movePwmToward(int current, int target, int maximumStep) {
  if (current < target) {
    const int next = current + maximumStep;
    return next < target ? next : target;
  }
  if (current > target) {
    const int next = current - maximumStep;
    return next > target ? next : target;
  }
  return current;
}

void startSyncMotion(int basePwm, unsigned long durationMs) {
  if (!motionStartAllowed()) {
    return;
  }

  if (leftEncoderForwardSign == 0 || rightEncoderForwardSign == 0) {
    stopMotorOutputsImmediately();
    armed = false;
    console.println();
    console.println("[SYNC command blocked]");
    console.println("reason          : both encoder signs must be checked after restart");
    console.println("next            : arm + check left, then arm + check right");
    return;
  }

  if (basePwm < MIN_PWM || basePwm > SYNC_MAX_BASE_PWM) {
    finishMotion("INVALID_SYNC_PWM", true);
    console.print("Error: SYNC base PWM must be between ");
    console.print(MIN_PWM);
    console.print(" and ");
    console.println(SYNC_MAX_BASE_PWM);
    return;
  }

  if (durationMs < 500 || durationMs > MAX_DURATION_MS) {
    finishMotion("INVALID_SYNC_DURATION", true);
    console.println("Error: SYNC duration must be between 500 and 1000 ms.");
    return;
  }

  resetEncoderCounts();

  const unsigned long now = millis();
  activeCommand = "SYNC";
  motionMode = MotionMode::SYNC_TIMED;
  moving = true;
  timedStopDeadline = now + durationMs;

  syncBasePwm = basePwm;
  syncLeftPwm = basePwm;
  syncRightPwm = basePwm;
  syncStartMs = now;
  syncNextControlMs = now + SYNC_START_DELAY_MS;
  syncNextReportMs = now + SYNC_REPORT_INTERVAL_MS;
  syncLeftBestProgress = 0;
  syncRightBestProgress = 0;
  syncLeftLastProgressMs = now;
  syncRightLastProgressMs = now;

  driveMotors(syncLeftPwm, syncRightPwm);

  console.println();
  console.println("[Stage 7 synchronization started]");
  console.print("base PWM        : ");
  console.println(syncBasePwm);
  console.print("duration        : ");
  console.print(durationMs);
  console.println(" ms");
  console.println("controller      : boost lagging wheel only");
  console.println("safety          : both wheels must remain suspended");
}

void monitorSyncMotion() {
  if (!moving || motionMode != MotionMode::SYNC_TIMED) {
    return;
  }

  const unsigned long now = millis();
  int32_t physicalLeft;
  int32_t physicalRight;
  readPhysicalEncoderCounts(physicalLeft, physicalRight);

  if (physicalLeft < -SYNC_REVERSE_LIMIT_PULSES) {
    finishMotion("SYNC_REVERSE_LEFT", true);
    return;
  }
  if (physicalRight < -SYNC_REVERSE_LIMIT_PULSES) {
    finishMotion("SYNC_REVERSE_RIGHT", true);
    return;
  }

  if (physicalLeft > syncLeftBestProgress) {
    syncLeftBestProgress = physicalLeft;
    syncLeftLastProgressMs = now;
  }
  if (physicalRight > syncRightBestProgress) {
    syncRightBestProgress = physicalRight;
    syncRightLastProgressMs = now;
  }

  if (now - syncLeftLastProgressMs >= STALL_TIMEOUT_MS) {
    finishMotion("STALL_LEFT", true);
    return;
  }
  if (now - syncRightLastProgressMs >= STALL_TIMEOUT_MS) {
    finishMotion("STALL_RIGHT", true);
    return;
  }

  if (static_cast<int32_t>(now - timedStopDeadline) >= 0) {
    finishMotion("SYNC_COMPLETE", true);
    return;
  }

  if (static_cast<int32_t>(now - syncNextControlMs) < 0) {
    return;
  }

  do {
    syncNextControlMs += SYNC_CONTROL_INTERVAL_MS;
  } while (static_cast<int32_t>(now - syncNextControlMs) >= 0);

  const float leftEquivalent = normalizedEquivalentPulses(
      physicalLeft,
      LEFT_PULSES_PER_REV);
  const float rightEquivalent = normalizedEquivalentPulses(
      physicalRight,
      RIGHT_PULSES_PER_REV);
  const float errorEquivalent = leftEquivalent - rightEquivalent;

  int targetLeftPwm = syncBasePwm;
  int targetRightPwm = syncBasePwm;

  if (errorEquivalent > SYNC_DEADBAND_EQUIV_PULSES) {
    int boost = static_cast<int>(lroundf(
        (errorEquivalent - SYNC_DEADBAND_EQUIV_PULSES) *
        SYNC_KP_PWM_PER_EQUIV_PULSE));
    if (boost < 1) {
      boost = 1;
    }
    if (boost > SYNC_MAX_BOOST_PWM) {
      boost = SYNC_MAX_BOOST_PWM;
    }
    targetRightPwm = syncBasePwm + boost;

  } else if (errorEquivalent < -SYNC_DEADBAND_EQUIV_PULSES) {
    int boost = static_cast<int>(lroundf(
        (-errorEquivalent - SYNC_DEADBAND_EQUIV_PULSES) *
        SYNC_KP_PWM_PER_EQUIV_PULSE));
    if (boost < 1) {
      boost = 1;
    }
    if (boost > SYNC_MAX_BOOST_PWM) {
      boost = SYNC_MAX_BOOST_PWM;
    }
    targetLeftPwm = syncBasePwm + boost;
  }

  if (targetLeftPwm > MAX_PWM) {
    targetLeftPwm = MAX_PWM;
  }
  if (targetRightPwm > MAX_PWM) {
    targetRightPwm = MAX_PWM;
  }

  syncLeftPwm = movePwmToward(
      syncLeftPwm,
      targetLeftPwm,
      SYNC_MAX_PWM_STEP);
  syncRightPwm = movePwmToward(
      syncRightPwm,
      targetRightPwm,
      SYNC_MAX_PWM_STEP);
  driveMotors(syncLeftPwm, syncRightPwm);

  if (static_cast<int32_t>(now - syncNextReportMs) >= 0) {
    syncNextReportMs = now + SYNC_REPORT_INTERVAL_MS;
    console.print("SYNC t=");
    console.print(now - syncStartMs);
    console.print(" ms; L=");
    console.print(physicalLeft);
    console.print("; R=");
    console.print(physicalRight);
    console.print("; error=");
    console.print(errorEquivalent, 2);
    console.print("; PWM=");
    console.print(syncLeftPwm);
    console.print("/");
    console.println(syncRightPwm);
  }
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

  console.println();
  console.println("[Encoder check started]");
  console.print("wheel           : ");
  console.println(wheel == CheckWheel::LEFT ? "left" : "right");
  console.print("duration        : ");
  console.print(ENCODER_CHECK_DURATION_MS);
  console.println(" ms");
  console.println("watch           : this wheel must move toward the robot's front");
}

void finishEncoderCheck() {
  const CheckWheel checkedWheel = activeCheckWheel;

  stopMotorOutputsImmediately();
  moving = false;
  delay(100);
  armed = false;
  armedCommandSourceValid = false;

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

  console.println();
  console.println("========================================");
  console.println("[Encoder check finished]");
  console.print("wheel           : ");
  console.println(checkedWheel == CheckWheel::LEFT ? "left" : "right");
  console.print("result          : ");
  console.println(checkPassed ? "pulse check passed" : "pulse check not passed");
  console.print("active raw      : ");
  console.print(activeRaw);
  console.println(" pulses");
  console.print("other raw       : ");
  console.print(inactiveRaw);
  console.println(" pulses");

  if (checkPassed) {
    console.print("learned sign    : ");
    console.println(activeRaw > 0 ? "+1" : "-1");
    console.println("visual decision : continue only if this wheel moved forward");
    console.println("next            : arm and check the other wheel");
  } else if (!enoughPulses) {
    console.println("reason          : too few pulses from the active encoder");
    console.println("next            : stop testing and inspect encoder power/signal connections");
  } else {
    console.println("reason          : the inactive encoder also changed too much");
    console.println("next            : stop testing and inspect mapping or electrical noise");
  }

  console.println("safety          : disarmed");
  console.println("========================================");
  clearMotionState();
}

uint16_t calculateApproachMaxCycles(
    int32_t requestedLeftTarget,
    int32_t requestedRightTarget) {

  const int32_t maximumTarget =
      requestedLeftTarget > requestedRightTarget
          ? requestedLeftTarget
          : requestedRightTarget;
  const float scaledCycles =
      static_cast<float>(maximumTarget) *
      APPROACH_MAX_CYCLES_PER_TARGET_PULSE;
  uint32_t calculatedCycles =
      static_cast<uint32_t>(ceilf(scaledCycles)) +
      APPROACH_MAX_CYCLE_MARGIN;

  if (calculatedCycles < APPROACH_MIN_MAX_CYCLES) {
    calculatedCycles = APPROACH_MIN_MAX_CYCLES;
  }
  if (calculatedCycles > APPROACH_ABSOLUTE_MAX_CYCLES) {
    calculatedCycles = APPROACH_ABSOLUTE_MAX_CYCLES;
  }
  return static_cast<uint16_t>(calculatedCycles);
}

unsigned long calculateApproachTimeoutMs(uint16_t cycleLimit) {
  unsigned long calculatedTimeout =
      static_cast<unsigned long>(cycleLimit) *
      TARGET_APPROACH_CYCLE_BUDGET_MS +
      TARGET_APPROACH_TIMEOUT_MARGIN_MS;

  if (calculatedTimeout < TARGET_MIN_TOTAL_TIMEOUT_MS) {
    calculatedTimeout = TARGET_MIN_TOTAL_TIMEOUT_MS;
  }
  if (calculatedTimeout > TARGET_MAX_TOTAL_TIMEOUT_MS) {
    calculatedTimeout = TARGET_MAX_TOTAL_TIMEOUT_MS;
  }
  return calculatedTimeout;
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
    console.println("Error: at least one target must be positive.");
    return;
  }

  if (requestedLeftTarget > 0 && leftEncoderForwardSign == 0) {
    stopMotorOutputsImmediately();
    armed = false;
    console.println();
    console.println("[Target command blocked]");
    console.println("reason          : left encoder sign has not been checked");
    console.println("next            : arm, then send 'check left'");
    return;
  }

  if (requestedRightTarget > 0 && rightEncoderForwardSign == 0) {
    stopMotorOutputsImmediately();
    armed = false;
    console.println();
    console.println("[Target command blocked]");
    console.println("reason          : right encoder sign has not been checked");
    console.println("next            : arm, then send 'check right'");
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
  targetSyncEnabled =
      command == "FDS" && leftTargetActive && rightTargetActive;
  targetPulseApproachEnabled = targetSyncEnabled;

  leftBrakeActive = false;
  rightBrakeActive = false;
  leftBrakeReleaseMs = 0;
  rightBrakeReleaseMs = 0;
  leftCountAtBrake = 0;
  rightCountAtBrake = 0;

  leftApproachState = leftTargetActive
      ? ApproachWheelState::READY
      : ApproachWheelState::DONE;
  rightApproachState = rightTargetActive
      ? ApproachWheelState::READY
      : ApproachWheelState::DONE;
  leftApproachDeadlineMs = 0;
  rightApproachDeadlineMs = 0;
  leftApproachBurstMs = 0;
  rightApproachBurstMs = 0;
  leftApproachStartCount = 0;
  rightApproachStartCount = 0;
  leftApproachRate = APPROACH_INITIAL_RATE_PULSES_PER_MS;
  rightApproachRate = APPROACH_INITIAL_RATE_PULSES_PER_MS;
  leftApproachNoProgress = 0;
  rightApproachNoProgress = 0;
  approachCycleCount = 0;
  activeApproachMaxCycles = targetPulseApproachEnabled
      ? calculateApproachMaxCycles(
          requestedLeftTarget,
          requestedRightTarget)
      : APPROACH_MIN_MAX_CYCLES;
  activeTargetTimeoutMs = targetPulseApproachEnabled
      ? calculateApproachTimeoutMs(activeApproachMaxCycles)
      : TARGET_MIN_TOTAL_TIMEOUT_MS;
  accuracyRecoveryEntered = false;
  leftLeadingWheelHeld = false;
  rightLeadingWheelHeld = false;

  leftBestProgress = 0;
  rightBestProgress = 0;
  leftLastProgressMs = now;
  rightLastProgressMs = now;

  if (targetSyncEnabled) {
    syncBasePwm = MIN_PWM;
    syncLeftPwm = syncBasePwm;
    syncRightPwm = syncBasePwm;
    syncStartMs = now;
    syncNextControlMs = now + SYNC_START_DELAY_MS;
    syncNextReportMs = now + SYNC_REPORT_INTERVAL_MS;
  }

  const int initialLeftPwm = targetPulseApproachEnabled
      ? 0
      : LEFT_TARGET_PWM;
  const int initialRightPwm = targetPulseApproachEnabled
      ? 0
      : RIGHT_TARGET_PWM;

  driveMotors(
      leftTargetActive ? initialLeftPwm : 0,
      rightTargetActive ? initialRightPwm : 0);

  String displayCommand = command;
  displayCommand.toLowerCase();

  console.println();
  console.println("[Motion started]");
  console.print("mode            : ");
  console.println(targetPulseApproachEnabled
      ? "Stage 7B V5 adaptive pulse approach with dynamic limits"
      : "legacy target motion");
  console.print("command         : ");
  console.println(displayCommand);
  console.print("left target     : ");
  if (leftTargetActive) {
    console.print(leftTargetPulses);
    console.print(" pulses at PWM ");
    console.println(initialLeftPwm);
  } else {
    console.println("not used");
  }
  console.print("right target    : ");
  if (rightTargetActive) {
    console.print(rightTargetPulses);
    console.print(" pulses at PWM ");
    console.println(initialRightPwm);
  } else {
    console.println("not used");
  }

  if (targetPulseApproachEnabled) {
    console.println("controller      : PWM 80 short burst, fast stop, settle, adaptive next burst");
    console.println("start rule      : both wheels start each approach cycle together when possible");
    console.print("burst range     : ");
    console.print(APPROACH_MIN_BURST_MS);
    console.print(" to ");
    console.print(APPROACH_MAX_BURST_MS);
    console.println(" ms");
    console.print("dynamic brake   : ");
    console.print(TARGET_BRAKE_PWM);
    console.print(" PWM for ");
    console.print(TARGET_BRAKE_HOLD_MS);
    console.println(" ms");
    console.print("settle time     : ");
    console.print(APPROACH_SETTLE_MS);
    console.println(" ms");
    console.print("finish deadband : ");
    console.print(APPROACH_DEADBAND_PULSES);
    console.println(" pulses");
    console.print("cycle limit     : ");
    console.println(activeApproachMaxCycles);
    console.print("total timeout   : ");
    console.print(activeTargetTimeoutMs);
    console.println(" ms");
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

void updateTargetSynchronization(
    int32_t physicalLeft,
    int32_t physicalRight,
    unsigned long now) {

  if (!targetSyncEnabled ||
      leftTargetDone ||
      rightTargetDone ||
      static_cast<int32_t>(now - syncNextControlMs) < 0) {
    return;
  }

  do {
    syncNextControlMs += SYNC_CONTROL_INTERVAL_MS;
  } while (static_cast<int32_t>(now - syncNextControlMs) >= 0);

  const float leftEquivalent = normalizedEquivalentPulses(
      physicalLeft,
      LEFT_PULSES_PER_REV);
  const float rightEquivalent = normalizedEquivalentPulses(
      physicalRight,
      RIGHT_PULSES_PER_REV);
  const float errorEquivalent = leftEquivalent - rightEquivalent;

  int targetLeftPwm = syncBasePwm;
  int targetRightPwm = syncBasePwm;

  if (errorEquivalent > SYNC_DEADBAND_EQUIV_PULSES) {
    int boost = static_cast<int>(lroundf(
        (errorEquivalent - SYNC_DEADBAND_EQUIV_PULSES) *
        SYNC_KP_PWM_PER_EQUIV_PULSE));
    if (boost < 1) {
      boost = 1;
    }
    if (boost > SYNC_MAX_BOOST_PWM) {
      boost = SYNC_MAX_BOOST_PWM;
    }
    targetRightPwm = syncBasePwm + boost;

  } else if (errorEquivalent < -SYNC_DEADBAND_EQUIV_PULSES) {
    int boost = static_cast<int>(lroundf(
        (-errorEquivalent - SYNC_DEADBAND_EQUIV_PULSES) *
        SYNC_KP_PWM_PER_EQUIV_PULSE));
    if (boost < 1) {
      boost = 1;
    }
    if (boost > SYNC_MAX_BOOST_PWM) {
      boost = SYNC_MAX_BOOST_PWM;
    }
    targetLeftPwm = syncBasePwm + boost;
  }

  syncLeftPwm = movePwmToward(
      syncLeftPwm,
      targetLeftPwm,
      SYNC_MAX_PWM_STEP);
  syncRightPwm = movePwmToward(
      syncRightPwm,
      targetRightPwm,
      SYNC_MAX_PWM_STEP);

  driveMotors(syncLeftPwm, syncRightPwm);

  if (static_cast<int32_t>(now - syncNextReportMs) >= 0) {
    syncNextReportMs = now + SYNC_REPORT_INTERVAL_MS;
    console.print("FDS t=");
    console.print(now - syncStartMs);
    console.print(" ms; L=");
    console.print(physicalLeft);
    console.print("/");
    console.print(leftTargetPulses);
    console.print("; R=");
    console.print(physicalRight);
    console.print("/");
    console.print(rightTargetPulses);
    console.print("; error=");
    console.print(errorEquivalent, 2);
    console.print("; PWM=");
    console.print(syncLeftPwm);
    console.print("/");
    console.println(syncRightPwm);
  }
}

// ============================================================
// Stage 7B V3 自适应脉冲逼近
// ============================================================

int32_t approachAllowedOvershootPulses(int32_t target) {
  const int32_t allowed = static_cast<int32_t>(ceilf(
      static_cast<float>(target) * FDS_MAX_FINAL_ERROR_PERCENT / 100.0f));
  return allowed > 1 ? allowed : 1;
}

unsigned long calculateApproachBurstMs(
    int32_t remainingPulses,
    float estimatedRate,
    uint8_t noProgressCycles) {

  int32_t usableRemaining = remainingPulses - APPROACH_DEADBAND_PULSES;
  if (usableRemaining < 1) {
    usableRemaining = 1;
  }

  float desiredIncrement =
      static_cast<float>(usableRemaining) *
      APPROACH_DESIRED_REMAINING_FRACTION;
  if (desiredIncrement < 4.0f) {
    desiredIncrement = 4.0f;
  }

  float safeRate = estimatedRate;
  if (safeRate < 0.10f) {
    safeRate = 0.10f;
  }

  unsigned long burstMs = static_cast<unsigned long>(lroundf(
      desiredIncrement / safeRate));

  // 如果上一小步没有产生进度，下一步逐级增加通电时间；仍受 45 ms 上限保护。
  burstMs += static_cast<unsigned long>(noProgressCycles) * 5UL;

  if (burstMs < APPROACH_MIN_BURST_MS) {
    burstMs = APPROACH_MIN_BURST_MS;
  }
  if (burstMs > APPROACH_MAX_BURST_MS) {
    burstMs = APPROACH_MAX_BURST_MS;
  }
  return burstMs;
}

void updateApproachRate(
    float& estimatedRate,
    int32_t pulseDelta,
    unsigned long burstMs) {

  if (pulseDelta <= 0 || burstMs == 0) {
    return;
  }

  float measuredRate =
      static_cast<float>(pulseDelta) / static_cast<float>(burstMs);
  if (measuredRate < 0.05f) {
    measuredRate = 0.05f;
  }
  if (measuredRate > 4.0f) {
    measuredRate = 4.0f;
  }

  estimatedRate =
      (1.0f - APPROACH_RATE_EWMA_NEW_WEIGHT) * estimatedRate +
      APPROACH_RATE_EWMA_NEW_WEIGHT * measuredRate;
}

bool prepareApproachWheel(
    const char* wheelName,
    int32_t currentCount,
    int32_t targetCount,
    ApproachWheelState& state,
    bool& targetDone,
    void (*stopOneMotor)(int),
    const char* reverseReason,
    const char* overshootReason) {

  if (state == ApproachWheelState::DONE) {
    return true;
  }

  if (currentCount < -APPROACH_REVERSE_LIMIT_PULSES) {
    finishMotion(reverseReason, true);
    return false;
  }

  const int32_t overshoot = currentCount - targetCount;
  if (overshoot > approachAllowedOvershootPulses(targetCount)) {
    finishMotion(overshootReason, true);
    return false;
  }

  const int32_t remaining = targetCount - currentCount;
  if (remaining <= APPROACH_DEADBAND_PULSES) {
    stopOneMotor(0);
    state = ApproachWheelState::DONE;
    targetDone = true;

    console.println();
    console.println("[Pulse approach wheel complete]");
    console.print("wheel           : ");
    console.println(wheelName);
    console.print("final approach  : ");
    console.print(currentCount);
    console.print(" / ");
    console.print(targetCount);
    console.println(" pulses");
  }

  return true;
}

bool startNextApproachCycle(
    int32_t physicalLeft,
    int32_t physicalRight,
    unsigned long now) {

  // V3 的 fds 10 实测证明：到第 60 cycle 时，轮子可能已经符合正式
  // 10% / 5% 精度门槛，只是没有进入固定 6-pulse 死区。先按正式门槛
  // 验收，避免把合格结果误判为 cycle limit。
  if (approachCycleCount >= APPROACH_NORMAL_CYCLES &&
      fdsFinalAccuracyPassed(
          leftTargetPulses,
          rightTargetPulses,
          physicalLeft,
          physicalRight)) {
    console.println();
    console.println("[Formal FDS accuracy reached]");
    console.print("cycle           : ");
    console.println(approachCycleCount);
    console.println("decision        : finish without chasing the fixed 6-pulse deadband");
    finishMotion("TARGET_COMPLETE", true);
    return false;
  }

  if (!prepareApproachWheel(
          "left",
          physicalLeft,
          leftTargetPulses,
          leftApproachState,
          leftTargetDone,
          setLeftMotor,
          "APPROACH_REVERSE_LEFT",
          "APPROACH_OVERSHOOT_LEFT")) {
    return false;
  }

  if (!prepareApproachWheel(
          "right",
          physicalRight,
          rightTargetPulses,
          rightApproachState,
          rightTargetDone,
          setRightMotor,
          "APPROACH_REVERSE_RIGHT",
          "APPROACH_OVERSHOOT_RIGHT")) {
    return false;
  }

  if (leftTargetDone && rightTargetDone) {
    finishMotion("TARGET_COMPLETE", true);
    return false;
  }

  if (approachCycleCount >= activeApproachMaxCycles) {
    finishMotion("APPROACH_CYCLE_LIMIT", true);
    return false;
  }
  ++approachCycleCount;

  bool driveLeftThisCycle = !leftTargetDone;
  bool driveRightThisCycle = !rightTargetDone;
  bool catchUpMode = false;
  float normalizedProgressDifferencePercent = 0.0f;

  // 60 个常规 cycle 后，如果还没有同时满足精度门槛，冻结领先轮，只让
  // 落后轮追赶。比较的是各自 target 的归一化进度，不直接比较原始 pulses。
  if (approachCycleCount > APPROACH_NORMAL_CYCLES &&
      !leftTargetDone && !rightTargetDone) {
    accuracyRecoveryEntered = true;
    const float leftProgress =
        static_cast<float>(physicalLeft) /
        static_cast<float>(leftTargetPulses);
    const float rightProgress =
        static_cast<float>(physicalRight) /
        static_cast<float>(rightTargetPulses);
    normalizedProgressDifferencePercent =
        100.0f * (leftProgress - rightProgress);

    if (normalizedProgressDifferencePercent >
        APPROACH_CATCH_UP_THRESHOLD_PERCENT) {
      driveLeftThisCycle = false;
      catchUpMode = true;
      leftLeadingWheelHeld = true;
      setLeftMotor(0);
      leftApproachState = ApproachWheelState::READY;
    } else if (normalizedProgressDifferencePercent <
               -APPROACH_CATCH_UP_THRESHOLD_PERCENT) {
      driveRightThisCycle = false;
      catchUpMode = true;
      rightLeadingWheelHeld = true;
      setRightMotor(0);
      rightApproachState = ApproachWheelState::READY;
    }
  }

  if (driveLeftThisCycle) {
    const int32_t remaining = leftTargetPulses - physicalLeft;
    leftApproachBurstMs = calculateApproachBurstMs(
        remaining,
        leftApproachRate,
        leftApproachNoProgress);
    leftApproachStartCount = physicalLeft;
    leftApproachDeadlineMs = now + leftApproachBurstMs;
    leftApproachState = ApproachWheelState::DRIVING;
    setLeftMotor(APPROACH_PWM);
  }

  if (driveRightThisCycle) {
    const int32_t remaining = rightTargetPulses - physicalRight;
    rightApproachBurstMs = calculateApproachBurstMs(
        remaining,
        rightApproachRate,
        rightApproachNoProgress);
    rightApproachStartCount = physicalRight;
    rightApproachDeadlineMs = now + rightApproachBurstMs;
    rightApproachState = ApproachWheelState::DRIVING;
    setRightMotor(APPROACH_PWM);
  }

  console.println();
  console.println("[Pulse approach cycle started]");
  console.print("cycle           : ");
  console.println(approachCycleCount);
  console.print("phase           : ");
  console.println(
      approachCycleCount <= APPROACH_NORMAL_CYCLES
          ? "normal approach"
          : "accuracy recovery");
  if (approachCycleCount > APPROACH_NORMAL_CYCLES) {
    accuracyRecoveryEntered = true;
    if (approachCycleCount == APPROACH_NORMAL_CYCLES + 1) {
      console.println("phase meaning   : fine-distance correction; NOT an ESP32 reset");
    }
    console.print("progress diff   : ");
    console.print(normalizedProgressDifferencePercent, 2);
    console.println("% (left - right)");
    console.print("catch-up mode   : ");
    console.println(catchUpMode ? "active" : "not needed");
  }
  console.print("left plan       : ");
  if (leftTargetDone) {
    console.println("done");
  } else if (!driveLeftThisCycle) {
    console.println("held; right wheel is catching up");
  } else {
    console.print(physicalLeft);
    console.print("/");
    console.print(leftTargetPulses);
    console.print("; PWM 80 for ");
    console.print(leftApproachBurstMs);
    console.println(" ms");
  }
  console.print("right plan      : ");
  if (rightTargetDone) {
    console.println("done");
  } else if (!driveRightThisCycle) {
    console.println("held; left wheel is catching up");
  } else {
    console.print(physicalRight);
    console.print("/");
    console.print(rightTargetPulses);
    console.print("; PWM 80 for ");
    console.print(rightApproachBurstMs);
    console.println(" ms");
  }
  return true;
}

bool updateOneApproachWheel(
    const char* wheelName,
    ApproachWheelState& state,
    unsigned long& deadlineMs,
    unsigned long burstMs,
    int32_t startCount,
    int32_t currentCount,
    float& estimatedRate,
    uint8_t& noProgressCycles,
    void (*startBrake)(),
    void (*stopOneMotor)(int),
    const char* stallReason) {

  const unsigned long now = millis();

  if (state == ApproachWheelState::DRIVING &&
      static_cast<int32_t>(now - deadlineMs) >= 0) {
    startBrake();
    state = ApproachWheelState::BRAKING;
    deadlineMs = now + TARGET_BRAKE_HOLD_MS;
    return true;
  }

  if (state == ApproachWheelState::BRAKING &&
      static_cast<int32_t>(now - deadlineMs) >= 0) {
    stopOneMotor(0);
    state = ApproachWheelState::SETTLING;
    deadlineMs = now + APPROACH_SETTLE_MS;
    return true;
  }

  if (state == ApproachWheelState::SETTLING &&
      static_cast<int32_t>(now - deadlineMs) >= 0) {
    const int32_t pulseDelta = currentCount - startCount;

    if (pulseDelta > 0) {
      noProgressCycles = 0;
      updateApproachRate(estimatedRate, pulseDelta, burstMs);
    } else {
      ++noProgressCycles;
      if (noProgressCycles >= APPROACH_MAX_NO_PROGRESS_CYCLES) {
        finishMotion(stallReason, true);
        return false;
      }
    }

    console.println();
    console.println("[Pulse approach cycle settled]");
    console.print("wheel           : ");
    console.println(wheelName);
    console.print("burst result    : +");
    console.print(pulseDelta);
    console.print(" pulses in ");
    console.print(burstMs);
    console.println(" ms");
    console.print("settled count   : ");
    console.println(currentCount);
    console.print("estimated rate  : ");
    console.print(estimatedRate, 3);
    console.println(" pulses/ms");

    state = ApproachWheelState::READY;
  }

  return true;
}

void monitorPulseApproachMotion() {
  if (!moving || motionMode != MotionMode::TARGET ||
      !targetPulseApproachEnabled) {
    return;
  }

  int32_t physicalLeft;
  int32_t physicalRight;
  readPhysicalEncoderCounts(physicalLeft, physicalRight);

  if (!updateOneApproachWheel(
          "left",
          leftApproachState,
          leftApproachDeadlineMs,
          leftApproachBurstMs,
          leftApproachStartCount,
          physicalLeft,
          leftApproachRate,
          leftApproachNoProgress,
          startLeftDynamicBrake,
          setLeftMotor,
          "APPROACH_STALL_LEFT")) {
    return;
  }

  if (!moving) {
    return;
  }

  if (!updateOneApproachWheel(
          "right",
          rightApproachState,
          rightApproachDeadlineMs,
          rightApproachBurstMs,
          rightApproachStartCount,
          physicalRight,
          rightApproachRate,
          rightApproachNoProgress,
          startRightDynamicBrake,
          setRightMotor,
          "APPROACH_STALL_RIGHT")) {
    return;
  }

  if (!moving) {
    return;
  }

  const bool leftReady =
      leftApproachState == ApproachWheelState::READY ||
      leftApproachState == ApproachWheelState::DONE;
  const bool rightReady =
      rightApproachState == ApproachWheelState::READY ||
      rightApproachState == ApproachWheelState::DONE;

  if (leftReady && rightReady) {
    readPhysicalEncoderCounts(physicalLeft, physicalRight);
    startNextApproachCycle(physicalLeft, physicalRight, millis());
    return;
  }

  if (millis() - targetStartMs >= activeTargetTimeoutMs) {
    finishMotion("TARGET_TIMEOUT", true);
  }
}

void monitorTargetMotion() {
  if (!moving || motionMode != MotionMode::TARGET) {
    return;
  }

  if (targetPulseApproachEnabled) {
    monitorPulseApproachMotion();
    return;
  }

  const unsigned long now = millis();

  if (leftBrakeActive &&
      static_cast<int32_t>(now - leftBrakeReleaseMs) >= 0) {
    setLeftMotor(0);
    leftBrakeActive = false;
    console.println("left brake      : released to output off");
  }

  if (rightBrakeActive &&
      static_cast<int32_t>(now - rightBrakeReleaseMs) >= 0) {
    setRightMotor(0);
    rightBrakeActive = false;
    console.println("right brake     : released to output off");
  }

  int32_t physicalLeft;
  int32_t physicalRight;
  readPhysicalEncoderCounts(physicalLeft, physicalRight);

  // 先检查异常脉冲，再检查是否到达目标，避免假脉冲被误判为完成。
  if (leftTargetActive && !leftTargetDone &&
      pulseCountIsImplausible(physicalLeft, leftTargetPulses)) {
    finishMotion("ENCODER_SPIKE_LEFT", true);
    return;
  }

  if (rightTargetActive && !rightTargetDone &&
      pulseCountIsImplausible(physicalRight, rightTargetPulses)) {
    finishMotion("ENCODER_SPIKE_RIGHT", true);
    return;
  }

  if (leftTargetActive && !leftTargetDone) {
    if (physicalLeft >= leftTargetPulses) {
      leftCountAtBrake = physicalLeft;

      if (targetSyncEnabled) {
        startLeftDynamicBrake();
        leftBrakeActive = true;
        leftBrakeReleaseMs = now + TARGET_BRAKE_HOLD_MS;
      } else {
        setLeftMotor(0);
      }

      leftTargetDone = true;
      console.println();
      console.println("[Wheel target reached]");
      console.println("wheel           : left");
      console.print(targetSyncEnabled
          ? "count at brake  : "
          : "count at stop   : ");
      console.print(physicalLeft);
      console.print(" / ");
      console.println(leftTargetPulses);

      if (targetSyncEnabled) {
        console.print("brake hold      : ");
        console.print(TARGET_BRAKE_HOLD_MS);
        console.println(" ms");
      }

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
      rightCountAtBrake = physicalRight;

      if (targetSyncEnabled) {
        startRightDynamicBrake();
        rightBrakeActive = true;
        rightBrakeReleaseMs = now + TARGET_BRAKE_HOLD_MS;
      } else {
        setRightMotor(0);
      }

      rightTargetDone = true;
      console.println();
      console.println("[Wheel target reached]");
      console.println("wheel           : right");
      console.print(targetSyncEnabled
          ? "count at brake  : "
          : "count at stop   : ");
      console.print(physicalRight);
      console.print(" / ");
      console.println(rightTargetPulses);

      if (targetSyncEnabled) {
        console.print("brake hold      : ");
        console.print(TARGET_BRAKE_HOLD_MS);
        console.println(" ms");
      }

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

  updateTargetSynchronization(physicalLeft, physicalRight, now);

  if (leftTargetDone && rightTargetDone &&
      !leftBrakeActive && !rightBrakeActive) {
    finishMotion("TARGET_COMPLETE", true);
    return;
  }

  if (now - targetStartMs >= activeTargetTimeoutMs) {
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
    armedCommandSourceValid = false;
  }

  String reasonCode = String(reason);
  reasonCode.toLowerCase();
  String displayInput = line;
  displayInput.toLowerCase();

  console.println();
  console.println("[Command rejected]");
  console.print("reason code     : ");
  console.println(reasonCode);
  console.print("input           : ");
  console.println(displayInput);
  console.println("next            : send 'help' to view the command guide");
}

void processCommand(String line, CommandSource source) {
  line.trim();

  if (line.length() == 0) {
    return;
  }

  String receivedLine = line;
  line.toUpperCase();
  currentCommandSource = source;

  // TCP客户端每100 ms左右发送PING。它只更新链路生命状态，
  // 不改变ARM、编码器或运动状态，也不刷屏。
  if (line == "PING") {
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

  // STOP 始终具有最高优先级。
  if (line == "STOP") {
    finishMotion("USER_STOP", true);
    return;
  }

  if (line == "ARM") {
    if (moving) {
      finishMotion("ARM_DURING_MOTION", true);
      console.println("Error: 'arm' cannot be sent during motion. Send it again after stopping.");
      return;
    }

    stopMotorOutputsImmediately();
    clearMotionState();
    armed = true;
    armedCommandSource = source;
    armedCommandSourceValid = true;
    console.println();
    console.println("[Ready]");
    console.println("safety          : armed for one limited motion");
    console.println("next            : send one motion command");
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
      console.println("Error: learned signs cannot be cleared during motion.");
      return;
    }

    stopMotorOutputsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    leftEncoderForwardSign = 0;
    rightEncoderForwardSign = 0;
    clearMotionState();
    console.println();
    console.println("[Encoder signs cleared]");
    console.println("safety          : disarmed");
    console.println("next            : repeat 'arm' + 'check left', then 'arm' + 'check right'");
    return;
  }

  if (line == "ZERO") {
    if (moving) {
      console.println("Error: encoder counts cannot be reset during motion.");
      return;
    }

    resetEncoderCounts();
    console.println("Encoder counts were reset to zero.");
    return;
  }

  char commandBuffer[12] = {0};
  char argument1[24] = {0};
  char argument2[24] = {0};
  char extraBuffer[12] = {0};

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
      console.println("Expected format : check left  OR  check right");
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
      console.println("Expected wheel  : left or right");
    }
    return;
  }

  if (command == "SYNC") {
    if (fieldCount != 3) {
      rejectCommand("INVALID_SYNC_FORMAT", line);
      console.println("Expected format : sync 80 1000");
      return;
    }

    long pwmLong;
    long durationLong;
    if (!parseLongStrict(argument1, pwmLong) ||
        !parseLongStrict(argument2, durationLong) ||
        pwmLong < 0 || durationLong < 0) {
      rejectCommand("INVALID_SYNC_NUMBER", line);
      return;
    }

    startSyncMotion(
        static_cast<int>(pwmLong),
        static_cast<unsigned long>(durationLong));
    return;
  }

  if (isTimedMotionCommand(command)) {
    if (fieldCount != 3) {
      rejectCommand("INVALID_TIMED_FORMAT", line);
      console.println("Expected format : f 160 1000");
      return;
    }

    long pwmLong;
    long durationLong;

    if (!parseLongStrict(argument1, pwmLong) ||
        !parseLongStrict(argument2, durationLong) ||
        pwmLong < 0 || durationLong < 0) {
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
      console.println("Expected format : testl 100");
      return;
    }

    long targetLong;
    if (!parseLongStrict(argument1, targetLong) ||
        targetLong < MIN_TEST_PULSES ||
        targetLong > MAX_TEST_PULSES) {
      rejectCommand("INVALID_TEST_TARGET", line);
      console.print("Allowed pulses  : ");
      console.print(MIN_TEST_PULSES);
      console.print(" to ");
      console.println(MAX_TEST_PULSES);
      return;
    }

    if (command == "TESTL") {
      startTargetMotion(command, static_cast<int32_t>(targetLong), 0);
    } else {
      startTargetMotion(command, 0, static_cast<int32_t>(targetLong));
    }
    return;
  }

  if (command == "FD" || command == "FDS") {
    if (fieldCount != 2) {
      rejectCommand(
          command == "FDS"
              ? "INVALID_FDS_FORMAT"
              : "INVALID_FD_FORMAT",
          line);
      console.println(command == "FDS"
          ? "Expected format : fds 20"
          : "Expected format : fd 20");
      return;
    }

    float distanceCm;
    if (!parseFloatStrict(argument1, distanceCm) ||
        distanceCm < MIN_DISTANCE_CM ||
        distanceCm > MAX_DISTANCE_CM) {
      rejectCommand("INVALID_DISTANCE", line);
      console.print("Allowed distance: ");
      console.print(MIN_DISTANCE_CM, 1);
      console.print(" to ");
      console.print(MAX_DISTANCE_CM, 1);
      console.println(" cm");
      return;
    }

    const int32_t calculatedLeftTarget = static_cast<int32_t>(lroundf(
        distanceCm / WHEEL_CIRCUMFERENCE_CM * LEFT_PULSES_PER_REV));

    const int32_t calculatedRightTarget = static_cast<int32_t>(lroundf(
        distanceCm / WHEEL_CIRCUMFERENCE_CM * RIGHT_PULSES_PER_REV));

    console.println();
    console.println("[Distance plan]");
    console.print("controller      : ");
    console.println(command == "FDS"
        ? "Stage 7B V5 adaptive pulse approach with dynamic limits"
        : "legacy fixed-PWM distance");
    console.print("distance        : ");
    console.print(distanceCm, 2);
    console.println(" cm");
    console.print("left target     : ");
    console.print(calculatedLeftTarget);
    console.println(" pulses");
    console.print("right target    : ");
    console.print(calculatedRightTarget);
    console.println(" pulses");

    startTargetMotion(
        command,
        calculatedLeftTarget,
        calculatedRightTarget);
    return;
  }

  rejectCommand("UNKNOWN_COMMAND", line);
}

// ============================================================
// USB / Wi-Fi TCP 共用输入与无线安全
// ============================================================

void disarmForTcpLinkLoss(const char* reason) {
  const bool tcpOwnedMotion =
      moving && activeMotionSource == CommandSource::TCP;
  const bool tcpOwnedArm =
      armed && armedCommandSourceValid &&
      armedCommandSource == CommandSource::TCP;

  if (tcpOwnedMotion) {
    finishMotion(reason, true);
    return;
  }

  if (tcpOwnedArm) {
    stopMotorOutputsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    clearMotionState();
    console.println();
    console.println("[TCP safety]");
    console.println("result          : Wi-Fi ARM cancelled");
    console.println("safety          : disarmed");
    console.println("reason          : TCP control link was lost before an action");
  }
}

void handleInputLineTooLong(CommandSource source) {
  if (moving) {
    finishMotion(
        source == CommandSource::TCP
            ? "TCP_LINE_TOO_LONG"
            : "SERIAL_LINE_TOO_LONG",
        true);
  } else {
    stopMotorOutputsImmediately();
    armed = false;
    armedCommandSourceValid = false;
    clearMotionState();
  }

  console.println();
  console.println("[Input rejected]");
  console.println("reason          : command line exceeded 95 characters");
  console.println("safety          : disarmed");
}

void readCommandStream(
    Stream& input,
    String& lineBuffer,
    CommandSource source) {

  while (input.available() > 0) {
    const char incoming = static_cast<char>(input.read());

    if (source == CommandSource::TCP) {
      lastTcpHeartbeatMs = millis();
    }

    if (incoming == '\n' || incoming == '\r') {
      if (lineBuffer.length() > 0) {
        processCommand(lineBuffer, source);
        lineBuffer = "";
      }

    } else if (incoming >= 32 && incoming <= 126) {
      if (lineBuffer.length() < INPUT_LINE_MAX_LENGTH) {
        lineBuffer += incoming;
      } else {
        lineBuffer = "";
        handleInputLineTooLong(source);
      }
    }
  }
}

void serviceTcpConnection() {
  // 先处理旧客户端断开，确保由TCP启动的动作立即停止。
  if (tcpClientActive && !tcpClient.connected()) {
    disarmForTcpLinkLoss("TCP_DISCONNECT");
    tcpClient.stop();
    tcpClientActive = false;
    tcpLine = "";
    console.println();
    console.println("[TCP client disconnected]");
    console.println("safety          : disarmed if TCP owned ARM or motion");
  }

  WiFiClient candidate = tcpServer.available();
  if (candidate) {
    if (tcpClientActive && tcpClient.connected()) {
      candidate.println("BUSY: Atlas already has one TCP control client.");
      candidate.stop();
    } else {
      tcpClient = candidate;
      tcpClientActive = true;
      tcpClient.setNoDelay(true);
      tcpLine = "";
      lastTcpHeartbeatMs = millis();

      console.println();
      console.println("========================================");
      console.println("[TCP client connected]");
      console.print("remote IP       : ");
      console.println(tcpClient.remoteIP());
      console.println("safety          : disarmed until ARM is received");
      console.println("next            : send status, config, or help");
      console.println("========================================");
    }
  }

  if (tcpClientActive && tcpClient.connected()) {
    readCommandStream(tcpClient, tcpLine, CommandSource::TCP);
  }

  if (moving && activeMotionSource == CommandSource::TCP &&
      millis() - lastTcpHeartbeatMs > TCP_HEARTBEAT_TIMEOUT_MS) {
    finishMotion("TCP_HEARTBEAT_TIMEOUT", true);
  }
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
  tcpLine.reserve(96);

  armed = false;
  armedCommandSourceValid = false;
  leftEncoderForwardSign = 0;
  rightEncoderForwardSign = 0;
  clearMotionState();

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

  console.println();
  console.println("========================================");
  console.println("Atlas 7C wireless bridge v1 is ready");
  console.println("motor baseline  : Stage 7B V5 unchanged");
  console.println("motors          : stopped");
  console.println("safety          : disarmed");
  console.println("encoder mode    : A rising edge, 1x count");
  console.println("left mapping    : gpio 25/26");
  console.println("right mapping   : gpio 18/19");
  console.println("encoder signs   : not checked after this restart");
  console.print("wifi AP         : ");
  console.println(accessPointStarted ? WIFI_AP_SSID : "START FAILED");
  console.print("wifi IP         : ");
  console.println(WiFi.softAPIP());
  console.print("tcp port        : ");
  console.println(WIFI_TCP_PORT);
  console.println("tcp clients     : maximum 1");
  console.print("heartbeat stop  : ");
  console.print(TCP_HEARTBEAT_TIMEOUT_MS);
  console.println(" ms during TCP motion");
  console.println("next            : connect Wi-Fi and send status; keep motor power off");
  console.println("help            : send 'help'");
  console.println("========================================");
}

void loop() {
  serviceTcpConnection();
  readCommandStream(Serial, serialLine, CommandSource::USB_SERIAL);

  if (moving && motionMode == MotionMode::TIMED &&
      static_cast<int32_t>(millis() - timedStopDeadline) >= 0) {
    finishMotion("ACTION_COMPLETE", true);
  }

  monitorSyncMotion();

  if (moving && motionMode == MotionMode::ENCODER_CHECK &&
      static_cast<int32_t>(millis() - timedStopDeadline) >= 0) {
    finishEncoderCheck();
  }

  monitorTargetMotion();
}
