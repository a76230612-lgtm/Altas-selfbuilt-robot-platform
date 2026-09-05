"""
Atlas 6.0 - Stage 10A Windows Serial Acceptance Test
"""

import argparse
import sys
import time

try:
    import serial
except ImportError:
    print("ERROR: pyserial is not installed.")
    print(r'Install with: .\.venv\Scripts\python.exe -m pip install pyserial')
    sys.exit(2)

BAUD = 115200


class TestFailure(Exception):
    pass


def read_lines(ser, duration=0.8):
    deadline = time.time() + duration
    lines = []
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line:
            print(f"ESP32 << {line}")
            lines.append(line)
    return lines


def send_and_collect(ser, command, duration=0.6):
    print(f"PC    >> {command}")
    ser.write((command + "\n").encode("utf-8"))
    ser.flush()
    return read_lines(ser, duration)


def require(lines, expected, test_name):
    if expected not in lines:
        raise TestFailure(
            f"{test_name}: expected '{expected}' but received {lines}"
        )
    print(f"{test_name}: PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM3")
    args = parser.parse_args()

    print("=" * 78)
    print("Atlas 6.0 - Stage 10A Bare-Board Serial Acceptance Test")
    print("=" * 78)
    print(f"Port : {args.port}")
    print(f"Baud : {BAUD}")
    print()

    try:
        ser = serial.Serial(
            port=args.port,
            baudrate=BAUD,
            timeout=0.08,
            write_timeout=1.0,
        )
    except Exception as e:
        print(f"SERIAL OPEN: FAIL - {e}")
        sys.exit(3)

    try:
        time.sleep(1.5)
        print("Initial ESP32 output:")
        read_lines(ser, 1.0)
        ser.reset_input_buffer()

        lines = send_and_collect(ser, "CMD,STATUS")
        require(lines, "STATUS,DISARMED", "01 STATUS after boot")

        lines = send_and_collect(ser, "CMD,PING")
        require(lines, "ACK,PING", "02 PING")

        lines = send_and_collect(ser, "CMD,ARM")
        require(lines, "ACK,ARM", "03 ARM ACK")
        require(lines, "STATUS,ARMED", "04 ARMED state")

        time.sleep(0.10)
        lines = send_and_collect(ser, "CMD,HEARTBEAT", 0.20)
        require(lines, "ACK,HEARTBEAT", "05 HEARTBEAT #1")

        time.sleep(0.10)
        lines = send_and_collect(ser, "CMD,HEARTBEAT", 0.20)
        require(lines, "ACK,HEARTBEAT", "06 HEARTBEAT #2")

        lines = send_and_collect(ser, "CMD,STOP")
        require(lines, "ACK,STOP", "07 STOP ACK")
        require(lines, "STATUS,STOPPED", "08 STOPPED state")
        require(lines, "STATUS,ARMED", "09 STOP keeps ARM state")

        lines = send_and_collect(ser, "CMD,FORWARD,80,500")
        require(lines, "ERROR,BAREBOARD_NO_MOTION", "10 Motion rejection")

        lines = send_and_collect(ser, "CMD,THIS_IS_INVALID")
        require(lines, "ERROR,INVALID_COMMAND", "11 Invalid command rejection")

        lines = send_and_collect(ser, "CMD,ARM")
        require(lines, "ACK,ARM", "12 Re-ARM")

        print("Waiting 0.65 s with NO heartbeat...")
        lines = read_lines(ser, 0.75)
        require(lines, "ERROR,HEARTBEAT_TIMEOUT", "13 Heartbeat timeout event")
        require(lines, "STATUS,DISARMED", "14 Timeout forces DISARMED")

        lines = send_and_collect(ser, "CMD,STATUS")
        require(lines, "STATUS,DISARMED", "15 Final status")

        print()
        print("=" * 78)
        print("STAGE 10A BARE-BOARD SERIAL RESULT: PASS")
        print("=" * 78)

    except TestFailure as e:
        print()
        print("=" * 78)
        print("STAGE 10A BARE-BOARD SERIAL RESULT: FAIL")
        print("=" * 78)
        print(e)
        sys.exit(10)

    finally:
        ser.close()


if __name__ == "__main__":
    main()
