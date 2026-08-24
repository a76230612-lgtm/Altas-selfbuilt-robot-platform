import time
from datetime import datetime
from pathlib import Path

import cv2
import serial


# =====================================================
# Atlas 5.0 Stage 12C
# Camera + ESP32 Terminal Control Safe Version
#
# Purpose:
# - Open USB camera.
# - Connect to ESP32 OLED body firmware.
# - Control Atlas from PyCharm terminal input.
# - Avoid camera-window keyboard focus problems.
# - Reduce servo jitter by ARM -> ACTION -> DISARM.
#
# This stage does NOT change Arduino code.
#
# Required:
# python -m pip install opencv-python pyserial
#
# ESP32 firmware:
# atlas5_body_firmware_oled_v1_success.ino
# =====================================================

SERIAL_PORT = "COM4"   # 改成你的 ESP32 端口，例如 COM3 / COM4 / COM5
BAUD_RATE = 115200
TIMEOUT = 2
READY_TEXT = "READY_FOR_NEXT_COMMAND"

BASE_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = BASE_DIR / "atlas5_camera_snapshots"

SNAPSHOT_DIR.mkdir(exist_ok=True)

CAMERA_INDEX_LIST = [0, 1, 2, 3, 4]


# =====================================================
# ESP32 HAL
# =====================================================

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

            print(f"[HAL OK] Connected to {self.port} at {self.baud_rate}")
            self.read_startup_messages()
            return True

        except serial.SerialException as error:
            print("[HAL ERROR] Could not connect to ESP32.")
            print("Reason:", error)
            print()
            print("请检查：")
            print("1. Arduino Serial Monitor 是否关闭")
            print("2. COM 口是否写对")
            print("3. ESP32 USB 是否插好")
            print("4. USB 线是否正常")
            return False

    def read_startup_messages(self):
        print("\n[HAL INFO] Reading ESP32 startup messages...")

        start_time = time.time()

        while time.time() - start_time < 2.0:
            if self.ser and self.ser.in_waiting > 0:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line:
                    print("[ESP32]", line)
            else:
                time.sleep(0.05)

    def close(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            print("[HAL OK] Serial closed.")

    def send(self, command, max_wait=10):
        if self.ser is None or not self.ser.is_open:
            print("[HAL ERROR] Serial is not open.")
            return False

        command = command.strip().upper()

        print(f"\n[HAL SEND] {command}")

        try:
            self.ser.write((command + "\n").encode("utf-8"))
            self.ser.flush()

        except serial.SerialException as error:
            print("[HAL ERROR] Failed to write command.")
            print("Reason:", error)
            return False

        start_time = time.time()
        got_ready = False

        while time.time() - start_time < max_wait:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode(errors="ignore").strip()

                    if line:
                        print("[ESP32]", line)

                        if READY_TEXT in line:
                            got_ready = True
                            break

                else:
                    time.sleep(0.05)

            except serial.SerialException as error:
                print("[HAL ERROR] Serial read failed.")
                print("Reason:", error)
                return False

        if not got_ready:
            print("[HAL WARNING] Did not receive READY_FOR_NEXT_COMMAND.")
            return False

        return True

    def ping(self):
        return self.send("PING", max_wait=4)

    def ledtest(self):
        return self.send("LEDTEST", max_wait=6)

    def oledtest(self):
        return self.send("OLEDTEST", max_wait=6)

    def arm(self):
        return self.send("ARM", max_wait=8)

    def disarm(self):
        return self.send("DISARM", max_wait=6)

    def idle(self):
        return self.send("IDLE", max_wait=10)

    def listening(self):
        return self.send("LISTENING", max_wait=10)

    def thinking(self):
        return self.send("THINKING", max_wait=10)

    def success(self):
        return self.send("SUCCESS", max_wait=10)

    def encourage(self):
        return self.send("ENCOURAGE", max_wait=12)

    def warning(self):
        return self.send("WARNING", max_wait=10)

    def error(self):
        return self.send("ERROR", max_wait=10)

    def behavior_test(self):
        return self.send("BEHAVIOR_TEST", max_wait=30)


# =====================================================
# Camera
# =====================================================

def find_camera():
    print("正在搜索摄像头...")

    for index in CAMERA_INDEX_LIST:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

        if cap.isOpened():
            ret, frame = cap.read()

            if ret and frame is not None:
                print(f"[OK] 找到摄像头，Camera Index = {index}")
                return cap, index

        cap.release()

    print("[ERROR] 没有找到可用摄像头。")
    print("请检查：")
    print("1. 摄像头 USB 是否插好")
    print("2. 摄像头是否被其他软件占用")
    print("3. Windows 摄像头权限是否打开")
    return None, None


def show_camera_once(cap, camera_index):
    ret, frame = cap.read()

    if not ret or frame is None:
        print("[CAMERA ERROR] 无法读取摄像头画面。")
        return None

    cv2.putText(
        frame,
        "Atlas 5.0 Camera Terminal Control",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Camera Index: {camera_index}",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Control from PyCharm Terminal",
        (20, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.imshow("Atlas 5.0 Camera Terminal Control", frame)
    cv2.waitKey(1)

    return frame


def save_snapshot(frame):
    if frame is None:
        print("[PHOTO ERROR] 没有可保存的画面。")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = SNAPSHOT_DIR / f"atlas5_camera_terminal_{timestamp}.jpg"

    cv2.imwrite(str(file_path), frame)
    print(f"[OK] 已保存截图：{file_path}")


# =====================================================
# Safe Behavior
# =====================================================

def run_safe_behavior(hal, behavior_name):
    print()
    print("========================================")
    print(f"[SAFE MODE] {behavior_name}")
    print("========================================")

    if not hal.arm():
        print("[SAFE MODE ERROR] ARM failed.")
        return False

    ok = False

    if behavior_name == "IDLE":
        ok = hal.idle()

    elif behavior_name == "LISTENING":
        ok = hal.listening()

    elif behavior_name == "THINKING":
        ok = hal.thinking()

    elif behavior_name == "SUCCESS":
        ok = hal.success()

    elif behavior_name == "ENCOURAGE":
        ok = hal.encourage()

    elif behavior_name == "WARNING":
        ok = hal.warning()

    elif behavior_name == "ERROR":
        ok = hal.error()

    elif behavior_name == "BEHAVIOR_TEST":
        ok = hal.behavior_test()

    else:
        print("[SAFE MODE ERROR] Unknown behavior.")
        ok = False

    print("[SAFE MODE] DISARM after action.")
    hal.disarm()

    return ok


# =====================================================
# Menu
# =====================================================

def print_menu():
    print()
    print("========== Atlas 5.0 Stage 12C Terminal Control ==========")
    print("请输入指令，然后按 Enter：")
    print()
    print("i  -> IDLE")
    print("l  -> LISTENING")
    print("t  -> THINKING")
    print("s  -> SUCCESS")
    print("e  -> ENCOURAGE")
    print("w  -> WARNING")
    print("r  -> ERROR")
    print("b  -> BEHAVIOR_TEST")
    print("p  -> 保存当前摄像头截图")
    print("c  -> 刷新摄像头画面")
    print("q  -> 退出")
    print("==========================================================")


# =====================================================
# Main
# =====================================================

def main():
    print("Atlas 5.0 Stage 12C - Camera + Terminal Control Safe Version")
    print("这个版本解决：摄像头窗口按键焦点不稳定的问题。")
    print("所有指令都在 PyCharm Terminal 输入。")
    print()
    print("运行前确认：")
    print("1. ESP32 正在运行 OLED 版身体固件")
    print("2. Arduino Serial Monitor 已关闭")
    print("3. ESP32 USB 已连接")
    print("4. 摄像头 USB 已连接电脑")
    print("5. 四节 AA 电池盒稍后按提示打开")
    print()

    hal = AtlasHAL(SERIAL_PORT, BAUD_RATE, TIMEOUT)

    if not hal.connect():
        return

    cap, camera_index = find_camera()

    if cap is None:
        hal.close()
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    last_frame = None

    try:
        if not hal.ping():
            print("[MAIN ERROR] PING failed.")
            return

        if not hal.ledtest():
            print("[MAIN ERROR] LEDTEST failed.")
            return

        hal.oledtest()

        print("\n请打开四节 AA 电池盒。")
        input("打开电池盒后，按 Enter 继续...")

        print("\n[MAIN] 初始硬件测试：ARM -> IDLE -> DISARM")
        run_safe_behavior(hal, "IDLE")

        last_frame = show_camera_once(cap, camera_index)

        while True:
            print_menu()

            command = input("请输入指令：").strip().lower()

            last_frame = show_camera_once(cap, camera_index)

            if command == "i":
                run_safe_behavior(hal, "IDLE")

            elif command == "l":
                run_safe_behavior(hal, "LISTENING")

            elif command == "t":
                run_safe_behavior(hal, "THINKING")

            elif command == "s":
                run_safe_behavior(hal, "SUCCESS")

            elif command == "e":
                run_safe_behavior(hal, "ENCOURAGE")

            elif command == "w":
                run_safe_behavior(hal, "WARNING")

            elif command == "r":
                run_safe_behavior(hal, "ERROR")

            elif command == "b":
                run_safe_behavior(hal, "BEHAVIOR_TEST")

            elif command == "p":
                save_snapshot(last_frame)

            elif command == "c":
                print("[CAMERA] 已刷新画面。")

            elif command == "q":
                print("[INFO] 退出 Stage 12C Terminal Control。")
                break

            else:
                print("[INPUT ERROR] 无效指令，请输入 i/l/t/s/e/w/r/b/p/c/q。")

    finally:
        print("\n[MAIN] Final DISARM and cleanup...")
        hal.disarm()
        hal.close()

        cap.release()
        cv2.destroyAllWindows()

        print("[MAIN OK] Program finished.")
        print("退出后请关闭四节 AA 电池盒。")


if __name__ == "__main__":
    main()