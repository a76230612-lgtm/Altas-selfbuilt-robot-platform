import serial
import time
import sounddevice as sd
from scipy.io.wavfile import write
from enum import Enum
from datetime import datetime
import os


# =====================================================
# Atlas 5.0 Stage 9
# Real Voice Input Preparation Layer
#
# Purpose:
# - Use real microphone recording.
# - Trigger Atlas LISTENING behavior while recording.
# - Save recorded voice as WAV.
# - Ask user to manually type what was said.
# - Send the confirmed text into the Stage 8 dialogue engine.
#
# This stage does NOT use automatic speech recognition yet.
#
# ESP32 firmware:
# - atlas5_stage4_behavior_firmware_v2_stable_success.ino
#
# Hardware:
# - ESP32 powered by USB
# - Servos powered by 4xAA battery box
# - Battery negative connected to ESP32 GND
#
# Required Python packages:
# pip install pyserial sounddevice scipy
# =====================================================

SERIAL_PORT = "COM6"   # 改成你的 ESP32 端口，例如 COM3 / COM4 / COM5
BAUD_RATE = 115200
TIMEOUT = 2
READY_TEXT = "READY_FOR_NEXT_COMMAND"

SAMPLE_RATE = 16000
RECORD_SECONDS = 4

VOICE_DIR = "atlas5_voice_records"
DIALOGUE_LOG_FILE = "atlas5_stage9_voice_dialogue_log.txt"


# =====================================================
# Behavior States
# =====================================================

class AtlasState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SUCCESS = "SUCCESS"
    ENCOURAGE = "ENCOURAGE"
    WARNING = "WARNING"
    ERROR = "ERROR"


