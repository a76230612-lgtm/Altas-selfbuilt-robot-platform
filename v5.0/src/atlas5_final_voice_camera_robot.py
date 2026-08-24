import json
import tempfile
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

import cv2
import numpy as np
import pyttsx3
import serial
import sounddevice as sd
import speech_recognition as sr
from scipy.io.wavfile import write as write_wav


# =====================================================
# Atlas 5.0 Final Stable Program v1
#
# Integrated Functions:
# - Camera preview through OpenCV
# - Terminal menu control
# - Real voice recording
# - SpeechRecognition voice-to-text
# - pyttsx3 text-to-speech
# - ESP32 OLED / LED / Pan-Tilt behavior control
# - Safe Mode: ARM -> ACTION -> DISARM
#
# This program DOES NOT change ESP32 firmware.
#
# ESP32 firmware required:
# - atlas5_body_firmware_oled_v1_success.ino
#
# Required packages:
# python -m pip install pyserial opencv-python sounddevice scipy numpy SpeechRecognition pyttsx3
# =====================================================


# ===================== Serial Config =====================

SERIAL_PORT = "COM4"   # 改成你的 ESP32 端口，例如 COM3 / COM4 / COM5
BAUD_RATE = 115200
TIMEOUT = 2
READY_TEXT = "READY_FOR_NEXT_COMMAND"


# ===================== Paths =====================

BASE_DIR = Path(__file__).resolve().parent

SNAPSHOT_DIR = BASE_DIR / "atlas5_final_camera_snapshots"
VOICE_LOG_FILE = BASE_DIR / "atlas5_final_voice_camera_log.txt"
VOICE_DATA_FILE = BASE_DIR / "atlas5_final_voice_camera_data.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"

SNAPSHOT_DIR.mkdir(exist_ok=True)


# ===================== Audio Config =====================

SAMPLE_RATE = 16000
DEFAULT_RECORD_SECONDS = 5


# ===================== Camera Config =====================

CAMERA_INDEX_LIST = [0, 1, 2, 3, 4]


# =====================================================
# States and Intents
# =====================================================

class AtlasState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SUCCESS = "SUCCESS"
    ENCOURAGE = "ENCOURAGE"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DialogueIntent(Enum):
    GREETING = "GREETING"
    SELF_INTRO = "SELF_INTRO"
    NORMAL_QUESTION = "NORMAL_QUESTION"
    ENCOURAGEMENT_REQUEST = "ENCOURAGEMENT_REQUEST"
    WARNING_EVENT = "WARNING_EVENT"
    ERROR_EVENT = "ERROR_EVENT"
    STATUS_CHECK = "STATUS_CHECK"
    PROJECT_QUESTION = "PROJECT_QUESTION"
    CAMERA_EVENT = "CAMERA_EVENT"
    BEHAVIOR_TEST_EVENT = "BEHAVIOR_TEST_EVENT"
    IDLE_EVENT = "IDLE_EVENT"
    QUIT = "QUIT"
    UNKNOWN = "UNKNOWN"


# =====================================================
# Logs and Data
# =====================================================

def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_log(title, content):
    text = (
        "\n" + "=" * 70 + "\n"
        f"{title}\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(VOICE_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    with open(PROJECT_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n[LOG] 已写入日志")
    print(f"[LOG] Voice Camera Log: {VOICE_LOG_FILE}")
    print(f"[LOG] Project Log: {PROJECT_LOG_FILE}")


def create_default_data():
    return {
        "student_name": "Eric",
        "robot_name": "Atlas",
        "version": "Atlas 5.0 Final Stable Program v1",
        "records": []
    }


