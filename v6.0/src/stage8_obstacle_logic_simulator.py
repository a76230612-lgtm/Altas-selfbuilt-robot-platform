#!/usr/bin/env python3

import csv
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


# ============================================================
# Atlas 6.0 Stage 8
# Obstacle Safety Logic Simulator
#
# 只模拟安全逻辑：
# - 不连接ESP32
# - 不连接US-100
# - 不发送任何电机命令
# ============================================================

MIN_VALID_DISTANCE_CM = 2.0
MAX_VALID_DISTANCE_CM = 400.0

FORCE_STOP_THRESHOLD_CM = 25.0
CLEAR_THRESHOLD_CM = 50.0

NORMAL_PWM = 80
CAUTION_PWM = 40

LOG_FILE = Path(__file__).with_name(
    "stage8_obstacle_simulator_log.csv"
)


@dataclass(frozen=True)
class Decision:
    requested_command: str
    input_distance_cm: Optional[float]
    safety_state: str
    final_command: str
    final_pwm: int
    reason: str


def distance_is_valid(distance_cm: Optional[float]) -> bool:
    if distance_cm is None:
        return False

    if not math.isfinite(distance_cm):
        return False

    return (
        MIN_VALID_DISTANCE_CM
        <= distance_cm
        <= MAX_VALID_DISTANCE_CM
    )


def make_safe_decision(
    requested_command: str,
    distance_cm: Optional[float],
) -> Decision:

    command = requested_command.strip().upper()

    # 用户STOP永远具有最高优先级。
    if command == "STOP":
        return Decision(
            requested_command=command,
            input_distance_cm=distance_cm,
            safety_state="USER_STOP",
            final_command="STOP",
            final_pwm=0,
            reason="User requested STOP.",
        )

    # 本阶段只模拟FORWARD。
    if command != "FORWARD":
        return Decision(
            requested_command=command,
            input_distance_cm=distance_cm,
            safety_state="INVALID_COMMAND",
            final_command="STOP",
            final_pwm=0,
            reason="Only FORWARD and STOP are allowed in this simulator.",
        )

    # 无效数据不得解释为道路安全。
    if not distance_is_valid(distance_cm):
        return Decision(
            requested_command=command,
            input_distance_cm=distance_cm,
            safety_state="SENSOR_INVALID",
            final_command="STOP",
            final_pwm=0,
            reason="Distance data is missing, non-finite, or out of range.",
        )

    assert distance_cm is not None

    # 小于25cm：立即停车。
    if distance_cm < FORCE_STOP_THRESHOLD_CM:
        return Decision(
            requested_command=command,
            input_distance_cm=distance_cm,
            safety_state="FORCE_STOP",
            final_command="STOP",
            final_pwm=0,
            reason="Obstacle is closer than 25 cm.",
        )

    # 25cm到50cm，包括两个边界：降速和警告。
    if distance_cm <= CLEAR_THRESHOLD_CM:
        return Decision(
            requested_command=command,
            input_distance_cm=distance_cm,
            safety_state="CAUTION",
            final_command="FORWARD",
            final_pwm=CAUTION_PWM,
            reason="Obstacle is between 25 cm and 50 cm.",
        )

    # 大于50cm：允许正常前进。
    return Decision(
        requested_command=command,
        input_distance_cm=distance_cm,
        safety_state="CLEAR",
        final_command="FORWARD",
        final_pwm=NORMAL_PWM,
        reason="Obstacle is farther than 50 cm.",
    )


def append_log(decision: Decision) -> None:
    file_exists = LOG_FILE.exists()

    with LOG_FILE.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        writer = csv.writer(csv_file)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "requested_command",
                "input_distance_cm",
                "safety_state",
                "final_command",
                "final_pwm",
                "reason",
            ])

        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            decision.requested_command,
            (
                "INVALID"
                if decision.input_distance_cm is None
                else decision.input_distance_cm
            ),
            decision.safety_state,
            decision.final_command,
            decision.final_pwm,
            decision.reason,
        ])


