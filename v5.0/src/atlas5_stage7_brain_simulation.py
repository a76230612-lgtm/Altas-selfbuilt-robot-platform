import serial
import time
from enum import Enum


# =====================================================
# Atlas 5.0 Stage 7
# Atlas Brain Input Simulation Layer
#
# Purpose:
# - Simulate a simple "Atlas Brain" using typed text input.
# - Convert user text into behavior states.
# - Use the Stage 6 Behavior State Machine + Python HAL structure.
#
# System:
# User typed text
#   -> Brain input simulation
#   -> Behavior State Machine
#   -> Python HAL
#   -> Serial
#   -> ESP32 Behavior Firmware
#   -> Pan / Tilt / LED
#
# ESP32 firmware:
# - atlas5_stage4_behavior_firmware_v2_stable_success.ino
#
# Hardware:
# - ESP32 powered by USB
# - Servos powered by 4xAA battery box
# - Battery negative connected to ESP32 GND
#
# Important:
# - Close Arduino Serial Monitor before running this script.
# - Turn on 4xAA battery box when the program asks you to.
# =====================================================

SERIAL_PORT = "COM6"   # 改成你的 ESP32 端口，例如 COM3 / COM4 / COM5
BAUD_RATE = 115200
TIMEOUT = 2
READY_TEXT = "READY_FOR_NEXT_COMMAND"


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
# Brain Intent Types
# =====================================================

class BrainIntent(Enum):
    NORMAL_QUESTION = "NORMAL_QUESTION"
    GREETING = "GREETING"
    NEED_ENCOURAGEMENT = "NEED_ENCOURAGEMENT"
    DIRECT_ENCOURAGE = "DIRECT_ENCOURAGE"
    WARNING_EVENT = "WARNING_EVENT"
    ERROR_EVENT = "ERROR_EVENT"
    IDLE_EVENT = "IDLE_EVENT"
    BEHAVIOR_TEST_EVENT = "BEHAVIOR_TEST_EVENT"
    UNKNOWN = "UNKNOWN"
    QUIT = "QUIT"


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

    def run_sequence(self, states, pause_seconds=0.4):
        for state in states:
            ok = self.go_to_state(state)
            if not ok:
                return False
            time.sleep(pause_seconds)
        return True


# =====================================================
# Atlas Brain Simulation
# =====================================================

