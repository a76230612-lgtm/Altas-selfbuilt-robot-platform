/*
  ==============================================================================
  Atlas 6.0 - Integrated Release Candidate V3.1 FIXED
  Controller: ESP32 DEVKIT V1
  ==============================================================================

  L298N
    ENA -> GPIO13
    IN1 -> GPIO14
    IN2 -> GPIO4
    ENB -> GPIO33
    IN3 -> GPIO32
    IN4 -> GPIO23

  Encoder
    LEFT A  -> GPIO25
    LEFT B  -> GPIO26
    RIGHT A -> GPIO18
    RIGHT B -> GPIO19

  US-100
    TRIG -> GPIO27
    ECHO -> GPIO34

  Servo
    SIGNAL -> GPIO21
    VCC    -> ESP32 5V
    GND    -> GND

  Distance:
    <10 cm      -> BLOCKED
    10 - <15 cm -> CAUTION
    >=15 cm     -> CLEAR

  Scan:
    LEFT 5
    CENTER 90
    RIGHT 175
    CENTER 90
    repeat

  Boot:
    DISARMED
    AUTO OFF
    MODE US_ONLY
    SWEEP ON

  WiFi:
    SSID: ATLAS_6_0
    PASS: atlas6000
    TCP : 8888
  ==============================================================================
*/

#include <Arduino.h>
#include <WiFi.h>
#include <esp_arduino_version.h>

// ==============================================================================
// PINS
// ==============================================================================

static const uint8_t L_EN  = 13;
static const uint8_t L_IN1 = 14;
static const uint8_t L_IN2 = 4;

static const uint8_t R_EN  = 33;
static const uint8_t R_IN1 = 32;
static const uint8_t R_IN2 = 23;

static const uint8_t ENC_L_A = 25;
static const uint8_t ENC_L_B = 26;

static const uint8_t ENC_R_A = 18;
static const uint8_t ENC_R_B = 19;

static const uint8_t US_TRIG = 27;
static const uint8_t US_ECHO = 34;

static const uint8_t SERVO_PIN = 21;

// ==============================================================================
// WIFI
// ==============================================================================

static const char* AP_SSID = "ATLAS_6_0";
static const char* AP_PASS = "atlas6000";
static const uint16_t TCP_PORT = 8888;

WiFiServer server(TCP_PORT);
WiFiClient client;

// ==============================================================================
// PWM COMPATIBILITY
// ==============================================================================

static const uint8_t CH_L = 0;
static const uint8_t CH_R = 1;
static const uint8_t CH_SERVO = 2;

bool pwmAttachCompat(
  uint8_t pin,
  uint8_t channel,
  uint32_t freq,
  uint8_t bits
) {

#if ESP_ARDUINO_VERSION_MAJOR >= 3

  (void)channel;

  return ledcAttach(
    pin,
    freq,
    bits
  );

#else

  double result =
    ledcSetup(
      channel,
      freq,
      bits
    );

  if (result <= 0) {
    return false;
  }

  ledcAttachPin(
    pin,
    channel
  );

  return true;

#endif
}


void pwmWriteCompat(
  uint8_t pin,
  uint8_t channel,
  uint32_t duty
) {

#if ESP_ARDUINO_VERSION_MAJOR >= 3

  (void)channel;

  ledcWrite(
    pin,
    duty
  );

#else

  (void)pin;

  ledcWrite(
    channel,
    duty
  );

#endif
}

// ==============================================================================
// MOTOR
// ==============================================================================

static const uint32_t MOTOR_FREQ = 5000;
static const uint8_t MOTOR_BITS = 8;

static const bool LEFT_INVERTED = true;
static const bool RIGHT_INVERTED = false;

static const int DEFAULT_DRIVE_PWM = 80;
static const int DEFAULT_TURN_PWM = 80;

static const uint32_t TURN_PULSE_MS = 300;

int drivePwm = DEFAULT_DRIVE_PWM;

// ==============================================================================
// ENCODER
// ==============================================================================

volatile long encL = 0;
volatile long encR = 0;

static const float LEFT_PPR = 632.05f;
static const float RIGHT_PPR = 634.17f;
static const float WHEEL_CIRC_CM = 21.40f;


void IRAM_ATTR isrL() {

  bool a =
    digitalRead(
      ENC_L_A
    );

  bool b =
    digitalRead(
      ENC_L_B
    );

  if (a == b) {
    encL++;
  } else {
    encL--;
  }
}


void IRAM_ATTR isrR() {

  bool a =
    digitalRead(
      ENC_R_A
    );

  bool b =
    digitalRead(
      ENC_R_B
    );

  if (a == b) {
    encR++;
  } else {
    encR--;
  }
}

// ==============================================================================
// RANGE STATES
// ==============================================================================

static const uint8_t RG_UNKNOWN = 0;
static const uint8_t RG_BLOCKED = 1;
static const uint8_t RG_CAUTION = 2;
static const uint8_t RG_CLEAR = 3;

