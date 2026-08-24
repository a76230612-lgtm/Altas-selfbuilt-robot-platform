import json
from datetime import datetime, date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

EMOTION_FILE = BASE_DIR / "emotion_memory.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


class EmotionMemory:
    def __init__(self, data):
        self.student_name = data.get("student_name", "Eric")
        self.emotion_memory_version = data.get(
            "emotion_memory_version",
            "Atlas 3.0 Emotion Memory v1"
        )
        self.emotion_records = data.get("emotion_records", [])

    def to_dict(self):
        return {
            "student_name": self.student_name,
            "emotion_memory_version": self.emotion_memory_version,
            "emotion_records": self.emotion_records
        }

    def add_record(self, record):
        self.emotion_records.append(record)

    def get_recent_records(self, count=5):
        return self.emotion_records[-count:]

    def generate_summary(self):
        total = len(self.emotion_records)

        if total == 0:
            return "目前还没有研发情绪记录。"

        tired_count = 0
        stuck_count = 0
        failed_count = 0
        long_debug_count = 0

        for record in self.emotion_records:
            feeling = record.get("feeling", "")
            debug_hours = record.get("debug_hours", 0)

            if "累" in feeling or "疲惫" in feeling:
                tired_count += 1

            if "卡住" in feeling or "不知道" in feeling:
                stuck_count += 1

            if "失败" in feeling or "报错" in feeling:
                failed_count += 1

            if debug_hours >= 3:
                long_debug_count += 1

        summary = (
            f"Eric 目前一共有 {total} 条研发情绪记录。\n"
            f"疲惫记录：{tired_count} 次。\n"
            f"卡住记录：{stuck_count} 次。\n"
            f"失败或报错记录：{failed_count} 次。\n"
            f"连续调试 3 小时以上记录：{long_debug_count} 次。\n\n"
            "机器人判断：这些记录不是心理诊断，而是研发节奏记录。"
        )

        return summary

    def generate_support_advice(self, latest_record):
        feeling = latest_record.get("feeling", "")
        debug_hours = latest_record.get("debug_hours", 0)
        problem = latest_record.get("problem", "")
        next_step = latest_record.get("next_step", "")

        lines = []

        lines.append(f"{self.student_name}，我已经记录了你今天的研发状态。")
        lines.append("")
        lines.append("先说明：")
        lines.append("我不是心理医生。我只作为研发导师，帮助你调整 Debug 节奏。")
        lines.append("")

        lines.append("机器人判断：")

        if debug_hours >= 4:
            lines.append(
                f"你今天已经连续调试 {debug_hours} 小时，时间偏长。"
            )
            lines.append(
                "现在不建议继续硬撑。建议先休息 15 到 20 分钟，再回来只测试一个最小问题。"
            )

        elif debug_hours >= 2:
            lines.append(
                f"你今天已经调试 {debug_hours} 小时。"
            )
            lines.append(
                "建议不要继续扩大功能，只保留一个最小测试目标。"
            )

        else:
            lines.append(
                f"你今天调试时间是 {debug_hours} 小时，还在可控范围。"
            )

        if "失败" in feeling or "报错" in feeling:
            lines.append(
                "失败和报错是研发过程的一部分。现在最重要的是记录触发条件和已经尝试过的方法。"
            )

        if "卡住" in feeling or "不知道" in feeling:
            lines.append(
                "卡住通常不是能力问题，而是任务太大。下一步要把任务缩小。"
            )

        if "烦" in feeling or "崩溃" in feeling or "不想做" in feeling:
            lines.append(
                "现在不要用情绪判断项目价值。先暂停，再用 Project Log 判断今天有没有推进。"
            )

        lines.append("")
        lines.append("当前问题：")
        lines.append(problem if problem else "未填写具体问题。")

        lines.append("")
        lines.append("建议下一步：")
        if next_step:
            lines.append(next_step)
        else:
            lines.append("先记录 Bug，再做一个最小复现测试。")

        lines.append("")
        lines.append("今天最低完成标准：")
        lines.append("只要记录了问题、调试时间、下一步方向，今天就不是失败的一天。")

        return "\n".join(lines)


def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_today_text():
    return date.today().strftime("%Y-%m-%d")


def write_to_project_log(title, content):
    text = (
        "\n" + "=" * 70 + "\n"
        f"{title}\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(PROJECT_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 project_log.txt")
    print(f"日志文件位置：{PROJECT_LOG_FILE}")


def create_default_data():
    return {
        "student_name": "Eric",
        "emotion_memory_version": "Atlas 3.0 Emotion Memory v1",
        "emotion_records": []
    }