class AtlasBrainSimulator:
    def __init__(self, state_machine: AtlasBehaviorStateMachine):
        self.machine = state_machine

    def classify_input(self, user_text: str) -> BrainIntent:
        text = user_text.strip().lower()

        if text in ["q", "quit", "exit", "退出"]:
            return BrainIntent.QUIT

        if text in ["idle", "待机", "rest", "stop"]:
            return BrainIntent.IDLE_EVENT

        if text in ["test", "behavior test", "行为测试"]:
            return BrainIntent.BEHAVIOR_TEST_EVENT

        if text in ["hello", "hi", "hey", "你好", "嗨"]:
            return BrainIntent.GREETING

        if text in ["help", "encourage me", "我需要鼓励", "鼓励我", "加油"]:
            return BrainIntent.NEED_ENCOURAGEMENT

        if text in ["encourage", "encouragement", "鼓励"]:
            return BrainIntent.DIRECT_ENCOURAGE

        if text in ["warning", "warn", "danger", "careful", "警告", "危险", "小心"]:
            return BrainIntent.WARNING_EVENT

        if text in ["error", "wrong", "fail", "failed", "bug", "错误", "失败", "报错"]:
            return BrainIntent.ERROR_EVENT

        if "?" in text or "what" in text or "why" in text or "how" in text:
            return BrainIntent.NORMAL_QUESTION

        if "什么" in text or "为什么" in text or "怎么" in text or "如何" in text:
            return BrainIntent.NORMAL_QUESTION

        if len(text) > 0:
            return BrainIntent.NORMAL_QUESTION

        return BrainIntent.UNKNOWN

    def handle_input(self, user_text: str):
        intent = self.classify_input(user_text)

        print()
        print("========================================")
        print(f"[BRAIN] User input: {user_text}")
        print(f"[BRAIN] Intent: {intent.value}")
        print("========================================")

        if intent == BrainIntent.QUIT:
            return False

        if intent == BrainIntent.IDLE_EVENT:
            self.machine.go_to_state(AtlasState.IDLE)
            return True

        if intent == BrainIntent.BEHAVIOR_TEST_EVENT:
            self.machine.run_behavior_test()
            return True

        if intent == BrainIntent.GREETING:
            self.handle_greeting()
            return True

        if intent == BrainIntent.NORMAL_QUESTION:
            self.handle_normal_question(user_text)
            return True

        if intent == BrainIntent.NEED_ENCOURAGEMENT:
            self.handle_need_encouragement()
            return True

        if intent == BrainIntent.DIRECT_ENCOURAGE:
            self.machine.go_to_state(AtlasState.ENCOURAGE)
            return True

        if intent == BrainIntent.WARNING_EVENT:
            self.machine.go_to_state(AtlasState.WARNING)
            return True

        if intent == BrainIntent.ERROR_EVENT:
            self.machine.go_to_state(AtlasState.ERROR)
            return True

        self.machine.go_to_state(AtlasState.ERROR)
        return True

    def handle_greeting(self):
        print("[BRAIN] Handling greeting.")

        self.machine.run_sequence([
            AtlasState.LISTENING,
            AtlasState.THINKING,
            AtlasState.SUCCESS,
            AtlasState.IDLE
        ])

        print("[BRAIN RESPONSE] Hello. Atlas is ready.")

    def handle_normal_question(self, user_text: str):
        print("[BRAIN] Handling normal question.")
        print(f"[BRAIN] Simulated question: {user_text}")

        self.machine.run_sequence([
            AtlasState.LISTENING,
            AtlasState.THINKING,
            AtlasState.SUCCESS,
            AtlasState.IDLE
        ])

        print("[BRAIN RESPONSE] I understood the question. This is a simulated answer.")

    def handle_need_encouragement(self):
        print("[BRAIN] Handling encouragement request.")

        self.machine.run_sequence([
            AtlasState.LISTENING,
            AtlasState.THINKING,
            AtlasState.ENCOURAGE,
            AtlasState.IDLE
        ])

        print("[BRAIN RESPONSE] Keep going. You are making progress.")


# =====================================================
# User Interface
# =====================================================

def print_help():
    print()
    print("========== Atlas 5.0 Stage 7 Brain Simulation ==========")
    print("输入普通文字，Atlas 会模拟理解并执行行为。")
    print()
    print("Examples:")
    print("hello                  -> 问候流程")
    print("what can you do?       -> 普通问题流程")
    print("help                   -> 鼓励流程")
    print("encourage              -> 直接鼓励状态")
    print("warning                -> 警告状态")
    print("error                  -> 错误状态")
    print("idle                   -> 回到待机")
    print("test                   -> 运行 BEHAVIOR_TEST")
    print("quit / q               -> DISARM 并退出")
    print("========================================================")


def main():
    print("Atlas 5.0 Stage 7 - Atlas Brain Input Simulation")
    print("Before running:")
    print("1. ESP32 must run Stage 4 Behavior Firmware v2 Stable Success.")
    print("2. Arduino Serial Monitor must be closed.")
    print("3. ESP32 USB must be connected.")
    print("4. Servos must be powered by 4xAA battery box.")
    print("5. Battery negative must connect to ESP32 GND.")
    print()

    hal = AtlasHAL(SERIAL_PORT, BAUD_RATE, TIMEOUT)

    if not hal.connect():
        return

    machine = AtlasBehaviorStateMachine(hal)
    brain = AtlasBrainSimulator(machine)

    try:
        if not machine.start():
            print("[MAIN ERROR] Could not start Atlas.")
            return

        print_help()

        while True:
            user_text = input("\nYou: ").strip()

            if not user_text:
                continue

            should_continue = brain.handle_input(user_text)

            if not should_continue:
                break

    finally:
        machine.stop()
        hal.close()
        print("\n[MAIN OK] Program finished.")


if __name__ == "__main__":
    main()