static const float BLOCKED_CM = 10.0f;
static const float CAUTION_CM = 15.0f;

float distL = NAN;
float distC = NAN;
float distR = NAN;

uint8_t rangeL = RG_UNKNOWN;
uint8_t rangeC = RG_UNKNOWN;
uint8_t rangeR = RG_UNKNOWN;

uint32_t distLms = 0;
uint32_t distCms = 0;
uint32_t distRms = 0;

static const uint32_t CENTER_STALE_MS = 1200;
static const uint32_t SIDE_STALE_MS = 2200;

// ==============================================================================
// US-100
// ==============================================================================

static const uint32_t ECHO_TIMEOUT_US = 25000UL;

static const uint8_t US_N = 3;
static const uint8_t US_MIN_VALID = 2;

static const uint32_t US_GAP_MS = 35;

// ==============================================================================
// SERVO
// ==============================================================================

static const uint32_t SERVO_FREQ = 50;
static const uint8_t SERVO_BITS = 16;

static const uint32_t SERVO_MAX_DUTY =
  (1UL << SERVO_BITS) - 1UL;

static const uint16_t SERVO_MIN_US = 1000;
static const uint16_t SERVO_MAX_US = 2000;

static const int ANG_LEFT = 5;
static const int ANG_CENTER = 90;
static const int ANG_RIGHT = 175;

static const bool SERVO_REVERSED = false;

static const uint32_t SERVO_SETTLE_MS = 220;

// Scan states
static const uint8_t POS_LEFT = 0;
static const uint8_t POS_CENTER_A = 1;
static const uint8_t POS_RIGHT = 2;
static const uint8_t POS_CENTER_B = 3;

uint8_t scanPos = POS_CENTER_A;

bool sweepOn = true;
bool servoWaiting = false;

uint32_t servoMoveMs = 0;

// ==============================================================================
// CAMERA STATES
// ==============================================================================

static const uint8_t CE_UNKNOWN = 0;
static const uint8_t CE_SAFE = 1;
static const uint8_t CE_EDGE = 2;

static const uint8_t CS_UNKNOWN = 0;
static const uint8_t CS_FREE = 1;
static const uint8_t CS_BLOCKED = 2;

uint8_t camEdge = CE_UNKNOWN;
uint8_t camL = CS_UNKNOWN;
uint8_t camR = CS_UNKNOWN;

uint32_t cameraMs = 0;

static const uint32_t CAMERA_STALE_MS = 1200;

// ==============================================================================
// ROBOT STATES
// ==============================================================================

static const uint8_t US_ONLY = 0;
static const uint8_t FUSION = 1;

static const uint8_t STOPPED = 0;
static const uint8_t FORWARD = 1;
static const uint8_t BACKWARD = 2;
static const uint8_t TURN_LEFT = 3;
static const uint8_t TURN_RIGHT = 4;

uint8_t mode = US_ONLY;
uint8_t motion = STOPPED;

bool armed = false;
bool autoOn = false;

uint32_t turnUntilMs = 0;

int previousTurn = 0;

uint32_t lastNoPathMsgMs = 0;

// ==============================================================================
// NETWORK SAFETY
// ==============================================================================

static const uint32_t HB_TIMEOUT_MS = 350;

uint32_t lastNetMs = 0;

bool hadClient = false;
bool networkControl = false;

// ==============================================================================
// COMMAND BUFFERS
// ==============================================================================

String serialBuf = "";
String netBuf = "";

uint32_t serialLastByteMs = 0;
uint32_t netLastByteMs = 0;

static const uint32_t COMMAND_IDLE_FLUSH_MS = 40;

uint32_t lastStatusMs = 0;

// ==============================================================================
// STATE NAME HELPERS
// ==============================================================================

const char* rangeName(
  uint8_t state
) {

  if (state == RG_BLOCKED) {
    return "BLOCKED";
  }

  if (state == RG_CAUTION) {
    return "CAUTION";
  }

  if (state == RG_CLEAR) {
    return "CLEAR";
  }

  return "UNKNOWN";
}


const char* motionName(
  uint8_t state
) {

  if (state == FORWARD) {
    return "FORWARD";
  }

  if (state == BACKWARD) {
    return "BACKWARD";
  }

  if (state == TURN_LEFT) {
    return "TURN_LEFT";
  }

  if (state == TURN_RIGHT) {
    return "TURN_RIGHT";
  }

  return "STOPPED";
}


const char* modeName() {

  if (mode == FUSION) {
    return "FUSION";
  }

  return "US_ONLY";
}


const char* camEdgeName() {

  if (camEdge == CE_SAFE) {
    return "SAFE";
  }

  if (camEdge == CE_EDGE) {
    return "EDGE";
  }

  return "UNKNOWN";
}


const char* camSideName(
  uint8_t state
) {

  if (state == CS_FREE) {
    return "FREE";
  }

  if (state == CS_BLOCKED) {
    return "BLOCKED";
  }

  return "UNKNOWN";
}

// ==============================================================================
// OUTPUT
// ==============================================================================

