#include <Servo.h>

/*
  =====================================================
  Atlas 5.0 Stage 2
  Mechanical Base + Pan-Tilt Head Stability Test

  Current Stage Goal:
  - Test mechanical body structure
  - Test pan servo and tilt servo
  - Test LED feedback
  - Run 50-times stability test

  Hardware Mapping:
  D6  = Pan Servo  / Head left-right
  D7  = Tilt Servo / Head up-down
  D8  = Green LED  / Success
  D9  = Yellow LED / Thinking / Moving
  D10 = Red LED    / Error / Warning

  OLED is installed physically, but not used in this test.
  Camera is external and should not be mounted on the head in Stage 2.
  =====================================================
*/

// -----------------------------
// Pin definitions
// -----------------------------
const int PAN_SERVO_PIN = 6;
const int TILT_SERVO_PIN = 7;

const int GREEN_LED_PIN = 8;
const int YELLOW_LED_PIN = 9;
const int RED_LED_PIN = 10;

// -----------------------------
// Servo objects
// -----------------------------
Servo panServo;
Servo tiltServo;

// -----------------------------
// Servo angle settings
// Keep the range conservative to protect the structure.
// -----------------------------
const int PAN_CENTER = 90;
const int PAN_LEFT = 60;
const int PAN_RIGHT = 120;

const int TILT_CENTER = 90;
const int TILT_UP = 75;
const int TILT_DOWN = 108;

// Current servo positions
int currentPan = PAN_CENTER;
int currentTilt = TILT_CENTER;

// Motion speed
const int STEP_DELAY = 15;

// Serial command
String command = "";

// -----------------------------
// Setup
// -----------------------------
void setup() {
  Serial.begin(9600);
  Serial.setTimeout(100);

  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);

  allLedsOff();

  delay(500);

  panServo.attach(PAN_SERVO_PIN);
  tiltServo.attach(TILT_SERVO_PIN);

  centerHead();

  successBlink();

  Serial.println("ATLAS_5_STAGE_2_READY");
  Serial.println("Mechanical Base + Pan-Tilt Head Test");
  Serial.println("------------------------------------");
  Serial.println("Commands:");
  Serial.println("PING");
  Serial.println("CENTER");
  Serial.println("LEFT");
  Serial.println("RIGHT");
  Serial.println("UP");
  Serial.println("DOWN");
  Serial.println("NOD");
  Serial.println("SHAKE");
  Serial.println("TEST");
  Serial.println("TEST50");
  Serial.println("HELP");
  Serial.println("------------------------------------");
}

// -----------------------------
// Main loop
// -----------------------------
void loop() {
  if (Serial.available() > 0) {
    command = Serial.readStringUntil('\n');
    command.trim();
    command.toUpperCase();

    if (command.length() == 0) {
      return;
    }

    Serial.print("RECEIVED: ");
    Serial.println(command);

    if (command == "PING" || command == "CMD:PING") {
      Serial.println("PONG");
      Serial.println("OK:PING");
    }

    else if (command == "CENTER" || command == "CMD:CENTER") {
      movingLed();
      centerHead();
      successLed();
      Serial.println("OK:CENTER");
    }

    else if (command == "LEFT" || command == "CMD:MOTION:LOOK_LEFT") {
      movingLed();
      movePan(PAN_LEFT);
      successLed();
      Serial.println("OK:LEFT");
    }

    else if (command == "RIGHT" || command == "CMD:MOTION:LOOK_RIGHT") {
      movingLed();
      movePan(PAN_RIGHT);
      successLed();
      Serial.println("OK:RIGHT");
    }

    else if (command == "UP") {
      movingLed();
      moveTilt(TILT_UP);
      successLed();
      Serial.println("OK:UP");
    }

    else if (command == "DOWN" || command == "CMD:MOTION:LOOK_DOWN") {
      movingLed();
      moveTilt(TILT_DOWN);
      successLed();
      Serial.println("OK:DOWN");
    }

    else if (command == "NOD" || command == "CMD:MOTION:NOD_SLOW") {
      movingLed();
      nodSlow();
      successLed();
      Serial.println("OK:NOD");
    }

    else if (command == "SHAKE" || command == "CMD:MOTION:SHAKE_NO") {
      movingLed();
      shakeSlow();
      successLed();
      Serial.println("OK:SHAKE");
    }

    else if (command == "TEST") {
      movingLed();
      testOnce();
      successLed();
      Serial.println("OK:TEST");
    }

    else if (command == "TEST50") {
      movingLed();
      testFiftyTimes();
      successLed();
      Serial.println("OK:TEST50");
    }

    else if (command == "HELP") {
      showHelp();
    }

    else {
      errorLed();
      Serial.println("UNKNOWN_COMMAND");
      Serial.println("ERROR:UNKNOWN_COMMAND");
      Serial.println("Type HELP to see commands.");
    }
  }
}

