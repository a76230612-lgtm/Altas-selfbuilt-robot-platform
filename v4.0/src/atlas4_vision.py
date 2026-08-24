import cv2
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

VISION_LOG_FILE = BASE_DIR / "vision_log.txt"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_to_vision_log(content):
    text = (
        "\n" + "=" * 70 + "\n"
        f"Atlas 4.0 Vision Log\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(VISION_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 vision_log.txt")
    print(f"Vision Log 位置：{VISION_LOG_FILE}")


def write_to_project_log(title, content):
    text = (
        "\n" + "=" * 70 + "\n"
        f"{title}\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(PROJECT_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 project_log.txt")
    print(f"Project Log 位置：{PROJECT_LOG_FILE}")


def test_camera_once():
    print("\n正在测试摄像头是否可以打开...")

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        message = (
            "摄像头打开失败。\n"
            "请检查：\n"
            "1. 摄像头是否被其他软件占用\n"
            "2. Windows 是否允许 Cursor / Python 使用摄像头\n"
            "3. 如果是外接 USB 摄像头，请重新插拔\n"
            "4. 如果内置摄像头不行，可以把 cv2.VideoCapture(0) 改成 cv2.VideoCapture(1)"
        )

        print(message)

        write_to_vision_log(message)
        write_to_project_log(
            "Atlas 4.0 Vision 摄像头测试失败",
            message
        )

        return

    success, frame = camera.read()

    if not success:
        message = "摄像头可以打开，但无法读取画面。"
        print(message)

        write_to_vision_log(message)
        write_to_project_log(
            "Atlas 4.0 Vision 摄像头读取失败",
            message
        )

        camera.release()
        return

    message = "摄像头测试成功。Atlas 4.0 可以读取摄像头画面。"
    print(message)

    write_to_vision_log(message)
    write_to_project_log(
        "Atlas 4.0 Vision 摄像头测试成功",
        message
    )

    camera.release()


def start_vision_detection():
    print("\n启动 Atlas 4.0 Vision 检测。")
    print("说明：")
    print("1. 摄像头窗口打开后，请让 Eric 面对摄像头。")
    print("2. 检测到人脸时，会显示 Eric is present。")
    print("3. 没检测到人脸时，会显示 Eric is not present。")
    print("4. 按 q 退出摄像头窗口。")

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        message = (
            "摄像头打开失败。请检查摄像头权限、连接状态，或尝试把 VideoCapture(0) 改成 VideoCapture(1)。"
        )

        print(message)

        write_to_vision_log(message)
        write_to_project_log(
            "Atlas 4.0 Vision 启动失败",
            message
        )

        return

    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_detector = cv2.CascadeClassifier(face_cascade_path)

    if face_detector.empty():
        message = "OpenCV 人脸检测模型加载失败。"
        print(message)

        write_to_vision_log(message)
        write_to_project_log(
            "Atlas 4.0 Vision 人脸模型加载失败",
            message
        )

        camera.release()
        return

    last_status = None
    present_count = 0
    absent_count = 0

    write_to_vision_log("Atlas 4.0 Vision 检测已启动。")
    write_to_project_log(
        "Atlas 4.0 Vision 检测启动",
        "摄像头检测已启动。目标：判断 Eric 是否在画面前。"
    )

    while True:
        success, frame = camera.read()

        if not success:
            print("无法读取摄像头画面。")
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_detector.detectMultiScale(
            gray_frame,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )

        if len(faces) > 0:
            status = "Eric is present"
            present_count += 1
        else:
            status = "Eric is not present"
            absent_count += 1

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.putText(
            frame,
            status,
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0) if len(faces) > 0 else (0, 0, 255),
            2
        )

        cv2.putText(
            frame,
            "Press q to quit",
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.imshow("Atlas 4.0 Vision - Eric Presence Detection", frame)

        if status != last_status:
            log_message = f"Vision 状态变化：{status}"
            print(log_message)
            write_to_vision_log(log_message)
            last_status = status

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    summary = (
        "Atlas 4.0 Vision 检测结束。\n"
        f"检测到 Eric 在场的帧数：{present_count}\n"
        f"未检测到 Eric 的帧数：{absent_count}\n"
        "说明：这是 Atlas 4.0 第一阶段 Vision 的基础检测结果。"
    )

    print("\n" + summary)

    write_to_vision_log(summary)
    write_to_project_log(
        "Atlas 4.0 Vision 检测结束",
        summary
    )


def show_vision_intro():
    print("\n==============================")
    print("Atlas 4.0")
    print("Stage 1: Vision")
    print("==============================")
    print("目标：让 Atlas 通过摄像头判断 Eric 是否在画面前。")
    print("当前阶段只做 Vision，不做语音输入、语音输出和记忆整合。")
    print(f"Vision Log 文件：{VISION_LOG_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")


def main():
    show_vision_intro()

    write_to_project_log(
        "Atlas 4.0 Vision 程序启动",
        "Atlas 4.0 第一阶段 Vision 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 测试摄像头是否能打开")
        print("2. 启动 Eric 是否在场检测")
        print("3. 测试 vision_log.txt 和 project_log.txt 写入")
        print("4. 退出")

        choice = input("请输入数字 1-4：").strip()

        if choice == "1":
            test_camera_once()

        elif choice == "2":
            start_vision_detection()

        elif choice == "3":
            test_text = (
                "这是 Atlas 4.0 Vision 第一阶段的日志写入测试。\n"
                "如果你能看到这段记录，说明 vision_log.txt 和 project_log.txt 都可以正常写入。"
            )

            write_to_vision_log(test_text)
            write_to_project_log(
                "Atlas 4.0 Vision 日志写入测试",
                test_text
            )

        elif choice == "4":
            write_to_project_log(
                "Atlas 4.0 Vision 程序退出",
                "Atlas 4.0 第一阶段 Vision 程序已退出。"
            )

            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 4。")


if __name__ == "__main__":
    main()