/*
  Atlas 6.0 - ESP32-S3 GPIO21 Electrical Test V1
  ------------------------------------------------
  PURPOSE:
    Verify that the physical pin labelled GPIO21 really outputs 0V / 3.3V.

  IMPORTANT:
    Disconnect the SERVO SIGNAL wire from GPIO21 during this test.
    Servo VCC/GND may remain connected, but for the cleanest test
    disconnect the servo completely.

  TEST WITH MULTIMETER:
    Black probe -> ESP32 GND
    Red probe   -> physical GPIO21 pin
    DC Voltage mode

  Expected:
    ~3.3V for 2 seconds
    ~0V   for 2 seconds
    repeating
*/

#include <Arduino.h>

static const uint8_t TEST_PIN = 21;

void setup() {
  pinMode(TEST_PIN, OUTPUT);
}

void loop() {
  digitalWrite(TEST_PIN, HIGH);
  delay(2000);

  digitalWrite(TEST_PIN, LOW);
  delay(2000);
}
