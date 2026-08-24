import time
from datetime import datetime
from pathlib import Path

import cv2
import serial


# =====================================================
# Atlas 5.0 Stage 12D
# Camera Motion Detection + Atlas Behavior
#
# Purpose:
# - Open USB camera.
# - Detect large motion in the camera frame.
# - Trigger Atlas behavior through ESP32 serial commands.
#
# This stage does NOT use face recognition.
# This stage does NOT use AI model.
#
# Required:
# python -m pip install opencv-python pyserial
#
# ESP32 firmware:
# atlas5_body_firmware_oled_v1_success.ino
# =====================================================

SERIAL_PORT = "COM6"   # 改成你的 ESP32 端口
BAUD_RATE = 115200
TIMEOUT = 2
READY_TEXT = "READY_FOR_NEXT_COMMAND"

BASE_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = BASE_DIR / "atlas5_camera_snapshots"

SNAPSHOT_DIR.mkdir(exist_ok=True)

CAMERA_INDEX_LIST = [0, 1, 2, 3, 4]

MOTION_AREA_THRESHOLD = 8000
TRIGGER_COOLDOWN_SECONDS = 5


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

    def warning(self):
        return self.send("WARNING", max_wait=10)

    def error(self):
        return self.send("ERROR", max_wait=10)


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
    return None, None


def draw_info(frame, camera_index, motion_area, motion_detected, auto_mode):
    status_text = "MOTION DETECTED" if motion_detected else "NO MOTION"
    auto_text = "AUTO ON" if auto_mode else "AUTO OFF"

    cv2.putText(
        frame,
        "Atlas 5.0 Camera Motion Detection",
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
        f"Motion Area: {motion_area}",
        (20, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Status: {status_text}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Mode: {auto_text}",
        (20, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Keys: a=toggle auto i=idle q=quit",
        (20, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )


def main():
    print("Atlas 5.0 Stage 12D - Camera Motion Detection + Atlas Behavior")
    print("本阶段：摄像头检测明显运动后，自动触发 Atlas 行为。")
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

        if not hal.arm():
            print("[MAIN ERROR] ARM failed.")
            return

        hal.idle()

        print()
        print("摄像头窗口操作：")
        print("a = 开关自动运动检测")
        print("i = 手动回到 IDLE")
        print("q = 退出")

        ret, frame1 = cap.read()
        ret, frame2 = cap.read()

        if not ret or frame1 is None or frame2 is None:
            print("[ERROR] 摄像头初始化帧失败。")
            return

        auto_mode = False
        last_trigger_time = 0

        while True:
            diff = cv2.absdiff(frame1, frame2)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 25, 255, cv2.THRESH_BINARY)
            dilated = cv2.dilate(thresh, None, iterations=2)

            contours, _ = cv2.findContours(
                dilated,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            motion_area = 0

            for contour in contours:
                area = cv2.contourArea(contour)
                motion_area += int(area)

                if area > 500:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(
                        frame1,
                        (x, y),
                        (x + w, y + h),
                        (255, 255, 255),
                        2
                    )

            motion_detected = motion_area > MOTION_AREA_THRESHOLD

            current_time = time.time()

            if auto_mode and motion_detected:
                if current_time - last_trigger_time > TRIGGER_COOLDOWN_SECONDS:
                    print()
                    print("[VISION] Motion detected. Triggering Atlas.")

                    hal.listening()
                    hal.thinking()
                    hal.success()
                    hal.idle()

                    last_trigger_time = current_time

            draw_info(
                frame1,
                camera_index,
                motion_area,
                motion_detected,
                auto_mode
            )

            cv2.imshow("Atlas 5.0 Motion Detection", frame1)

            frame1 = frame2
            ret, frame2 = cap.read()

            if not ret or frame2 is None:
                print("[ERROR] 摄像头读取失败。")
                break

            key = cv2.waitKey(1) & 0xFF

            if key == ord("a"):
                auto_mode = not auto_mode

                if auto_mode:
                    print("[MODE] Auto motion detection ON.")
                    hal.success()
                    hal.idle()
                else:
                    print("[MODE] Auto motion detection OFF.")
                    hal.idle()

            elif key == ord("i"):
                hal.idle()

            elif key == ord("q"):
                print("[INFO] 退出 Stage 12D。")
                break

    finally:
        print("\n[MAIN] Stopping Atlas...")
        hal.disarm()
        hal.close()

        cap.release()
        cv2.destroyAllWindows()

        print("[MAIN OK] Program finished.")
        print("退出后请关闭四节 AA 电池盒。")


if __name__ == "__main__":
    main()