void sendLine(
  const String& text
) {

  Serial.println(
    text
  );

  if (
    client.connected()
  ) {

    client.println(
      text
    );
  }
}

// ==============================================================================
// MOTOR CONTROL
// ==============================================================================

void oneMotor(
  uint8_t en,
  uint8_t channel,
  uint8_t in1,
  uint8_t in2,
  int value,
  bool inverted
) {

  value =
    constrain(
      value,
      -255,
      255
    );

  if (inverted) {
    value = -value;
  }

  if (value == 0) {

    digitalWrite(
      in1,
      LOW
    );

    digitalWrite(
      in2,
      LOW
    );

    pwmWriteCompat(
      en,
      channel,
      0
    );

    return;
  }

  bool forward =
    value > 0;

  int pwm =
    abs(value);

  digitalWrite(
    in1,
    forward ? HIGH : LOW
  );

  digitalWrite(
    in2,
    forward ? LOW : HIGH
  );

  pwmWriteCompat(
    en,
    channel,
    pwm
  );
}


void drive(
  int leftValue,
  int rightValue
) {

  oneMotor(
    L_EN,
    CH_L,
    L_IN1,
    L_IN2,
    leftValue,
    LEFT_INVERTED
  );

  oneMotor(
    R_EN,
    CH_R,
    R_IN1,
    R_IN2,
    rightValue,
    RIGHT_INVERTED
  );
}


void stopRobot(
  const char* reason
) {

  drive(
    0,
    0
  );

  motion =
    STOPPED;

  turnUntilMs =
    0;

  if (
    reason != nullptr
  ) {

    String output =
      "MOTION,STOP,REASON,";

    output +=
      reason;

    sendLine(
      output
    );
  }
}


void invalidateRangesAfterTurn() {

  distLms = 0;
  distCms = 0;
  distRms = 0;

  rangeL = RG_UNKNOWN;
  rangeC = RG_UNKNOWN;
  rangeR = RG_UNKNOWN;

  distL = NAN;
  distC = NAN;
  distR = NAN;
}


void startLeftTurn() {

  if (!armed) {
    return;
  }

  drive(
    -DEFAULT_TURN_PWM,
    DEFAULT_TURN_PWM
  );

  motion =
    TURN_LEFT;

  turnUntilMs =
    millis() +
    TURN_PULSE_MS;

  previousTurn =
    -1;

  sendLine(
    "AUTO,ACTION,TURN_LEFT"
  );
}


void startRightTurn() {

  if (!armed) {
    return;
  }

  drive(
    DEFAULT_TURN_PWM,
    -DEFAULT_TURN_PWM
  );

  motion =
    TURN_RIGHT;

  turnUntilMs =
    millis() +
    TURN_PULSE_MS;

  previousTurn =
    1;

  sendLine(
    "AUTO,ACTION,TURN_RIGHT"
  );
}

// ==============================================================================
// SERVO
// ==============================================================================

uint16_t angleToPulse(
  int logicalAngle
) {

  logicalAngle =
    constrain(
      logicalAngle,
      0,
      180
    );

  int physicalAngle =
    logicalAngle;

  if (SERVO_REVERSED) {

    physicalAngle =
      180 -
      logicalAngle;
  }

  return (uint16_t)map(
    physicalAngle,
    0,
    180,
    SERVO_MIN_US,
    SERVO_MAX_US
  );
}


uint32_t pulseToDuty(
  uint16_t pulseUs
) {

  const uint32_t periodUs =
    1000000UL /
    SERVO_FREQ;

  return (uint32_t)(
    (uint64_t)pulseUs *
    SERVO_MAX_DUTY /
    periodUs
  );
}


void servoAngle(
  int logicalAngle
) {

  uint16_t pulseUs =
    angleToPulse(
      logicalAngle
    );

  uint32_t duty =
    pulseToDuty(
      pulseUs
    );

  pwmWriteCompat(
    SERVO_PIN,
    CH_SERVO,
    duty
  );

  servoWaiting =
    true;

  servoMoveMs =
    millis();
}


int scanAngle(
  uint8_t position
) {

  if (
    position ==
    POS_LEFT
  ) {

    return ANG_LEFT;
  }

  if (
    position ==
    POS_RIGHT
  ) {

    return ANG_RIGHT;
  }

  return ANG_CENTER;
}


const char* scanName(
  uint8_t position
) {

  if (
    position ==
    POS_LEFT
  ) {

    return "LEFT";
  }

  if (
    position ==
    POS_RIGHT
  ) {

    return "RIGHT";
  }

  return "CENTER";
}


void nextScan() {

  if (
    scanPos ==
    POS_LEFT
  ) {

    scanPos =
      POS_CENTER_A;

  } else if (
    scanPos ==
    POS_CENTER_A
  ) {

    scanPos =
      POS_RIGHT;

  } else if (
    scanPos ==
    POS_RIGHT
  ) {

    scanPos =
      POS_CENTER_B;

  } else {

    scanPos =
      POS_LEFT;
  }

  servoAngle(
    scanAngle(
      scanPos
    )
  );
}

