import json
import time
from datetime import datetime
from pathlib import Path

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except Exception:
    SERIAL_AVAILABLE = False


# ============================================================
# Atlas 4.0 Stage 6
# Hardware Feedback Python Controller
# Robust Serial Version
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"
HARDWARE_LOG_FILE = BASE_DIR / "hardware_feedback_log.txt"
CONFIG_FILE = BASE_DIR / "atlas4_config.json"

# 默认端口。即使这里写 COM6，程序也会自动扫描其他串口。
DEFAULT_SERIAL_PORT = "COM4"
BAUD_RATE = 9600

VALID_COMMANDS = [
    "PING",
    "STATUS",
    "TEST",
    "HAPPY",
    "THINKING",
    "WARNING",
    "ERROR",
    "NOD",
    "OFF"
]

EXPECTED_RESPONSES = {
    "PING": ["PONG", "OK:PING"],
    "STATUS": ["STATUS_OK", "OK:STATUS"],
    "TEST": ["FULL_TEST_DONE", "OK:TEST"],
    "HAPPY": ["HAPPY_OK", "OK:HAPPY"],
    "THINKING": ["THINKING_OK", "OK:THINKING"],
    "WARNING": ["WARNING_OK", "OK:WARNING"],
    "ERROR": ["ERROR_OK", "OK:ERROR"],
    "NOD": ["NOD_OK", "OK:NOD"],
    "OFF": ["OFF_OK", "OK:OFF"]
}

COMMAND_READ_SECONDS = {
    "PING": 2.0,
    "STATUS": 2.5,
    "TEST": 6.0,
    "HAPPY": 3.0,
    "THINKING": 4.0,
    "WARNING": 4.0,
    "ERROR": 3.0,
    "NOD": 4.0,
    "OFF": 2.0
}


def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_write_text(file_path, text):
    try:
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(text)
    except Exception as error:
        print(f"\n日志写入失败：{file_path}")
        print(f"错误信息：{error}")


