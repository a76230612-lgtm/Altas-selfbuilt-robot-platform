import json
import tempfile
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

import numpy as np
import pyttsx3
import serial
import sounddevice as sd
import speech_recognition as sr
from scipy.io.wavfile import write as write_wav


# =====================================================
# Atlas 5.0 Stage 10B
# Google Speech Recognition + pyttsx3 Voice Output
#
# Purpose:
# - Use the successful Atlas 4.0 voice input method.
# - Use the successful Atlas 4.0 voice output method.
# - Integrate voice input, dialogue reply, TTS output, and ESP32 behavior.
#
# This version does NOT use Vosk.
#
# Required packages:
# python -m pip install pyserial sounddevice scipy numpy SpeechRecognition pyttsx3
#
# ESP32 firmware:
# atlas5_stage4_behavior_firmware_v2_stable_success.ino
# =====================================================

SERIAL_PORT = "COM4"   # 改成你的 ESP32 端口，例如 COM3 / COM4 / COM5
BAUD_RATE = 115200
TIMEOUT = 2
READY_TEXT = "READY_FOR_NEXT_COMMAND"

BASE_DIR = Path(__file__).resolve().parent

PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"
VOICE_LOG_FILE = BASE_DIR / "atlas5_stage10b_voice_log.txt"
VOICE_DATA_FILE = BASE_DIR / "atlas5_stage10b_voice_data.json"

SAMPLE_RATE = 16000
DEFAULT_RECORD_SECONDS = 5


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
    BEHAVIOR_TEST_EVENT = "BEHAVIOR_TEST_EVENT"
    IDLE_EVENT = "IDLE_EVENT"
    QUIT = "QUIT"
    UNKNOWN = "UNKNOWN"


# =====================================================
# Logs
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
    print(f"[LOG] Voice Log: {VOICE_LOG_FILE}")
    print(f"[LOG] Project Log: {PROJECT_LOG_FILE}")


def create_default_voice_data():
    return {
        "student_name": "Eric",
        "version": "Atlas 5.0 Stage 10B Google Voice + TTS",
        "records": []
    }


