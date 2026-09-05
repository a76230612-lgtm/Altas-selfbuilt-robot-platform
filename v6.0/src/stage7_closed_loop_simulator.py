from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


# ============================================================
# Atlas 6.0 Stage 7 — Closed-Loop Software Simulator
#
# 本程序只进行纯软件模拟：
# - 不连接ESP32
# - 不连接L298N
# - 不连接电机
# - 不修改Stage 6C V4
#
# 输出：
# 1. 开环模拟CSV
# 2. 闭环模拟CSV
# 3. 自动验收结果
# ============================================================


# -------------------- V4锁定标定值 --------------------

WHEEL_CIRCUMFERENCE_CM = 21.40
LEFT_PULSES_PER_REV = 632.05
RIGHT_PULSES_PER_REV = 634.17


# -------------------- Stage 7模拟参数 --------------------

BASE_PWM = 160.0
MIN_PWM = 80.0
MAX_PWM = 220.0

# 每100ms执行一次闭环计算。
CONTROL_INTERVAL_S = 0.100

# 每次模拟8秒。
SIMULATION_DURATION_S = 8.0

# 只用于虚拟电机的比例增益。
# 不能直接复制到实体电机代码。
KP = 4.0

# 当左右速度差小于平均速度的5%时暂时不修正。
DEADBAND_PERCENT = 0.05

# PWM相对160最多修正20。
MAX_CORRECTION_PWM = 20.0

# 每100ms最多改变5个PWM单位。
MAX_PWM_STEP = 5.0

# 模拟验收要求：闭环误差至少比开环降低30%。
MIN_ERROR_IMPROVEMENT_PERCENT = 30.0


# -------------------- 虚拟电机参数 --------------------

# 故意把右轮设置得比左轮慢。
# 这些只是虚拟系数，不代表实体电机参数。
LEFT_GAIN_CM_S_PER_PWM = 0.105
RIGHT_GAIN_CM_S_PER_PWM = 0.090

# 模拟电机不会瞬间达到目标速度。
MOTOR_TIME_CONSTANT_S = 0.35

# 模拟编码器的少量读数变化。
ENCODER_NOISE_STD_PULSES = 0.15

# 固定随机种子，使每次运行结果可以重复。
RANDOM_SEED = 20260809


# -------------------- 输出位置 --------------------

OUTPUT_DIRECTORY = Path("stage7_simulation_output")


def clamp(value: float, minimum: float, maximum: float) -> float:
    """把数值限制在最小值和最大值之间。"""
    return max(minimum, min(maximum, value))


def move_toward(
    current: float,
    target: float,
    maximum_step: float,
) -> float:
    """限制每个控制周期内PWM的最大变化量。"""

    if target > current:
        return min(current + maximum_step, target)

    return max(current - maximum_step, target)


@dataclass
class WheelModel:
    """一个简化的虚拟轮子模型。"""

    pulses_per_rev: float
    gain_cm_s_per_pwm: float

    speed_cm_s: float = 0.0
    encoder_count: int = 0
    fractional_pulses: float = 0.0

    def step(
        self,
        pwm: float,
        delta_time_s: float,
        rng: random.Random,
    ) -> int:
        """
        根据PWM计算虚拟轮速，并把运动距离转换成编码器脉冲。
        """

        # 低于MIN_PWM的部分在这个虚拟模型中不产生有效速度。
        effective_pwm = max(0.0, pwm - MIN_PWM)

        target_speed = (
            effective_pwm
            * self.gain_cm_s_per_pwm
        )

        # 使用一阶响应模拟电机的加速过程。
        response_fraction = min(
            1.0,
            delta_time_s / MOTOR_TIME_CONSTANT_S,
        )

        self.speed_cm_s += (
            response_fraction
            * (target_speed - self.speed_cm_s)
        )

        # 把本周期移动距离转换成编码器脉冲。
        ideal_pulses = (
            self.speed_cm_s
            * delta_time_s
            / WHEEL_CIRCUMFERENCE_CM
            * self.pulses_per_rev
        )

        # 加入非常小、且可重复的虚拟编码器噪声。
        noisy_pulses = max(
            0.0,
            ideal_pulses
            + rng.gauss(
                0.0,
                ENCODER_NOISE_STD_PULSES,
            ),
        )

        accumulated = (
            self.fractional_pulses
            + noisy_pulses
        )

        whole_pulses = int(accumulated)

        self.fractional_pulses = (
            accumulated
            - whole_pulses
        )

        self.encoder_count += whole_pulses

        return self.encoder_count


def pulses_to_speed_cm_s(
    pulse_delta: int,
    pulses_per_rev: float,
    delta_time_s: float,
) -> float:
    """
    把一个采样周期内新增的脉冲转换成cm/s。
    """

    return (
        pulse_delta
        / pulses_per_rev
        * WHEEL_CIRCUMFERENCE_CM
        / delta_time_s
    )


