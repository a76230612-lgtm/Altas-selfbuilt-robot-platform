# -*- coding: utf-8 -*-
"""
Atlas 4.0 Full Main Program
Vision + Voice Input + Voice Output + Memory Integration + Proactive Mentor + Hardware Feedback

说明：
1. 这是 Atlas 4.0 六个阶段的整合版主程序。
2. 代码会尽量兼容没有安装某些库、没有连接硬件、没有摄像头的情况。
3. Arduino 端需要先上传 Atlas 4.0 Stage 6 Arduino Serial Control 代码。
4. 默认 Arduino 端口为 COM4，如不正确，可在菜单中修改。
"""

import json
import tempfile
import time
from datetime import datetime, date, timedelta
from pathlib import Path

# =============================
# 可选依赖库
# =============================
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

try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except Exception:
    SERIAL_AVAILABLE = False


# =============================
# 文件路径
# =============================
BASE_DIR = Path(__file__).resolve().parent

ATLAS4_DATA_FILE = BASE_DIR / "atlas4_full_data.json"
ATLAS4_CONFIG_FILE = BASE_DIR / "atlas4_config.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"

VISION_LOG_FILE = BASE_DIR / "vision_log.txt"
VOICE_INPUT_LOG_FILE = BASE_DIR / "voice_input_log.txt"
VOICE_OUTPUT_LOG_FILE = BASE_DIR / "voice_output_log.txt"
MEMORY_INTEGRATION_LOG_FILE = BASE_DIR / "memory_integration_log.txt"
PROACTIVE_MENTOR_LOG_FILE = BASE_DIR / "proactive_mentor_log.txt"
HARDWARE_LOG_FILE = BASE_DIR / "hardware_feedback_log.txt"

# 旧阶段数据文件
VOICE_INPUT_DATA_FILE = BASE_DIR / "voice_input_data.json"
VOICE_OUTPUT_DATA_FILE = BASE_DIR / "voice_output_data.json"
MEMORY_INTEGRATION_DATA_FILE = BASE_DIR / "memory_integration_data.json"
PROACTIVE_MENTOR_DATA_FILE = BASE_DIR / "proactive_mentor_data.json"

# Atlas 3.0 / 综合版数据库
ATLAS_UNIFIED_DATA_FILE = BASE_DIR / "atlas_unified_data.json"
ATLAS_FINAL_DATA_FILE = BASE_DIR / "atlas_final_data.json"
ATLAS_INTEGRATED_DATA_FILE = BASE_DIR / "atlas_integrated_data.json"
ATLAS3_DATA_FILE = BASE_DIR / "atlas3_data.json"

# Atlas 3.0 分散旧文件
PROFILE_FILE = BASE_DIR / "profile.json"
SKILLS_FILE = BASE_DIR / "skills.json"
HISTORY_FILE = BASE_DIR / "history.json"
LEARNING_PLAN_FILE = BASE_DIR / "learning_plan.json"
EMOTION_FILE = BASE_DIR / "emotion_memory.json"
MENTOR_RECOMMENDATION_FILE = BASE_DIR / "mentor_recommendation.json"


# =============================
# 基础工具
# =============================
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
            return json.load(file)
    except Exception:
        return default_data


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def append_text_file(file_path, title, content):
    text = (
        "\n" + "=" * 70 + "\n"
        f"{title}\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + str(content) + "\n"
        + "=" * 70 + "\n"
    )

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(text)


def write_to_project_log(title, content):
    append_text_file(PROJECT_LOG_FILE, title, content)
    print("\n已写入 project_log.txt")
    print(f"Project Log 位置：{PROJECT_LOG_FILE}")


def write_stage_log(stage_name, file_path, title, content):
    append_text_file(file_path, title, content)
    write_to_project_log(title, content)
    print(f"\n已写入 {file_path.name}")
    print(f"{stage_name} Log 位置：{file_path}")


def create_default_config():
    return {
        "serial_port": "COM4",
        "baud_rate": 9600,
        "camera_index": 0,
        "voice_input_sample_rate": 16000,
        "default_voice_language": "en-US",
        "tts_rate": 160,
        "tts_volume": 1.0
    }


def load_config():
    config = safe_load_json(ATLAS4_CONFIG_FILE, create_default_config())
    default_config = create_default_config()

    for key, value in default_config.items():
        if key not in config:
            config[key] = value

    save_json(ATLAS4_CONFIG_FILE, config)
    return config


def save_config(config):
    save_json(ATLAS4_CONFIG_FILE, config)


def create_default_atlas4_data():
    return {
        "student_name": "Eric",
        "atlas_version": "Atlas 4.0 Full",
        "database_version": "Atlas 4.0 Full Unified Database v1",
        "vision_events": [],
        "voice_records": [],
        "voice_output_records": [],
        "memory_interactions": [],
        "proactive_records": [],
        "hardware_records": []
    }


def load_atlas4_data():
    data = safe_load_json(ATLAS4_DATA_FILE, create_default_atlas4_data())
    default_data = create_default_atlas4_data()

    for key, value in default_data.items():
        if key not in data:
            data[key] = value

    save_json(ATLAS4_DATA_FILE, data)
    return data


def save_atlas4_data(data):
    save_json(ATLAS4_DATA_FILE, data)


def add_atlas4_record(list_key, record):
    data = load_atlas4_data()

    if list_key not in data or not isinstance(data[list_key], list):
        data[list_key] = []

    data[list_key].append(record)
    save_atlas4_data(data)


