import serial
import time


# =====================================================
# Atlas 5.0 Stage 5
# Python HAL Ping Test
#
# Purpose:
# - Test whether Python can talk to ESP32 through Serial.
# - ESP32 should already be running:
#   atlas5_stage4_behavior_firmware_v2_stable_success.ino
#
# Before running:
# - Close Arduino Serial Monitor.
# - Set the correct COM port below.
# =====================================================

SERIAL_PORT = "COM6"   # 改成你的 ESP32 端口，例如 COM3 / COM4 / COM5
BAUD_RATE = 115200
TIMEOUT = 2


def open_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        time.sleep(2)
        print(f"[OK] Connected to {SERIAL_PORT} at {BAUD_RATE}")
        return ser
    except serial.SerialException as e:
        print("[ERROR] Could not open serial port.")
        print("Reason:", e)
        print()
        print("请检查：")
        print("1. ESP32 是否已经插入电脑")
        print("2. Arduino IDE 串口监视器是否已经关闭")
        print("3. SERIAL_PORT 是否写对，例如 COM3 / COM4 / COM5")
        print("4. USB 线是否正常")
        return None


def read_available_lines(ser, wait_seconds=1.0):
    end_time = time.time() + wait_seconds
    lines = []

    while time.time() < end_time:
        if ser.in_waiting > 0:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                lines.append(line)
        else:
            time.sleep(0.05)

    return lines


def send_command(ser, command):
    print(f"\n[SEND] {command}")
    ser.write((command + "\n").encode("utf-8"))
    ser.flush()

    lines = read_available_lines(ser, wait_seconds=2.0)

    for line in lines:
        print("[ESP32]", line)

    return lines


def main():
    ser = open_serial()
    if ser is None:
        return

    try:
        print("\n[INFO] Reading ESP32 startup messages...")
        startup_lines = read_available_lines(ser, wait_seconds=2.0)
        for line in startup_lines:
            print("[ESP32]", line)

        send_command(ser, "PING")

    finally:
        ser.close()
        print("\n[OK] Serial closed.")


if __name__ == "__main__":
    main()