// ==============================================================================
// US-100
// ==============================================================================

float readUsOnce() {

  digitalWrite(
    US_TRIG,
    LOW
  );

  delayMicroseconds(
    3
  );

  digitalWrite(
    US_TRIG,
    HIGH
  );

  delayMicroseconds(
    10
  );

  digitalWrite(
    US_TRIG,
    LOW
  );

  uint32_t duration =
    pulseIn(
      US_ECHO,
      HIGH,
      ECHO_TIMEOUT_US
    );

  if (
    duration ==
    0
  ) {

    return NAN;
  }

  float cm =
    duration *
    0.0343f /
    2.0f;

  if (
    cm < 2.0f ||
    cm > 400.0f
  ) {

    return NAN;
  }

  return cm;
}


void sortSmall(
  float* values,
  uint8_t count
) {

  for (
    uint8_t i = 0;
    i < count;
    i++
  ) {

    for (
      uint8_t j = i + 1;
      j < count;
      j++
    ) {

      if (
        values[j] <
        values[i]
      ) {

        float temporary =
          values[i];

        values[i] =
          values[j];

        values[j] =
          temporary;
      }
    }
  }
}


float readUsMedian() {

  float values[US_N];

  uint8_t validCount =
    0;

  for (
    uint8_t i = 0;
    i < US_N;
    i++
  ) {

    float cm =
      readUsOnce();

    if (
      !isnan(cm)
    ) {

      values[
        validCount
      ] = cm;

      validCount++;
    }

    if (
      i + 1 <
      US_N
    ) {

      delay(
        US_GAP_MS
      );
    }
  }

  if (
    validCount <
    US_MIN_VALID
  ) {

    return NAN;
  }

  sortSmall(
    values,
    validCount
  );

  if (
    validCount %
    2
  ) {

    return values[
      validCount /
      2
    ];
  }

  float lower =
    values[
      validCount /
      2 -
      1
    ];

  float upper =
    values[
      validCount /
      2
    ];

  return (
    lower +
    upper
  ) / 2.0f;
}


uint8_t classifyRange(
  float cm
) {

  if (
    isnan(cm)
  ) {

    return RG_UNKNOWN;
  }

  if (
    cm <
    BLOCKED_CM
  ) {

    return RG_BLOCKED;
  }

  if (
    cm <
    CAUTION_CM
  ) {

    return RG_CAUTION;
  }

  return RG_CLEAR;
}


void storeScan() {

  float cm =
    readUsMedian();

  uint8_t state =
    classifyRange(
      cm
    );

  uint32_t now =
    millis();

  if (
    scanPos ==
    POS_LEFT
  ) {

    distL = cm;
    rangeL = state;
    distLms = now;

  } else if (
    scanPos ==
    POS_RIGHT
  ) {

    distR = cm;
    rangeR = state;
    distRms = now;

  } else {

    distC = cm;
    rangeC = state;
    distCms = now;
  }

  String output =
    "SCAN,";

  output +=
    scanName(
      scanPos
    );

  output +=
    ",";

  if (
    isnan(cm)
  ) {

    output +=
      "INVALID,UNKNOWN";

  } else {

    output +=
      String(
        cm,
        1
      );

    output +=
      ",CM,";

    output +=
      rangeName(
        state
      );
  }

  sendLine(
    output
  );
}


void serviceSweep() {

  if (
    !sweepOn
  ) {

    return;
  }

  if (
    !servoWaiting
  ) {

    servoAngle(
      scanAngle(
        scanPos
      )
    );

    return;
  }

  if (
    millis() -
    servoMoveMs <
    SERVO_SETTLE_MS
  ) {

    return;
  }

  servoWaiting =
    false;

  storeScan();

  nextScan();
}

// ==============================================================================
// DATA FRESHNESS
// ==============================================================================

bool fresh(
  uint32_t timestamp,
  uint32_t maxAge
) {

  if (
    timestamp ==
    0
  ) {

    return false;
  }

  return (
    millis() -
    timestamp <=
    maxAge
  );
}


bool cameraFresh() {

  return fresh(
    cameraMs,
    CAMERA_STALE_MS
  );
}


bool centerFresh() {

  return fresh(
    distCms,
    CENTER_STALE_MS
  );
}


bool leftFresh() {

  return fresh(
    distLms,
    SIDE_STALE_MS
  );
}


bool rightFresh() {

  return fresh(
    distRms,
    SIDE_STALE_MS
  );
}

// ==============================================================================
// SENSOR FUSION
// ==============================================================================

bool cameraGate() {

  if (
    mode ==
    US_ONLY
  ) {

    return true;
  }

  if (
    !cameraFresh()
  ) {

    return false;
  }

  return (
    camEdge ==
    CE_SAFE
  );
}


