import cv2
from datetime import datetime
from pathlib import Path


# =====================================================
# Atlas 5.0 Stage 12B
# Camera Standalone Test
#
# Purpose:
# - Test USB camera.
# - Show live camera preview.
# - Save snapshots.
#
# This file does NOT connect to ESP32.
#
# Required:
# python -m pip install opencv-python
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = BASE_DIR / "atlas5_camera_snapshots"

SNAPSHOT_DIR.mkdir(exist_ok=True)

CAMERA_INDEX_LIST = [0, 1, 2, 3, 4]


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
    print("2. Windows 摄像头权限是否打开")
    print("3. 摄像头是否被微信、腾讯会议、浏览器、相机 App 占用")
    print("4. 重新插拔摄像头")
    return None, None


def save_snapshot(frame):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = SNAPSHOT_DIR / f"atlas5_camera_snapshot_{timestamp}.jpg"

    cv2.imwrite(str(file_path), frame)

    print(f"[OK] 已保存截图：{file_path}")


def main():
    print("Atlas 5.0 Stage 12B - Camera Standalone Test")
    print("本阶段只测试摄像头，不连接 ESP32。")
    print()
    print("操作说明：")
    print("按 s 保存截图")
    print("按 q 退出")
    print()

    cap, camera_index = find_camera()

    if cap is None:
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"[INFO] Camera Index: {camera_index}")
    print("[INFO] 摄像头窗口打开后，按 q 退出。")

    while True:
        ret, frame = cap.read()

        if not ret or frame is None:
            print("[ERROR] 无法读取摄像头画面。")
            break

        height, width = frame.shape[:2]

        cv2.putText(
            frame,
            "Atlas 5.0 Camera Test",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
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

        cv2.circle(
            frame,
            (width // 2, height // 2),
            6,
            (255, 255, 255),
            -1
        )

        cv2.imshow("Atlas 5.0 Camera Test", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            save_snapshot(frame)

        elif key == ord("q"):
            print("[INFO] 退出摄像头测试。")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()