# =============================
# 长期记忆读取：Atlas 3.0 / 旧数据库兼容
# =============================
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
                "skills_learned": ["Profile", "Skill Database", "Project History", "Learning Planner", "Emotion Memory", "Mentor Recommendation"],
                "transfer_to_atlas": "Atlas 3.0 建立了 Eric Digital Twin 成长画像。"
            },
            {
                "project_name": "Atlas 4.0",
                "version": "4.0",
                "status": "in_progress",
                "skills_learned": ["Vision", "Voice Input", "Voice Output", "Memory Integration", "Proactive Mentor", "Hardware Feedback"],
                "transfer_to_atlas": "Atlas 4.0 正在把视觉、语音、长期记忆、主动导师和硬件反馈整合为多模态导师。"
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


# =============================
# Hardware Feedback：Arduino 串口控制
# =============================
def list_serial_ports():
    if not SERIAL_AVAILABLE:
        message = "pyserial 不可用。请先运行：pip install pyserial"
        print("\n" + message)
        write_stage_log("Hardware", HARDWARE_LOG_FILE, "Atlas 4.0 Hardware Feedback 串口检测失败", message)
        return []

    ports = list(serial.tools.list_ports.comports())

    print("\n当前检测到的串口设备：")
    print("-" * 70)

    if not ports:
        print("没有检测到任何串口。")
        return []

    for index, port in enumerate(ports):
        print(f"{index}. 端口：{port.device} | 名称：{port.description}")

    print("-" * 70)
    return ports


def update_serial_port():
    config = load_config()
    ports = list_serial_ports()

    if not ports:
        print("\n没有串口可选。")
        return

    choice = input("\n请输入 Arduino 对应端口编号，例如 0：").strip()

    if not choice.isdigit():
        print("请输入数字编号。")
        return

    index = int(choice)

    if index < 0 or index >= len(ports):
        print("编号超出范围。")
        return

    config["serial_port"] = ports[index].device
    save_config(config)

    content = f"已设置 Arduino 串口端口为：{config['serial_port']}"
    print("\n" + content)
    write_stage_log("Hardware", HARDWARE_LOG_FILE, "Atlas 4.0 设置 Arduino 端口", content)


def connect_arduino():
    config = load_config()
    port = config.get("serial_port", "COM4")
    baud_rate = int(config.get("baud_rate", 9600))

    if not SERIAL_AVAILABLE:
        message = "pyserial 没有安装。请运行：pip install pyserial"
        print("\n" + message)
        write_stage_log("Hardware", HARDWARE_LOG_FILE, "Atlas 4.0 Hardware Feedback Arduino 连接失败", message)
        return None

    try:
        print(f"\n正在连接 Arduino：{port}，波特率：{baud_rate}")
        arduino = serial.Serial(port, baud_rate, timeout=2)
        time.sleep(2)
        arduino.reset_input_buffer()
        arduino.reset_output_buffer()

        message = f"Arduino 连接成功：{port}"
        print(message)
        write_stage_log("Hardware", HARDWARE_LOG_FILE, "Atlas 4.0 Hardware Feedback Arduino 连接成功", message)
        return arduino

    except Exception as error:
        message = (
            f"Arduino 连接失败：{error}\n\n"
            "请检查：\n"
            "1. Arduino 是否插入电脑\n"
            "2. Arduino IDE 串口监视器是否关闭\n"
            "3. atlas4_config.json 里的 serial_port 是否正确\n"
            "4. 可先在菜单中选择：Hardware 设置 Arduino 端口"
        )
        print("\n" + message)
        write_stage_log("Hardware", HARDWARE_LOG_FILE, "Atlas 4.0 Hardware Feedback Arduino 连接失败", message)
        return None


def close_arduino(arduino):
    if arduino is not None:
        try:
            arduino.close()
            print("\nArduino 连接已关闭。")
        except Exception:
            pass


def send_hardware_command(command, keep_log=True):
    command = command.strip().upper()

    if command not in ["PING", "HAPPY", "THINKING", "WARNING", "ERROR", "NOD", "OFF", "STATUS", "TEST"]:
        print("\n指令无效。可用指令：PING / HAPPY / THINKING / WARNING / ERROR / NOD / OFF / STATUS / TEST")
        return False

    arduino = connect_arduino()

    if arduino is None:
        return False

    try:
        arduino.write((command + "\n").encode("utf-8"))
        arduino.flush()
        time.sleep(1)

        lines = []
        while arduino.in_waiting > 0:
            line = arduino.readline().decode("utf-8", errors="ignore").strip()
            if line:
                lines.append(line)

        response_text = "\n".join(lines) if lines else "无返回"

        content = (
            f"已发送硬件指令：{command}\n"
            f"Arduino 返回：\n{response_text}"
        )

        print("\n" + content)

        if keep_log:
            write_stage_log("Hardware", HARDWARE_LOG_FILE, "Atlas 4.0 Hardware Feedback 发送指令", content)
            add_atlas4_record("hardware_records", {
                "time": get_now_text(),
                "command": command,
                "response": lines,
                "status": "sent"
            })

        return True

    except Exception as error:
        message = f"发送硬件指令失败：{error}"
        print("\n" + message)
        write_stage_log("Hardware", HARDWARE_LOG_FILE, "Atlas 4.0 Hardware Feedback 发送失败", message)
        return False

    finally:
        close_arduino(arduino)


def hardware_basic_test():
    print("\n开始硬件基础测试：STATUS / PING / TEST / OFF")

    for command in ["STATUS", "PING", "TEST", "OFF"]:
        print(f"\n测试：{command}")
        send_hardware_command(command)
        time.sleep(1)


def hardware_scene_demo():
    print("\n开始 Atlas 4.0 场景硬件反馈 Demo。")

    scenes = [
        ("THINKING", "Atlas 正在读取 Eric 的长期记忆。"),
        ("HAPPY", "Atlas 成功生成 Morning Brief。"),
        ("NOD", "Atlas 点头确认今天任务。"),
        ("WARNING", "Atlas 提醒不要一次增加太多功能。"),
        ("HAPPY", "Eric 完成一个最小测试。"),
        ("OFF", "测试结束，关闭硬件反馈。")
    ]

    lines = []

    for command, description in scenes:
        line = f"{description} → {command}"
        print("\n" + line)
        lines.append(line)
        send_hardware_command(command)
        time.sleep(1)

    content = "Atlas 4.0 场景硬件反馈 Demo 完成。\n\n" + "\n".join(lines)
    write_stage_log("Hardware", HARDWARE_LOG_FILE, "Atlas 4.0 Hardware Feedback 场景 Demo", content)


# =============================
# Voice Output：文字转语音
# =============================
def create_tts_engine():
    if not TTS_AVAILABLE:
        raise RuntimeError("pyttsx3 不可用。请先运行：pip install pyttsx3")

    return pyttsx3.init()


def speak_text(text, rate=None, volume=None, voice_index=None, log=True):
    if not text:
        text = "Hello Eric. This is Atlas."

    config = load_config()

    if rate is None:
        rate = int(config.get("tts_rate", 160))

    if volume is None:
        volume = float(config.get("tts_volume", 1.0))

    try:
        engine = create_tts_engine()
        voices = engine.getProperty("voices")
        selected_voice_name = "default"

        if voice_index is not None and voices:
            if 0 <= voice_index < len(voices):
                selected_voice = voices[voice_index]
                engine.setProperty("voice", selected_voice.id)
                selected_voice_name = getattr(selected_voice, "name", "selected_voice")

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

        if log:
            write_stage_log("Voice Output", VOICE_OUTPUT_LOG_FILE, "Atlas 4.0 Voice Output 语音输出成功", content)
            add_atlas4_record("voice_output_records", {
                "time": get_now_text(),
                "text": text,
                "voice_name": selected_voice_name,
                "rate": rate,
                "volume": volume,
                "status": "spoken"
            })

        return True

    except Exception as error:
        message = f"语音输出失败：{error}"
        print("\n" + message)
        write_stage_log("Voice Output", VOICE_OUTPUT_LOG_FILE, "Atlas 4.0 Voice Output 语音输出失败", message)
        return False


def list_voices():
    if not TTS_AVAILABLE:
        print("\npyttsx3 不可用。请先运行：pip install pyttsx3")
        return

    try:
        engine = create_tts_engine()
        voices = engine.getProperty("voices")

        print("\n电脑可用语音：")
        print("-" * 70)

        lines = []
        for index, voice in enumerate(voices):
            voice_name = getattr(voice, "name", "Unknown")
            voice_id = getattr(voice, "id", "Unknown")
            text = f"{index}. 语音名称：{voice_name}\n   语音 ID：{voice_id}"
            print(text)
            print("-" * 70)
            lines.append(text)

        write_stage_log("Voice Output", VOICE_OUTPUT_LOG_FILE, "Atlas 4.0 Voice Output 查看语音列表", "\n\n".join(lines))

    except Exception as error:
        print(f"\n读取语音列表失败：{error}")


def voice_output_menu():
    while True:
        print("\nVoice Output 菜单：")
        print("1. 查看电脑语音列表")
        print("2. 测试英文语音")
        print("3. 测试中文语音")
        print("4. 自定义让 Atlas 说一句话")
        print("5. Atlas Greeting")
        print("6. Atlas Task Reminder")
        print("7. 返回主菜单")

        choice = input("请输入数字 1-7：").strip()

        if choice == "1":
            list_voices()
        elif choice == "2":
            speak_text("Hello Eric. I am Atlas. I can speak now.")
        elif choice == "3":
            speak_text("你好 Eric，我是 Atlas。现在我已经可以说话了。", rate=150)
        elif choice == "4":
            text = input("请输入想让 Atlas 说的话：").strip()
            speak_text(text)
        elif choice == "5":
            speak_text("Hello Eric. I am Atlas. I can see you, hear you, speak to you, read your memory, and control hardware feedback.")
        elif choice == "6":
            speak_text("Eric, test one function first, record the result, and then continue.")
        elif choice == "7":
            break
        else:
            print("输入无效。")


# =============================
# Voice Input：录音和语音识别
# =============================
def list_audio_devices():
    if not VOICE_INPUT_AVAILABLE:
        print("\nVoice Input 依赖不可用。请安装：pip install SpeechRecognition sounddevice scipy numpy")
        return

    try:
        devices = sd.query_devices()

        print("\n当前电脑音频设备：")
        print("-" * 70)

        lines = []
        for index, device in enumerate(devices):
            name = device.get("name", "Unknown")
            max_input_channels = device.get("max_input_channels", 0)
            max_output_channels = device.get("max_output_channels", 0)
            line = f"{index}. {name} | 输入通道：{max_input_channels} | 输出通道：{max_output_channels}"
            print(line)
            lines.append(line)

        print("-" * 70)
        write_stage_log("Voice Input", VOICE_INPUT_LOG_FILE, "Atlas 4.0 Voice Input 音频设备检测", "\n".join(lines))

    except Exception as error:
        print(f"\n音频设备读取失败：{error}")


def record_audio_to_temp_wav(duration_seconds=5, sample_rate=None):
    if not VOICE_INPUT_AVAILABLE:
        raise RuntimeError("Voice Input 依赖不可用。请安装 SpeechRecognition sounddevice scipy numpy。")

    config = load_config()

    if sample_rate is None:
        sample_rate = int(config.get("voice_input_sample_rate", 16000))

    print("\n准备开始录音。")
    print(f"录音时长：{duration_seconds} 秒。")
    print("开始录音...")

    audio_data = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )
    sd.wait()

    print("录音结束。")

    audio_data = np.asarray(audio_data)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file_path = temp_file.name
    temp_file.close()

    write_wav(temp_file_path, sample_rate, audio_data)

    return temp_file_path