def write_to_hardware_log(content):
    text = (
        "\n" + "=" * 70 + "\n"
        "Atlas 4.0 Hardware Feedback Log\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    safe_write_text(HARDWARE_LOG_FILE, text)

    print("\n已写入 hardware_feedback_log.txt")
    print(f"Hardware Feedback Log 位置：{HARDWARE_LOG_FILE}")


def write_to_project_log(title, content):
    text = (
        "\n" + "=" * 70 + "\n"
        f"{title}\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    safe_write_text(PROJECT_LOG_FILE, text)

    print("\n已写入 project_log.txt")
    print(f"Project Log 位置：{PROJECT_LOG_FILE}")


def load_config():
    config = {
        "serial_port": DEFAULT_SERIAL_PORT,
        "baud_rate": BAUD_RATE,
        "camera_index": 0,
        "voice_input_sample_rate": 16000,
        "default_voice_language": "en-US",
        "tts_rate": 160,
        "tts_volume": 1.0
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                old_config = json.load(file)

            if isinstance(old_config, dict):
                config.update(old_config)

        except Exception as error:
            print(f"\natlas4_config.json 读取失败，将使用默认配置。错误：{error}")

    return config


def save_config(serial_port):
    config = load_config()
    config["serial_port"] = serial_port
    config["baud_rate"] = BAUD_RATE

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=2)

        print(f"\n已保存 Arduino 串口到 atlas4_config.json：{serial_port}")

    except Exception as error:
        print(f"\n保存 atlas4_config.json 失败：{error}")


def get_configured_port():
    config = load_config()
    return str(config.get("serial_port", DEFAULT_SERIAL_PORT)).strip()


def get_serial_ports():
    if not SERIAL_AVAILABLE:
        return []

    return list(serial.tools.list_ports.comports())


def list_serial_ports():
    if not SERIAL_AVAILABLE:
        message = "pyserial 不可用。请先运行：pip install pyserial"
        print("\n" + message)
        write_to_hardware_log(message)
        return []

    ports = get_serial_ports()

    if not ports:
        message = "没有检测到串口设备。请检查 Arduino 是否插入电脑。"
        print("\n" + message)
        write_to_hardware_log(message)
        write_to_project_log(
            "Atlas 4.0 Hardware Feedback 串口检测",
            message
        )
        return []

    lines = []
    lines.append("当前检测到的串口设备：")

    print("\n当前检测到的串口设备：")
    print("-" * 70)

    for index, port in enumerate(ports):
        line = f"{index}. 端口：{port.device} | 名称：{port.description}"
        print(line)
        lines.append(line)

    print("-" * 70)

    content = "\n".join(lines)

    write_to_hardware_log(content)
    write_to_project_log(
        "Atlas 4.0 Hardware Feedback 串口设备列表",
        content
    )

    return ports


def build_candidate_ports(preferred_port=None):
    ports = get_serial_ports()
    detected_ports = [port.device for port in ports]

    candidates = []

    if preferred_port:
        candidates.append(preferred_port)

    configured_port = get_configured_port()
    if configured_port:
        candidates.append(configured_port)

    if DEFAULT_SERIAL_PORT:
        candidates.append(DEFAULT_SERIAL_PORT)

    for port_name in detected_ports:
        candidates.append(port_name)

    final_candidates = []
    seen = set()

    for item in candidates:
        if not item:
            continue

        name = str(item).strip()

        if not name:
            continue

        upper_name = name.upper()

        if upper_name not in seen:
            final_candidates.append(name)
            seen.add(upper_name)

    return final_candidates


def read_serial_lines(arduino, seconds=2.0):
    lines = []
    end_time = time.time() + seconds

    while time.time() < end_time:
        try:
            if arduino.in_waiting > 0:
                raw_line = arduino.readline()
                line = raw_line.decode("utf-8", errors="ignore").strip()

                if line:
                    lines.append(line)
                    print(f"Arduino 返回：{line}")
            else:
                time.sleep(0.05)

        except Exception as error:
            lines.append(f"READ_ERROR:{error}")
            break

    return lines


def response_contains(lines, expected_tokens):
    joined_text = "\n".join(lines)

    for token in expected_tokens:
        if token in joined_text:
            return True

    return False


def explain_serial_error(error):
    error_text = str(error)

    if "Access is denied" in error_text or "PermissionError" in error_text:
        return (
            "串口被占用。最常见原因：Arduino IDE 串口监视器、串口绘图器、"
            "另一个 Python 程序、另一个 Cursor 终端还在占用 Arduino。"
        )

    if "FileNotFoundError" in error_text or "could not open port" in error_text:
        return (
            "这个 COM 端口不存在或已经变化。请先查看设备管理器，或者用本程序的串口扫描功能。"
        )

    if "ClearCommError" in error_text or "GetOverlappedResult" in error_text:
        return (
            "Windows 串口状态异常。建议拔掉 Arduino，等待 3 秒后重新插入，再运行程序。"
        )

    return "未知串口错误。请检查 Arduino 是否插入、端口是否正确、是否被其他程序占用。"


def open_port(port_name):
    arduino = serial.Serial(
        port=port_name,
        baudrate=BAUD_RATE,
        timeout=0.2,
        write_timeout=1
    )

    return arduino


def connect_arduino(preferred_port=None):
    if not SERIAL_AVAILABLE:
        message = "pyserial 没有安装。请运行：pip install pyserial"
        print("\n" + message)
        write_to_hardware_log(message)
        return None, None

    ports = get_serial_ports()

    if not ports:
        message = (
            "没有检测到任何串口设备。\n"
            "请确认：\n"
            "1. Arduino 已经插入电脑\n"
            "2. USB 数据线不是只能充电的线\n"
            "3. Windows 设备管理器里能看到 COM 端口"
        )
        print("\n" + message)
        write_to_hardware_log(message)
        write_to_project_log(
            "Atlas 4.0 Hardware Feedback Arduino 连接失败",
            message
        )
        return None, None

    candidates = build_candidate_ports(preferred_port)

    print("\n准备自动连接 Arduino。")
    print("候选端口：")
    for item in candidates:
        print(f"- {item}")

    all_errors = []

    for port_name in candidates:
        arduino = None

        try:
            print(f"\n正在尝试连接端口：{port_name}")

            arduino = open_port(port_name)

            # Arduino UNO / Nano 打开串口后通常会自动重启。
            # 这里必须等待，否则 Python 可能在 Arduino 未准备好时就发指令。
            time.sleep(2.8)

            print("读取 Arduino 启动信息...")
            boot_lines = read_serial_lines(arduino, seconds=1.2)

            try:
                arduino.reset_input_buffer()
                arduino.reset_output_buffer()
            except Exception:
                pass

            print("发送握手指令：PING")
            arduino.write(b"PING\n")
            arduino.flush()

            response_lines = read_serial_lines(arduino, seconds=2.5)

            all_lines = boot_lines + response_lines

            if response_contains(all_lines, ["PONG", "OK:PING"]):
                message = (
                    f"Arduino 连接成功：{port_name}\n"
                    "握手成功：Python 已发送 PING，Arduino 已返回 PONG。"
                )

                print("\n" + message)

                save_config(port_name)

                write_to_hardware_log(
                    message + "\n\nArduino 返回内容：\n" + "\n".join(all_lines)
                )

                write_to_project_log(
                    "Atlas 4.0 Hardware Feedback Arduino 连接成功",
                    message
                )

                return arduino, port_name

            else:
                detail = (
                    f"{port_name} 可以打开，但没有收到 PONG。\n"
                    "这说明该端口可能不是 Atlas Arduino，或者 Arduino 代码没有正确上传。\n"
                    "返回内容：\n"
                    + ("\n".join(all_lines) if all_lines else "无返回")
                )

                print("\n" + detail)
                all_errors.append(detail)

                try:
                    arduino.close()
                except Exception:
                    pass

        except Exception as error:
            reason = explain_serial_error(error)
            detail = (
                f"{port_name} 连接失败。\n"
                f"原始错误：{error}\n"
                f"判断：{reason}"
            )

            print("\n" + detail)
            all_errors.append(detail)

            if arduino is not None:
                try:
                    arduino.close()
                except Exception:
                    pass

    final_message = (
        "Arduino 自动连接失败。\n\n"
        "已经尝试过以下端口：\n"
        + "\n".join([f"- {item}" for item in candidates])
        + "\n\n详细错误：\n"
        + "\n\n".join(all_errors)
        + "\n\n最可信处理方式：\n"
        "1. 关闭 Arduino IDE 串口监视器\n"
        "2. 关闭 Arduino 串口绘图器\n"
        "3. 关闭所有正在运行的 Python / Cursor 终端\n"
        "4. 拔掉 Arduino，等待 3 秒，再插回电脑\n"
        "5. 重新运行本程序，先选 1 查看串口，再选 2 自动连接\n"
    )

    print("\n" + final_message)

    write_to_hardware_log(final_message)
    write_to_project_log(
        "Atlas 4.0 Hardware Feedback Arduino 自动连接失败",
        final_message
    )

    return None, None


def close_arduino(arduino):
    if arduino is not None:
        try:
            arduino.close()
            print("\nArduino 连接已关闭。")
        except Exception:
            pass


def send_command(arduino, command):
    command = command.strip().upper()

    if command not in VALID_COMMANDS:
        message = (
            f"无效指令：{command}\n"
            f"可用指令：{', '.join(VALID_COMMANDS)}"
        )
        print("\n" + message)
        write_to_hardware_log(message)
        return False

    if arduino is None:
        message = "Arduino 未连接，不能发送指令。"
        print("\n" + message)
        write_to_hardware_log(message)
        return False

    try:
        print(f"\n发送硬件指令：{command}")

        try:
            arduino.reset_input_buffer()
        except Exception:
            pass

        arduino.write((command + "\n").encode("utf-8"))
        arduino.flush()

        wait_seconds = COMMAND_READ_SECONDS.get(command, 3.0)
        response_lines = read_serial_lines(arduino, seconds=wait_seconds)

        expected_tokens = EXPECTED_RESPONSES.get(command, [])
        success = response_contains(response_lines, expected_tokens)

        if success:
            result = "成功"
        else:
            result = "未确认成功"

        message = (
            f"已发送硬件指令：{command}\n"
            f"执行结果：{result}\n"
            f"期望返回：{expected_tokens}\n"
            "Arduino 返回内容：\n"
            + ("\n".join(response_lines) if response_lines else "无返回")
        )

        print("\n" + message)

        write_to_hardware_log(message)
        write_to_project_log(
            "Atlas 4.0 Hardware Feedback 发送指令",
            message
        )

        return success

    except Exception as error:
        message = (
            f"发送指令失败：{error}\n"
            f"判断：{explain_serial_error(error)}"
        )

        print("\n" + message)

        write_to_hardware_log(message)
        write_to_project_log(
            "Atlas 4.0 Hardware Feedback 发送指令失败",
            message
        )

        return False


def connect_send_close(command):
    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is None:
            return False

        return send_command(arduino, command)

    finally:
        close_arduino(arduino)


def manual_set_serial_port():
    ports = list_serial_ports()

    if not ports:
        return

    choice = input("\n请输入 Arduino 对应的编号，例如 0 / 1 / 2：").strip()

    if not choice.isdigit():
        print("输入无效。")
        return

    index = int(choice)

    if index < 0 or index >= len(ports):
        print("编号超出范围。")
        return

    selected_port = ports[index].device
    save_config(selected_port)

    message = f"已手动设置 Arduino 串口：{selected_port}"
    print("\n" + message)

    write_to_hardware_log(message)
    write_to_project_log(
        "Atlas 4.0 Hardware Feedback 手动设置串口",
        message
    )


def test_single_command():
    print("\n单个指令测试。")
    print(f"可用指令：{', '.join(VALID_COMMANDS)}")
    print("建议先测试：PING")
    print("然后测试：STATUS")
    print("最后测试：HAPPY / THINKING / WARNING / NOD / OFF")

    command = input("\n请输入要发送的指令：").strip().upper()

    if command not in VALID_COMMANDS:
        print("指令无效。")
        return

    connect_send_close(command)


def run_basic_feedback_test():
    print("\n开始基础硬件反馈测试。")
    print("将依次发送：PING / STATUS / HAPPY / THINKING / WARNING / ERROR / NOD / OFF")

    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is None:
            return

        commands = [
            ("PING", "确认 Python 与 Arduino 是否真正连通"),
            ("STATUS", "读取 Arduino 硬件状态"),
            ("HAPPY", "任务成功 / 开心反馈"),
            ("THINKING", "Atlas 正在思考"),
            ("WARNING", "提醒 Eric 注意"),
            ("ERROR", "出现错误"),
            ("NOD", "舵机点头"),
            ("OFF", "关闭反馈")
        ]

        lines = []

        for command, description in commands:
            line = f"{command} - {description}"
            print("\n测试：" + line)
            lines.append(line)

            send_command(arduino, command)
            time.sleep(0.8)

        content = (
            "基础硬件反馈测试完成。\n"
            "已测试：\n"
            + "\n".join(lines)
        )

        write_to_hardware_log(content)
        write_to_project_log(
            "Atlas 4.0 Hardware Feedback 基础测试完成",
            content
        )

    finally:
        close_arduino(arduino)


def run_full_hardware_test():
    print("\n开始 Arduino 全硬件 TEST。")
    print("将发送 TEST，让 Arduino 自动测试绿灯、黄灯、红灯、舵机、OLED。")

    connect_send_close("TEST")


def run_atlas_scene_test():
    print("\n开始 Atlas 场景反馈测试。")
    print("这一步模拟 Atlas 4.0 的真实使用场景。")

    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is None:
            return

        scenes = [
            ("THINKING", "Atlas 正在读取 Eric 的长期记忆。"),
            ("HAPPY", "Atlas 成功生成 Morning Brief。"),
            ("NOD", "Atlas 点头确认今天任务。"),
            ("WARNING", "Atlas 发现任务长期未推进，提醒 Eric。"),
            ("HAPPY", "Eric 完成一个最小测试，Atlas 给出成功反馈。"),
            ("OFF", "测试结束，关闭硬件反馈。")
        ]

        lines = []

        for command, description in scenes:
            line = f"{description} → 发送 {command}"
            print("\n" + line)
            lines.append(line)

            send_command(arduino, command)
            time.sleep(1.0)

        content = (
            "Atlas 4.0 场景反馈测试完成。\n\n"
            + "\n".join(lines)
        )

        write_to_hardware_log(content)
        write_to_project_log(
            "Atlas 4.0 Hardware Feedback 场景测试完成",
            content
        )

    finally:
        close_arduino(arduino)


def run_proactive_mentor_hardware_demo():
    print("\n开始 Proactive Mentor + Hardware Feedback Demo。")
    print("这一步模拟第五阶段主动导师和第六阶段硬件反馈的连接。")

    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is None:
            return

        steps = [
            ("THINKING", "Atlas 正在思考今天的任务。"),
            ("HAPPY", "Atlas 生成主动导师 Morning Brief 成功。"),
            ("NOD", "Atlas 点头确认：今天先完成一个最小测试。"),
            ("WARNING", "Atlas 提醒：不要一次增加太多功能。"),
            ("OFF", "硬件反馈结束。")
        ]

        lines = []

        for command, description in steps:
            line = f"{description} → {command}"
            print("\n" + line)
            lines.append(line)

            send_command(arduino, command)
            time.sleep(1.0)

        content = (
            "Proactive Mentor + Hardware Feedback Demo 完成。\n\n"
            + "\n".join(lines)
        )

        write_to_hardware_log(content)
        write_to_project_log(
            "Atlas 4.0 Proactive Mentor + Hardware Feedback Demo",
            content
        )

    finally:
        close_arduino(arduino)


def test_log_write():
    content = (
        "这是 Atlas 4.0 Hardware Feedback 第六阶段的日志写入测试。\n"
        "如果你能看到这段记录，说明 hardware_feedback_log.txt 和 project_log.txt 都可以正常写入。"
    )

    write_to_hardware_log(content)
    write_to_project_log(
        "Atlas 4.0 Hardware Feedback 日志写入测试",
        content
    )


def show_intro():
    configured_port = get_configured_port()

    print("\n==============================")
    print("Atlas 4.0")
    print("Stage 6: Hardware Feedback")
    print("Robust Serial Version")
    print("==============================")
    print("目标：让 Atlas 通过 Arduino、LED、舵机、OLED 表达状态。")
    print("当前阶段只做 Hardware Feedback，不新增 AI 功能。")
    print(f"默认 Arduino 端口：{DEFAULT_SERIAL_PORT}")
    print(f"配置文件端口：{configured_port}")
    print(f"波特率：{BAUD_RATE}")
    print(f"Config 文件：{CONFIG_FILE}")
    print(f"Hardware Log 文件：{HARDWARE_LOG_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")


def show_menu():
    print("\n请选择功能：")
    print("1. 查看电脑串口设备")
    print("2. 自动连接 Arduino，并用 PING/PONG 验证")
    print("3. 手动选择 Arduino 串口，并保存到 atlas4_config.json")
    print("4. 发送单个硬件指令")
    print("5. 基础硬件反馈测试")
    print("6. Arduino 全硬件 TEST")
    print("7. Atlas 场景反馈测试")
    print("8. Proactive Mentor + Hardware Feedback Demo")
    print("9. 测试 hardware_feedback_log.txt 和 project_log.txt 写入")
    print("10. 退出")


def main():
    show_intro()

    write_to_project_log(
        "Atlas 4.0 Hardware Feedback 程序启动",
        "Atlas 4.0 第六阶段 Hardware Feedback 程序已启动。"
    )

    while True:
        show_menu()

        choice = input("请输入数字 1-10：").strip()

        if choice == "1":
            list_serial_ports()

        elif choice == "2":
            arduino = None

            try:
                arduino, port_name = connect_arduino()

                if arduino is not None:
                    print(f"\n最终确认：Arduino 已连接，端口：{port_name}")

            finally:
                close_arduino(arduino)

        elif choice == "3":
            manual_set_serial_port()

        elif choice == "4":
            test_single_command()

        elif choice == "5":
            run_basic_feedback_test()

        elif choice == "6":
            run_full_hardware_test()

        elif choice == "7":
            run_atlas_scene_test()

        elif choice == "8":
            run_proactive_mentor_hardware_demo()

        elif choice == "9":
            test_log_write()

        elif choice == "10":
            write_to_project_log(
                "Atlas 4.0 Hardware Feedback 程序退出",
                "Atlas 4.0 第六阶段 Hardware Feedback 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 10。")


if __name__ == "__main__":
    main()