def load_voice_data():
    if not VOICE_DATA_FILE.exists():
        data = create_default_voice_data()
        save_voice_data(data)
        return data

    try:
        with open(VOICE_DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        data = create_default_voice_data()

    if "records" not in data:
        data["records"] = []

    save_voice_data(data)
    return data


def save_voice_data(data):
    with open(VOICE_DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def save_voice_record(language, recognized_text, intent, reply, status):
    data = load_voice_data()

    record = {
        "time": get_now_text(),
        "language": language,
        "recognized_text": recognized_text,
        "intent": intent,
        "reply": reply,
        "status": status
    }

    data["records"].append(record)
    save_voice_data(data)


# =====================================================
# Python HAL
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

    def close(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            print("[HAL OK] Serial closed.")

    def read_startup_messages(self):
        print("\n[HAL INFO] Reading ESP32 startup messages...")
        start_time = time.time()

        while time.time() - start_time < 2:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line:
                    print("[ESP32]", line)
            else:
                time.sleep(0.05)

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

    def arm(self):
        return self.send("ARM", max_wait=8)

    def disarm(self):
        return self.send("DISARM", max_wait=6)

    def behavior(self, state: AtlasState):
        return self.send(state.value, max_wait=10)

    def behavior_test(self):
        return self.send("BEHAVIOR_TEST", max_wait=30)


# =====================================================
# Behavior State Machine
# =====================================================

class AtlasBehaviorStateMachine:
    def __init__(self, hal: AtlasHAL):
        self.hal = hal
        self.current_state = None
        self.is_armed = False

    def start(self):
        print("\n[STATE MACHINE] Starting Atlas...")

        if not self.hal.ping():
            print("[STATE MACHINE ERROR] PING failed.")
            return False

        if not self.hal.ledtest():
            print("[STATE MACHINE ERROR] LEDTEST failed.")
            return False

        print("\n[STATE MACHINE] 请确认四节 AA 电池盒已经打开。")
        input("打开电池盒后，按 Enter 继续...")

        if not self.hal.arm():
            print("[STATE MACHINE ERROR] ARM failed.")
            return False

        self.is_armed = True

        if not self.go_to_state(AtlasState.IDLE):
            print("[STATE MACHINE ERROR] Failed to enter IDLE.")
            return False

        print("[STATE MACHINE OK] Atlas started and entered IDLE.")
        return True

    def stop(self):
        print("\n[STATE MACHINE] Stopping Atlas...")

        if self.is_armed:
            self.hal.disarm()
            self.is_armed = False

        print("[STATE MACHINE OK] Atlas stopped.")

    def go_to_state(self, new_state: AtlasState):
        if not self.is_armed:
            print("[STATE MACHINE ERROR] Atlas is not armed.")
            return False

        print()
        print("========================================")
        print(f"[STATE MACHINE] Current state: {self.current_state}")
        print(f"[STATE MACHINE] Target state:  {new_state.value}")
        print("========================================")

        success = self.hal.behavior(new_state)

        if success:
            self.current_state = new_state
            print(f"[STATE MACHINE OK] New state: {self.current_state.value}")
            return True

        print(f"[STATE MACHINE ERROR] Failed to enter state: {new_state.value}")
        return False

    def run_sequence(self, states, pause_seconds=0.35):
        for state in states:
            ok = self.go_to_state(state)
            if not ok:
                return False
            time.sleep(pause_seconds)
        return True

    def run_behavior_test(self):
        return self.hal.behavior_test()


# =====================================================
# Voice Input: Atlas 4.0 method
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
# Voice Output: Atlas 4.0 method
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
# Dialogue Engine
# =====================================================

class AtlasDialogueEngine:
    def __init__(self, machine: AtlasBehaviorStateMachine, voice_output: AtlasVoiceOutput):
        self.machine = machine
        self.voice_output = voice_output

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
            return "Hello Eric. I am Atlas. I can hear you and speak now."

        if intent == DialogueIntent.SELF_INTRO:
            return (
                "I am Atlas 5.0, a desktop hardware robot prototype. "
                "I can listen to your voice, understand simple intent, speak a reply, "
                "and control my head and lights."
            )

        if intent == DialogueIntent.NORMAL_QUESTION:
            return (
                "I heard your question. This is a simulated answer. "
                "In a later stage, I can connect to a real AI brain."
            )

        if intent == DialogueIntent.ENCOURAGEMENT_REQUEST:
            return (
                "Keep going, Eric. You have already completed many difficult steps. "
                "Test one function at a time, and the robot will become more stable."
            )

        if intent == DialogueIntent.WARNING_EVENT:
            return "Warning detected. Please check the cables, power system, and mechanical movement."

        if intent == DialogueIntent.ERROR_EVENT:
            return "Error detected. Stop and test one module at a time."

        if intent == DialogueIntent.STATUS_CHECK:
            return (
                "System status. Voice input is active. Voice output is active. "
                "Python HAL is active. ESP32 behavior firmware is active."
            )

        if intent == DialogueIntent.PROJECT_QUESTION:
            return (
                "Atlas is currently using the Atlas 4.0 voice input and output method "
                "inside the Atlas 5.0 behavior system."
            )

        if intent == DialogueIntent.IDLE_EVENT:
            return "Atlas is returning to idle state."

        if intent == DialogueIntent.BEHAVIOR_TEST_EVENT:
            return "Starting behavior test."

        return "I did not understand clearly, but I am still running."

    def handle_recognized_text(self, recognized_text, language_name):
        print()
        print("===================================================")
        print(f"[VOICE RECOGNIZED] {recognized_text}")
        print("===================================================")

        if not recognized_text:
            reply = "I did not hear clearly. Please try again."
            print(f"[ATLAS REPLY] {reply}")

            self.voice_output.speak_text(reply)
            self.machine.run_sequence([
                AtlasState.ERROR,
                AtlasState.IDLE
            ])

            save_voice_record(
                language=language_name,
                recognized_text="",
                intent="UNKNOWN",
                reply=reply,
                status="not_recognized"
            )

            write_log(
                "Atlas 5.0 Stage 10B 语音未识别",
                reply
            )

            return True

        intent = self.classify_input(recognized_text)
        reply = self.generate_reply(intent, recognized_text)

        print(f"[DIALOGUE INTENT] {intent.value}")
        print(f"[ATLAS REPLY] {reply}")

        if intent == DialogueIntent.QUIT:
            return False

        if intent == DialogueIntent.IDLE_EVENT:
            self.machine.go_to_state(AtlasState.IDLE)
            self.voice_output.speak_text(reply)

        elif intent == DialogueIntent.BEHAVIOR_TEST_EVENT:
            self.voice_output.speak_text(reply)
            self.machine.run_behavior_test()
            self.machine.go_to_state(AtlasState.IDLE)

        elif intent == DialogueIntent.ENCOURAGEMENT_REQUEST:
            self.machine.go_to_state(AtlasState.THINKING)
            self.voice_output.speak_text(reply)
            self.machine.run_sequence([
                AtlasState.ENCOURAGE,
                AtlasState.IDLE
            ])

        elif intent == DialogueIntent.WARNING_EVENT:
            self.machine.go_to_state(AtlasState.THINKING)
            self.voice_output.speak_text(reply)
            self.machine.run_sequence([
                AtlasState.WARNING,
                AtlasState.IDLE
            ])

        elif intent == DialogueIntent.ERROR_EVENT:
            self.machine.go_to_state(AtlasState.THINKING)
            self.voice_output.speak_text(reply)
            self.machine.run_sequence([
                AtlasState.ERROR,
                AtlasState.IDLE
            ])

        else:
            self.machine.go_to_state(AtlasState.THINKING)
            self.voice_output.speak_text(reply)
            self.machine.run_sequence([
                AtlasState.SUCCESS,
                AtlasState.IDLE
            ])

        save_voice_record(
            language=language_name,
            recognized_text=recognized_text,
            intent=intent.value,
            reply=reply,
            status="recognized"
        )

        write_log(
            "Atlas 5.0 Stage 10B 语音对话成功",
            (
                f"识别文本：{recognized_text}\n"
                f"意图：{intent.value}\n"
                f"回复：{reply}"
            )
        )

        return True


# =====================================================
# Main
# =====================================================

def print_menu():
    print()
    print("============== Atlas 5.0 Stage 10B ==============")
    print("1. 查看音频输入设备")
    print("2. 查看电脑可用语音输出列表")
    print("3. 英文语音对话测试")
    print("4. 中文语音对话测试")
    print("5. Behavior Test")
    print("6. 退出")
    print("=================================================")


def main():
    print("Atlas 5.0 Stage 10B - Google Voice Input + pyttsx3 Voice Output")
    print("本阶段使用 Atlas 4.0 已成功的 Voice Input / Voice Output 方法。")
    print("不使用 Vosk，不需要模型路径。")
    print()
    print("运行前确认：")
    print("1. ESP32 正在运行 Stage 4 Behavior Firmware v2 Stable Success")
    print("2. Arduino Serial Monitor 已关闭")
    print("3. ESP32 USB 已连接")
    print("4. 四节 AA 电池盒稍后按提示打开")
    print("5. 电脑网络可用")
    print()

    write_log(
        "Atlas 5.0 Stage 10B 程序启动",
        "程序启动。使用 speech_recognition + pyttsx3。"
    )

    voice_input = AtlasVoiceInput()
    voice_output = AtlasVoiceOutput(rate=165, volume=1.0, voice_index=None)

    hal = AtlasHAL(SERIAL_PORT, BAUD_RATE, TIMEOUT)

    if not hal.connect():
        return

    machine = AtlasBehaviorStateMachine(hal)
    dialogue = AtlasDialogueEngine(machine, voice_output)

    try:
        if not machine.start():
            print("[MAIN ERROR] Could not start Atlas.")
            return

        while True:
            print_menu()
            choice = input("请输入数字 1-6：").strip()

            if choice == "1":
                voice_input.list_audio_devices()

            elif choice == "2":
                voice_output.list_voices()

            elif choice == "3":
                print("\n英文语音对话测试。")
                print("建议说：hello atlas / who are you / I am tired / warning / error / status")
                duration_text = input("录音几秒？直接回车默认 5 秒：").strip()

                if duration_text.isdigit():
                    duration_seconds = int(duration_text)
                else:
                    duration_seconds = DEFAULT_RECORD_SECONDS

                if duration_seconds < 2:
                    duration_seconds = 2

                if duration_seconds > 15:
                    duration_seconds = 15

                machine.go_to_state(AtlasState.LISTENING)

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
                    machine.run_sequence([
                        AtlasState.ERROR,
                        AtlasState.IDLE
                    ])

            elif choice == "4":
                print("\n中文语音对话测试。")
                print("建议说：你好 / 你是谁 / 我需要鼓励 / 警告 / 错误 / 状态")
                duration_text = input("录音几秒？直接回车默认 5 秒：").strip()

                if duration_text.isdigit():
                    duration_seconds = int(duration_text)
                else:
                    duration_seconds = DEFAULT_RECORD_SECONDS

                if duration_seconds < 2:
                    duration_seconds = 2

                if duration_seconds > 15:
                    duration_seconds = 15

                machine.go_to_state(AtlasState.LISTENING)

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
                    machine.run_sequence([
                        AtlasState.ERROR,
                        AtlasState.IDLE
                    ])

            elif choice == "5":
                voice_output.speak_text("Starting behavior test.")
                machine.run_behavior_test()
                machine.go_to_state(AtlasState.IDLE)

            elif choice == "6":
                voice_output.speak_text("Atlas is shutting down.")
                break

            else:
                print("输入无效，请输入 1 到 6。")

    finally:
        machine.stop()
        hal.close()

        write_log(
            "Atlas 5.0 Stage 10B 程序退出",
            "程序已退出。"
        )

        print("\n程序已退出。")
        print("退出后请关闭四节 AA 电池盒。")


if __name__ == "__main__":
    main()