def recognize_speech_from_wav(wav_path, language):
    recognizer = sr.Recognizer()

    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)

    try:
        return recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as error:
        raise RuntimeError(f"语音识别服务连接失败：{error}")


def record_and_recognize_once(language=None, duration_seconds=None):
    if not VOICE_INPUT_AVAILABLE:
        print("\nVoice Input 依赖不可用。请安装：pip install SpeechRecognition sounddevice scipy numpy")
        return ""

    if language is None:
        print("\n选择识别语言：")
        print("1. English")
        print("2. 中文")
        language_choice = input("请输入 1 或 2：").strip()
        language = "zh-CN" if language_choice == "2" else "en-US"

    language_name = "中文" if language == "zh-CN" else "English"

    if duration_seconds is None:
        duration_text = input("\n录音几秒？建议 5 秒，直接回车默认 5 秒：").strip()
        duration_seconds = int(duration_text) if duration_text.isdigit() else 5

    duration_seconds = max(2, min(15, duration_seconds))

    try:
        wav_path = record_audio_to_temp_wav(duration_seconds=duration_seconds)
        recognized_text = recognize_speech_from_wav(wav_path, language=language)

        if recognized_text:
            status = "recognized"
            print("\nAtlas 听到的内容：")
            print("-" * 70)
            print(recognized_text)
            print("-" * 70)
        else:
            status = "not_recognized"
            print("\n没有识别到清楚语音。")

        record = {
            "time": get_now_text(),
            "language": language_name,
            "duration_seconds": duration_seconds,
            "recognized_text": recognized_text,
            "status": status
        }

        add_atlas4_record("voice_records", record)

        # 同步保存旧文件，兼容 Memory Integration 阶段读取
        old_data = safe_load_json(VOICE_INPUT_DATA_FILE, {"student_name": "Eric", "voice_records": []})
        if "voice_records" not in old_data:
            old_data["voice_records"] = []
        old_data["voice_records"].append(record)
        save_json(VOICE_INPUT_DATA_FILE, old_data)

        content = (
            f"识别语言：{language_name}\n"
            f"录音时长：{duration_seconds} 秒\n"
            f"识别状态：{status}\n"
            f"识别结果：{recognized_text}"
        )

        write_stage_log("Voice Input", VOICE_INPUT_LOG_FILE, "Atlas 4.0 Voice Input 单次语音识别", content)
        return recognized_text

    except Exception as error:
        message = f"Voice Input 运行失败：{error}"
        print("\n" + message)
        write_stage_log("Voice Input", VOICE_INPUT_LOG_FILE, "Atlas 4.0 Voice Input 运行失败", message)
        return ""