def run_simulation(
    closed_loop: bool,
) -> list[dict[str, float | int | str]]:
    """
    运行一次开环或闭环模拟。
    """

    rng = random.Random(RANDOM_SEED)

    left_wheel = WheelModel(
        pulses_per_rev=LEFT_PULSES_PER_REV,
        gain_cm_s_per_pwm=LEFT_GAIN_CM_S_PER_PWM,
    )

    right_wheel = WheelModel(
        pulses_per_rev=RIGHT_PULSES_PER_REV,
        gain_cm_s_per_pwm=RIGHT_GAIN_CM_S_PER_PWM,
    )

    applied_left_pwm = BASE_PWM
    applied_right_pwm = BASE_PWM

    previous_left_count = 0
    previous_right_count = 0

    rows: list[dict[str, float | int | str]] = []

    step_count = round(
        SIMULATION_DURATION_S
        / CONTROL_INTERVAL_S
    )

    for step_number in range(
        1,
        step_count + 1,
    ):
        time_s = (
            step_number
            * CONTROL_INTERVAL_S
        )

        # 使用本周期正在生效的PWM驱动两个虚拟轮子。
        left_count = left_wheel.step(
            applied_left_pwm,
            CONTROL_INTERVAL_S,
            rng,
        )

        right_count = right_wheel.step(
            applied_right_pwm,
            CONTROL_INTERVAL_S,
            rng,
        )

        # 计算本周期新增脉冲。
        left_delta = (
            left_count
            - previous_left_count
        )

        right_delta = (
            right_count
            - previous_right_count
        )

        previous_left_count = left_count
        previous_right_count = right_count

        # 把新增脉冲转换成实际速度。
        left_speed = pulses_to_speed_cm_s(
            left_delta,
            LEFT_PULSES_PER_REV,
            CONTROL_INTERVAL_S,
        )

        right_speed = pulses_to_speed_cm_s(
            right_delta,
            RIGHT_PULSES_PER_REV,
            CONTROL_INTERVAL_S,
        )

        # 固定误差定义：
        # error > 0 表示左轮更快。
        error_cm_s = (
            left_speed
            - right_speed
        )

        average_speed = (
            left_speed
            + right_speed
        ) / 2.0

        if average_speed > 0.001:
            relative_error = (
                error_cm_s
                / average_speed
            )
        else:
            relative_error = 0.0

        correction_pwm = 0.0

        next_left_pwm = applied_left_pwm
        next_right_pwm = applied_right_pwm

        if closed_loop:
            # 只有超过5%死区才进行修正。
            if (
                abs(relative_error)
                >= DEADBAND_PERCENT
            ):
                correction_pwm = clamp(
                    KP * error_cm_s,
                    -MAX_CORRECTION_PWM,
                    MAX_CORRECTION_PWM,
                )

            # error > 0：
            # 左轮更快，因此降低左轮PWM，
            # 同时提高右轮PWM。
            target_left_pwm = clamp(
                BASE_PWM - correction_pwm,
                MIN_PWM,
                MAX_PWM,
            )

            target_right_pwm = clamp(
                BASE_PWM + correction_pwm,
                MIN_PWM,
                MAX_PWM,
            )

            # 限制每100ms最多变化5。
            next_left_pwm = move_toward(
                applied_left_pwm,
                target_left_pwm,
                MAX_PWM_STEP,
            )

            next_right_pwm = move_toward(
                applied_right_pwm,
                target_right_pwm,
                MAX_PWM_STEP,
            )

        rows.append(
            {
                "mode": (
                    "closed_loop"
                    if closed_loop
                    else "open_loop"
                ),
                "time_s": round(time_s, 3),
                "left_count": left_count,
                "right_count": right_count,
                "left_delta": left_delta,
                "right_delta": right_delta,
                "left_speed_cm_s": round(
                    left_speed,
                    4,
                ),
                "right_speed_cm_s": round(
                    right_speed,
                    4,
                ),
                "error_cm_s": round(
                    error_cm_s,
                    4,
                ),
                "relative_error_percent": round(
                    relative_error * 100.0,
                    3,
                ),
                "applied_left_pwm": round(
                    applied_left_pwm,
                    3,
                ),
                "applied_right_pwm": round(
                    applied_right_pwm,
                    3,
                ),
                "correction_pwm": round(
                    correction_pwm,
                    3,
                ),
                "next_left_pwm": round(
                    next_left_pwm,
                    3,
                ),
                "next_right_pwm": round(
                    next_right_pwm,
                    3,
                ),
            }
        )

        applied_left_pwm = next_left_pwm
        applied_right_pwm = next_right_pwm

    return rows


def write_csv(
    file_path: Path,
    rows: list[dict[str, float | int | str]],
) -> None:
    """保存模拟结果。"""

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with file_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)