int chooseTurn() {

  bool leftOK =
    leftFresh() &&
    rangeL ==
    RG_CLEAR;

  bool rightOK =
    rightFresh() &&
    rangeR ==
    RG_CLEAR;

  if (
    !leftOK &&
    !rightOK
  ) {

    return 0;
  }

  if (
    leftOK &&
    !rightOK
  ) {

    return -1;
  }

  if (
    !leftOK &&
    rightOK
  ) {

    return 1;
  }

  float leftScore =
    0.0f;

  float rightScore =
    0.0f;

  if (
    !isnan(
      distL
    )
  ) {

    leftScore =
      distL;
  }

  if (
    !isnan(
      distR
    )
  ) {

    rightScore =
      distR;
  }

  if (
    mode ==
    FUSION &&
    cameraFresh()
  ) {

    if (
      camL ==
      CS_BLOCKED
    ) {

      leftScore -=
        20.0f;

    } else if (
      camL ==
      CS_FREE
    ) {

      leftScore +=
        5.0f;
    }

    if (
      camR ==
      CS_BLOCKED
    ) {

      rightScore -=
        20.0f;

    } else if (
      camR ==
      CS_FREE
    ) {

      rightScore +=
        5.0f;
    }
  }

  float difference =
    leftScore -
    rightScore;

  if (
    difference >=
    5.0f
  ) {

    return -1;
  }

  if (
    difference <=
    -5.0f
  ) {

    return 1;
  }

  if (
    previousTurn !=
    0
  ) {

    return previousTurn;
  }

  return -1;
}

// ==============================================================================
// AUTO NAVIGATION
// ==============================================================================

void serviceTurn() {

  if (
    turnUntilMs ==
    0
  ) {

    return;
  }

  if (
    (int32_t)(
      millis() -
      turnUntilMs
    ) >= 0
  ) {

    stopRobot(
      nullptr
    );

    invalidateRangesAfterTurn();

    scanPos =
      POS_CENTER_A;

    servoWaiting =
      false;
  }
}


void serviceAuto() {

  if (
    !armed ||
    !autoOn
  ) {

    return;
  }

  if (
    turnUntilMs !=
    0
  ) {

    return;
  }

  if (
    !cameraGate()
  ) {

    if (
      motion !=
      STOPPED
    ) {

      stopRobot(
        "CAMERA_GATE"
      );
    }

    return;
  }

  if (
    !centerFresh() ||
    rangeC ==
    RG_UNKNOWN
  ) {

    if (
      motion !=
      STOPPED
    ) {

      stopRobot(
        "CENTER_UNKNOWN_OR_STALE"
      );
    }

    return;
  }

  if (
    rangeC ==
    RG_CLEAR
  ) {

    if (
      motion !=
      FORWARD
    ) {

      drive(
        drivePwm,
        drivePwm
      );

      motion =
        FORWARD;

      sendLine(
        "AUTO,ACTION,FORWARD"
      );
    }

    return;
  }

  // CAUTION / BLOCKED both stop first.
  if (
    motion !=
    STOPPED
  ) {

    if (
      rangeC ==
      RG_BLOCKED
    ) {

      stopRobot(
        "CENTER_BLOCKED"
      );

    } else {

      stopRobot(
        "CENTER_CAUTION"
      );
    }
  }

  int direction =
    chooseTurn();

  if (
    direction <
    0
  ) {

    startLeftTurn();

  } else if (
    direction >
    0
  ) {

    startRightTurn();

  } else {

    if (
      millis() -
      lastNoPathMsgMs >
      800
    ) {

      lastNoPathMsgMs =
        millis();

      sendLine(
        "AUTO,ACTION,NO_SAFE_PATH"
      );
    }
  }
}

// ==============================================================================
// STATUS
// ==============================================================================

void sendStatus() {

  long leftCount;
  long rightCount;

  noInterrupts();

  leftCount =
    encL;

  rightCount =
    encR;

  interrupts();

  String output =
    "STATUS,";

  if (armed) {

    output +=
      "ARMED";

  } else {

    output +=
      "DISARMED";
  }

  output +=
    ",AUTO,";

  if (autoOn) {

    output +=
      "ON";

  } else {

    output +=
      "OFF";
  }

  output +=
    ",MODE,";

  output +=
    modeName();

  output +=
    ",MOTION,";

  output +=
    motionName(
      motion
    );

  output +=
    ",L,";

  if (
    isnan(
      distL
    )
  ) {

    output +=
      "NA";

  } else {

    output +=
      String(
        distL,
        1
      );
  }

  output += ",";
  output += rangeName(rangeL);

  output += ",C,";

  if (
    isnan(
      distC
    )
  ) {

    output +=
      "NA";

  } else {

    output +=
      String(
        distC,
        1
      );
  }

  output += ",";
  output += rangeName(rangeC);

  output += ",R,";

  if (
    isnan(
      distR
    )
  ) {

    output +=
      "NA";

  } else {

    output +=
      String(
        distR,
        1
      );
  }

  output += ",";
  output += rangeName(rangeR);

  output += ",ENC_L,";
  output += String(leftCount);

  output += ",ENC_R,";
  output += String(rightCount);

  output += ",CAM_EDGE,";
  output += camEdgeName();

  output += ",CAM_L,";
  output += camSideName(camL);

  output += ",CAM_R,";
  output += camSideName(camR);

  sendLine(
    output
  );
}

