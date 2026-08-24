#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Atlas 4.0 Full Main
Single-file integrated version

包含功能：
Stage 1  Vision：摄像头检测 Eric 是否在场
Stage 2  Voice Input：录音并转文字
Stage 3  Voice Output：文字转语音
Stage 4  Memory Integration：读取 Atlas 3.0 / 综合长期记忆并回答
Stage 5  Proactive Mentor：主动生成 Morning Brief、昨天总结、今天任务、未推进任务提醒
Stage 6  Hardware Feedback：Python 串口控制 Arduino 的 LED / 舵机 / OLED 反馈

运行：
python atlas4_full_main.py
或：
py atlas4_full_main.py
"""

import json
import tempfile
import time
from datetime import datetime, date, timedelta
from pathlib import Path


# ============================================================
# Optional imports
# ============================================================

try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False

try:
    import numpy as np
    import sounddevice as sd
    from scipy.io.wavfile import write as write_wav
    import speech_recognition as sr
    VOICE_INPUT_AVAILABLE = True
except Exception:
    VOICE_INPUT_AVAILABLE = False
    np = None
    sd = None
    write_wav = None
    sr = None

try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False
    pyttsx3 = None

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except Exception:
    SERIAL_AVAILABLE = False
    serial = None


# ============================================================
# Global paths and settings
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "atlas4_config.json"
FULL_DATA_FILE = BASE_DIR / "atlas4_full_data.json"

PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"
VISION_LOG_FILE = BASE_DIR / "vision_log.txt"
VOICE_INPUT_LOG_FILE = BASE_DIR / "voice_input_log.txt"
VOICE_OUTPUT_LOG_FILE = BASE_DIR / "voice_output_log.txt"
MEMORY_INTEGRATION_LOG_FILE = BASE_DIR / "memory_integration_log.txt"
PROACTIVE_MENTOR_LOG_FILE = BASE_DIR / "proactive_mentor_log.txt"
HARDWARE_LOG_FILE = BASE_DIR / "hardware_feedback_log.txt"

VOICE_INPUT_DATA_FILE = BASE_DIR / "voice_input_data.json"
VOICE_OUTPUT_DATA_FILE = BASE_DIR / "voice_output_data.json"
MEMORY_INTEGRATION_DATA_FILE = BASE_DIR / "memory_integration_data.json"
PROACTIVE_MENTOR_DATA_FILE = BASE_DIR / "proactive_mentor_data.json"

ATLAS_UNIFIED_DATA_FILE = BASE_DIR / "atlas_unified_data.json"
ATLAS_FINAL_DATA_FILE = BASE_DIR / "atlas_final_data.json"
ATLAS_INTEGRATED_DATA_FILE = BASE_DIR / "atlas_integrated_data.json"
ATLAS3_DATA_FILE = BASE_DIR / "atlas3_data.json"

PROFILE_FILE = BASE_DIR / "profile.json"
SKILLS_FILE = BASE_DIR / "skills.json"
HISTORY_FILE = BASE_DIR / "history.json"
LEARNING_PLAN_FILE = BASE_DIR / "learning_plan.json"
EMOTION_FILE = BASE_DIR / "emotion_memory.json"
MENTOR_RECOMMENDATION_FILE = BASE_DIR / "mentor_recommendation.json"

DEFAULT_CONFIG = {
    "serial_port": "COM6",
    "backup_serial_ports": ["COM4", "COM5", "COM3", "COM7", "COM8"],
    "baud_rate": 9600,
    "camera_index": 0,
    "voice_input_sample_rate": 16000,
    "default_voice_language": "en-US",
    "tts_rate": 160,
    "tts_volume": 1.0
}

VALID_HARDWARE_COMMANDS = [
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


# ============================================================
# Basic utilities
# ============================================================

def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_today_text():
    return date.today().strftime("%Y-%m-%d")


def get_yesterday_text():
    return (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")


def parse_date(date_text):
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except Exception:
        return None


def safe_load_json(file_path, default_data):
    if not file_path.exists():
        return default_data

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except Exception:
        return default_data


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def safe_write_text(file_path, text):
    try:
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(text)
    except Exception as error:
        print(f"\n日志写入失败：{file_path}")
        print(f"错误信息：{error}")


def write_block_log(file_path, title, content, echo=True):
    text = (
        "\n" + "=" * 70 + "\n"
        + title + "\n"
        + f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + str(content) + "\n"
        + "=" * 70 + "\n"
    )

    safe_write_text(file_path, text)

    if echo:
        print(f"\n已写入：{file_path.name}")
        print(f"位置：{file_path}")


def write_to_project_log(title, content):
    write_block_log(PROJECT_LOG_FILE, title, content)


def write_to_vision_log(content):
    write_block_log(VISION_LOG_FILE, "Atlas 4.0 Vision Log", content)


def write_to_voice_input_log(content):
    write_block_log(VOICE_INPUT_LOG_FILE, "Atlas 4.0 Voice Input Log", content)


def write_to_voice_output_log(content):
    write_block_log(VOICE_OUTPUT_LOG_FILE, "Atlas 4.0 Voice Output Log", content)


def write_to_memory_log(content):
    write_block_log(MEMORY_INTEGRATION_LOG_FILE, "Atlas 4.0 Memory Integration Log", content)


def write_to_proactive_log(content):
    write_block_log(PROACTIVE_MENTOR_LOG_FILE, "Atlas 4.0 Proactive Mentor Log", content)


def write_to_hardware_log(content):
    write_block_log(HARDWARE_LOG_FILE, "Atlas 4.0 Hardware Feedback Log", content)


def load_config():
    config = dict(DEFAULT_CONFIG)

    if CONFIG_FILE.exists():
        try:
            old_config = safe_load_json(CONFIG_FILE, {})
            if isinstance(old_config, dict):
                config.update(old_config)
        except Exception:
            pass

    save_json(CONFIG_FILE, config)
    return config


def save_config_value(key, value):
    config = load_config()
    config[key] = value
    save_json(CONFIG_FILE, config)
    return config


def record_full_event(event_type, content):
    data = safe_load_json(FULL_DATA_FILE, {
        "student_name": "Eric",
        "atlas4_full_version": "Atlas 4.0 Full Main v1",
        "events": []
    })

    if "events" not in data:
        data["events"] = []

    data["events"].append({
        "time": get_now_text(),
        "event_type": event_type,
        "content": content
    })

    save_json(FULL_DATA_FILE, data)


def pause():
    input("\n按回车继续...")


# ============================================================
# Status
# ============================================================

def show_system_status():
    config = load_config()

    lines = []
    lines.append("Atlas 4.0 系统状态")
    lines.append("")
    lines.append(f"Python 文件夹：{BASE_DIR}")
    lines.append(f"Config 文件：{CONFIG_FILE}")
    lines.append(f"Full Data 文件：{FULL_DATA_FILE}")
    lines.append("")
    lines.append("依赖库状态：")
    lines.append(f"- OpenCV / Vision：{'OK' if CV2_AVAILABLE else 'MISSING'}")
    lines.append(f"- Voice Input：{'OK' if VOICE_INPUT_AVAILABLE else 'MISSING'}")
    lines.append(f"- Voice Output / pyttsx3：{'OK' if TTS_AVAILABLE else 'MISSING'}")
    lines.append(f"- Hardware / pyserial：{'OK' if SERIAL_AVAILABLE else 'MISSING'}")
    lines.append("")
    lines.append("当前配置：")
    lines.append(f"- Arduino 串口：{config.get('serial_port')}")
    lines.append(f"- 备用串口：{config.get('backup_serial_ports')}")
    lines.append(f"- 波特率：{config.get('baud_rate')}")
    lines.append(f"- 摄像头编号：{config.get('camera_index')}")
    lines.append(f"- 语音识别采样率：{config.get('voice_input_sample_rate')}")
    lines.append(f"- 默认语音识别语言：{config.get('default_voice_language')}")
    lines.append(f"- TTS 语速：{config.get('tts_rate')}")
    lines.append(f"- TTS 音量：{config.get('tts_volume')}")
    lines.append("")
    lines.append("长期记忆文件检测：")

    for file_path in [
        ATLAS_UNIFIED_DATA_FILE,
        ATLAS_FINAL_DATA_FILE,
        ATLAS_INTEGRATED_DATA_FILE,
        ATLAS3_DATA_FILE,
        PROFILE_FILE,
        SKILLS_FILE,
        HISTORY_FILE,
        LEARNING_PLAN_FILE,
        EMOTION_FILE,
        MENTOR_RECOMMENDATION_FILE,
    ]:
        lines.append(f"- {file_path.name}：{'FOUND' if file_path.exists() else 'not found'}")

    content = "\n".join(lines)

    print("\n" + content)
    write_to_project_log("Atlas 4.0 Full Main 系统状态检查", content)
    record_full_event("system_status", content)


def test_all_logs():
    content = (
        "Atlas 4.0 Full Main 日志写入测试。\n"
        "如果你能看到这些记录，说明所有核心日志文件都可以正常写入。"
    )

    write_to_project_log("Atlas 4.0 Full Main 日志写入测试", content)
    write_to_vision_log(content)
    write_to_voice_input_log(content)
    write_to_voice_output_log(content)
    write_to_memory_log(content)
    write_to_proactive_log(content)
    write_to_hardware_log(content)
    record_full_event("log_test", content)


# ============================================================
# Stage 1: Vision
# ============================================================

def test_camera_once():
    if not CV2_AVAILABLE:
        message = "OpenCV 不可用。请先运行：pip install opencv-python"
        print("\n" + message)
        write_to_vision_log(message)
        return False

    config = load_config()
    camera_index = int(config.get("camera_index", 0))

    print(f"\n正在测试摄像头是否可以打开，camera_index={camera_index} ...")

    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        message = (
            f"摄像头打开失败。当前 camera_index={camera_index}\n"
            "请检查：\n"
            "1. 摄像头是否被其他软件占用\n"
            "2. Windows 是否允许 Cursor / Python 使用摄像头\n"
            "3. 如果是外接 USB 摄像头，请重新插拔\n"
            "4. 可以在配置菜单把 camera_index 改成 1 或 2"
        )
        print(message)
        write_to_vision_log(message)
        write_to_project_log("Atlas 4.0 Vision 摄像头测试失败", message)
        return False

    success, frame = camera.read()
    camera.release()

    if not success:
        message = "摄像头可以打开，但无法读取画面。"
        print(message)
        write_to_vision_log(message)
        write_to_project_log("Atlas 4.0 Vision 摄像头读取失败", message)
        return False

    message = "摄像头测试成功。Atlas 4.0 可以读取摄像头画面。"
    print(message)
    write_to_vision_log(message)
    write_to_project_log("Atlas 4.0 Vision 摄像头测试成功", message)
    return True


def start_vision_detection():
    if not CV2_AVAILABLE:
        message = "OpenCV 不可用。请先运行：pip install opencv-python"
        print("\n" + message)
        write_to_vision_log(message)
        return

    config = load_config()
    camera_index = int(config.get("camera_index", 0))

    print("\n启动 Atlas 4.0 Vision 检测。")
    print("1. 摄像头窗口打开后，请让 Eric 面对摄像头。")
    print("2. 检测到人脸时，会显示 Eric is present。")
    print("3. 没检测到人脸时，会显示 Eric is not present。")
    print("4. 按 q 退出摄像头窗口。")
    print(f"当前 camera_index：{camera_index}")

    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        message = f"摄像头打开失败。当前 camera_index={camera_index}。"
        print(message)
        write_to_vision_log(message)
        write_to_project_log("Atlas 4.0 Vision 启动失败", message)
        return

    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_detector = cv2.CascadeClassifier(face_cascade_path)

    if face_detector.empty():
        message = "OpenCV 人脸检测模型加载失败。"
        print(message)
        write_to_vision_log(message)
        write_to_project_log("Atlas 4.0 Vision 人脸模型加载失败", message)
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
    write_to_project_log("Atlas 4.0 Vision 检测结束", summary)


def set_camera_index():
    current = load_config().get("camera_index", 0)
    print(f"\n当前 camera_index：{current}")
    text = input("请输入新的摄像头编号，例如 0 / 1 / 2：").strip()

    if not text.isdigit():
        print("输入无效。")
        return

    index = int(text)
    save_config_value("camera_index", index)
    print(f"已保存 camera_index：{index}")


# ============================================================
# Stage 2: Voice Input
# ============================================================

def create_default_voice_data():
    return {
        "student_name": "Eric",
        "voice_input_version": "Atlas 4.0 Voice Input v1",
        "voice_records": []
    }


def load_voice_data():
    data = safe_load_json(VOICE_INPUT_DATA_FILE, create_default_voice_data())

    if not isinstance(data, dict):
        data = create_default_voice_data()

    data.setdefault("student_name", "Eric")
    data.setdefault("voice_input_version", "Atlas 4.0 Voice Input v1")
    data.setdefault("voice_records", [])

    save_json(VOICE_INPUT_DATA_FILE, data)
    return data


def save_voice_record(text, language, duration_seconds, status):
    data = load_voice_data()

    record = {
        "time": get_now_text(),
        "language": language,
        "duration_seconds": duration_seconds,
        "recognized_text": text,
        "status": status
    }

    data["voice_records"].append(record)
    save_json(VOICE_INPUT_DATA_FILE, data)
    return record


def list_audio_devices():
    if not VOICE_INPUT_AVAILABLE:
        message = (
            "Voice Input 依赖库不可用。\n"
            "请先运行：pip install numpy sounddevice scipy SpeechRecognition"
        )
        print("\n" + message)
        write_to_voice_input_log(message)
        return

    print("\n当前电脑音频设备：")
    print("-" * 70)

    try:
        devices = sd.query_devices()
        lines = []

        for index, device in enumerate(devices):
            name = device.get("name", "Unknown")
            max_input_channels = device.get("max_input_channels", 0)
            max_output_channels = device.get("max_output_channels", 0)

            line = (
                f"{index}. {name} | "
                f"输入通道：{max_input_channels} | "
                f"输出通道：{max_output_channels}"
            )

            print(line)
            lines.append(line)

        print("-" * 70)

        content = "已成功读取电脑音频设备列表：\n" + "\n".join(lines)
        write_to_voice_input_log(content)
        write_to_project_log("Atlas 4.0 Voice Input 音频设备检测成功", content)

    except Exception as error:
        message = f"音频设备读取失败：{error}"
        print(message)
        write_to_voice_input_log(message)
        write_to_project_log("Atlas 4.0 Voice Input 音频设备检测失败", message)


def record_audio_to_temp_wav(duration_seconds=5, sample_rate=16000):
    if not VOICE_INPUT_AVAILABLE:
        raise RuntimeError("Voice Input 依赖库不可用。请安装 numpy sounddevice scipy SpeechRecognition。")

    print("\n准备开始录音。")
    print(f"请 Eric 对着麦克风说话，录音时长：{duration_seconds} 秒。")
    print("开始录音...")

    try:
        audio_data = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()

    except Exception as error:
        raise RuntimeError(f"录音失败：{error}")

    print("录音结束。")

    audio_data = np.asarray(audio_data)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file_path = temp_file.name
    temp_file.close()

    write_wav(temp_file_path, sample_rate, audio_data)

    return temp_file_path


def recognize_speech_from_wav(wav_path, language):
    if not VOICE_INPUT_AVAILABLE:
        raise RuntimeError("SpeechRecognition 不可用。")

    recognizer = sr.Recognizer()

    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)

    try:
        recognized_text = recognizer.recognize_google(audio, language=language)
        return recognized_text

    except sr.UnknownValueError:
        return ""

    except sr.RequestError as error:
        raise RuntimeError(
            f"语音识别服务连接失败：{error}\n"
            "可能原因：网络不可用，或 Google Speech Recognition 暂时无法访问。"
        )


def record_and_recognize_once():
    if not VOICE_INPUT_AVAILABLE:
        message = (
            "Voice Input 依赖库不可用。\n"
            "请先运行：pip install numpy sounddevice scipy SpeechRecognition"
        )
        print("\n" + message)
        write_to_voice_input_log(message)
        return ""

    print("\n选择识别语言：")
    print("1. English")
    print("2. 中文")
    language_choice = input("请输入 1 或 2：").strip()

    if language_choice == "2":
        language = "zh-CN"
        language_name = "中文"
    else:
        language = "en-US"
        language_name = "English"

    duration_text = input("\n录音几秒？建议 5 秒，直接回车默认 5 秒：").strip()

    if duration_text.isdigit():
        duration_seconds = int(duration_text)
    else:
        duration_seconds = 5

    duration_seconds = max(2, min(15, duration_seconds))
    sample_rate = int(load_config().get("voice_input_sample_rate", 16000))

    try:
        wav_path = record_audio_to_temp_wav(
            duration_seconds=duration_seconds,
            sample_rate=sample_rate
        )
        recognized_text = recognize_speech_from_wav(wav_path, language=language)

        if recognized_text:
            status = "recognized"
            content = (
                f"识别语言：{language_name}\n"
                f"录音时长：{duration_seconds} 秒\n"
                f"识别结果：{recognized_text}"
            )
            print("\nAtlas 听到的内容：")
            print("-" * 70)
            print(recognized_text)
            print("-" * 70)

        else:
            status = "not_recognized"
            content = (
                f"识别语言：{language_name}\n"
                f"录音时长：{duration_seconds} 秒\n"
                "识别结果：没有识别到清楚语音。\n"
                "建议：靠近麦克风，说话慢一点，环境安静一点。"
            )
            print("\n没有识别到清楚语音。")
            print("建议：靠近麦克风，说话慢一点，环境安静一点。")

        save_voice_record(
            text=recognized_text,
            language=language_name,
            duration_seconds=duration_seconds,
            status=status
        )

        write_to_voice_input_log(content)
        write_to_project_log("Atlas 4.0 Voice Input 单次语音识别", content)
        return recognized_text

    except Exception as error:
        message = f"Voice Input 运行失败：{error}"

        print("\n" + message)

        save_voice_record(
            text="",
            language=language_name,
            duration_seconds=duration_seconds,
            status="error"
        )

        write_to_voice_input_log(message)
        write_to_project_log("Atlas 4.0 Voice Input 运行失败", message)
        return ""


def continuous_voice_test():
    print("\n连续语音识别测试。")
    print("每次录音 5 秒。")
    print("输入 q 可以退出连续测试。")

    while True:
        command = input("\n按回车开始一次录音，输入 q 退出：").strip().lower()

        if command == "q":
            print("已退出连续语音识别测试。")
            break

        record_and_recognize_once()


def show_recent_voice_records():
    data = load_voice_data()
    records = data.get("voice_records", [])

    if not records:
        message = "目前还没有语音识别记录。"
        print("\n" + message)
        write_to_voice_input_log(message)
        return

    recent_records = records[-5:]
    lines = []

    print("\n最近 5 条语音识别记录：")
    print("-" * 70)

    for record in recent_records:
        text = (
            f"时间：{record.get('time', '')}\n"
            f"语言：{record.get('language', '')}\n"
            f"录音时长：{record.get('duration_seconds', '')} 秒\n"
            f"状态：{record.get('status', '')}\n"
            f"识别结果：{record.get('recognized_text', '')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    content = "\n\n".join(lines)
    write_to_voice_input_log(content)
    write_to_project_log("Atlas 4.0 Voice Input 查看最近语音记录", content)


def get_latest_voice_input_text():
    data = safe_load_json(VOICE_INPUT_DATA_FILE, {})
    records = data.get("voice_records", [])

    if not records:
        return ""

    for record in reversed(records):
        text = record.get("recognized_text", "")
        status = record.get("status", "")

        if text and status == "recognized":
            return text

    return ""


# ============================================================
# Stage 3: Voice Output
# ============================================================

def create_default_voice_output_data():
    return {
        "student_name": "Eric",
        "voice_output_version": "Atlas 4.0 Voice Output v1",
        "voice_output_records": []
    }


def load_voice_output_data():
    data = safe_load_json(VOICE_OUTPUT_DATA_FILE, create_default_voice_output_data())

    if not isinstance(data, dict):
        data = create_default_voice_output_data()

    data.setdefault("student_name", "Eric")
    data.setdefault("voice_output_version", "Atlas 4.0 Voice Output v1")
    data.setdefault("voice_output_records", [])

    save_json(VOICE_OUTPUT_DATA_FILE, data)
    return data


def save_voice_output_record(text, voice_name, rate, volume, status):
    data = load_voice_output_data()

    record = {
        "time": get_now_text(),
        "text": text,
        "voice_name": voice_name,
        "rate": rate,
        "volume": volume,
        "status": status
    }

    data["voice_output_records"].append(record)
    save_json(VOICE_OUTPUT_DATA_FILE, data)
    return record


def create_tts_engine():
    if not TTS_AVAILABLE:
        raise RuntimeError("pyttsx3 不可用。请先运行：pip install pyttsx3")

    try:
        engine = pyttsx3.init()
        return engine
    except Exception as error:
        raise RuntimeError(f"pyttsx3 初始化失败：{error}")


def list_voices():
    print("\n正在读取电脑可用语音列表...")

    if not TTS_AVAILABLE:
        message = "pyttsx3 不可用。请先运行：pip install pyttsx3"
        print("\n" + message)
        write_to_voice_output_log(message)
        return

    try:
        engine = create_tts_engine()
        voices = engine.getProperty("voices")

        print("\n电脑可用语音：")
        print("-" * 70)

        if not voices:
            print("没有读取到语音。")
            return

        lines = []

        for index, voice in enumerate(voices):
            voice_name = getattr(voice, "name", "Unknown")
            voice_id = getattr(voice, "id", "Unknown")
            languages = getattr(voice, "languages", [])

            text = (
                f"{index}. 语音名称：{voice_name}\n"
                f"   语音 ID：{voice_id}\n"
                f"   languages：{languages}"
            )

            print(text)
            print("-" * 70)
            lines.append(text)

        content = "已成功读取电脑可用语音列表：\n\n" + "\n\n".join(lines)

        write_to_voice_output_log(content)
        write_to_project_log("Atlas 4.0 Voice Output 查看语音列表", content)

    except Exception as error:
        message = f"读取语音列表失败：{error}"
        print("\n" + message)
        write_to_voice_output_log(message)
        write_to_project_log("Atlas 4.0 Voice Output 读取语音列表失败", message)


def speak_text(text, rate=None, volume=None, voice_index=None, log=True):
    if not text:
        text = "Hello Eric. This is Atlas."

    config = load_config()
    if rate is None:
        rate = int(config.get("tts_rate", 160))
    if volume is None:
        volume = float(config.get("tts_volume", 1.0))

    if not TTS_AVAILABLE:
        message = "pyttsx3 不可用，无法语音输出。请运行：pip install pyttsx3"
        print("\n" + message)
        if log:
            write_to_voice_output_log(message)
        return False

    try:
        engine = create_tts_engine()

        voices = engine.getProperty("voices")
        selected_voice_name = "default"

        if voice_index is not None and voices:
            if 0 <= voice_index < len(voices):
                selected_voice = voices[voice_index]
                engine.setProperty("voice", selected_voice.id)
                selected_voice_name = getattr(selected_voice, "name", "selected_voice")
            else:
                selected_voice_name = "default"

        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)

        print("\nAtlas 正在说：")
        print("-" * 70)
        print(text)
        print("-" * 70)

        engine.say(text)
        engine.runAndWait()

        content = (
            f"语音输出成功。\n"
            f"文本：{text}\n"
            f"语音：{selected_voice_name}\n"
            f"语速：{rate}\n"
            f"音量：{volume}"
        )

        save_voice_output_record(
            text=text,
            voice_name=selected_voice_name,
            rate=rate,
            volume=volume,
            status="spoken"
        )

        if log:
            write_to_voice_output_log(content)
            write_to_project_log("Atlas 4.0 Voice Output 语音输出成功", content)

        return True

    except Exception as error:
        message = f"语音输出失败：{error}"
        print("\n" + message)

        save_voice_output_record(
            text=text,
            voice_name="unknown",
            rate=rate,
            volume=volume,
            status="error"
        )

        if log:
            write_to_voice_output_log(message)
            write_to_project_log("Atlas 4.0 Voice Output 语音输出失败", message)

        return False


def test_basic_speech():
    return speak_text("Hello Eric. I am Atlas. I can speak now.")


def test_chinese_speech():
    return speak_text("你好 Eric，我是 Atlas。现在我已经可以说话了。", rate=150)


def custom_speech():
    print("\n自定义语音输出。")
    text = input("请输入想让 Atlas 说的话：").strip()

    if not text:
        text = "Hello Eric. This is Atlas."

    rate_text = input("语速，建议 150 到 180，直接回车默认配置值：").strip()

    if rate_text.isdigit():
        rate = int(rate_text)
    else:
        rate = int(load_config().get("tts_rate", 160))

    rate = max(80, min(260, rate))

    volume_text = input("音量 0.0 到 1.0，直接回车默认配置值：").strip()

    try:
        volume = float(volume_text) if volume_text else float(load_config().get("tts_volume", 1.0))
    except Exception:
        volume = 1.0

    volume = max(0, min(1, volume))

    voice_index_text = input("语音编号，直接回车使用默认语音：").strip()

    if voice_index_text.isdigit():
        voice_index = int(voice_index_text)
    else:
        voice_index = None

    return speak_text(text=text, rate=rate, volume=volume, voice_index=voice_index)


def atlas_greeting():
    text = (
        "Hello Eric. I am Atlas. "
        "I can see you, hear you, and now I can speak to you. "
        "Today, I will help you continue your AI mentor robot project."
    )
    return speak_text(text, rate=160)


def atlas_task_reminder():
    text = (
        "Eric, here is your task reminder. "
        "Do not add too many new features at once. "
        "Test one function, record the result, and then continue."
    )
    return speak_text(text, rate=160)


def atlas_debug_reminder():
    text = (
        "Eric, if you have been debugging for a long time, "
        "take a short break first. "
        "Then come back and test only one small problem."
    )
    return speak_text(text, rate=155)


def show_recent_voice_output_records():
    data = load_voice_output_data()
    records = data.get("voice_output_records", [])

    if not records:
        message = "目前还没有 Voice Output 记录。"
        print("\n" + message)
        write_to_voice_output_log(message)
        return

    recent_records = records[-5:]
    lines = []

    print("\n最近 5 条 Voice Output 记录：")
    print("-" * 70)

    for record in recent_records:
        text = (
            f"时间：{record.get('time', '')}\n"
            f"文本：{record.get('text', '')}\n"
            f"语音：{record.get('voice_name', '')}\n"
            f"语速：{record.get('rate', '')}\n"
            f"音量：{record.get('volume', '')}\n"
            f"状态：{record.get('status', '')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    content = "\n\n".join(lines)
    write_to_voice_output_log(content)
    write_to_project_log("Atlas 4.0 Voice Output 查看最近语音输出记录", content)


# ============================================================
# Stage 4 / 5: Memory shared functions
# ============================================================

def create_default_memory():
    return {
        "student_name": "Eric",
        "profile": {
            "name": "Eric",
            "age": 13,
            "goal": "AI Systems Engineer",
            "current_project": "Atlas",
            "current_version": "Atlas 4.0",
            "learning_style": "喜欢通过项目实战学习，不喜欢重复听很多理论。",
            "interests": ["AI", "Robot", "Python", "Basketball"],
            "strengths": ["Arduino", "Python", "OpenCV", "Project Iteration"],
            "weaknesses": ["ROS2", "Advanced Robot System Design"]
        },
        "skills": {
            "Arduino": {"score": 95, "level": "strong"},
            "Python": {"score": 80, "level": "good"},
            "OpenCV": {"score": 75, "level": "good"},
            "YOLO": {"score": 60, "level": "developing"},
            "ROS2": {"score": 0, "level": "not_started"}
        },
        "project_history": [
            {
                "project_name": "智能植物养护系统",
                "version": "1.0 - 1.1",
                "status": "completed",
                "skills_learned": ["Arduino", "Sensors", "Serial Communication"],
                "transfer_to_atlas": "植物项目训练了硬件控制、传感器和串口通信。"
            },
            {
                "project_name": "Atlas 1.0",
                "version": "1.0",
                "status": "completed",
                "skills_learned": ["Python", "JSON", "OpenCV", "Project Log"],
                "transfer_to_atlas": "Atlas 1.0 建立了记忆、日志、导师建议和摄像头基础。"
            },
            {
                "project_name": "Atlas 2.0",
                "version": "2.0",
                "status": "completed",
                "skills_learned": ["Project Database", "Daily Task", "Bug Manager", "Weekly Report"],
                "transfer_to_atlas": "Atlas 2.0 建立了项目管理、每日任务、Bug 和周报能力。"
            },
            {
                "project_name": "Atlas 3.0",
                "version": "3.0",
                "status": "completed",
                "skills_learned": [
                    "Profile",
                    "Skill Database",
                    "Project History",
                    "Learning Planner",
                    "Emotion Memory",
                    "Mentor Recommendation"
                ],
                "transfer_to_atlas": "Atlas 3.0 建立了 Eric Digital Twin 成长画像。"
            },
            {
                "project_name": "Atlas 4.0",
                "version": "4.0",
                "status": "in_progress",
                "skills_learned": [
                    "Vision",
                    "Voice Input",
                    "Voice Output",
                    "Memory Integration",
                    "Proactive Mentor",
                    "Hardware Feedback"
                ],
                "transfer_to_atlas": "Atlas 4.0 正在把视觉、语音、长期记忆、主动导师和硬件反馈能力整合起来。"
            }
        ],
        "daily_learning_plans": [],
        "emotion_records": [],
        "recommendations": [],
        "daily_tasks": [],
        "bugs": [],
        "weekly_reports": []
    }


def convert_projects_to_history(projects):
    history = []

    for project in projects:
        history.append({
            "project_name": project.get("name", "未命名项目"),
            "version": "unknown",
            "status": project.get("status", "unknown"),
            "skills_learned": [],
            "transfer_to_atlas": project.get("description", "")
        })

    return history


def normalize_memory_data(data):
    default_memory = create_default_memory()

    if not isinstance(data, dict):
        return default_memory

    memory = {
        "student_name": data.get("student_name", "Eric"),
        "profile": data.get("profile", default_memory["profile"]),
        "skills": data.get("skills", default_memory["skills"]),
        "project_history": data.get("project_history", default_memory["project_history"]),
        "daily_learning_plans": data.get("daily_learning_plans", []),
        "emotion_records": data.get("emotion_records", []),
        "recommendations": data.get("recommendations", []),
        "daily_tasks": data.get("daily_tasks", []),
        "bugs": data.get("bugs", []),
        "weekly_reports": data.get("weekly_reports", [])
    }

    if not memory["project_history"] and isinstance(data.get("projects"), list):
        memory["project_history"] = convert_projects_to_history(data["projects"])

    return memory


def load_memory():
    candidate_files = [
        ATLAS_UNIFIED_DATA_FILE,
        ATLAS_FINAL_DATA_FILE,
        ATLAS_INTEGRATED_DATA_FILE,
        ATLAS3_DATA_FILE
    ]

    for file_path in candidate_files:
        if file_path.exists():
            data = safe_load_json(file_path, {})
            memory = normalize_memory_data(data)
            return memory, file_path.name

    profile = safe_load_json(PROFILE_FILE, {})
    skills_data = safe_load_json(SKILLS_FILE, {})
    history_data = safe_load_json(HISTORY_FILE, {})
    learning_plan_data = safe_load_json(LEARNING_PLAN_FILE, {})
    emotion_data = safe_load_json(EMOTION_FILE, {})
    recommendation_data = safe_load_json(MENTOR_RECOMMENDATION_FILE, {})

    if profile or skills_data or history_data:
        memory = create_default_memory()

        if profile:
            memory["profile"] = profile

        if isinstance(skills_data.get("skills"), dict):
            memory["skills"] = skills_data["skills"]

        if isinstance(history_data.get("project_history"), list):
            memory["project_history"] = history_data["project_history"]

        if isinstance(learning_plan_data.get("daily_learning_plans"), list):
            memory["daily_learning_plans"] = learning_plan_data["daily_learning_plans"]

        if isinstance(emotion_data.get("emotion_records"), list):
            memory["emotion_records"] = emotion_data["emotion_records"]

        if isinstance(recommendation_data.get("recommendations"), list):
            memory["recommendations"] = recommendation_data["recommendations"]

        return memory, "Atlas 3.0 separated JSON files"

    return create_default_memory(), "default memory"


def get_skill_score(memory, skill_name):
    skill = memory.get("skills", {}).get(skill_name)

    if not isinstance(skill, dict):
        return None

    return skill.get("score", None)


def format_profile_summary(memory):
    profile = memory.get("profile", {})

    interests = profile.get("interests", [])
    strengths = profile.get("strengths", [])
    weaknesses = profile.get("weaknesses", [])

    interests_text = "、".join(interests) if interests else "暂无"
    strengths_text = "、".join(strengths) if strengths else "暂无"
    weaknesses_text = "、".join(weaknesses) if weaknesses else "暂无"

    return (
        f"Eric 的当前成长画像：\n"
        f"- 年龄：{profile.get('age', 13)}\n"
        f"- 长期目标：{profile.get('goal', 'AI Systems Engineer')}\n"
        f"- 当前项目：{profile.get('current_project', 'Atlas')}\n"
        f"- 当前版本：{profile.get('current_version', 'Atlas 4.0')}\n"
        f"- 兴趣：{interests_text}\n"
        f"- 强项：{strengths_text}\n"
        f"- 需要补强：{weaknesses_text}\n"
        f"- 学习风格：{profile.get('learning_style', '喜欢通过项目实战学习')}"
    )


def format_skill_summary(memory):
    skills = memory.get("skills", {})
    lines = ["Eric 的技能状态："]

    for skill_name, skill_info in skills.items():
        if isinstance(skill_info, dict):
            lines.append(
                f"- {skill_name}：{skill_info.get('score', 0)} 分，level：{skill_info.get('level', 'unknown')}"
            )
        else:
            lines.append(f"- {skill_name}：{skill_info}")

    return "\n".join(lines)


def format_project_history_summary(memory):
    history = memory.get("project_history", [])

    if not history:
        return "目前没有 Project History。"

    lines = ["Eric 的项目历史："]

    for project in history:
        project_name = project.get("project_name", "未命名项目")
        version = project.get("version", "unknown")
        status = project.get("status", "unknown")
        skills = project.get("skills_learned", [])
        transfer = project.get("transfer_to_atlas", "")

        skills_text = "、".join(skills) if skills else "暂无技能记录"

        lines.append(
            f"- {project_name} ({version}) | 状态：{status} | 学到：{skills_text}"
        )

        if transfer:
            lines.append(f"  迁移价值：{transfer}")

    return "\n".join(lines)


def get_latest_learning_plan_text(memory):
    plans = memory.get("daily_learning_plans", [])

    if not plans:
        return "目前没有 Learning Plan 记录。"

    latest = plans[-1]

    return (
        f"最近一次 Learning Plan：\n"
        f"- 日期：{latest.get('date', '')}\n"
        f"- 今日重点：{latest.get('today_focus', '')}\n"
        f"- 原因：{latest.get('reason', '')}\n"
        f"- 任务 1：{latest.get('task_1', '')}\n"
        f"- 任务 2：{latest.get('task_2', '')}\n"
        f"- 任务 3：{latest.get('task_3', '')}\n"
        f"- 状态：{latest.get('status', '')}"
    )


def get_latest_emotion_text(memory):
    records = memory.get("emotion_records", [])

    if not records:
        return "目前没有 Emotion Memory 记录。"

    latest = records[-1]

    return (
        f"最近一次研发状态：\n"
        f"- 状态：{latest.get('feeling', '')}\n"
        f"- 连续调试时间：{latest.get('debug_hours', 0)} 小时\n"
        f"- 问题：{latest.get('problem', '')}\n"
        f"- 下一步：{latest.get('next_step', '')}"
    )


def answer_question_with_memory(question, memory):
    question_lower = question.lower()

    skills = memory.get("skills", {})

    ros2_score = skills.get("ROS2", {}).get("score", None) if isinstance(skills.get("ROS2"), dict) else None
    arduino_score = skills.get("Arduino", {}).get("score", None) if isinstance(skills.get("Arduino"), dict) else None
    python_score = skills.get("Python", {}).get("score", None) if isinstance(skills.get("Python"), dict) else None
    opencv_score = skills.get("OpenCV", {}).get("score", None) if isinstance(skills.get("OpenCV"), dict) else None

    if (
        "下一步" in question
        or "今天" in question
        or "学什么" in question
        or "next" in question_lower
        or "today" in question_lower
        or "what should i do" in question_lower
    ):
        if ros2_score is not None and ros2_score < 40:
            return (
                "Eric，根据你的长期记忆，我建议你下一步继续补 ROS2。\n\n"
                f"原因是：Arduino 当前约 {arduino_score} 分，Python 当前约 {python_score} 分，OpenCV 当前约 {opencv_score} 分，"
                f"但 ROS2 目前只有 {ros2_score} 分。\n\n"
                "如果你未来要做真正的机器人系统，ROS2 是必须补上的能力。"
            )

        return (
            "Eric，根据你的长期记忆，下一步建议继续推进 Atlas 4.0 的多模态整合。\n"
            "现在你已经完成 Vision、Voice Input、Voice Output、Memory Integration、Proactive Mentor，当前重点是 Hardware Feedback 和总集成。"
        )

    if "ros" in question_lower or "ros2" in question_lower:
        return (
            f"Eric，你现在需要关注 ROS2。\n\n"
            f"你的 ROS2 当前分数是 {ros2_score}。\n"
            "你的 Arduino、Python、OpenCV 已经有基础，所以你不需要继续重复基础 Arduino。\n"
            "如果未来要做真正的机器人系统，ROS2 是下一阶段必须补上的能力。"
        )

    if "arduino" in question_lower:
        return (
            f"Eric，你的 Arduino 当前分数是 {arduino_score}。\n\n"
            "这已经是你的强项。你可以继续用 Arduino 做硬件反馈，"
            "但不建议继续停留在基础 Arduino。下一步更应该进入 ROS2、视觉、语音和系统整合。"
        )

    if "3.0" in question or "atlas 3" in question_lower:
        return (
            "Eric，Atlas 3.0 的核心成果是 Eric Digital Twin。\n\n"
            "它包括 Profile、Skill Database、Project History、Learning Planner、Emotion Memory 和 Mentor Recommendation。\n"
            "这些长期记忆现在会成为 Atlas 4.0 Memory Integration 的基础。"
        )

    if "4.0" in question or "atlas 4" in question_lower:
        return (
            "Eric，Atlas 4.0 的目标是把 Atlas 从记忆和规划助手升级为多模态导师。\n\n"
            "它包含 Vision、Voice Input、Voice Output、Memory Integration、Proactive Mentor 和 Hardware Feedback。"
        )

    if "植物" in question or "plant" in question_lower:
        return (
            "Eric，你的智能植物养护系统不是孤立项目。\n\n"
            "它训练了 Arduino、传感器、硬件接线和项目迭代能力。"
            "这些能力后来迁移到了 Atlas 的硬件反馈、摄像头检测和多模态系统设计里。"
        )

    if "历史" in question or "project history" in question_lower or "past project" in question_lower:
        return format_project_history_summary(memory)

    if "技能" in question or "skill" in question_lower:
        return format_skill_summary(memory)

    if "画像" in question or "profile" in question_lower or "who am i" in question_lower:
        return format_profile_summary(memory)

    if "计划" in question or "learning plan" in question_lower:
        return get_latest_learning_plan_text(memory)

    if "debug" in question_lower or "调试" in question or "累" in question or "卡住" in question:
        emotion_text = get_latest_emotion_text(memory)

        return (
            f"{emotion_text}\n\n"
            "如果你已经连续调试很久，Atlas 建议先休息 15 到 20 分钟，"
            "然后回来只测试一个最小问题。"
        )

    return (
        f"Eric，我已经读取了你的长期记忆。\n\n"
        f"{format_profile_summary(memory)}\n\n"
        "你可以继续问：\n"
        "1. 我下一步应该做什么？\n"
        "2. 为什么要学 ROS2？\n"
        "3. 我的项目历史是什么？\n"
        "4. 我现在的技能状态是什么？"
    )


# ============================================================
# Stage 4: Memory Integration
# ============================================================

def create_default_memory_integration_data():
    return {
        "student_name": "Eric",
        "memory_integration_version": "Atlas 4.0 Memory Integration v1",
        "memory_interactions": []
    }


def load_memory_integration_data():
    data = safe_load_json(MEMORY_INTEGRATION_DATA_FILE, create_default_memory_integration_data())

    if not isinstance(data, dict):
        data = create_default_memory_integration_data()

    data.setdefault("student_name", "Eric")
    data.setdefault("memory_integration_version", "Atlas 4.0 Memory Integration v1")
    data.setdefault("memory_interactions", [])

    save_json(MEMORY_INTEGRATION_DATA_FILE, data)
    return data


def save_memory_interaction(question, answer, source):
    data = load_memory_integration_data()

    record = {
        "time": get_now_text(),
        "question": question,
        "answer": answer,
        "source": source
    }

    data["memory_interactions"].append(record)
    save_json(MEMORY_INTEGRATION_DATA_FILE, data)

    return record


def show_memory_source():
    memory, source = load_memory()

    content = (
        f"Atlas 4.0 当前读取到的长期记忆来源：{source}\n\n"
        f"{format_profile_summary(memory)}\n\n"
        f"{format_skill_summary(memory)}\n\n"
        f"Project History 数量：{len(memory.get('project_history', []))} 个\n"
        f"Learning Plan 数量：{len(memory.get('daily_learning_plans', []))} 条\n"
        f"Emotion Memory 数量：{len(memory.get('emotion_records', []))} 条\n"
        f"Mentor Recommendation 数量：{len(memory.get('recommendations', []))} 条\n"
        f"Daily Task 数量：{len(memory.get('daily_tasks', []))} 条\n"
        f"Bug 数量：{len(memory.get('bugs', []))} 条"
    )

    print("\n长期记忆来源检测结果：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_memory_log(content)
    write_to_project_log("Atlas 4.0 Memory Integration 检测长期记忆来源", content)
    record_full_event("memory_source", content)


def answer_latest_voice_input():
    memory, source = load_memory()
    question = get_latest_voice_input_text()

    if not question:
        message = (
            "没有找到最近一次有效语音识别文本。\n"
            "请先录音并成功识别一句话；或者手动输入问题测试 Memory Integration。"
        )

        print("\n" + message)
        write_to_memory_log(message)
        write_to_project_log("Atlas 4.0 Memory Integration 读取语音失败", message)
        return ""

    answer = answer_question_with_memory(question, memory)

    content = (
        f"长期记忆来源：{source}\n\n"
        f"Eric 最近语音问题：\n{question}\n\n"
        f"Atlas 基于长期记忆的回答：\n{answer}"
    )

    save_memory_interaction(
        question=question,
        answer=answer,
        source="latest voice input + " + source
    )

    print("\nAtlas 读取最近语音，并根据长期记忆回答：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_memory_log(content)
    write_to_project_log("Atlas 4.0 Memory Integration 语音问题记忆回答", content)
    record_full_event("memory_answer_latest_voice", content)

    return answer


def answer_manual_question():
    memory, source = load_memory()

    question = input("\n请输入 Eric 的问题，例如：我下一步应该做什么？").strip()

    if not question:
        question = "我下一步应该做什么？"

    answer = answer_question_with_memory(question, memory)

    content = (
        f"长期记忆来源：{source}\n\n"
        f"Eric 手动输入问题：\n{question}\n\n"
        f"Atlas 基于长期记忆的回答：\n{answer}"
    )

    save_memory_interaction(
        question=question,
        answer=answer,
        source="manual input + " + source
    )

    print("\nAtlas 基于长期记忆的回答：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_memory_log(content)
    write_to_project_log("Atlas 4.0 Memory Integration 手动问题记忆回答", content)
    record_full_event("memory_answer_manual", content)

    return answer


def answer_question_direct(question, source_label="direct input"):
    memory, source = load_memory()
    answer = answer_question_with_memory(question, memory)

    save_memory_interaction(
        question=question,
        answer=answer,
        source=source_label + " + " + source
    )

    content = (
        f"长期记忆来源：{source}\n\n"
        f"问题：\n{question}\n\n"
        f"回答：\n{answer}"
    )

    write_to_memory_log(content)
    write_to_project_log("Atlas 4.0 Memory Integration 直接问答", content)
    record_full_event("memory_answer_direct", content)

    return answer


def show_recent_memory_interactions():
    data = load_memory_integration_data()
    records = data.get("memory_interactions", [])

    if not records:
        message = "目前还没有 Memory Integration 问答记录。"
        print("\n" + message)
        write_to_memory_log(message)
        return

    recent_records = records[-5:]
    lines = []

    print("\n最近 5 条 Memory Integration 问答记录：")
    print("-" * 70)

    for record in recent_records:
        text = (
            f"时间：{record.get('time', '')}\n"
            f"来源：{record.get('source', '')}\n"
            f"问题：{record.get('question', '')}\n"
            f"回答：{record.get('answer', '')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    content = "\n\n".join(lines)
    write_to_memory_log(content)
    write_to_project_log("Atlas 4.0 Memory Integration 查看最近问答记录", content)


# ============================================================
# Stage 5: Proactive Mentor
# ============================================================

def create_default_proactive_data():
    return {
        "student_name": "Eric",
        "proactive_mentor_version": "Atlas 4.0 Proactive Mentor v1",
        "proactive_records": []
    }


def load_proactive_data():
    data = safe_load_json(PROACTIVE_MENTOR_DATA_FILE, create_default_proactive_data())

    if not isinstance(data, dict):
        data = create_default_proactive_data()

    data.setdefault("student_name", "Eric")
    data.setdefault("proactive_mentor_version", "Atlas 4.0 Proactive Mentor v1")
    data.setdefault("proactive_records", [])

    save_json(PROACTIVE_MENTOR_DATA_FILE, data)
    return data


def save_proactive_record(record_type, content, source):
    data = load_proactive_data()

    record = {
        "time": get_now_text(),
        "record_type": record_type,
        "content": content,
        "source": source
    }

    data["proactive_records"].append(record)
    save_json(PROACTIVE_MENTOR_DATA_FILE, data)

    return record


def get_project_log_yesterday_summary():
    yesterday = get_yesterday_text()

    if not PROJECT_LOG_FILE.exists():
        return "没有找到 project_log.txt。"

    try:
        text = PROJECT_LOG_FILE.read_text(encoding="utf-8")
    except Exception:
        return "project_log.txt 读取失败。"

    blocks = text.split("=" * 70)
    matched_blocks = []

    for block in blocks:
        if yesterday in block:
            clean_block = block.strip()
            if clean_block:
                matched_blocks.append(clean_block)

    if not matched_blocks:
        return f"没有在 project_log.txt 中找到 {yesterday} 的明确记录。"

    recent_blocks = matched_blocks[-3:]
    lines = [f"从 project_log.txt 找到 {yesterday} 的记录："]

    for index, block in enumerate(recent_blocks, start=1):
        short_block = block.replace("\n\n", "\n")
        if len(short_block) > 600:
            short_block = short_block[:600] + "..."
        lines.append(f"\n记录 {index}：\n{short_block}")

    return "\n".join(lines)


def get_yesterday_learning_plan_summary(memory):
    yesterday = get_yesterday_text()
    plans = memory.get("daily_learning_plans", [])

    matched = []

    for plan in plans:
        if plan.get("date") == yesterday:
            matched.append(plan)

    if not matched:
        return f"没有找到 {yesterday} 的 Learning Plan。"

    latest = matched[-1]

    return (
        f"昨天 Learning Plan：\n"
        f"- 日期：{latest.get('date', '')}\n"
        f"- 重点：{latest.get('today_focus', '')}\n"
        f"- 原因：{latest.get('reason', '')}\n"
        f"- 状态：{latest.get('status', '')}\n"
        f"- 复盘：{latest.get('evening_review', '') if latest.get('evening_review') else '暂无'}"
    )


def get_yesterday_emotion_summary(memory):
    yesterday = get_yesterday_text()
    records = memory.get("emotion_records", [])

    matched = []

    for record in records:
        if record.get("date") == yesterday:
            matched.append(record)

    if not matched:
        return f"没有找到 {yesterday} 的 Emotion Memory。"

    latest = matched[-1]

    return (
        f"昨天研发状态：\n"
        f"- 状态：{latest.get('feeling', '')}\n"
        f"- 连续调试：{latest.get('debug_hours', 0)} 小时\n"
        f"- 问题：{latest.get('problem', '')}\n"
        f"- 下一步：{latest.get('next_step', '')}"
    )


def summarize_yesterday(memory):
    lines = []
    lines.append("昨天工作总结")
    lines.append("")
    lines.append(get_yesterday_learning_plan_summary(memory))
    lines.append("")
    lines.append(get_yesterday_emotion_summary(memory))
    lines.append("")
    lines.append(get_project_log_yesterday_summary())

    return "\n".join(lines)


def decide_today_task(memory):
    profile = memory.get("profile", {})
    current_version = profile.get("current_version", "Atlas 4.0")

    ros2_score = get_skill_score(memory, "ROS2")
    yolo_score = get_skill_score(memory, "YOLO")
    python_score = get_skill_score(memory, "Python")

    if "4.0" in current_version or "Atlas 4.0" in current_version:
        return {
            "focus": "Atlas 4.0 Full Integration",
            "reason": "Vision、Voice Input、Voice Output、Memory Integration、Proactive Mentor 和 Hardware Feedback 已经分阶段建立，现在应该让它们进入同一个主程序并测试完整链路。",
            "task_1": "运行 atlas4_full_main.py。",
            "task_2": "先测试系统状态、摄像头、语音输出和硬件 PING。",
            "task_3": "最后测试 Voice → Memory → Voice Output → Hardware Feedback 完整链路。",
            "estimated_time": "1.5 到 2 小时"
        }

    if ros2_score is not None and ros2_score < 40:
        return {
            "focus": "ROS2",
            "reason": "Arduino、Python、OpenCV 已经有基础，但 ROS2 仍然是短板。",
            "task_1": "复习 ROS2 Node、Topic、Message。",
            "task_2": "整理一页 ROS2 学习笔记。",
            "task_3": "把 ROS2 学习计划写入 Project Log。",
            "estimated_time": "2 小时"
        }

    if yolo_score is not None and yolo_score < 80:
        return {
            "focus": "YOLO",
            "reason": "OpenCV 已经有基础，但 YOLO 还需要继续提高。",
            "task_1": "复习 YOLO 基本用途。",
            "task_2": "准备一个图像识别测试素材。",
            "task_3": "记录 YOLO 和 OpenCV 的区别。",
            "estimated_time": "2 小时"
        }

    if python_score is not None and python_score < 90:
        return {
            "focus": "Python Engineering",
            "reason": "Atlas 项目越来越大，需要更强的 Python 工程化能力。",
            "task_1": "整理当前代码文件清单。",
            "task_2": "画出 Vision、Voice、Memory 的模块关系。",
            "task_3": "准备后续整合版主程序。",
            "estimated_time": "2 小时"
        }

    return {
        "focus": "Atlas 4.0 Integration",
        "reason": "当前基础功能较完整，可以开始整合 Atlas 4.0 的视觉、语音和记忆系统。",
        "task_1": "检查 Stage 1 到 Stage 6 的日志。",
        "task_2": "确认每个阶段都能单独运行。",
        "task_3": "准备运行 Full Demo。",
        "estimated_time": "2 小时"
    }


def check_inactive_tasks(memory, inactive_days=3):
    today = date.today()
    warnings = []

    plans = memory.get("daily_learning_plans", [])
    tasks = memory.get("daily_tasks", [])

    for plan in plans:
        plan_date = parse_date(plan.get("date", ""))

        if plan_date is None:
            continue

        age = (today - plan_date).days
        status = plan.get("status", "")

        if age >= inactive_days and status not in ["完成", "completed", "done"]:
            warnings.append(
                f"Learning Plan 已经 {age} 天没有完成闭环："
                f"{plan.get('today_focus', '未知重点')} | 状态：{status}"
            )

    for task in tasks:
        task_date = parse_date(task.get("date", ""))

        if task_date is None:
            continue

        age = (today - task_date).days
        status = task.get("status", "")

        if age >= inactive_days and status not in ["完成", "completed", "done"]:
            warnings.append(
                f"Daily Task 已经 {age} 天没有完成闭环："
                f"{task.get('today_plan', '未知任务')} | 状态：{status}"
            )

    if not warnings:
        return "目前没有发现超过 3 天未推进的任务。"

    lines = []
    lines.append("长期未推进任务提醒：")

    for warning in warnings:
        lines.append(f"- {warning}")

    lines.append("")
    lines.append("建议：今天不要新增太多功能，先关闭一个旧任务或补一次复盘。")

    return "\n".join(lines)


def generate_morning_brief(memory, source):
    profile = memory.get("profile", {})
    today_task = decide_today_task(memory)
    yesterday_summary = summarize_yesterday(memory)
    inactive_warning = check_inactive_tasks(memory)

    name = profile.get("name", "Eric")
    goal = profile.get("goal", "AI Systems Engineer")
    current_project = profile.get("current_project", "Atlas")
    current_version = profile.get("current_version", "Atlas 4.0")

    lines = []

    lines.append(f"Good morning, {name}.")
    lines.append("")
    lines.append("I am Atlas 4.0 Proactive Mentor.")
    lines.append("")
    lines.append("一、当前项目状态")
    lines.append(f"- 长期目标：{goal}")
    lines.append(f"- 当前项目：{current_project}")
    lines.append(f"- 当前版本：{current_version}")
    lines.append(f"- 记忆来源：{source}")
    lines.append("")
    lines.append("二、昨天总结")
    lines.append(yesterday_summary)
    lines.append("")
    lines.append("三、今天建议")
    lines.append(f"- 今日重点：{today_task['focus']}")
    lines.append(f"- 原因：{today_task['reason']}")
    lines.append(f"- 任务 1：{today_task['task_1']}")
    lines.append(f"- 任务 2：{today_task['task_2']}")
    lines.append(f"- 任务 3：{today_task['task_3']}")
    lines.append(f"- 预计时间：{today_task['estimated_time']}")
    lines.append("")
    lines.append("四、未推进任务提醒")
    lines.append(inactive_warning)
    lines.append("")
    lines.append("五、Atlas 主动导师提醒")
    lines.append("今天不要同时扩大太多功能。先完成一个最小测试，再写入 Project Log。")

    return "\n".join(lines)


def build_short_speech(memory):
    profile = memory.get("profile", {})
    today_task = decide_today_task(memory)
    inactive_warning = check_inactive_tasks(memory)

    name = profile.get("name", "Eric")
    focus = today_task["focus"]

    if "没有发现超过 3 天未推进" in inactive_warning:
        warning_sentence = "I do not see any task inactive for more than three days."
    else:
        warning_sentence = "Some tasks may have been inactive. Please check the warning list."

    return (
        f"Good morning, {name}. "
        f"This is Atlas 4.0 Proactive Mentor. "
        f"Today I suggest you focus on {focus}. "
        f"The reason is: {today_task['reason']} "
        f"Your first task is: {today_task['task_1']} "
        f"{warning_sentence} "
        f"Please finish one small test first, then update the project log."
    )


def generate_and_show_morning_brief():
    memory, source = load_memory()
    brief = generate_morning_brief(memory, source)

    save_proactive_record(
        record_type="morning_brief",
        content=brief,
        source=source
    )

    print("\nAtlas 4.0 Proactive Morning Brief：")
    print("-" * 70)
    print(brief)
    print("-" * 70)

    write_to_proactive_log(brief)
    write_to_project_log("Atlas 4.0 Proactive Mentor 生成 Morning Brief", brief)
    record_full_event("morning_brief", brief)

    return brief


def generate_and_speak_morning_brief():
    memory, source = load_memory()
    brief = generate_morning_brief(memory, source)
    short_speech = build_short_speech(memory)

    spoken = speak_text(short_speech, rate=155)
    status = "spoken" if spoken else "text_only"

    content = (
        f"语音状态：{status}\n\n"
        f"语音简版内容：\n{short_speech}\n\n"
        f"完整 Morning Brief：\n{brief}"
    )

    save_proactive_record(
        record_type="spoken_morning_brief",
        content=content,
        source=source
    )

    print("\nAtlas 4.0 Proactive Mentor 已生成语音版 Morning Brief：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_proactive_log(content)
    write_to_project_log("Atlas 4.0 Proactive Mentor 语音 Morning Brief", content)
    record_full_event("spoken_morning_brief", content)

    return brief


def show_yesterday_summary():
    memory, source = load_memory()
    content = summarize_yesterday(memory)

    print("\n昨天工作总结：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    save_proactive_record("yesterday_summary", content, source)
    write_to_proactive_log(content)
    write_to_project_log("Atlas 4.0 Proactive Mentor 昨天总结", content)


def show_today_task():
    memory, source = load_memory()
    task = decide_today_task(memory)

    content = (
        f"今天建议任务：\n"
        f"- 今日重点：{task['focus']}\n"
        f"- 原因：{task['reason']}\n"
        f"- 任务 1：{task['task_1']}\n"
        f"- 任务 2：{task['task_2']}\n"
        f"- 任务 3：{task['task_3']}\n"
        f"- 预计时间：{task['estimated_time']}"
    )

    print("\n今天建议任务：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    save_proactive_record("today_task", content, source)
    write_to_proactive_log(content)
    write_to_project_log("Atlas 4.0 Proactive Mentor 今日任务建议", content)


def show_inactive_task_warning():
    memory, source = load_memory()
    content = check_inactive_tasks(memory)

    print("\n未推进任务提醒：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    save_proactive_record("inactive_task_warning", content, source)
    write_to_proactive_log(content)
    write_to_project_log("Atlas 4.0 Proactive Mentor 未推进任务提醒", content)


def show_recent_proactive_records():
    data = load_proactive_data()
    records = data.get("proactive_records", [])

    if not records:
        message = "目前还没有 Proactive Mentor 记录。"
        print("\n" + message)
        write_to_proactive_log(message)
        return

    recent_records = records[-5:]
    lines = []

    print("\n最近 5 条 Proactive Mentor 记录：")
    print("-" * 70)

    for record in recent_records:
        text = (
            f"时间：{record.get('time', '')}\n"
            f"类型：{record.get('record_type', '')}\n"
            f"来源：{record.get('source', '')}\n"
            f"内容：\n{record.get('content', '')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    content = "\n\n".join(lines)
    write_to_proactive_log(content)
    write_to_project_log("Atlas 4.0 Proactive Mentor 查看最近记录", content)


# ============================================================
# Stage 6: Hardware Feedback
# ============================================================

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
        write_to_project_log("Atlas 4.0 Hardware Feedback 串口检测", message)
        return []

    lines = ["当前检测到的串口设备："]

    print("\n当前检测到的串口设备：")
    print("-" * 70)

    for index, port in enumerate(ports):
        line = f"{index}. 端口：{port.device} | 名称：{port.description}"
        print(line)
        lines.append(line)

    print("-" * 70)

    content = "\n".join(lines)

    write_to_hardware_log(content)
    write_to_project_log("Atlas 4.0 Hardware Feedback 串口设备列表", content)

    return ports


def build_candidate_ports(preferred_port=None):
    ports = get_serial_ports()
    detected_ports = [port.device for port in ports]
    config = load_config()

    candidates = []

    if preferred_port:
        candidates.append(preferred_port)

    configured_port = config.get("serial_port", "")
    if configured_port:
        candidates.append(configured_port)

    for backup in config.get("backup_serial_ports", []):
        candidates.append(backup)

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
        return "这个 COM 端口不存在或已经变化。请先查看串口设备列表。"

    if "ClearCommError" in error_text or "GetOverlappedResult" in error_text:
        return "Windows 串口状态异常。建议拔掉 Arduino，等待 3 秒后重新插入，再运行程序。"

    return "未知串口错误。请检查 Arduino 是否插入、端口是否正确、是否被其他程序占用。"


def open_port(port_name):
    config = load_config()
    baud_rate = int(config.get("baud_rate", 9600))

    arduino = serial.Serial(
        port=port_name,
        baudrate=baud_rate,
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
        write_to_project_log("Atlas 4.0 Hardware Feedback Arduino 连接失败", message)
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
            # 必须等待，否则 Python 可能在 Arduino 未准备好时就发指令。
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

                save_config_value("serial_port", port_name)

                write_to_hardware_log(
                    message + "\n\nArduino 返回内容：\n" + "\n".join(all_lines)
                )

                write_to_project_log("Atlas 4.0 Hardware Feedback Arduino 连接成功", message)
                record_full_event("hardware_connected", message)

                return arduino, port_name

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
        "5. 重新运行本程序，先查看串口，再自动连接\n"
    )

    print("\n" + final_message)

    write_to_hardware_log(final_message)
    write_to_project_log("Atlas 4.0 Hardware Feedback Arduino 自动连接失败", final_message)
    record_full_event("hardware_connection_failed", final_message)

    return None, None


def close_arduino(arduino):
    if arduino is not None:
        try:
            arduino.close()
            print("\nArduino 连接已关闭。")
        except Exception:
            pass


def send_hardware_command(arduino, command):
    command = command.strip().upper()

    if command not in VALID_HARDWARE_COMMANDS:
        message = (
            f"无效指令：{command}\n"
            f"可用指令：{', '.join(VALID_HARDWARE_COMMANDS)}"
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

        result = "成功" if success else "未确认成功"

        message = (
            f"已发送硬件指令：{command}\n"
            f"执行结果：{result}\n"
            f"期望返回：{expected_tokens}\n"
            "Arduino 返回内容：\n"
            + ("\n".join(response_lines) if response_lines else "无返回")
        )

        print("\n" + message)

        write_to_hardware_log(message)
        write_to_project_log("Atlas 4.0 Hardware Feedback 发送指令", message)
        record_full_event("hardware_command", message)

        return success

    except Exception as error:
        message = (
            f"发送指令失败：{error}\n"
            f"判断：{explain_serial_error(error)}"
        )

        print("\n" + message)

        write_to_hardware_log(message)
        write_to_project_log("Atlas 4.0 Hardware Feedback 发送指令失败", message)
        record_full_event("hardware_command_failed", message)

        return False


def connect_send_close(command):
    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is None:
            return False

        return send_hardware_command(arduino, command)

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
    save_config_value("serial_port", selected_port)

    message = f"已手动设置 Arduino 串口：{selected_port}"
    print("\n" + message)

    write_to_hardware_log(message)
    write_to_project_log("Atlas 4.0 Hardware Feedback 手动设置串口", message)


def test_single_hardware_command():
    print("\n单个指令测试。")
    print(f"可用指令：{', '.join(VALID_HARDWARE_COMMANDS)}")
    print("建议先测试：PING")
    print("然后测试：STATUS")
    print("最后测试：HAPPY / THINKING / WARNING / NOD / OFF")

    command = input("\n请输入要发送的指令：").strip().upper()

    if command not in VALID_HARDWARE_COMMANDS:
        print("指令无效。")
        return

    connect_send_close(command)


def run_basic_hardware_feedback_test():
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

            send_hardware_command(arduino, command)
            time.sleep(0.8)

        content = (
            "基础硬件反馈测试完成。\n"
            "已测试：\n"
            + "\n".join(lines)
        )

        write_to_hardware_log(content)
        write_to_project_log("Atlas 4.0 Hardware Feedback 基础测试完成", content)

    finally:
        close_arduino(arduino)


def run_full_hardware_test():
    print("\n开始 Arduino 全硬件 TEST。")
    print("将发送 TEST，让 Arduino 自动测试绿灯、黄灯、红灯、舵机、OLED。")
    connect_send_close("TEST")


def run_atlas_scene_hardware_test():
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

            send_hardware_command(arduino, command)
            time.sleep(1.0)

        content = "Atlas 4.0 场景反馈测试完成。\n\n" + "\n".join(lines)

        write_to_hardware_log(content)
        write_to_project_log("Atlas 4.0 Hardware Feedback 场景测试完成", content)

    finally:
        close_arduino(arduino)


# ============================================================
# Integrated demos
# ============================================================

def run_morning_brief_with_voice_and_hardware():
    print("\n开始完整 Demo：Morning Brief + Voice Output + Hardware Feedback")
    print("流程：Hardware THINKING → 生成 Morning Brief → 语音播放 → Hardware HAPPY + NOD → OFF")

    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is not None:
            send_hardware_command(arduino, "THINKING")

        memory, source = load_memory()
        brief = generate_morning_brief(memory, source)
        short_speech = build_short_speech(memory)

        save_proactive_record("full_demo_morning_brief", brief, source)

        print("\n完整 Morning Brief：")
        print("-" * 70)
        print(brief)
        print("-" * 70)

        spoken = speak_text(short_speech, rate=155)

        if arduino is not None:
            if spoken:
                send_hardware_command(arduino, "HAPPY")
                send_hardware_command(arduino, "NOD")
            else:
                send_hardware_command(arduino, "WARNING")

            send_hardware_command(arduino, "OFF")

        content = (
            f"完整 Demo 完成。\n"
            f"记忆来源：{source}\n"
            f"语音状态：{'spoken' if spoken else 'text_only'}\n\n"
            f"Morning Brief：\n{brief}"
        )

        write_to_proactive_log(content)
        write_to_project_log("Atlas 4.0 Full Demo：Morning Brief + Voice + Hardware", content)
        record_full_event("full_demo_morning_brief_voice_hardware", content)

    finally:
        close_arduino(arduino)


def run_voice_memory_voice_hardware_chain():
    print("\n开始完整链路 Demo：Voice Input → Memory Integration → Voice Output → Hardware Feedback")
    print("流程：录音 → 转文字 → 长期记忆回答 → 语音输出 → Arduino 硬件反馈")

    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is not None:
            send_hardware_command(arduino, "THINKING")

        question = record_and_recognize_once()

        if not question:
            print("\n没有得到有效语音文本，改为手动输入问题。")
            question = input("请输入 Eric 的问题，例如：我下一步应该做什么？").strip()

        if not question:
            question = "我下一步应该做什么？"

        answer = answer_question_direct(question, source_label="voice/full chain")

        print("\nAtlas 回答：")
        print("-" * 70)
        print(answer)
        print("-" * 70)

        spoken = speak_text(answer, rate=155)

        if arduino is not None:
            if spoken:
                send_hardware_command(arduino, "HAPPY")
                send_hardware_command(arduino, "NOD")
            else:
                send_hardware_command(arduino, "WARNING")

            send_hardware_command(arduino, "OFF")

        content = (
            "完整链路 Demo 完成。\n\n"
            f"问题：{question}\n\n"
            f"回答：{answer}\n\n"
            f"语音状态：{'spoken' if spoken else 'text_only'}"
        )

        write_to_project_log("Atlas 4.0 Full Chain：Voice → Memory → Voice → Hardware", content)
        record_full_event("full_chain_voice_memory_voice_hardware", content)

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

            send_hardware_command(arduino, command)
            time.sleep(1.0)

        content = "Proactive Mentor + Hardware Feedback Demo 完成。\n\n" + "\n".join(lines)

        write_to_hardware_log(content)
        write_to_project_log("Atlas 4.0 Proactive Mentor + Hardware Feedback Demo", content)
        record_full_event("proactive_hardware_demo", content)

    finally:
        close_arduino(arduino)


# ============================================================
# Config menu
# ============================================================

def configure_tts():
    config = load_config()
    print(f"\n当前 TTS 语速：{config.get('tts_rate')}")
    print(f"当前 TTS 音量：{config.get('tts_volume')}")

    rate_text = input("输入新语速，建议 150-180，回车不修改：").strip()
    if rate_text.isdigit():
        rate = int(rate_text)
        rate = max(80, min(260, rate))
        save_config_value("tts_rate", rate)
        print(f"已保存 TTS 语速：{rate}")

    volume_text = input("输入新音量 0.0-1.0，回车不修改：").strip()
    if volume_text:
        try:
            volume = float(volume_text)
            volume = max(0, min(1, volume))
            save_config_value("tts_volume", volume)
            print(f"已保存 TTS 音量：{volume}")
        except Exception:
            print("音量输入无效。")


def show_current_config():
    config = load_config()
    print("\n当前 atlas4_config.json：")
    print("-" * 70)
    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("-" * 70)


# ============================================================
# Menus
# ============================================================

def show_intro():
    print("\n==============================")
    print("Atlas 4.0 Full Main")
    print("Single-file Integrated Version")
    print("==============================")
    print("包含：Vision / Voice Input / Voice Output / Memory Integration / Proactive Mentor / Hardware Feedback")
    print("重点：先单项测试，再运行完整 Demo。")
    print(f"程序文件夹：{BASE_DIR}")
    print("==============================")


def config_menu():
    while True:
        print("\n配置菜单：")
        print("1. 查看当前配置")
        print("2. 查看电脑串口设备")
        print("3. 手动选择 Arduino 串口")
        print("4. 自动连接 Arduino，并用 PING/PONG 验证")
        print("5. 设置摄像头编号 camera_index")
        print("6. 查看电脑可用语音列表")
        print("7. 设置 TTS 语速和音量")
        print("8. 返回主菜单")

        choice = input("请输入数字 1-8：").strip()

        if choice == "1":
            show_current_config()

        elif choice == "2":
            list_serial_ports()

        elif choice == "3":
            manual_set_serial_port()

        elif choice == "4":
            arduino = None
            try:
                arduino, port_name = connect_arduino()
                if arduino is not None:
                    print(f"\n最终确认：Arduino 已连接，端口：{port_name}")
            finally:
                close_arduino(arduino)

        elif choice == "5":
            set_camera_index()

        elif choice == "6":
            list_voices()

        elif choice == "7":
            configure_tts()

        elif choice == "8":
            break

        else:
            print("输入无效。")


def vision_menu():
    while True:
        print("\nStage 1 Vision 菜单：")
        print("1. 测试摄像头是否能打开")
        print("2. 启动 Eric 是否在场检测")
        print("3. 设置摄像头编号 camera_index")
        print("4. 返回主菜单")

        choice = input("请输入数字 1-4：").strip()

        if choice == "1":
            test_camera_once()
        elif choice == "2":
            start_vision_detection()
        elif choice == "3":
            set_camera_index()
        elif choice == "4":
            break
        else:
            print("输入无效。")


def voice_input_menu():
    while True:
        print("\nStage 2 Voice Input 菜单：")
        print("1. 查看电脑音频设备")
        print("2. 录音一次并转换成文字")
        print("3. 连续语音识别测试")
        print("4. 查看最近语音识别记录")
        print("5. 返回主菜单")

        choice = input("请输入数字 1-5：").strip()

        if choice == "1":
            list_audio_devices()
        elif choice == "2":
            record_and_recognize_once()
        elif choice == "3":
            continuous_voice_test()
        elif choice == "4":
            show_recent_voice_records()
        elif choice == "5":
            break
        else:
            print("输入无效。")


def voice_output_menu():
    while True:
        print("\nStage 3 Voice Output 菜单：")
        print("1. 查看电脑可用语音列表")
        print("2. 测试英文语音输出")
        print("3. 测试中文语音输出")
        print("4. 自定义让 Atlas 说一句话")
        print("5. Atlas 问候语 Greeting")
        print("6. Atlas 任务提醒 Task Reminder")
        print("7. Atlas Debug 提醒")
        print("8. 查看最近 Voice Output 记录")
        print("9. 返回主菜单")

        choice = input("请输入数字 1-9：").strip()

        if choice == "1":
            list_voices()
        elif choice == "2":
            test_basic_speech()
        elif choice == "3":
            test_chinese_speech()
        elif choice == "4":
            custom_speech()
        elif choice == "5":
            atlas_greeting()
        elif choice == "6":
            atlas_task_reminder()
        elif choice == "7":
            atlas_debug_reminder()
        elif choice == "8":
            show_recent_voice_output_records()
        elif choice == "9":
            break
        else:
            print("输入无效。")


def memory_menu():
    while True:
        print("\nStage 4 Memory Integration 菜单：")
        print("1. 检测 Atlas 3.0 / 综合长期记忆来源")
        print("2. 读取最近一次语音识别文本，并根据长期记忆回答")
        print("3. 手动输入问题，并根据长期记忆回答")
        print("4. 查看最近 Memory Integration 问答记录")
        print("5. 返回主菜单")

        choice = input("请输入数字 1-5：").strip()

        if choice == "1":
            show_memory_source()
        elif choice == "2":
            answer_latest_voice_input()
        elif choice == "3":
            answer_manual_question()
        elif choice == "4":
            show_recent_memory_interactions()
        elif choice == "5":
            break
        else:
            print("输入无效。")


def proactive_menu():
    while True:
        print("\nStage 5 Proactive Mentor 菜单：")
        print("1. 检测长期记忆来源")
        print("2. 生成主动导师 Morning Brief")
        print("3. 生成并语音播放 Morning Brief")
        print("4. 只查看昨天工作总结")
        print("5. 只查看今天任务建议")
        print("6. 检查长期未推进任务")
        print("7. 查看最近 Proactive Mentor 记录")
        print("8. Proactive Mentor + Hardware Feedback Demo")
        print("9. 返回主菜单")

        choice = input("请输入数字 1-9：").strip()

        if choice == "1":
            show_memory_source()
        elif choice == "2":
            generate_and_show_morning_brief()
        elif choice == "3":
            generate_and_speak_morning_brief()
        elif choice == "4":
            show_yesterday_summary()
        elif choice == "5":
            show_today_task()
        elif choice == "6":
            show_inactive_task_warning()
        elif choice == "7":
            show_recent_proactive_records()
        elif choice == "8":
            run_proactive_mentor_hardware_demo()
        elif choice == "9":
            break
        else:
            print("输入无效。")


def hardware_menu():
    while True:
        print("\nStage 6 Hardware Feedback 菜单：")
        print("1. 查看电脑串口设备")
        print("2. 自动连接 Arduino，并用 PING/PONG 验证")
        print("3. 手动选择 Arduino 串口，并保存到 atlas4_config.json")
        print("4. 发送单个硬件指令")
        print("5. 基础硬件反馈测试")
        print("6. Arduino 全硬件 TEST")
        print("7. Atlas 场景反馈测试")
        print("8. Proactive Mentor + Hardware Feedback Demo")
        print("9. 返回主菜单")

        choice = input("请输入数字 1-9：").strip()

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
            test_single_hardware_command()

        elif choice == "5":
            run_basic_hardware_feedback_test()

        elif choice == "6":
            run_full_hardware_test()

        elif choice == "7":
            run_atlas_scene_hardware_test()

        elif choice == "8":
            run_proactive_mentor_hardware_demo()

        elif choice == "9":
            break

        else:
            print("输入无效。")


def show_main_menu():
    print("\n请选择功能：")
    print("1. 系统状态总览")
    print("2. 配置菜单：串口 / 摄像头 / 语音")
    print("3. Stage 1 Vision：摄像头检测 Eric 是否在场")
    print("4. Stage 2 Voice Input：录音并转文字")
    print("5. Stage 3 Voice Output：文字转语音")
    print("6. Stage 4 Memory Integration：长期记忆问答")
    print("7. Stage 5 Proactive Mentor：主动导师")
    print("8. Stage 6 Hardware Feedback：Arduino 硬件反馈")
    print("9. 完整 Demo：Morning Brief + Voice Output + Hardware Feedback")
    print("10. 完整链路：Voice Input → Memory → Voice Output → Hardware")
    print("11. 测试所有日志写入")
    print("12. 退出")


def main():
    show_intro()

    load_config()

    write_to_project_log(
        "Atlas 4.0 Full Main 程序启动",
        "Atlas 4.0 六阶段整合版主程序已启动。"
    )

    record_full_event("program_start", "Atlas 4.0 Full Main started.")

    while True:
        show_main_menu()

        choice = input("请输入数字 1-12：").strip()

        if choice == "1":
            show_system_status()

        elif choice == "2":
            config_menu()

        elif choice == "3":
            vision_menu()

        elif choice == "4":
            voice_input_menu()

        elif choice == "5":
            voice_output_menu()

        elif choice == "6":
            memory_menu()

        elif choice == "7":
            proactive_menu()

        elif choice == "8":
            hardware_menu()

        elif choice == "9":
            run_morning_brief_with_voice_and_hardware()

        elif choice == "10":
            run_voice_memory_voice_hardware_chain()

        elif choice == "11":
            test_all_logs()

        elif choice == "12":
            write_to_project_log(
                "Atlas 4.0 Full Main 程序退出",
                "Atlas 4.0 六阶段整合版主程序已退出。"
            )
            record_full_event("program_exit", "Atlas 4.0 Full Main exited.")
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 12。")


if __name__ == "__main__":
    main()