def steady_rows(
    rows: list[dict[str, float | int | str]],
) -> list[dict[str, float | int | str]]:
    """
    忽略启动后的前2秒，只分析进入稳定状态的数据。
    """

    return [
        row
        for row in rows
        if float(row["time_s"]) >= 2.0
    ]


def average_absolute_error(
    rows: list[dict[str, float | int | str]],
) -> float:
    """计算稳定阶段的平均绝对速度误差。"""

    return mean(
        abs(float(row["error_cm_s"]))
        for row in steady_rows(rows)
    )


def print_sample_rows(
    title: str,
    rows: list[dict[str, float | int | str]],
) -> None:
    """每1秒显示一行代表数据。"""

    print(f"\n{title}")

    print(
        "time  left_v  right_v  "
        "error   left_pwm  right_pwm"
    )

    for row in rows[9::10]:
        print(
            f"{float(row['time_s']):>4.1f}  "
            f"{float(row['left_speed_cm_s']):>6.2f}  "
            f"{float(row['right_speed_cm_s']):>7.2f}  "
            f"{float(row['error_cm_s']):>6.2f}  "
            f"{float(row['applied_left_pwm']):>8.1f}  "
            f"{float(row['applied_right_pwm']):>9.1f}"
        )


def main() -> None:
    # 第一组：开环，两边一直使用PWM160。
    open_loop_rows = run_simulation(
        closed_loop=False
    )

    # 第二组：闭环，允许比例控制修正PWM。
    closed_loop_rows = run_simulation(
        closed_loop=True
    )

    open_loop_path = (
        OUTPUT_DIRECTORY
        / "stage7_open_loop.csv"
    )

    closed_loop_path = (
        OUTPUT_DIRECTORY
        / "stage7_closed_loop.csv"
    )

    write_csv(
        open_loop_path,
        open_loop_rows,
    )

    write_csv(
        closed_loop_path,
        closed_loop_rows,
    )

    print_sample_rows(
        "OPEN LOOP: same PWM, no correction",
        open_loop_rows,
    )

    print_sample_rows(
        "CLOSED LOOP: proportional correction",
        closed_loop_rows,
    )

    open_error = average_absolute_error(
        open_loop_rows
    )

    closed_error = average_absolute_error(
        closed_loop_rows
    )

    if open_error > 0.0:
        improvement_percent = (
            (open_error - closed_error)
            / open_error
            * 100.0
        )
    else:
        improvement_percent = 0.0

    closed_pwm_values = [
        float(row[key])
        for row in closed_loop_rows
        for key in (
            "applied_left_pwm",
            "applied_right_pwm",
        )
    ]

    pwm_is_safe = all(
        MIN_PWM <= value <= MAX_PWM
        for value in closed_pwm_values
    )

    correction_limit_respected = all(
        (
            BASE_PWM
            - MAX_CORRECTION_PWM
        )
        <= value
        <= (
            BASE_PWM
            + MAX_CORRECTION_PWM
        )
        for value in closed_pwm_values
    )

    average_closed_left_pwm = mean(
        float(row["applied_left_pwm"])
        for row in steady_rows(
            closed_loop_rows
        )
    )

    average_closed_right_pwm = mean(
        float(row["applied_right_pwm"])
        for row in steady_rows(
            closed_loop_rows
        )
    )

    # 虚拟左轮更快，所以正确控制方向应为：
    # 左PWM平均值 < 右PWM平均值。
    direction_is_correct = (
        average_closed_left_pwm
        < average_closed_right_pwm
    )

    improvement_is_sufficient = (
        improvement_percent
        >= MIN_ERROR_IMPROVEMENT_PERCENT
    )

    print("\nSUMMARY")

    print(
        "Open-loop mean absolute error  : "
        f"{open_error:.3f} cm/s"
    )

    print(
        "Closed-loop mean absolute error: "
        f"{closed_error:.3f} cm/s"
    )

    print(
        "Error improvement              : "
        f"{improvement_percent:.1f}%"
    )

    print(
        "PWM stayed inside 80..220      : "
        f"{'PASS' if pwm_is_safe else 'FAIL'}"
    )

    print(
        "PWM stayed inside base +/- 20  : "
        f"{'PASS' if correction_limit_respected else 'FAIL'}"
    )

    print(
        "Correction direction is right  : "
        f"{'PASS' if direction_is_correct else 'FAIL'}"
    )

    print(
        "Error improvement >= 30%       : "
        f"{'PASS' if improvement_is_sufficient else 'FAIL'}"
    )

    print(
        f"CSV file                       : "
        f"{open_loop_path}"
    )

    print(
        f"CSV file                       : "
        f"{closed_loop_path}"
    )

    if not (
        pwm_is_safe
        and correction_limit_respected
        and direction_is_correct
        and improvement_is_sufficient
    ):
        raise SystemExit(
            "Simulation acceptance check failed."
        )

    print(
        "\nRESULT: "
        "STAGE 7 SOFTWARE SIMULATION PASSED"
    )


if __name__ == "__main__":
    main()