def load_data():
    if not EMOTION_FILE.exists():
        data = create_default_data()
        save_data(data)
        return data

    try:
        with open(EMOTION_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        data = create_default_data()
        save_data(data)

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "emotion_memory_version" not in data:
        data["emotion_memory_version"] = "Atlas 3.0 Emotion Memory v1"

    if "emotion_records" not in data:
        data["emotion_records"] = []

    save_data(data)
    return data


def save_data(data):
    with open(EMOTION_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_emotion_memory():
    return EmotionMemory(load_data())


def save_emotion_memory(memory):
    save_data(memory.to_dict())


def add_emotion_record(memory):
    print("\n开始记录今天的研发情绪。")
    print("注意：这不是心理诊断，只是研发节奏记录。")

    feeling = input("今天的研发状态，例如：调试失败、有点卡住、连续 Debug 很久：").strip()
    debug_hours_text = input("今天连续调试了几个小时？例如 4：").strip()
    problem = input("今天主要卡在哪个问题？").strip()
    attempted = input("已经尝试过什么方法？").strip()
    next_step = input("下一步准备怎么做？").strip()

    if not feeling:
        feeling = "今天有点卡住。"

    if debug_hours_text.isdigit():
        debug_hours = int(debug_hours_text)
    else:
        debug_hours = 1

    if debug_hours < 0:
        debug_hours = 0

    if not problem:
        problem = "未填写具体问题"

    if not attempted:
        attempted = "未填写已尝试方法"

    if not next_step:
        next_step = "先把问题缩小，再做最小复现测试。"

    record = {
        "date": get_today_text(),
        "time": datetime.now().strftime("%H:%M:%S"),
        "feeling": feeling,
        "debug_hours": debug_hours,
        "problem": problem,
        "attempted": attempted,
        "next_step": next_step
    }

    memory.add_record(record)
    save_emotion_memory(memory)

    advice = memory.generate_support_advice(record)

    content = (
        f"日期：{record['date']} {record['time']}\n"
        f"研发状态：{feeling}\n"
        f"连续调试时间：{debug_hours} 小时\n"
        f"卡住的问题：{problem}\n"
        f"已尝试方法：{attempted}\n"
        f"下一步：{next_step}\n\n"
        f"机器人回应：\n{advice}"
    )

    print("\n研发情绪记录已保存：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Emotion Memory 新增研发情绪记录",
        content
    )


def show_recent_records(memory):
    records = memory.get_recent_records()

    if not records:
        message = "目前还没有研发情绪记录。"
        print("\n" + message)
        write_to_project_log("Atlas 3.0 Emotion Memory 查看最近记录", message)
        return

    lines = []

    print("\n最近研发情绪记录：")
    print("-" * 70)

    for record in records:
        text = (
            f"日期：{record.get('date')} {record.get('time')}\n"
            f"状态：{record.get('feeling')}\n"
            f"调试时间：{record.get('debug_hours')} 小时\n"
            f"问题：{record.get('problem')}\n"
            f"下一步：{record.get('next_step')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    write_to_project_log(
        "Atlas 3.0 Emotion Memory 查看最近记录",
        "\n\n".join(lines)
    )


def show_emotion_summary(memory):
    summary = memory.generate_summary()

    print("\n研发情绪记忆总结：")
    print("-" * 70)
    print(summary)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Emotion Memory 研发情绪总结",
        summary
    )


def robot_reminder(memory):
    if not memory.emotion_records:
        reminder = (
            "目前还没有研发情绪记录。\n"
            "建议今天先记录一次 Debug 状态，之后 Atlas 才能根据历史节奏提醒你。"
        )
    else:
        latest = memory.emotion_records[-1]
        reminder = memory.generate_support_advice(latest)

    print("\n机器人提醒：")
    print("-" * 70)
    print(reminder)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Emotion Memory 机器人提醒",
        reminder
    )


def test_log_write():
    content = (
        "这是 Atlas 3.0 Emotion Memory 的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明第五阶段日志保存正常。"
    )

    write_to_project_log(
        "Atlas 3.0 Emotion Memory 日志写入测试",
        content
    )


def show_intro(memory):
    print("\n==============================")
    print("Atlas 3.0")
    print("Stage 5: Emotion Memory")
    print("==============================")
    print(f"学生：{memory.student_name}")
    print(f"数据库版本：{memory.emotion_memory_version}")
    print(f"Emotion Memory 文件：{EMOTION_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")
    print("当前目标：记录 Eric 的研发情绪和 Debug 节奏")
    print("==============================")


def main():
    memory = load_emotion_memory()
    show_intro(memory)

    write_to_project_log(
        "Atlas 3.0 Emotion Memory 程序启动",
        "Atlas 3.0 第五阶段 Emotion Memory 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 新增今天的研发情绪记录")
        print("2. 查看最近研发情绪记录")
        print("3. 查看研发情绪总结")
        print("4. 机器人根据最近状态提醒 Eric")
        print("5. 测试 project_log.txt 是否能写入")
        print("6. 退出")

        choice = input("请输入数字 1-6：").strip()

        if choice == "1":
            add_emotion_record(memory)

        elif choice == "2":
            show_recent_records(memory)

        elif choice == "3":
            show_emotion_summary(memory)

        elif choice == "4":
            robot_reminder(memory)

        elif choice == "5":
            test_log_write()

        elif choice == "6":
            write_to_project_log(
                "Atlas 3.0 Emotion Memory 程序退出",
                "Atlas 3.0 第五阶段 Emotion Memory 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 6。")
            write_to_project_log(
                "Atlas 3.0 Emotion Memory 无效输入",
                f"用户输入了无效菜单数字：{choice}"
            )


if __name__ == "__main__":
    main()