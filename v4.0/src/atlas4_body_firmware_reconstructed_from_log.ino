/*
  Atlas 4.0 body firmware — reconstructed reference, NOT the historical original.

  Reconstructed only from verified project_log.txt evidence:
  - Arduino/CH340, 9600 baud
  - Green D8, Yellow D9, Red D10, Servo D6, OLED 0x3C
  - PING, STATUS, HAPPY, THINKING, WARNING, ERROR, NOD, OFF

  Verify mechanical direction and OLED library before flashing.
*/
#include <Servo.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

const int GREEN_LED_PIN = 8;
const int YELLOW_LED_PIN = 9;
const int RED_LED_PIN = 10;
const int SERVO_PIN = 6;
const int SERVO_CENTER = 90;
const int SERVO_NOD = 108;
Servo headServo;
Adafruit_SSD1306 display(128, 64, &Wire, -1);
bool oledOk = false;

void leds(bool g, bool y, bool r) {
  digitalWrite(GREEN_LED_PIN, g ? HIGH : LOW);
  digitalWrite(YELLOW_LED_PIN, y ? HIGH : LOW);
  digitalWrite(RED_LED_PIN, r ? HIGH : LOW);
}

void showText(const char* line1, const char* line2 = "") {
  if (!oledOk) return;
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 18);
  display.println(line1);
  display.println(line2);
  display.display();
}

void replyOk(const String &name) {
  Serial.println(name + "_OK");
  Serial.println("OK:" + name);
}

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(100);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  leds(false, false, false);
  headServo.attach(SERVO_PIN);
  headServo.write(SERVO_CENTER);
  Wire.begin();
  oledOk = display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  showText("Atlas 4.0", "READY");
  Serial.println("ATLAS_4_READY");
}

void loop() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  cmd.toUpperCase();
  if (!cmd.length()) return;
  Serial.println("CMD:" + cmd);

  if (cmd == "PING") {
    Serial.println("PONG"); Serial.println("OK:PING");
  } else if (cmd == "STATUS") {
    Serial.println("STATUS_OK");
    Serial.println("GREEN_LED_PIN:8"); Serial.println("YELLOW_LED_PIN:9");
    Serial.println("RED_LED_PIN:10"); Serial.println("SERVO_PIN:6");
    Serial.println("BAUD_RATE:9600");
    Serial.println(oledOk ? "OLED_OK_ADDRESS:0x3C" : "OLED_NOT_FOUND");
    Serial.println("OK:STATUS");
  } else if (cmd == "HAPPY") {
    leds(true, false, false); showText("HAPPY", ":)"); replyOk("HAPPY");
  } else if (cmd == "THINKING") {
    leds(false, true, false); showText("THINKING", "..."); replyOk("THINKING");
  } else if (cmd == "WARNING") {
    leds(false, true, true); showText("WARNING", "CHECK"); replyOk("WARNING");
  } else if (cmd == "ERROR") {
    leds(false, false, true); showText("ERROR", "STOP"); replyOk("ERROR");
  } else if (cmd == "NOD") {
    headServo.write(SERVO_NOD); delay(350); headServo.write(SERVO_CENTER); delay(350); replyOk("NOD");
  } else if (cmd == "OFF") {
    leds(false, false, false); headServo.write(SERVO_CENTER); showText("Atlas 4.0", "IDLE"); replyOk("OFF");
  } else {
    Serial.println("ERROR:UNKNOWN_COMMAND");
  }
}