# =============================
# Vision：摄像头检测 Eric 是否在场
# =============================
def test_camera_once():
    if not CV2_AVAILABLE:
        message = "OpenCV 不可用。请运行：pip install opencv-python numpy"
        print("\n" + message)
        write_stage_log("Vision", VISION_LOG_FILE, "Atlas 4.0 Vision OpenCV 不可用", message)
        return False

    config = load_config()
    camera_index = int(config.get("camera_index", 0))

    print("\n正在测试摄像头是否可以打开...")
    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        message = (
            f"摄像头打开失败，camera_index={camera_index}。\n"
            "请检查摄像头权限、是否被其他软件占用，或把 camera_index 改成 1。"
        )
        print(message)
        write_stage_log("Vision", VISION_LOG_FILE, "Atlas 4.0 Vision 摄像头测试失败", message)
        return False

    success, frame = camera.read()
    camera.release()

    if not success:
        message = "摄像头可以打开，但无法读取画面。"
        print(message)
        write_stage_log("Vision", VISION_LOG_FILE, "Atlas 4.0 Vision 摄像头读取失败", message)
        return False

    message = "摄像头测试成功。Atlas 4.0 可以读取摄像头画面。"
    print(message)
    write_stage_log("Vision", VISION_LOG_FILE, "Atlas 4.0 Vision 摄像头测试成功", message)
    return True