# =====================================================
# Dialogue Intent Types
# =====================================================

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
        except serial.SerialException as e:
            print("[HAL ERROR] Could not connect to ESP32.")
            print("Reason:", e)
            print()
            print("请检查：")
            print("1. Arduino Serial Monitor 是否已经关闭")
            print("2. COM 端口是否写对")
            print("3. ESP32 是否插好")
            print("4. USB 线是否正常")
            return False

    def close(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            print("[HAL OK] Serial closed.")

    def read_startup_messages(self):
        print("\n[HAL INFO] Reading ESP32 startup messages...")
        start_time = time.time()

        while time.time() - start_time < 2.0:
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
        except serial.SerialException as e:
            print("[HAL ERROR] Failed to write command.")
            print("Reason:", e)
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

            except serial.SerialException as e:
                print("[HAL ERROR] Serial read failed.")
                print("Reason:", e)
                return False

        if not got_ready:
            print("[HAL WARNING] Did not receive READY_FOR_NEXT_COMMAND.")
            print("可能原因：")
            print("1. Atlas 还在执行动作")
            print("2. 舵机卡住")
            print("3. ESP32 重启")
            print("4. 串口暂时异常")
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

        print("\n[STATE MACHINE] Please make sure the 4xAA battery box is ON.")
        input("确认四节 AA 电池盒已经打开后，按 Enter 继续...")

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

    def run_behavior_test(self):
        if not self.is_armed:
            print("[STATE MACHINE ERROR] Atlas is not armed.")
            return False

        print("\n[STATE MACHINE] Running BEHAVIOR_TEST...")
        success = self.hal.behavior_test()

        if success:
            self.current_state = AtlasState.IDLE
            print("[STATE MACHINE OK] BEHAVIOR_TEST finished.")
            return True

        print("[STATE MACHINE ERROR] BEHAVIOR_TEST failed.")
        return False

    def run_sequence(self, states, pause_seconds=0.35):
        for state in states:
            ok = self.go_to_state(state)
            if not ok:
                return False
            time.sleep(pause_seconds)
        return True


# =====================================================
# Voice Recorder
# =====================================================

class AtlasVoiceRecorder:
    def __init__(self, sample_rate=16000, record_seconds=4, output_dir=VOICE_DIR):
        self.sample_rate = sample_rate
        self.record_seconds = record_seconds
        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def show_devices(self):
        print("\n========== Audio Devices ==========")
        print(sd.query_devices())
        print("===================================")

    def record_once(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            self.output_dir,
            f"atlas5_voice_{timestamp}.wav"
        )

        print()
        print("[VOICE] Recording started.")
        print(f"[VOICE] Please speak for {self.record_seconds} seconds...")

        audio = sd.rec(
            int(self.record_seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        write(filename, self.sample_rate, audio)

        print("[VOICE] Recording finished.")
        print(f"[VOICE] Saved: {filename}")

        return filename


# =====================================================
# Dialogue Engine
# =====================================================

class AtlasDialogueEngine:
    def __init__(self, state_machine: AtlasBehaviorStateMachine):
        self.machine = state_machine
        self.dialogue_count = 0

    def classify_input(self, user_text: str) -> DialogueIntent:
        text = user_text.strip().lower()

        if text in ["q", "quit", "exit", "退出"]:
            return DialogueIntent.QUIT

        if text in ["idle", "rest", "stop", "待机", "休息"]:
            return DialogueIntent.IDLE_EVENT

        if text in ["test", "behavior test", "行为测试"]:
            return DialogueIntent.BEHAVIOR_TEST_EVENT

        if text in ["hello", "hi", "hey", "你好", "嗨", "hello atlas"]:
            return DialogueIntent.GREETING

        if text in ["who are you", "what are you", "introduce yourself", "你是谁", "介绍一下你自己"]:
            return DialogueIntent.SELF_INTRO

        if "what can you do" in text or "你能做什么" in text or "功能" in text:
            return DialogueIntent.SELF_INTRO

        if text in ["help", "encourage me", "我需要鼓励", "鼓励我", "加油"]:
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

        if "status" in text or "system" in text or "battery" in text or "状态" in text or "系统" in text or "电池" in text:
            return DialogueIntent.STATUS_CHECK

        if "atlas" in text or "robot" in text or "project" in text or "机器人" in text or "项目" in text:
            return DialogueIntent.PROJECT_QUESTION

        if "?" in text or "what" in text or "why" in text or "how" in text:
            return DialogueIntent.NORMAL_QUESTION

        if "什么" in text or "为什么" in text or "怎么" in text or "如何" in text:
            return DialogueIntent.NORMAL_QUESTION

        if len(text) > 0:
            return DialogueIntent.NORMAL_QUESTION

        return DialogueIntent.UNKNOWN

    def generate_reply(self, intent: DialogueIntent, user_text: str) -> str:
        if intent == DialogueIntent.GREETING:
            return "Hello. I am Atlas. I heard your voice input."

        if intent == DialogueIntent.SELF_INTRO:
            return (
                "I am Atlas 5.0, a hardware robot prototype. "
                "I can now react to recorded voice input through a Python dialogue flow."
            )

        if intent == DialogueIntent.NORMAL_QUESTION:
            return (
                "I understood the confirmed text from your voice input. "
                "This is still a simulated response. Real speech recognition will be added later."
            )

        if intent == DialogueIntent.ENCOURAGEMENT_REQUEST:
            return (
                "Keep going. You have already completed ESP32 control, Python HAL, "
                "behavior state machine, dialogue flow, and now microphone input preparation."
            )

        if intent == DialogueIntent.WARNING_EVENT:
            return "Warning detected. Please check the robot cables, power, and mechanical movement."

        if intent == DialogueIntent.ERROR_EVENT:
            return "Error detected. Stop and test one module at a time."

        if intent == DialogueIntent.STATUS_CHECK:
            return (
                "System status: microphone recording is active, dialogue flow is active, "
                "Python HAL is active, and ESP32 behavior firmware is active."
            )

        if intent == DialogueIntent.PROJECT_QUESTION:
            return (
                "Atlas is currently in Stage 9. "
                "The goal is to prepare real voice input before adding automatic speech recognition."
            )

        if intent == DialogueIntent.IDLE_EVENT:
            return "Atlas is returning to idle state."

        if intent == DialogueIntent.BEHAVIOR_TEST_EVENT:
            return "Starting behavior test."

        return "Input processed."

    def log_dialogue(self, user_text: str, intent: DialogueIntent, reply: str, audio_file=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        line = (
            f"[{timestamp}] "
            f"AUDIO: {audio_file} | "
            f"CONFIRMED_TEXT: {user_text} | "
            f"INTENT: {intent.value} | "
            f"ATLAS: {reply}\n"
        )

        try:
            with open(DIALOGUE_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError as e:
            print("[LOG WARNING] Could not write dialogue log.")
            print("Reason:", e)

    def handle_confirmed_text(self, user_text: str, audio_file=None):
        intent = self.classify_input(user_text)

        print()
        print("===================================================")
        print(f"[CONFIRMED TEXT] {user_text}")
        print(f"[DIALOGUE ENGINE] Intent: {intent.value}")
        print(f"[AUDIO FILE] {audio_file}")
        print("===================================================")

        if intent == DialogueIntent.QUIT:
            return False

        if intent == DialogueIntent.IDLE_EVENT:
            reply = self.generate_reply(intent, user_text)
            print(f"[ATLAS REPLY] {reply}")
            self.log_dialogue(user_text, intent, reply, audio_file)
            self.machine.go_to_state(AtlasState.IDLE)
            return True

        if intent == DialogueIntent.BEHAVIOR_TEST_EVENT:
            reply = self.generate_reply(intent, user_text)
            print(f"[ATLAS REPLY] {reply}")
            self.log_dialogue(user_text, intent, reply, audio_file)
            self.machine.run_behavior_test()
            return True

        if intent == DialogueIntent.WARNING_EVENT:
            return self.dialogue_warning(user_text, intent, audio_file)

        if intent == DialogueIntent.ERROR_EVENT:
            return self.dialogue_error(user_text, intent, audio_file)

        if intent == DialogueIntent.ENCOURAGEMENT_REQUEST:
            return self.dialogue_encouragement(user_text, intent, audio_file)

        return self.dialogue_normal(user_text, intent, audio_file)

    def dialogue_normal(self, user_text: str, intent: DialogueIntent, audio_file=None):
        self.dialogue_count += 1

        self.machine.run_sequence([
            AtlasState.THINKING
        ])

        reply = self.generate_reply(intent, user_text)

        print()
        print(f"[ATLAS REPLY] {reply}")
        self.log_dialogue(user_text, intent, reply, audio_file)

        self.machine.run_sequence([
            AtlasState.SUCCESS,
            AtlasState.IDLE
        ])

        return True

    def dialogue_encouragement(self, user_text: str, intent: DialogueIntent, audio_file=None):
        self.dialogue_count += 1

        self.machine.run_sequence([
            AtlasState.THINKING
        ])

        reply = self.generate_reply(intent, user_text)

        print()
        print(f"[ATLAS REPLY] {reply}")
        self.log_dialogue(user_text, intent, reply, audio_file)

        self.machine.run_sequence([
            AtlasState.ENCOURAGE,
            AtlasState.IDLE
        ])

        return True

    def dialogue_warning(self, user_text: str, intent: DialogueIntent, audio_file=None):
        self.dialogue_count += 1

        self.machine.run_sequence([
            AtlasState.THINKING
        ])

        reply = self.generate_reply(intent, user_text)

        print()
        print(f"[ATLAS REPLY] {reply}")
        self.log_dialogue(user_text, intent, reply, audio_file)

        self.machine.run_sequence([
            AtlasState.WARNING,
            AtlasState.IDLE
        ])

        return True

    def dialogue_error(self, user_text: str, intent: DialogueIntent, audio_file=None):
        self.dialogue_count += 1

        self.machine.run_sequence([
            AtlasState.THINKING
        ])

        reply = self.generate_reply(intent, user_text)

        print()
        print(f"[ATLAS REPLY] {reply}")
        self.log_dialogue(user_text, intent, reply, audio_file)

        self.machine.run_sequence([
            AtlasState.ERROR,
            AtlasState.IDLE
        ])

        return True


# =====================================================
# User Interface
# =====================================================

def print_help():
    print()
    print("============== Atlas 5.0 Stage 9 Voice Input Preparation ==============")
    print("This stage uses the real microphone, but does NOT use automatic speech recognition yet.")
    print()
    print("Flow:")
    print("1. Press Enter to start recording.")
    print("2. Atlas enters LISTENING.")
    print("3. Speak for 4 seconds.")
    print("4. Audio is saved as WAV.")
    print("5. Type what you said.")
    print("6. Atlas processes the confirmed text.")
    print()
    print("Try saying and then typing:")
    print("hello")
    print("who are you")
    print("what can you do?")
    print("I am tired")
    print("help")
    print("warning")
    print("error")
    print("status")
    print("test")
    print("q")
    print("=======================================================================")


def main():
    print("Atlas 5.0 Stage 9 - Real Voice Input Preparation Layer")
    print("Before running:")
    print("1. ESP32 must run Stage 4 Behavior Firmware v2 Stable Success.")
    print("2. Arduino Serial Monitor must be closed.")
    print("3. ESP32 USB must be connected.")
    print("4. Servos must be powered by 4xAA battery box.")
    print("5. Battery negative must connect to ESP32 GND.")
    print("6. This stage records real microphone audio but does not transcribe automatically.")
    print()

    hal = AtlasHAL(SERIAL_PORT, BAUD_RATE, TIMEOUT)

    if not hal.connect():
        return

    machine = AtlasBehaviorStateMachine(hal)
    recorder = AtlasVoiceRecorder()
    dialogue = AtlasDialogueEngine(machine)

    try:
        recorder.show_devices()

        if not machine.start():
            print("[MAIN ERROR] Could not start Atlas.")
            return

        print_help()

        while True:
            print()
            print("--------------------------------------------------")
            user_action = input("Press Enter to record voice, or type q to quit: ").strip().lower()

            if user_action in ["q", "quit", "exit"]:
                break

            machine.go_to_state(AtlasState.LISTENING)

            audio_file = recorder.record_once()

            confirmed_text = input("Type what you said in the recording: ").strip()

            if not confirmed_text:
                print("[INPUT WARNING] Empty confirmed text. Returning to IDLE.")
                machine.go_to_state(AtlasState.IDLE)
                continue

            should_continue = dialogue.handle_confirmed_text(
                confirmed_text,
                audio_file=audio_file
            )

            if not should_continue:
                break

    finally:
        machine.stop()
        hal.close()
        print("\n[MAIN OK] Program finished.")
        print(f"[MAIN INFO] Voice records folder: {VOICE_DIR}")
        print(f"[MAIN INFO] Dialogue log saved to: {DIALOGUE_LOG_FILE}")


if __name__ == "__main__":
    main()