// ==============================================================================
// HELP
// ==============================================================================

void printHelp() {

  sendLine(
    "HELP,PING|STATUS|ARM|DISARM|STOP|HB|HEARTBEAT"
  );

  sendLine(
    "HELP,AUTO,ON|AUTO,OFF"
  );

  sendLine(
    "HELP,MODE,US_ONLY|MODE,FUSION"
  );

  sendLine(
    "HELP,SWEEP,ON|SWEEP,OFF"
  );

  sendLine(
    "HELP,PWM,<0-255>|FWD|BACK|LEFT|RIGHT"
  );

  sendLine(
    "HELP,CAM,EDGE,SAFE|EDGE|UNKNOWN"
  );

  sendLine(
    "HELP,CAM,LEFT,FREE|BLOCKED|UNKNOWN"
  );

  sendLine(
    "HELP,CAM,RIGHT,FREE|BLOCKED|UNKNOWN"
  );
}

// ==============================================================================
// CAMERA COMMANDS
// ==============================================================================

void cameraCmd(
  const String& input
) {

  if (
    input ==
    "CAM,EDGE,SAFE"
  ) {

    camEdge =
      CE_SAFE;

  } else if (
    input ==
    "CAM,EDGE,EDGE"
  ) {

    camEdge =
      CE_EDGE;

  } else if (
    input ==
    "CAM,EDGE,UNKNOWN"
  ) {

    camEdge =
      CE_UNKNOWN;

  } else if (
    input ==
    "CAM,LEFT,FREE"
  ) {

    camL =
      CS_FREE;

  } else if (
    input ==
    "CAM,LEFT,BLOCKED"
  ) {

    camL =
      CS_BLOCKED;

  } else if (
    input ==
    "CAM,LEFT,UNKNOWN"
  ) {

    camL =
      CS_UNKNOWN;

  } else if (
    input ==
    "CAM,RIGHT,FREE"
  ) {

    camR =
      CS_FREE;

  } else if (
    input ==
    "CAM,RIGHT,BLOCKED"
  ) {

    camR =
      CS_BLOCKED;

  } else if (
    input ==
    "CAM,RIGHT,UNKNOWN"
  ) {

    camR =
      CS_UNKNOWN;

  } else {

    sendLine(
      "ERROR,BAD_CAMERA_COMMAND"
    );

    return;
  }

  cameraMs =
    millis();

  sendLine(
    "ACK,CAMERA"
  );
}

// ==============================================================================
// COMMAND PARSER
// ==============================================================================