// =====================================================
// LED functions
// =====================================================
void allLedsOff() {
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
}

void successLed() {
  allLedsOff();
  digitalWrite(GREEN_LED_PIN, HIGH);
}

void movingLed() {
  allLedsOff();
  digitalWrite(YELLOW_LED_PIN, HIGH);
}

void errorLed() {
  allLedsOff();
  digitalWrite(RED_LED_PIN, HIGH);
}

void successBlink() {
  allLedsOff();

  for (int i = 0; i < 3; i++) {
    digitalWrite(GREEN_LED_PIN, HIGH);
    delay(120);
    digitalWrite(GREEN_LED_PIN, LOW);
    delay(120);
  }
}

// =====================================================
// Servo control functions
// =====================================================
void centerHead() {
  smoothMovePan(currentPan, PAN_CENTER);
  smoothMoveTilt(currentTilt, TILT_CENTER);

  currentPan = PAN_CENTER;
  currentTilt = TILT_CENTER;

  delay(300);
}

void movePan(int targetAngle) {
  smoothMovePan(currentPan, targetAngle);
  currentPan = targetAngle;
  delay(250);
}

void moveTilt(int targetAngle) {
  smoothMoveTilt(currentTilt, targetAngle);
  currentTilt = targetAngle;
  delay(250);
}

void smoothMovePan(int fromAngle, int toAngle) {
  if (fromAngle < toAngle) {
    for (int angle = fromAngle; angle <= toAngle; angle++) {
      panServo.write(angle);
      delay(STEP_DELAY);
    }
  } else {
    for (int angle = fromAngle; angle >= toAngle; angle--) {
      panServo.write(angle);
      delay(STEP_DELAY);
    }
  }
}

void smoothMoveTilt(int fromAngle, int toAngle) {
  if (fromAngle < toAngle) {
    for (int angle = fromAngle; angle <= toAngle; angle++) {
      tiltServo.write(angle);
      delay(STEP_DELAY);
    }
  } else {
    for (int angle = fromAngle; angle >= toAngle; angle--) {
      tiltServo.write(angle);
      delay(STEP_DELAY);
    }
  }
}

// =====================================================
// Motion functions
// =====================================================
void nodSlow() {
  Serial.println("NOD_START");

  moveTilt(TILT_DOWN);
  delay(200);

  moveTilt(TILT_CENTER);
  delay(200);

  Serial.println("NOD_DONE");
}

void shakeSlow() {
  Serial.println("SHAKE_START");

  movePan(PAN_LEFT);
  delay(180);

  movePan(PAN_RIGHT);
  delay(180);

  movePan(PAN_CENTER);
  delay(200);

  Serial.println("SHAKE_DONE");
}

void testOnce() {
  Serial.println("TEST_START");

  centerHead();
  delay(300);

  movePan(PAN_LEFT);
  delay(200);

  movePan(PAN_RIGHT);
  delay(200);

  movePan(PAN_CENTER);
  delay(300);

  moveTilt(TILT_DOWN);
  delay(200);

  moveTilt(TILT_UP);
  delay(200);

  moveTilt(TILT_CENTER);
  delay(300);

  nodSlow();
  delay(200);

  shakeSlow();
  delay(200);

  centerHead();

  Serial.println("TEST_DONE");
}

void testFiftyTimes() {
  Serial.println("TEST50_START");
  Serial.println("Goal: check base stability, head weight, wire drag, servo load, and structure looseness.");

  for (int i = 1; i <= 50; i++) {
    Serial.print("TEST_COUNT: ");
    Serial.println(i);

    shakeSlow();
    delay(150);

    nodSlow();
    delay(150);

    centerHead();
    delay(200);
  }

  Serial.println("TEST50_DONE");
}

// =====================================================
// Help
// =====================================================
void showHelp() {
  Serial.println("Atlas 5.0 Stage 2 Commands:");
  Serial.println("PING    -> Check serial connection");
  Serial.println("CENTER  -> Return pan and tilt servos to center");
  Serial.println("LEFT    -> Head looks left");
  Serial.println("RIGHT   -> Head looks right");
  Serial.println("UP      -> Head looks up");
  Serial.println("DOWN    -> Head looks down");
  Serial.println("NOD     -> Slow nod");
  Serial.println("SHAKE   -> Slow shake");
  Serial.println("TEST    -> One full mechanical motion test");
  Serial.println("TEST50  -> 50-times stability test");
  Serial.println("HELP    -> Show command list");
}
