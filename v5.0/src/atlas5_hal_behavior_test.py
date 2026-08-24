import serial
import time


# =====================================================
# Atlas 5.0 Stage 5
# Python HAL Behavior Test
#
# Purpose:
# - Use Python to send behavior-state commands to ESP32.
# - ESP32 runs Stage 4 Behavior Firmware v2 Stable.
#
# Hardware:
# - ESP32 powered by USB
# - Servos powered by 4xAA battery box
# - Battery GND connected to ESP32 GND
#
# Important:
# - Close Arduino Serial Monitor before running this script.
# - Turn on servo battery box before ARM.
# =====================================================

SERIAL_PORT = "COM6"   # 改成你的 ESP32 端口
BAUD_RATE = 115200
TIMEOUT = 2

READY_TEXT = "READY_FOR_NEXT_COMMAND"


class AtlasHAL:
    def __init__(self, port, baud_rate=115200, timeout=2):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.ser = None

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            time.sleep(2)
            print(f"[OK] Connected to {self.port} at {self.baud_rate}")
            self.read_startup()
            return True
        except serial.SerialException as e:
            print("[ERROR] Could not connect to ESP32.")
            print("Reason:", e)
            print()
            print("请检查：")
            print("1. Arduino 串口监视器是否关闭")
            print("2. COM 端口是否写对")
            print("3. ESP32 是否插好")
            print("4. USB 线是否正常")
            return False

    def close(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            print("[OK] Serial closed.")

    def read_startup(self):
        print("\n[INFO] Reading startup messages...")
        start_time = time.time()
        while time.time() - start_time < 2.0:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line:
                    print("[ESP32]", line)
            else:
                time.sleep(0.05)

    def send(self, command, wait_for_ready=True, max_wait=8):
        if self.ser is None or not self.ser.is_open:
            print("[ERROR] Serial is not open.")
            return False

        command = command.strip().upper()
        print(f"\n[SEND] {command}")

        self.ser.write((command + "\n").encode("utf-8"))
        self.ser.flush()

        start_time = time.time()
        got_ready = False

        while time.time() - start_time < max_wait:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode(errors="ignore").strip()

                if line:
                    print("[ESP32]", line)

                    if READY_TEXT in line:
                        got_ready = True
                        break
            else:
                time.sleep(0.05)

        if wait_for_ready and not got_ready:
            print("[WARNING] Did not receive READY_FOR_NEXT_COMMAND.")
            print("可能原因：")
            print("1. ESP32 正在执行动作，还没结束")
            print("2. 指令拼写错误")
            print("3. 舵机卡住导致动作拖延")
            print("4. 串口通信临时异常")
            return False

        return True

    def ping(self):
        return self.send("PING", max_wait=4)

    def ledtest(self):
        return self.send("LEDTEST", max_wait=5)

    def arm(self):
        return self.send("ARM", max_wait=8)

    def disarm(self):
        return self.send("DISARM", max_wait=5)

    def idle(self):
        return self.send("IDLE", max_wait=6)

    def listening(self):
        return self.send("LISTENING", max_wait=6)

    def thinking(self):
        return self.send("THINKING", max_wait=8)

    def success(self):
        return self.send("SUCCESS", max_wait=6)

    def encourage(self):
        return self.send("ENCOURAGE", max_wait=8)

    def warning(self):
        return self.send("WARNING", max_wait=8)

    def error(self):
        return self.send("ERROR", max_wait=6)

    def behavior_test(self):
        return self.send("BEHAVIOR_TEST", max_wait=25)


def main():
    atlas = AtlasHAL(SERIAL_PORT, BAUD_RATE, TIMEOUT)

    if not atlas.connect():
        return

    try:
        print("\n===== Atlas 5.0 Python HAL Behavior Test =====")
        print("请确认：")
        print("1. 四节 AA 电池盒已经打开")
        print("2. 舵机供电正常")
        print("3. 电池盒负极已连接 ESP32 GND")
        print()

        atlas.ping()
        atlas.ledtest()
        atlas.arm()

        atlas.idle()
        atlas.listening()
        atlas.thinking()
        atlas.success()
        atlas.encourage()
        atlas.warning()
        atlas.error()
        atlas.idle()

        atlas.behavior_test()

        atlas.disarm()

        print("\n[OK] Python HAL behavior test finished.")

    finally:
        atlas.close()


if __name__ == "__main__":
    main()