void command(
  String input,
  bool fromNetwork
) {

  input.trim();

  if (
    input.length() ==
    0
  ) {

    return;
  }

  String upper =
    input;

  upper.toUpperCase();

  // Stage 10 compatibility
  if (
    upper.startsWith(
      "CMD,"
    )
  ) {

    upper =
      upper.substring(
        4
      );
  }

  if (
    fromNetwork
  ) {

    networkControl =
      true;

    lastNetMs =
      millis();
  }

  if (
    upper == "HELP" ||
    upper == "H"
  ) {

    printHelp();
    return;
  }

  if (
    upper ==
    "PING"
  ) {

    sendLine(
      "PONG"
    );

    return;
  }

  if (
    upper ==
    "STATUS"
  ) {

    sendStatus();
    return;
  }

  if (
    upper == "HB" ||
    upper == "HEARTBEAT"
  ) {

    sendLine(
      "ACK,HEARTBEAT"
    );

    return;
  }

  if (
    upper ==
    "ARM"
  ) {

    armed =
      true;

    stopRobot(
      nullptr
    );

    sendLine(
      "ACK,ARM"
    );

    return;
  }

  if (
    upper ==
    "DISARM"
  ) {

    autoOn =
      false;

    armed =
      false;

    stopRobot(
      "DISARM"
    );

    sendLine(
      "ACK,DISARM"
    );

    return;
  }

  if (
    upper ==
    "STOP"
  ) {

    autoOn =
      false;

    stopRobot(
      "USER_STOP"
    );

    sendLine(
      "ACK,STOP"
    );

    return;
  }

  if (
    upper ==
    "AUTO,ON"
  ) {

    if (
      !armed
    ) {

      sendLine(
        "ERROR,NOT_ARMED"
      );

      return;
    }

    autoOn =
      true;

    sendLine(
      "ACK,AUTO,ON"
    );

    return;
  }

  if (
    upper ==
    "AUTO,OFF"
  ) {

    autoOn =
      false;

    stopRobot(
      "AUTO_OFF"
    );

    sendLine(
      "ACK,AUTO,OFF"
    );

    return;
  }

  if (
    upper ==
    "MODE,US_ONLY"
  ) {

    mode =
      US_ONLY;

    sendLine(
      "ACK,MODE,US_ONLY"
    );

    return;
  }

  if (
    upper ==
    "MODE,FUSION"
  ) {

    mode =
      FUSION;

    sendLine(
      "ACK,MODE,FUSION"
    );

    return;
  }

  if (
    upper ==
    "SWEEP,ON"
  ) {

    sweepOn =
      true;

    servoWaiting =
      false;

    sendLine(
      "ACK,SWEEP,ON"
    );

    return;
  }

  if (
    upper ==
    "SWEEP,OFF"
  ) {

    sweepOn =
      false;

    servoAngle(
      ANG_CENTER
    );

    sendLine(
      "ACK,SWEEP,OFF"
    );

    return;
  }

  if (
    upper.startsWith(
      "PWM,"
    )
  ) {

    int comma =
      upper.indexOf(
        ','
      );

    int requested =
      upper.substring(
        comma + 1
      ).toInt();

    drivePwm =
      constrain(
        requested,
        0,
        255
      );

    String response =
      "ACK,PWM,";

    response +=
      String(
        drivePwm
      );

    sendLine(
      response
    );

    return;
  }

  if (
    upper ==
    "FWD"
  ) {

    autoOn =
      false;

    if (
      !armed
    ) {

      sendLine(
        "ERROR,NOT_ARMED"
      );

      return;
    }

    drive(
      drivePwm,
      drivePwm
    );

    motion =
      FORWARD;

    sendLine(
      "ACK,FWD"
    );

    return;
  }

  if (
    upper ==
    "BACK"
  ) {

    autoOn =
      false;

    if (
      !armed
    ) {

      sendLine(
        "ERROR,NOT_ARMED"
      );

      return;
    }

    drive(
      -drivePwm,
      -drivePwm
    );

    motion =
      BACKWARD;

    sendLine(
      "ACK,BACK"
    );

    return;
  }

  if (
    upper ==
    "LEFT"
  ) {

    autoOn =
      false;

    if (
      !armed
    ) {

      sendLine(
        "ERROR,NOT_ARMED"
      );

      return;
    }

    startLeftTurn();

    return;
  }

  if (
    upper ==
    "RIGHT"
  ) {

    autoOn =
      false;

    if (
      !armed
    ) {

      sendLine(
        "ERROR,NOT_ARMED"
      );

      return;
    }

    startRightTurn();

    return;
  }

  if (
    upper.startsWith(
      "CAM,"
    )
  ) {

    cameraCmd(
      upper
    );

    return;
  }

  String error =
    "ERROR,UNKNOWN_COMMAND,";

  error +=
    upper;

  sendLine(
    error
  );
}

// ==============================================================================
// SERIAL
// ==============================================================================

void serviceSerial() {

  while (
    Serial.available()
  ) {

    char c =
      (char)Serial.read();

    serialLastByteMs =
      millis();

    if (
      c == '\r' ||
      c == '\n'
    ) {

      if (
        serialBuf.length()
      ) {

        command(
          serialBuf,
          false
        );

        serialBuf = "";
      }

    } else {

      if (
        serialBuf.length() <
        160
      ) {

        serialBuf +=
          c;
      }
    }
  }

  // Supports "No line ending".
  if (
    serialBuf.length() &&
    millis() -
    serialLastByteMs >=
    COMMAND_IDLE_FLUSH_MS
  ) {

    command(
      serialBuf,
      false
    );

    serialBuf = "";
  }
}

// ==============================================================================
// WIFI CLIENT
// ==============================================================================

void acceptClient() {

  if (
    client.connected()
  ) {

    return;
  }

  WiFiClient candidate =
    server.available();

  if (
    candidate
  ) {

    client =
      candidate;

    netBuf = "";

    hadClient =
      true;

    networkControl =
      false;

    lastNetMs =
      millis();

    sendLine(
      "WIFI,CLIENT,CONNECTED"
    );
  }
}


void serviceNet() {

  if (
    !client.connected()
  ) {

    return;
  }

  while (
    client.available()
  ) {

    char c =
      (char)client.read();

    netLastByteMs =
      millis();

    if (
      c == '\r' ||
      c == '\n'
    ) {

      if (
        netBuf.length()
      ) {

        command(
          netBuf,
          true
        );

        netBuf = "";
      }

    } else {

      if (
        netBuf.length() <
        160
      ) {

        netBuf +=
          c;
      }
    }
  }

  if (
    netBuf.length() &&
    millis() -
    netLastByteMs >=
    COMMAND_IDLE_FLUSH_MS
  ) {

    command(
      netBuf,
      true
    );

    netBuf = "";
  }
}

// ==============================================================================
// NETWORK SAFETY
// ==============================================================================