def load_data():
    if not VOICE_DATA_FILE.exists():
        data = create_default_data()
        save_data(data)
        return data

    try:
        with open(VOICE_DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        data = create_default_data()

    if "records" not in data:
        data["records"] = []

    save_data(data)
    return data


def save_data(data):
    with open(VOICE_DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def save_record(language, recognized_text, intent, reply, status, snapshot_path=""):
    data = load_data()

    record = {
        "time": get_now_text(),
        "language": language,
        "recognized_text": recognized_text,
        "intent": intent,
        "reply": reply,
        "status": status,
        "snapshot_path": snapshot_path
    }

    data["records"].append(record)
    save_data(data)


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
            print("2. SERIAL_PORT 是否写对")
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
# Camera Manager
# =====================================================

class AtlasCamera:
    def __init__(self):
        self.cap = None
        self.camera_index = None
        self.last_frame = None

    def find_camera(self):
        print("正在搜索摄像头...")

        for index in CAMERA_INDEX_LIST:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

            if cap.isOpened():
                ret, frame = cap.read()

                if ret and frame is not None:
                    self.cap = cap
                    self.camera_index = index

                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

                    print(f"[CAMERA OK] 找到摄像头，Camera Index = {index}")
                    return True

            cap.release()

        print("[CAMERA ERROR] 没有找到可用摄像头。")
        print("请检查：")
        print("1. 摄像头 USB 是否插好")
        print("2. 摄像头是否被微信、腾讯会议、浏览器等占用")
        print("3. Windows 摄像头权限是否打开")
        return False

    def read_frame(self):
        if self.cap is None:
            return None

        ret, frame = self.cap.read()

        if not ret or frame is None:
            print("[CAMERA ERROR] 无法读取摄像头画面。")
            return None

        self.last_frame = frame
        return frame

    def show_once(self):
        frame = self.read_frame()

        if frame is None:
            return None

        self.draw_overlay(frame)
        cv2.imshow("Atlas 5.0 Final Camera", frame)
        cv2.waitKey(1)

        return frame

    def draw_overlay(self, frame):
        cv2.putText(
            frame,
            "Atlas 5.0 Final Program",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Camera Index: {self.camera_index}",
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "Voice + Camera + OLED + Servo",
            (20, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "Control from PyCharm Terminal",
            (20, 125),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2
        )

    def save_snapshot(self):
        frame = self.show_once()

        if frame is None:
            print("[PHOTO ERROR] 没有可保存的画面。")
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = SNAPSHOT_DIR / f"atlas5_final_snapshot_{timestamp}.jpg"

        cv2.imwrite(str(file_path), frame)
        print(f"[PHOTO OK] 已保存截图：{file_path}")

        return str(file_path)

    def close(self):
        if self.cap is not None:
            self.cap.release()

        cv2.destroyAllWindows()
        print("[CAMERA OK] Camera closed.")


# =====================================================
# Voice Input
# =====================================================

class AtlasVoiceInput:
    def list_audio_devices(self):
        print("\n当前电脑音频设备：")
        print("-" * 70)

        try:
            devices = sd.query_devices()

            for index, device in enumerate(devices):
                name = device.get("name", "Unknown")
                max_input_channels = device.get("max_input_channels", 0)
                max_output_channels = device.get("max_output_channels", 0)

                print(
                    f"{index}. {name} | "
                    f"输入通道：{max_input_channels} | "
                    f"输出通道：{max_output_channels}"
                )

            print("-" * 70)

        except Exception as error:
            print(f"音频设备读取失败：{error}")

    def record_audio_to_temp_wav(self, duration_seconds=5, sample_rate=16000):
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

    def recognize_speech_from_wav(self, wav_path, language):
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

    def record_and_recognize_once(self, language="en-US", duration_seconds=5):
        wav_path = self.record_audio_to_temp_wav(
            duration_seconds=duration_seconds,
            sample_rate=SAMPLE_RATE
        )

        recognized_text = self.recognize_speech_from_wav(
            wav_path,
            language=language
        )

        return recognized_text, wav_path


# =====================================================
# Voice Output
# =====================================================

class AtlasVoiceOutput:
    def __init__(self, rate=165, volume=1.0, voice_index=None):
        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index

    def create_tts_engine(self):
        try:
            engine = pyttsx3.init()
            return engine

        except Exception as error:
            raise RuntimeError(f"pyttsx3 初始化失败：{error}")

    def list_voices(self):
        print("\n正在读取电脑可用语音列表...")

        try:
            engine = self.create_tts_engine()
            voices = engine.getProperty("voices")

            print("\n电脑可用语音：")
            print("-" * 70)

            if not voices:
                print("没有读取到语音。")
                return

            for index, voice in enumerate(voices):
                voice_name = getattr(voice, "name", "Unknown")
                voice_id = getattr(voice, "id", "Unknown")
                languages = getattr(voice, "languages", [])

                print(f"{index}. 语音名称：{voice_name}")
                print(f"   语音 ID：{voice_id}")
                print(f"   languages：{languages}")
                print("-" * 70)

        except Exception as error:
            print(f"读取语音列表失败：{error}")

    def speak_text(self, text, rate=None, volume=None, voice_index=None):
        if not text:
            text = "Hello Eric. This is Atlas."

        if rate is None:
            rate = self.rate

        if volume is None:
            volume = self.volume

        if voice_index is None:
            voice_index = self.voice_index

        try:
            engine = self.create_tts_engine()

            voices = engine.getProperty("voices")
            selected_voice_name = "default"

            if voice_index is not None and voices:
                if 0 <= voice_index < len(voices):
                    selected_voice = voices[voice_index]
                    engine.setProperty("voice", selected_voice.id)
                    selected_voice_name = getattr(
                        selected_voice,
                        "name",
                        "selected_voice"
                    )

            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)

            print("\nAtlas 正在说：")
            print("-" * 70)
            print(text)
            print("-" * 70)

            engine.say(text)
            engine.runAndWait()

            return selected_voice_name

        except Exception as error:
            print(f"语音输出失败：{error}")
            return "error"


# =====================================================
# Safe Behavior Controller
# =====================================================

class AtlasSafeBehaviorController:
    def __init__(self, hal: AtlasHAL):
        self.hal = hal

    def run_behavior(self, behavior_name):
        print()
        print("========================================")
        print(f"[SAFE BEHAVIOR] {behavior_name}")
        print("========================================")

        if not self.hal.arm():
            print("[SAFE BEHAVIOR ERROR] ARM failed.")
            return False

        ok = False

        if behavior_name == "IDLE":
            ok = self.hal.idle()

        elif behavior_name == "LISTENING":
            ok = self.hal.listening()

        elif behavior_name == "THINKING":
            ok = self.hal.thinking()

        elif behavior_name == "SUCCESS":
            ok = self.hal.success()

        elif behavior_name == "ENCOURAGE":
            ok = self.hal.encourage()

        elif behavior_name == "WARNING":
            ok = self.hal.warning()

        elif behavior_name == "ERROR":
            ok = self.hal.error()

        elif behavior_name == "BEHAVIOR_TEST":
            ok = self.hal.behavior_test()

        else:
            print("[SAFE BEHAVIOR ERROR] Unknown behavior.")
            ok = False

        print("[SAFE BEHAVIOR] DISARM after action.")
        self.hal.disarm()

        return ok

    def run_dialogue_sequence(self, final_behavior):
        """
        Stable sequence for voice interaction:
        ARM -> LISTENING -> THINKING -> final behavior -> IDLE -> DISARM
        """

        print()
        print("========================================")
        print(f"[DIALOGUE SEQUENCE] Final behavior: {final_behavior}")
        print("========================================")

        if not self.hal.arm():
            print("[DIALOGUE ERROR] ARM failed.")
            return False

        if not self.hal.listening():
            self.hal.disarm()
            return False

        if not self.hal.thinking():
            self.hal.disarm()
            return False

        ok = False

        if final_behavior == "SUCCESS":
            ok = self.hal.success()

        elif final_behavior == "ENCOURAGE":
            ok = self.hal.encourage()

        elif final_behavior == "WARNING":
            ok = self.hal.warning()

        elif final_behavior == "ERROR":
            ok = self.hal.error()

        else:
            ok = self.hal.success()

        self.hal.idle()
        self.hal.disarm()

        return ok


# =====================================================
# Dialogue Engine
# =====================================================

class AtlasDialogueEngine:
    def __init__(
        self,
        voice_output: AtlasVoiceOutput,
        behavior_controller: AtlasSafeBehaviorController,
        camera: AtlasCamera
    ):
        self.voice_output = voice_output
        self.behavior = behavior_controller
        self.camera = camera

    def normalize_text(self, text):
        return text.strip().lower()

    def classify_input(self, user_text):
        text = self.normalize_text(user_text)

        if text in ["q", "quit", "exit", "退出"]:
            return DialogueIntent.QUIT

        if text in ["idle", "rest", "stop", "待机", "休息"]:
            return DialogueIntent.IDLE_EVENT

        if text in ["test", "behavior test", "行为测试"]:
            return DialogueIntent.BEHAVIOR_TEST_EVENT

        if text in ["hello", "hi", "hey", "hello atlas", "你好", "嗨"]:
            return DialogueIntent.GREETING

        if text in ["who are you", "what are you", "introduce yourself", "你是谁", "介绍一下你自己"]:
            return DialogueIntent.SELF_INTRO

        if "what can you do" in text or "你能做什么" in text or "功能" in text:
            return DialogueIntent.SELF_INTRO

        if text in ["help", "encourage me", "encourage", "我需要鼓励", "鼓励我", "加油"]:
            return DialogueIntent.ENCOURAGEMENT_REQUEST

        if "tired" in text or "sad" in text or "nervous" in text or "stressed" in text:
            return DialogueIntent.ENCOURAGEMENT_REQUEST

        if "累" in text or "难过" in text or "紧张" in text or "压力" in text:
            return DialogueIntent.ENCOURAGEMENT_REQUEST

        if text in ["warning", "warn", "danger", "careful", "警告", "危险", "小心"]:
            return DialogueIntent.WARNING_EVENT

        if "danger" in text or "warning" in text or "careful" in text:
            return DialogueIntent.WARNING_EVENT

        if "危险" in text or "警告" in text or "小心" in text:
            return DialogueIntent.WARNING_EVENT

        if text in ["error", "wrong", "fail", "failed", "bug", "错误", "失败", "报错"]:
            return DialogueIntent.ERROR_EVENT

        if "error" in text or "failed" in text or "bug" in text or "wrong" in text:
            return DialogueIntent.ERROR_EVENT

        if "错误" in text or "失败" in text or "报错" in text:
            return DialogueIntent.ERROR_EVENT

        if "status" in text or "system" in text or "battery" in text:
            return DialogueIntent.STATUS_CHECK

        if "状态" in text or "系统" in text or "电池" in text:
            return DialogueIntent.STATUS_CHECK

        if "camera" in text or "vision" in text or "see" in text:
            return DialogueIntent.CAMERA_EVENT

        if "摄像头" in text or "视觉" in text or "看见" in text:
            return DialogueIntent.CAMERA_EVENT

        if "atlas" in text or "robot" in text or "project" in text:
            return DialogueIntent.PROJECT_QUESTION

        if "机器人" in text or "项目" in text:
            return DialogueIntent.PROJECT_QUESTION

        if "what" in text or "why" in text or "how" in text:
            return DialogueIntent.NORMAL_QUESTION

        if "什么" in text or "为什么" in text or "怎么" in text or "如何" in text:
            return DialogueIntent.NORMAL_QUESTION

        if len(text) > 0:
            return DialogueIntent.NORMAL_QUESTION

        return DialogueIntent.UNKNOWN

    def generate_reply(self, intent, user_text):
        if intent == DialogueIntent.GREETING:
            return "Hello Eric. I am Atlas. My voice, camera, OLED, lights, and head movement are running together."

        if intent == DialogueIntent.SELF_INTRO:
            return (
                "I am Atlas 5.0, a desktop companion robot prototype. "
                "I can listen, speak, show camera preview, display states on OLED, and move my head."
            )

        if intent == DialogueIntent.NORMAL_QUESTION:
            return (
                "I heard your question. This final version is still rule based. "
                "In a future stage, I can connect to a real AI brain."
            )

        if intent == DialogueIntent.ENCOURAGEMENT_REQUEST:
            return (
                "Keep going, Eric. This is the final integrated version of Atlas 5.0. "
                "You have connected voice input, voice output, camera, OLED, and hardware behavior."
            )

        if intent == DialogueIntent.WARNING_EVENT:
            return "Warning detected. Please check the cables, servo power, and mechanical movement."

        if intent == DialogueIntent.ERROR_EVENT:
            return "Error detected. Stop and test one module at a time."

        if intent == DialogueIntent.STATUS_CHECK:
            return (
                "System status. Camera preview is active. Voice input is active. "
                "Voice output is active. ESP32 OLED body firmware is active."
            )

        if intent == DialogueIntent.CAMERA_EVENT:
            return "Camera is active. I can show the camera preview through Python OpenCV."

        if intent == DialogueIntent.PROJECT_QUESTION:
            return (
                "Atlas 5.0 final version combines camera input, voice input, voice output, "
                "OLED state display, LED feedback, and pan tilt movement."
            )

        if intent == DialogueIntent.IDLE_EVENT:
            return "Atlas is returning to idle state."

        if intent == DialogueIntent.BEHAVIOR_TEST_EVENT:
            return "Starting behavior test."

        return "I did not understand clearly, but the final system is still running."

    def final_behavior_for_intent(self, intent):
        if intent == DialogueIntent.ENCOURAGEMENT_REQUEST:
            return "ENCOURAGE"

        if intent == DialogueIntent.WARNING_EVENT:
            return "WARNING"

        if intent == DialogueIntent.ERROR_EVENT:
            return "ERROR"

        return "SUCCESS"

    def handle_recognized_text(self, recognized_text, language_name):
        print()
        print("===================================================")
        print(f"[VOICE RECOGNIZED] {recognized_text}")
        print("===================================================")

        if not recognized_text:
            reply = "I did not hear clearly. Please try again."

            print(f"[ATLAS REPLY] {reply}")
            self.voice_output.speak_text(reply)
            self.behavior.run_behavior("ERROR")

            save_record(
                language=language_name,
                recognized_text="",
                intent="UNKNOWN",
                reply=reply,
                status="not_recognized"
            )

            write_log(
                "Atlas 5.0 Final 语音未识别",
                reply
            )

            return True

        intent = self.classify_input(recognized_text)
        reply = self.generate_reply(intent, recognized_text)

        print(f"[DIALOGUE INTENT] {intent.value}")
        print(f"[ATLAS REPLY] {reply}")

        if intent == DialogueIntent.QUIT:
            return False

        if intent == DialogueIntent.BEHAVIOR_TEST_EVENT:
            self.voice_output.speak_text(reply)
            self.behavior.run_behavior("BEHAVIOR_TEST")

        elif intent == DialogueIntent.IDLE_EVENT:
            self.voice_output.speak_text(reply)
            self.behavior.run_behavior("IDLE")

        else:
            final_behavior = self.final_behavior_for_intent(intent)

            # First speak the reply, then move. This reduces timing conflicts.
            self.voice_output.speak_text(reply)
            self.behavior.run_dialogue_sequence(final_behavior)

        snapshot_path = ""

        if intent == DialogueIntent.CAMERA_EVENT:
            snapshot_path = self.camera.save_snapshot()

        save_record(
            language=language_name,
            recognized_text=recognized_text,
            intent=intent.value,
            reply=reply,
            status="recognized",
            snapshot_path=snapshot_path
        )

        write_log(
            "Atlas 5.0 Final 语音 + 摄像头 + 硬件对话成功",
            (
                f"识别文本：{recognized_text}\n"
                f"语言：{language_name}\n"
                f"意图：{intent.value}\n"
                f"回复：{reply}\n"
                f"截图：{snapshot_path}"
            )
        )

        return True


# =====================================================
# Menu
# =====================================================

def print_menu():
    print()
    print("========== Atlas 5.0 Final Stable Program v1 ==========")
    print("请输入数字或字母，然后按 Enter：")
    print()
    print("1  -> 英文语音对话")
    print("2  -> 中文语音对话")
    print("3  -> 查看音频输入设备")
    print("4  -> 查看电脑语音输出列表")
    print("5  -> 保存摄像头截图")
    print("6  -> 刷新摄像头画面")
    print("7  -> Behavior Test")
    print()
    print("i  -> 手动 IDLE")
    print("l  -> 手动 LISTENING")
    print("t  -> 手动 THINKING")
    print("s  -> 手动 SUCCESS")
    print("e  -> 手动 ENCOURAGE")
    print("w  -> 手动 WARNING")
    print("r  -> 手动 ERROR")
    print()
    print("q  -> 退出")
    print("=======================================================")


def get_duration_seconds():
    duration_text = input("录音几秒？直接回车默认 5 秒：").strip()

    if duration_text.isdigit():
        duration_seconds = int(duration_text)
    else:
        duration_seconds = DEFAULT_RECORD_SECONDS

    if duration_seconds < 2:
        duration_seconds = 2

    if duration_seconds > 15:
        duration_seconds = 15

    return duration_seconds


# =====================================================
# Main
# =====================================================

def main():
    print("Atlas 5.0 Final Stable Program v1")
    print("本程序整合：摄像头、语音输入、语音输出、OLED、LED、舵机。")
    print("不修改 ESP32 固件。")
    print()
    print("运行前确认：")
    print("1. ESP32 正在运行 atlas5_body_firmware_oled_v1_success.ino")
    print("2. Arduino Serial Monitor 已关闭")
    print("3. ESP32 USB 已连接")
    print("4. C950 摄像头 USB 已连接电脑")
    print("5. 四节 AA 电池盒稍后按提示打开")
    print("6. 电脑网络可用")
    print()

    write_log(
        "Atlas 5.0 Final 程序启动",
        "程序启动。整合 camera + voice input + voice output + ESP32 OLED body firmware。"
    )

    hal = AtlasHAL(SERIAL_PORT, BAUD_RATE, TIMEOUT)
    camera = AtlasCamera()
    voice_input = AtlasVoiceInput()
    voice_output = AtlasVoiceOutput(rate=165, volume=1.0, voice_index=None)

    if not hal.connect():
        return

    if not camera.find_camera():
        hal.close()
        return

    behavior = AtlasSafeBehaviorController(hal)
    dialogue = AtlasDialogueEngine(voice_output, behavior, camera)

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
        behavior.run_behavior("IDLE")

        camera.show_once()

        voice_output.speak_text("Atlas 5.0 final program is ready.")

        while True:
            camera.show_once()
            print_menu()

            command = input("请输入指令：").strip().lower()

            camera.show_once()

            if command == "1":
                print("\n英文语音对话。")
                print("建议说：hello atlas / who are you / I am tired / warning / error / status / camera")
                duration_seconds = get_duration_seconds()

                behavior.run_behavior("LISTENING")

                try:
                    recognized_text, wav_path = voice_input.record_and_recognize_once(
                        language="en-US",
                        duration_seconds=duration_seconds
                    )

                    print(f"[WAV] {wav_path}")

                    should_continue = dialogue.handle_recognized_text(
                        recognized_text,
                        language_name="English"
                    )

                    if not should_continue:
                        break

                except Exception as error:
                    print(f"\n[VOICE ERROR] {error}")
                    voice_output.speak_text("Voice input failed. Please check the network or microphone.")
                    behavior.run_behavior("ERROR")

            elif command == "2":
                print("\n中文语音对话。")
                print("建议说：你好 / 你是谁 / 我需要鼓励 / 警告 / 错误 / 状态 / 摄像头")
                duration_seconds = get_duration_seconds()

                behavior.run_behavior("LISTENING")

                try:
                    recognized_text, wav_path = voice_input.record_and_recognize_once(
                        language="zh-CN",
                        duration_seconds=duration_seconds
                    )

                    print(f"[WAV] {wav_path}")

                    should_continue = dialogue.handle_recognized_text(
                        recognized_text,
                        language_name="中文"
                    )

                    if not should_continue:
                        break

                except Exception as error:
                    print(f"\n[VOICE ERROR] {error}")
                    voice_output.speak_text("语音输入失败，请检查网络或麦克风。")
                    behavior.run_behavior("ERROR")

            elif command == "3":
                voice_input.list_audio_devices()

            elif command == "4":
                voice_output.list_voices()

            elif command == "5":
                snapshot_path = camera.save_snapshot()
                voice_output.speak_text("Camera snapshot saved.")
                write_log(
                    "Atlas 5.0 Final 摄像头截图",
                    f"截图文件：{snapshot_path}"
                )

            elif command == "6":
                camera.show_once()
                print("[CAMERA] 已刷新画面。")

            elif command == "7":
                voice_output.speak_text("Starting behavior test.")
                behavior.run_behavior("BEHAVIOR_TEST")

            elif command == "i":
                behavior.run_behavior("IDLE")

            elif command == "l":
                behavior.run_behavior("LISTENING")

            elif command == "t":
                behavior.run_behavior("THINKING")

            elif command == "s":
                behavior.run_behavior("SUCCESS")

            elif command == "e":
                behavior.run_behavior("ENCOURAGE")

            elif command == "w":
                behavior.run_behavior("WARNING")

            elif command == "r":
                behavior.run_behavior("ERROR")

            elif command == "q":
                voice_output.speak_text("Atlas is shutting down.")
                break

            else:
                print("[INPUT ERROR] 无效指令。")
                voice_output.speak_text("Invalid command.")

    finally:
        print("\n[MAIN] Final DISARM and cleanup...")
        hal.disarm()
        hal.close()
        camera.close()

        write_log(
            "Atlas 5.0 Final 程序退出",
            "程序已退出。"
        )

        print("\n[MAIN OK] Program finished.")
        print("退出后请关闭四节 AA 电池盒。")


if __name__ == "__main__":
    main()