def print_decision(decision: Decision) -> None:
    distance_text = (
        "INVALID"
        if decision.input_distance_cm is None
        else f"{decision.input_distance_cm:.2f} cm"
    )

    print()
    print("----------------------------------------")
    print(f"Requested command : {decision.requested_command}")
    print(f"Distance          : {distance_text}")
    print(f"Safety state      : {decision.safety_state}")
    print(f"Final command     : {decision.final_command}")
    print(f"Final PWM         : {decision.final_pwm}")
    print(f"Reason            : {decision.reason}")
    print("----------------------------------------")


def run_automatic_tests() -> bool:
    test_cases = [
        ("clear at 60 cm",
         "FORWARD", 60.0, "CLEAR", "FORWARD", 80),

        ("upper boundary at 50 cm",
         "FORWARD", 50.0, "CAUTION", "FORWARD", 40),

        ("caution at 30 cm",
         "FORWARD", 30.0, "CAUTION", "FORWARD", 40),

        ("lower boundary at 25 cm",
         "FORWARD", 25.0, "CAUTION", "FORWARD", 40),

        ("force stop at 24.9 cm",
         "FORWARD", 24.9, "FORCE_STOP", "STOP", 0),

        ("force stop at 20 cm",
         "FORWARD", 20.0, "FORCE_STOP", "STOP", 0),

        ("missing sensor value",
         "FORWARD", None, "SENSOR_INVALID", "STOP", 0),

        ("invalid zero distance",
         "FORWARD", 0.0, "SENSOR_INVALID", "STOP", 0),

        ("out-of-range distance",
         "FORWARD", 401.0, "SENSOR_INVALID", "STOP", 0),

        ("user stop",
         "STOP", 100.0, "USER_STOP", "STOP", 0),
    ]

    passed = 0

    print("Atlas 6.0 Stage 8 automatic safety tests")
    print()

    for (
        name,
        command,
        distance,
        expected_state,
        expected_command,
        expected_pwm,
    ) in test_cases:

        result = make_safe_decision(command, distance)

        test_passed = (
            result.safety_state == expected_state
            and result.final_command == expected_command
            and result.final_pwm == expected_pwm
        )

        print(
            f"{'PASS' if test_passed else 'FAIL'}"
            f" | {name}"
            f" | state={result.safety_state}"
            f" | command={result.final_command}"
            f" | pwm={result.final_pwm}"
        )

        if test_passed:
            passed += 1

    print()
    print(f"Automatic result: {passed}/{len(test_cases)} passed")

    return passed == len(test_cases)


def parse_distance(text: str) -> Optional[float]:
    cleaned = text.strip().upper()

    if cleaned in {"INVALID", "NONE", "TIMEOUT"}:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def interactive_mode() -> None:
    print()
    print("Interactive format:")
    print("  forward 60")
    print("  forward 30")
    print("  forward 20")
    print("  forward invalid")
    print("  stop 100")
    print("  quit")
    print()

    while True:
        raw = input("stage8> ").strip()

        if not raw:
            continue

        if raw.lower() == "quit":
            print("Simulator closed.")
            break

        parts = raw.split(maxsplit=1)

        if len(parts) != 2:
            print("Format error. Example: forward 30")
            continue

        command = parts[0]
        distance = parse_distance(parts[1])

        decision = make_safe_decision(
            command,
            distance,
        )

        print_decision(decision)
        append_log(decision)


def main() -> None:
    all_passed = run_automatic_tests()

    if not all_passed:
        print()
        print("STOP: automatic tests did not all pass.")
        print("Do not continue to the hardware test.")
        return

    print()
    print("All automatic tests passed.")
    print(f"Manual test log: {LOG_FILE}")

    interactive_mode()


if __name__ == "__main__":
    main()