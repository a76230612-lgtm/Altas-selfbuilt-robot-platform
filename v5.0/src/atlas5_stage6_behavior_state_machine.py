import serial
import time
from enum import Enum


# =====================================================
# Atlas 5.0 Stage 6
# Python Behavior State Machine
#
# Purpose:
# - Add a Python behavior state machine above the Python HAL.
# - Use keyboard events to simulate future voice / vision / AI events.
# - State machine decides which behavior command should be sent to ESP32.
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
# - Turn on 4xAA battery box before ARM.
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


# =====================================================
# User Interface
# =====================================================

def print_menu():
    print()
    print("========== Atlas 5.0 Stage 6 Menu ==========")
    print("1 -> IDLE")
    print("2 -> LISTENING")
    print("3 -> THINKING")
    print("4 -> SUCCESS")
    print("5 -> ENCOURAGE")
    print("6 -> WARNING")
    print("7 -> ERROR")
    print("8 -> BEHAVIOR_TEST")
    print("q -> DISARM and quit")
    print("============================================")


def main():
    print("Atlas 5.0 Stage 6 - Python Behavior State Machine")
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

    try:
        if not machine.start():
            print("[MAIN ERROR] Could not start Atlas.")
            return

        while True:
            print_menu()
            choice = input("请输入选项: ").strip().lower()

            if choice == "1":
                machine.go_to_state(AtlasState.IDLE)

            elif choice == "2":
                machine.go_to_state(AtlasState.LISTENING)

            elif choice == "3":
                machine.go_to_state(AtlasState.THINKING)

            elif choice == "4":
                machine.go_to_state(AtlasState.SUCCESS)

            elif choice == "5":
                machine.go_to_state(AtlasState.ENCOURAGE)

            elif choice == "6":
                machine.go_to_state(AtlasState.WARNING)

            elif choice == "7":
                machine.go_to_state(AtlasState.ERROR)

            elif choice == "8":
                machine.run_behavior_test()

            elif choice == "q":
                break

            else:
                print("[INPUT ERROR] Unknown option. Please choose 1-8 or q.")

    finally:
        machine.stop()
        hal.close()
        print("\n[MAIN OK] Program finished.")


if __name__ == "__main__":
    main()