void networkSafety() {

  if (
    client.connected()
  ) {

    hadClient =
      true;

    if (
      networkControl &&
      millis() -
      lastNetMs >
      HB_TIMEOUT_MS
    ) {

      autoOn =
        false;

      armed =
        false;

      networkControl =
        false;

      stopRobot(
        "HEARTBEAT_TIMEOUT"
      );

      sendLine(
        "ERROR,HEARTBEAT_TIMEOUT,DISARMED"
      );
    }

    return;
  }

  if (
    hadClient &&
    networkControl &&
    (
      autoOn ||
      motion != STOPPED
    )
  ) {

    autoOn =
      false;

    armed =
      false;

    networkControl =
      false;

    stopRobot(
      "NETWORK_DISCONNECT"
    );

    Serial.println(
      "ERROR,NETWORK_DISCONNECT,DISARMED"
    );
  }

  hadClient =
    false;
}

// ==============================================================================
// SETUP
// ==============================================================================

void setup() {

  Serial.begin(
    115200
  );

  delay(
    600
  );

  pinMode(
    L_IN1,
    OUTPUT
  );

  pinMode(
    L_IN2,
    OUTPUT
  );

  pinMode(
    R_IN1,
    OUTPUT
  );

  pinMode(
    R_IN2,
    OUTPUT
  );

  bool okL =
    pwmAttachCompat(
      L_EN,
      CH_L,
      MOTOR_FREQ,
      MOTOR_BITS
    );

  bool okR =
    pwmAttachCompat(
      R_EN,
      CH_R,
      MOTOR_FREQ,
      MOTOR_BITS
    );

  bool okServo =
    pwmAttachCompat(
      SERVO_PIN,
      CH_SERVO,
      SERVO_FREQ,
      SERVO_BITS
    );

  if (
    !okL ||
    !okR ||
    !okServo
  ) {

    Serial.println(
      "FATAL,PWM_ATTACH_FAILED"
    );

    while (
      true
    ) {

      delay(
        1000
      );
    }
  }

  stopRobot(
    nullptr
  );

  pinMode(
    ENC_L_A,
    INPUT_PULLUP
  );

  pinMode(
    ENC_L_B,
    INPUT_PULLUP
  );

  pinMode(
    ENC_R_A,
    INPUT_PULLUP
  );

  pinMode(
    ENC_R_B,
    INPUT_PULLUP
  );

  attachInterrupt(
    digitalPinToInterrupt(
      ENC_L_A
    ),
    isrL,
    CHANGE
  );

  attachInterrupt(
    digitalPinToInterrupt(
      ENC_R_A
    ),
    isrR,
    CHANGE
  );

  pinMode(
    US_TRIG,
    OUTPUT
  );

  pinMode(
    US_ECHO,
    INPUT
  );

  digitalWrite(
    US_TRIG,
    LOW
  );

  scanPos =
    POS_CENTER_A;

  servoAngle(
    ANG_CENTER
  );

  WiFi.mode(
    WIFI_AP
  );

  bool apOK =
    WiFi.softAP(
      AP_SSID,
      AP_PASS
    );

  if (
    apOK
  ) {

    server.begin();

  } else {

    Serial.println(
      "ERROR,WIFI_AP_FAILED"
    );
  }

  Serial.println();

  Serial.println(
    "================================================"
  );

  Serial.println(
    "ATLAS 6.0 INTEGRATED RELEASE CANDIDATE V3.1 FIXED"
  );

  Serial.println(
    "================================================"
  );

  Serial.print(
    "ARDUINO_ESP32_MAJOR,"
  );

  Serial.println(
    ESP_ARDUINO_VERSION_MAJOR
  );

  Serial.print(
    "WIFI,SSID,"
  );

  Serial.println(
    AP_SSID
  );

  Serial.print(
    "WIFI,IP,"
  );

  Serial.println(
    WiFi.softAPIP()
  );

  Serial.print(
    "WIFI,TCP_PORT,"
  );

  Serial.println(
    TCP_PORT
  );

  Serial.println(
    "DISTANCE,BLOCKED,<10CM"
  );

  Serial.println(
    "DISTANCE,CAUTION,10_TO_<15CM"
  );

  Serial.println(
    "DISTANCE,CLEAR,>=15CM"
  );

  Serial.println(
    "SERVO,SCAN,5-90-175-90,CONTINUOUS"
  );

  Serial.print(
    "ENCODER,LEFT_PPR,"
  );

  Serial.println(
    LEFT_PPR,
    2
  );

  Serial.print(
    "ENCODER,RIGHT_PPR,"
  );

  Serial.println(
    RIGHT_PPR,
    2
  );

  Serial.print(
    "WHEEL_CIRCUMFERENCE_CM,"
  );

  Serial.println(
    WHEEL_CIRC_CM,
    2
  );

  Serial.println(
    "BOOT,DISARMED,AUTO_OFF,MODE_US_ONLY,SWEEP_ON"
  );

  printHelp();
}

// ==============================================================================
// LOOP
// ==============================================================================

void loop() {

  acceptClient();

  serviceSerial();

  serviceNet();

  serviceSweep();

  serviceTurn();

  serviceAuto();

  networkSafety();

  if (
    millis() -
    lastStatusMs >=
    1000
  ) {

    lastStatusMs =
      millis();

    sendStatus();
  }

  delay(
    2
  );
}