def start_vision_detection(with_hardware=False):
    if not CV2_AVAILABLE:
        print("\nOpenCV 不可用。请运行：pip install opencv-python numpy")
        return

    config = load_config()
    camera_index = int(config.get("camera_index", 0))

    print("\n启动 Atlas 4.0 Vision 检测。")
    print("按 q 退出摄像头窗口。")

    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        message = f"摄像头打开失败，camera_index={camera_index}。"
        print("\n" + message)
        write_stage_log("Vision", VISION_LOG_FILE, "Atlas 4.0 Vision 启动失败", message)
        return

    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_detector = cv2.CascadeClassifier(face_cascade_path)

    if face_detector.empty():
        message = "OpenCV 人脸检测模型加载失败。"
        print("\n" + message)
        write_stage_log("Vision", VISION_LOG_FILE, "Atlas 4.0 Vision 人脸模型加载失败", message)
        camera.release()
        return

    last_status = None
    present_count = 0
    absent_count = 0

    write_stage_log("Vision", VISION_LOG_FILE, "Atlas 4.0 Vision 检测启动", "摄像头检测已启动。")

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
        cv2.putText(frame, "Press q to quit", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("Atlas 4.0 Vision - Eric Presence Detection", frame)

        if status != last_status:
            log_message = f"Vision 状态变化：{status}"
            print(log_message)
            append_text_file(VISION_LOG_FILE, "Atlas 4.0 Vision 状态变化", log_message)
            add_atlas4_record("vision_events", {
                "time": get_now_text(),
                "status": status
            })

            if with_hardware:
                if len(faces) > 0:
                    send_hardware_command("HAPPY")
                else:
                    send_hardware_command("THINKING")

            last_status = status

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    summary = (
        "Atlas 4.0 Vision 检测结束。\n"
        f"检测到 Eric 在场的帧数：{present_count}\n"
        f"未检测到 Eric 的帧数：{absent_count}"
    )
    print("\n" + summary)
    write_stage_log("Vision", VISION_LOG_FILE, "Atlas 4.0 Vision 检测结束", summary)


# =============================
# Memory Integration：根据长期记忆回答
# =============================
def get_latest_voice_input_text():
    # 先读整合数据库
    data = load_atlas4_data()
    records = data.get("voice_records", [])

    for record in reversed(records):
        text = record.get("recognized_text", "")
        status = record.get("status", "")
        if text and status == "recognized":
            return text

    # 再读旧 voice_input_data.json
    old_data = safe_load_json(VOICE_INPUT_DATA_FILE, {})
    old_records = old_data.get("voice_records", [])

    for record in reversed(old_records):
        text = record.get("recognized_text", "")
        status = record.get("status", "")
        if text and status == "recognized":
            return text

    return ""


def format_profile_summary(memory):
    profile = memory.get("profile", {})
    interests = profile.get("interests", [])
    strengths = profile.get("strengths", [])
    weaknesses = profile.get("weaknesses", [])

    return (
        f"Eric 的当前成长画像：\n"
        f"- 年龄：{profile.get('age', 13)}\n"
        f"- 长期目标：{profile.get('goal', 'AI Systems Engineer')}\n"
        f"- 当前项目：{profile.get('current_project', 'Atlas')}\n"
        f"- 当前版本：{profile.get('current_version', 'Atlas 4.0')}\n"
        f"- 兴趣：{'、'.join(interests) if interests else '暂无'}\n"
        f"- 强项：{'、'.join(strengths) if strengths else '暂无'}\n"
        f"- 需要补强：{'、'.join(weaknesses) if weaknesses else '暂无'}\n"
        f"- 学习风格：{profile.get('learning_style', '喜欢通过项目实战学习')}"
    )


def format_skill_summary(memory):
    skills = memory.get("skills", {})
    lines = ["Eric 的技能状态："]

    for skill_name, skill_info in skills.items():
        if isinstance(skill_info, dict):
            lines.append(f"- {skill_name}：{skill_info.get('score', 0)} 分，level：{skill_info.get('level', 'unknown')}")

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

        lines.append(f"- {project_name} ({version}) | 状态：{status} | 学到：{skills_text}")
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

    ros2_score = skills.get("ROS2", {}).get("score", None) if isinstance(skills.get("ROS2", {}), dict) else None
    arduino_score = skills.get("Arduino", {}).get("score", None) if isinstance(skills.get("Arduino", {}), dict) else None
    python_score = skills.get("Python", {}).get("score", None) if isinstance(skills.get("Python", {}), dict) else None
    opencv_score = skills.get("OpenCV", {}).get("score", None) if isinstance(skills.get("OpenCV", {}), dict) else None

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
            "Eric，根据你的长期记忆，下一步建议继续推进 Atlas 4.0 的完整整合。\n"
            "你已经完成 Vision、Voice Input、Voice Output、Memory Integration、Proactive Mentor 和 Hardware Feedback。"
        )

    if "ros" in question_lower or "ros2" in question_lower:
        return (
            f"Eric，你现在需要关注 ROS2。你的 ROS2 当前分数是 {ros2_score}。\n"
            "你的 Arduino、Python、OpenCV 已经有基础，所以不需要继续重复基础 Arduino。"
        )

    if "arduino" in question_lower or "硬件" in question:
        return (
            f"Eric，你的 Arduino 当前分数是 {arduino_score}。\n"
            "Atlas 4.0 已经可以通过 Python 给 Arduino 发送 HAPPY、THINKING、WARNING、NOD 等指令，形成硬件反馈。"
        )

    if "4.0" in question or "atlas 4" in question_lower:
        return (
            "Eric，Atlas 4.0 的目标是多模态导师：能看、能听、能说、能读取长期记忆、能主动提醒，并能控制硬件反馈。"
        )

    if "3.0" in question or "atlas 3" in question_lower:
        return (
            "Eric，Atlas 3.0 的核心成果是 Eric Digital Twin。它包括 Profile、Skill Database、Project History、Learning Planner、Emotion Memory 和 Mentor Recommendation。"
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
        return (
            f"{get_latest_emotion_text(memory)}\n\n"
            "如果你已经连续调试很久，Atlas 建议先休息 15 到 20 分钟，然后回来只测试一个最小问题。"
        )

    return (
        f"Eric，我已经读取了你的长期记忆。\n\n"
        f"{format_profile_summary(memory)}\n\n"
        "你可以问：我下一步应该做什么？为什么要学 ROS2？我的项目历史是什么？我现在的技能状态是什么？"
    )


def answer_manual_question(with_speech=False, with_hardware=False):
    memory, source = load_memory()
    question = input("\n请输入 Eric 的问题，例如：我下一步应该做什么？").strip()

    if not question:
        question = "我下一步应该做什么？"

    if with_hardware:
        send_hardware_command("THINKING")

    answer = answer_question_with_memory(question, memory)

    content = (
        f"长期记忆来源：{source}\n\n"
        f"Eric 问题：\n{question}\n\n"
        f"Atlas 回答：\n{answer}"
    )

    print("\nAtlas 基于长期记忆的回答：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_stage_log("Memory Integration", MEMORY_INTEGRATION_LOG_FILE, "Atlas 4.0 Memory Integration 手动问题记忆回答", content)
    add_atlas4_record("memory_interactions", {
        "time": get_now_text(),
        "question": question,
        "answer": answer,
        "source": source
    })

    if with_speech:
        speak_text(answer)

    if with_hardware:
        send_hardware_command("HAPPY")


def answer_latest_voice_input(with_speech=False, with_hardware=False):
    memory, source = load_memory()
    question = get_latest_voice_input_text()

    if not question:
        message = "没有找到最近一次有效语音识别文本。请先运行 Voice Input 录音识别。"
        print("\n" + message)
        write_stage_log("Memory Integration", MEMORY_INTEGRATION_LOG_FILE, "Atlas 4.0 Memory Integration 读取语音失败", message)
        return

    if with_hardware:
        send_hardware_command("THINKING")

    answer = answer_question_with_memory(question, memory)

    content = (
        f"长期记忆来源：{source}\n\n"
        f"Eric 最近语音问题：\n{question}\n\n"
        f"Atlas 基于长期记忆的回答：\n{answer}"
    )

    print("\nAtlas 读取最近语音，并根据长期记忆回答：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_stage_log("Memory Integration", MEMORY_INTEGRATION_LOG_FILE, "Atlas 4.0 Memory Integration 语音问题记忆回答", content)
    add_atlas4_record("memory_interactions", {
        "time": get_now_text(),
        "question": question,
        "answer": answer,
        "source": "latest voice input + " + source
    })

    if with_speech:
        speak_text(answer)

    if with_hardware:
        send_hardware_command("HAPPY")


# =============================
# Proactive Mentor：主动导师
# =============================
def get_skill_score(memory, skill_name):
    skill = memory.get("skills", {}).get(skill_name)
    if not isinstance(skill, dict):
        return None
    return skill.get("score", None)


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


def summarize_yesterday(memory):
    yesterday = get_yesterday_text()
    plans = memory.get("daily_learning_plans", [])
    emotions = memory.get("emotion_records", [])

    plan_text = f"没有找到 {yesterday} 的 Learning Plan。"
    emotion_text = f"没有找到 {yesterday} 的 Emotion Memory。"

    for plan in plans:
        if plan.get("date") == yesterday:
            plan_text = (
                f"昨天 Learning Plan：\n"
                f"- 日期：{plan.get('date', '')}\n"
                f"- 重点：{plan.get('today_focus', '')}\n"
                f"- 状态：{plan.get('status', '')}\n"
                f"- 复盘：{plan.get('evening_review', '') if plan.get('evening_review') else '暂无'}"
            )

    for record in emotions:
        if record.get("date") == yesterday:
            emotion_text = (
                f"昨天研发状态：\n"
                f"- 状态：{record.get('feeling', '')}\n"
                f"- 连续调试：{record.get('debug_hours', 0)} 小时\n"
                f"- 问题：{record.get('problem', '')}\n"
                f"- 下一步：{record.get('next_step', '')}"
            )

    return (
        "昨天工作总结\n\n"
        + plan_text
        + "\n\n"
        + emotion_text
        + "\n\n"
        + get_project_log_yesterday_summary()
    )


def decide_today_task(memory):
    profile = memory.get("profile", {})
    current_version = profile.get("current_version", "Atlas 4.0")

    ros2_score = get_skill_score(memory, "ROS2")
    yolo_score = get_skill_score(memory, "YOLO")
    python_score = get_skill_score(memory, "Python")

    if "4.0" in current_version or "Atlas 4.0" in current_version:
        return {
            "focus": "Atlas 4.0 Full Integration",
            "reason": "Vision、Voice Input、Voice Output、Memory Integration、Proactive Mentor 和 Hardware Feedback 已经分阶段跑通，现在应该测试完整整合版。",
            "task_1": "运行 atlas4_full_main.py。",
            "task_2": "测试一键 Full Demo。",
            "task_3": "录制 Atlas 4.0 2-3 分钟 Demo 视频。",
            "estimated_time": "2 小时"
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
            "task_2": "画出 Vision、Voice、Memory、Hardware 的模块关系。",
            "task_3": "优化整合版主程序。",
            "estimated_time": "2 小时"
        }

    return {
        "focus": "Atlas 4.0 Demo",
        "reason": "当前基础功能较完整，可以开始准备 Demo。",
        "task_1": "检查 Stage 1 到 Stage 6 的日志。",
        "task_2": "确认每个阶段都能单独运行。",
        "task_3": "准备最终展示。",
        "estimated_time": "2 小时"
    }


def check_inactive_tasks(memory, inactive_days=3):
    today = date.today()
    warnings = []

    for plan in memory.get("daily_learning_plans", []):
        plan_date = parse_date(plan.get("date", ""))
        if plan_date is None:
            continue
        age = (today - plan_date).days
        status = plan.get("status", "")
        if age >= inactive_days and status not in ["完成", "completed", "done"]:
            warnings.append(f"Learning Plan 已经 {age} 天没有完成闭环：{plan.get('today_focus', '未知重点')} | 状态：{status}")

    for task in memory.get("daily_tasks", []):
        task_date = parse_date(task.get("date", ""))
        if task_date is None:
            continue
        age = (today - task_date).days
        status = task.get("status", "")
        if age >= inactive_days and status not in ["完成", "completed", "done"]:
            warnings.append(f"Daily Task 已经 {age} 天没有完成闭环：{task.get('today_plan', '未知任务')} | 状态：{status}")

    if not warnings:
        return "目前没有发现超过 3 天未推进的任务。"

    return "长期未推进任务提醒：\n" + "\n".join([f"- {w}" for w in warnings]) + "\n\n建议：今天不要新增太多功能，先关闭一个旧任务或补一次复盘。"


def generate_morning_brief(memory, source):
    profile = memory.get("profile", {})
    today_task = decide_today_task(memory)
    yesterday_summary = summarize_yesterday(memory)
    inactive_warning = check_inactive_tasks(memory)

    name = profile.get("name", "Eric")
    goal = profile.get("goal", "AI Systems Engineer")
    current_project = profile.get("current_project", "Atlas")
    current_version = profile.get("current_version", "Atlas 4.0")

    return (
        f"Good morning, {name}.\n\n"
        "I am Atlas 4.0 Full Proactive Mentor.\n\n"
        "一、当前项目状态\n"
        f"- 长期目标：{goal}\n"
        f"- 当前项目：{current_project}\n"
        f"- 当前版本：{current_version}\n"
        f"- 记忆来源：{source}\n\n"
        "二、昨天总结\n"
        f"{yesterday_summary}\n\n"
        "三、今天建议\n"
        f"- 今日重点：{today_task['focus']}\n"
        f"- 原因：{today_task['reason']}\n"
        f"- 任务 1：{today_task['task_1']}\n"
        f"- 任务 2：{today_task['task_2']}\n"
        f"- 任务 3：{today_task['task_3']}\n"
        f"- 预计时间：{today_task['estimated_time']}\n\n"
        "四、未推进任务提醒\n"
        f"{inactive_warning}\n\n"
        "五、Atlas 主动导师提醒\n"
        "今天不要同时扩大太多功能。先完成一个最小测试，再写入 Project Log。"
    )


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
        f"This is Atlas 4.0 Full Proactive Mentor. "
        f"Today I suggest you focus on {focus}. "
        f"Your first task is: {today_task['task_1']} "
        f"{warning_sentence} "
        f"Please finish one small test first, then update the project log."
    )


def generate_morning_brief_action(with_speech=False, with_hardware=False):
    memory, source = load_memory()

    if with_hardware:
        send_hardware_command("THINKING")

    brief = generate_morning_brief(memory, source)

    print("\nAtlas 4.0 Full Morning Brief：")
    print("-" * 70)
    print(brief)
    print("-" * 70)

    write_stage_log("Proactive Mentor", PROACTIVE_MENTOR_LOG_FILE, "Atlas 4.0 Full Proactive Mentor Morning Brief", brief)
    add_atlas4_record("proactive_records", {
        "time": get_now_text(),
        "record_type": "morning_brief",
        "content": brief,
        "source": source
    })

    if with_speech:
        short_speech = build_short_speech(memory)
        speak_text(short_speech)

    if with_hardware:
        send_hardware_command("HAPPY")
        send_hardware_command("NOD")


# =============================
# 一键 Full Demo
# =============================
def one_click_full_demo():
    print("\n==============================")
    print("Atlas 4.0 One-Click Full Demo")
    print("==============================")
    print("这个 Demo 会按顺序展示：")
    print("1. 硬件 THINKING")
    print("2. 读取长期记忆")
    print("3. 生成 Morning Brief")
    print("4. 语音播放简版提醒")
    print("5. 硬件 HAPPY + NOD")
    print("6. 保存日志")
    print("==============================")

    use_hardware = input("是否启用 Arduino 硬件反馈？输入 y 启用：").strip().lower() == "y"
    use_speech = input("是否启用语音输出？输入 y 启用：").strip().lower() == "y"

    if use_hardware:
        send_hardware_command("THINKING")

    memory, source = load_memory()
    brief = generate_morning_brief(memory, source)
    short_speech = build_short_speech(memory)

    print("\n完整 Morning Brief：")
    print("-" * 70)
    print(brief)
    print("-" * 70)

    if use_speech:
        speak_text(short_speech)

    if use_hardware:
        send_hardware_command("HAPPY")
        send_hardware_command("NOD")

    content = (
        "Atlas 4.0 一键 Full Demo 完成。\n\n"
        f"记忆来源：{source}\n\n"
        f"语音简版：{short_speech}\n\n"
        f"完整 Morning Brief：\n{brief}"
    )

    write_to_project_log("Atlas 4.0 One-Click Full Demo", content)
    add_atlas4_record("proactive_records", {
        "time": get_now_text(),
        "record_type": "one_click_full_demo",
        "content": content,
        "source": source
    })

    print("\nAtlas 4.0 一键 Full Demo 已完成。")


def voice_to_memory_to_speech_to_hardware_demo():
    print("\n==============================")
    print("Voice → Memory → Speech → Hardware Demo")
    print("==============================")
    print("这一步会：录音识别 → 读取长期记忆回答 → 语音输出 → Arduino 硬件反馈")

    use_hardware = input("是否启用 Arduino 硬件反馈？输入 y 启用：").strip().lower() == "y"
    use_speech = input("是否启用语音输出？输入 y 启用：").strip().lower() == "y"

    if use_hardware:
        send_hardware_command("THINKING")

    question = record_and_recognize_once()

    if not question:
        print("\n没有识别到有效问题，Demo 停止。")
        if use_hardware:
            send_hardware_command("WARNING")
        return

    memory, source = load_memory()
    answer = answer_question_with_memory(question, memory)

    print("\nAtlas 回答：")
    print("-" * 70)
    print(answer)
    print("-" * 70)

    content = (
        f"Voice → Memory Demo\n"
        f"问题：{question}\n"
        f"记忆来源：{source}\n"
        f"回答：{answer}"
    )

    write_stage_log("Memory Integration", MEMORY_INTEGRATION_LOG_FILE, "Atlas 4.0 Voice-Memory-Speech-Hardware Demo", content)
    add_atlas4_record("memory_interactions", {
        "time": get_now_text(),
        "question": question,
        "answer": answer,
        "source": source
    })

    if use_speech:
        speak_text(answer)

    if use_hardware:
        send_hardware_command("HAPPY")


# =============================
# 设置与总览
# =============================
def show_dependency_status():
    config = load_config()
    memory, source = load_memory()

    lines = []
    lines.append("Atlas 4.0 Full 状态总览")
    lines.append("")
    lines.append(f"整合数据库：{ATLAS4_DATA_FILE}")
    lines.append(f"配置文件：{ATLAS4_CONFIG_FILE}")
    lines.append(f"Project Log：{PROJECT_LOG_FILE}")
    lines.append("")
    lines.append("依赖库状态：")
    lines.append(f"- OpenCV / Vision：{'OK' if CV2_AVAILABLE else 'MISSING'}")
    lines.append(f"- Voice Input：{'OK' if VOICE_INPUT_AVAILABLE else 'MISSING'}")
    lines.append(f"- Voice Output / pyttsx3：{'OK' if TTS_AVAILABLE else 'MISSING'}")
    lines.append(f"- Hardware / pyserial：{'OK' if SERIAL_AVAILABLE else 'MISSING'}")
    lines.append("")
    lines.append("当前配置：")
    lines.append(f"- Arduino 串口：{config.get('serial_port')}")
    lines.append(f"- 波特率：{config.get('baud_rate')}")
    lines.append(f"- 摄像头编号：{config.get('camera_index')}")
    lines.append("")
    lines.append(f"长期记忆来源：{source}")
    lines.append(format_profile_summary(memory))

    content = "\n".join(lines)

    print("\n" + content)
    write_to_project_log("Atlas 4.0 Full 状态总览", content)


def set_camera_index():
    config = load_config()
    old_index = config.get("camera_index", 0)
    text = input(f"请输入摄像头编号，当前是 {old_index}，通常 0 或 1：").strip()

    if not text.isdigit():
        print("请输入数字。")
        return

    config["camera_index"] = int(text)
    save_config(config)
    print(f"\n已设置 camera_index = {config['camera_index']}")


def test_all_logs():
    content = "这是 Atlas 4.0 Full Main 的日志写入测试。"

    write_stage_log("Vision", VISION_LOG_FILE, "Atlas 4.0 Full Vision Log Test", content)
    write_stage_log("Voice Input", VOICE_INPUT_LOG_FILE, "Atlas 4.0 Full Voice Input Log Test", content)
    write_stage_log("Voice Output", VOICE_OUTPUT_LOG_FILE, "Atlas 4.0 Full Voice Output Log Test", content)
    write_stage_log("Memory Integration", MEMORY_INTEGRATION_LOG_FILE, "Atlas 4.0 Full Memory Log Test", content)
    write_stage_log("Proactive Mentor", PROACTIVE_MENTOR_LOG_FILE, "Atlas 4.0 Full Proactive Log Test", content)
    write_stage_log("Hardware", HARDWARE_LOG_FILE, "Atlas 4.0 Full Hardware Log Test", content)


# =============================
# 主菜单
# =============================
def show_intro():
    config = load_config()
    load_atlas4_data()

    print("\n==============================")
    print("Atlas 4.0 Full Main Program")
    print("Vision + Voice + Memory + Proactive Mentor + Hardware")
    print("==============================")
    print("功能：")
    print("1. Vision：摄像头检测 Eric 是否在场")
    print("2. Voice Input：录音并转文字")
    print("3. Voice Output：文字转语音")
    print("4. Memory Integration：读取长期记忆回答")
    print("5. Proactive Mentor：主动导师 Morning Brief")
    print("6. Hardware Feedback：Python 控制 Arduino")
    print("7. Full Demo：完整链路展示")
    print("==============================")
    print(f"Arduino 串口：{config.get('serial_port')}")
    print(f"摄像头编号：{config.get('camera_index')}")
    print(f"整合数据库：{ATLAS4_DATA_FILE}")
    print("==============================")


def main():
    show_intro()
    write_to_project_log("Atlas 4.0 Full Main 程序启动", "atlas4_full_main.py 已启动。")

    while True:
        print("\n请选择功能：")
        print("1. 状态总览 / 检查依赖")
        print("2. 设置 Arduino 串口")
        print("3. 设置摄像头编号")
        print("4. 测试所有日志写入")
        print("")
        print("5. Vision：测试摄像头")
        print("6. Vision：启动 Eric 是否在场检测")
        print("7. Vision：启动检测 + 硬件反馈")
        print("")
        print("8. Voice Input：查看音频设备")
        print("9. Voice Input：录音一次并转文字")
        print("")
        print("10. Voice Output：语音输出菜单")
        print("")
        print("11. Memory：手动输入问题，基于长期记忆回答")
        print("12. Memory：读取最近一次语音识别，基于长期记忆回答")
        print("13. Memory + Speech + Hardware：手动问题完整回答")
        print("")
        print("14. Proactive Mentor：生成 Morning Brief")
        print("15. Proactive Mentor：生成 + 语音播放")
        print("16. Proactive Mentor：生成 + 语音 + 硬件反馈")
        print("")
        print("17. Hardware：查看串口设备")
        print("18. Hardware：发送单个指令")
        print("19. Hardware：基础测试 STATUS / PING / TEST / OFF")
        print("20. Hardware：Atlas 场景 Demo")
        print("")
        print("21. Full Demo：一键完整 Demo")
        print("22. Full Demo：Voice → Memory → Speech → Hardware")
        print("23. 退出")

        choice = input("请输入数字 1-23：").strip()

        if choice == "1":
            show_dependency_status()

        elif choice == "2":
            update_serial_port()

        elif choice == "3":
            set_camera_index()

        elif choice == "4":
            test_all_logs()

        elif choice == "5":
            test_camera_once()

        elif choice == "6":
            start_vision_detection(with_hardware=False)

        elif choice == "7":
            start_vision_detection(with_hardware=True)

        elif choice == "8":
            list_audio_devices()

        elif choice == "9":
            record_and_recognize_once()

        elif choice == "10":
            voice_output_menu()

        elif choice == "11":
            answer_manual_question(with_speech=False, with_hardware=False)

        elif choice == "12":
            answer_latest_voice_input(with_speech=False, with_hardware=False)

        elif choice == "13":
            answer_manual_question(with_speech=True, with_hardware=True)

        elif choice == "14":
            generate_morning_brief_action(with_speech=False, with_hardware=False)

        elif choice == "15":
            generate_morning_brief_action(with_speech=True, with_hardware=False)

        elif choice == "16":
            generate_morning_brief_action(with_speech=True, with_hardware=True)

        elif choice == "17":
            list_serial_ports()

        elif choice == "18":
            command = input("请输入指令 PING / HAPPY / THINKING / WARNING / ERROR / NOD / OFF / STATUS / TEST：").strip().upper()
            send_hardware_command(command)

        elif choice == "19":
            hardware_basic_test()

        elif choice == "20":
            hardware_scene_demo()

        elif choice == "21":
            one_click_full_demo()

        elif choice == "22":
            voice_to_memory_to_speech_to_hardware_demo()

        elif choice == "23":
            write_to_project_log("Atlas 4.0 Full Main 程序退出", "atlas4_full_main.py 已退出。")
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 23。")


if __name__ == "__main__":
    main()
