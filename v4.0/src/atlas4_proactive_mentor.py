import json
from datetime import datetime, date, timedelta
from pathlib import Path


try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False


BASE_DIR = Path(__file__).resolve().parent

PROACTIVE_MENTOR_LOG_FILE = BASE_DIR / "proactive_mentor_log.txt"
PROACTIVE_MENTOR_DATA_FILE = BASE_DIR / "proactive_mentor_data.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"

ATLAS_UNIFIED_DATA_FILE = BASE_DIR / "atlas_unified_data.json"
ATLAS_FINAL_DATA_FILE = BASE_DIR / "atlas_final_data.json"
ATLAS_INTEGRATED_DATA_FILE = BASE_DIR / "atlas_integrated_data.json"
ATLAS3_DATA_FILE = BASE_DIR / "atlas3_data.json"

PROFILE_FILE = BASE_DIR / "profile.json"
SKILLS_FILE = BASE_DIR / "skills.json"
HISTORY_FILE = BASE_DIR / "history.json"
LEARNING_PLAN_FILE = BASE_DIR / "learning_plan.json"
EMOTION_FILE = BASE_DIR / "emotion_memory.json"
MENTOR_RECOMMENDATION_FILE = BASE_DIR / "mentor_recommendation.json"


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


def write_to_proactive_log(content):
    text = (
        "\n" + "=" * 70 + "\n"
        "Atlas 4.0 Proactive Mentor Log\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(PROACTIVE_MENTOR_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 proactive_mentor_log.txt")
    print(f"Proactive Mentor Log 位置：{PROACTIVE_MENTOR_LOG_FILE}")


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
    print(f"Project Log 位置：{PROJECT_LOG_FILE}")


def create_default_proactive_data():
    return {
        "student_name": "Eric",
        "proactive_mentor_version": "Atlas 4.0 Proactive Mentor v1",
        "proactive_records": []
    }


def load_proactive_data():
    if not PROACTIVE_MENTOR_DATA_FILE.exists():
        data = create_default_proactive_data()
        save_json(PROACTIVE_MENTOR_DATA_FILE, data)
        return data

    data = safe_load_json(
        PROACTIVE_MENTOR_DATA_FILE,
        create_default_proactive_data()
    )

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "proactive_mentor_version" not in data:
        data["proactive_mentor_version"] = "Atlas 4.0 Proactive Mentor v1"

    if "proactive_records" not in data:
        data["proactive_records"] = []

    save_json(PROACTIVE_MENTOR_DATA_FILE, data)
    return data


def save_proactive_record(record_type, content, source):
    data = load_proactive_data()

    record = {
        "time": get_now_text(),
        "record_type": record_type,
        "content": content,
        "source": source
    }

    data["proactive_records"].append(record)
    save_json(PROACTIVE_MENTOR_DATA_FILE, data)

    return record


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
                "skills_learned": [
                    "Profile",
                    "Skill Database",
                    "Project History",
                    "Learning Planner",
                    "Emotion Memory",
                    "Mentor Recommendation"
                ],
                "transfer_to_atlas": "Atlas 3.0 建立了 Eric Digital Twin 成长画像。"
            },
            {
                "project_name": "Atlas 4.0",
                "version": "4.0",
                "status": "in_progress",
                "skills_learned": [
                    "Vision",
                    "Voice Input",
                    "Voice Output",
                    "Memory Integration",
                    "Proactive Mentor"
                ],
                "transfer_to_atlas": "Atlas 4.0 正在把视觉、语音、长期记忆和主动导师能力整合起来。"
            }
        ],
        "daily_learning_plans": [],
        "emotion_records": [],
        "recommendations": [],
        "daily_tasks": [],
        "bugs": [],
        "weekly_reports": []
    }


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


def get_skill_score(memory, skill_name):
    skill = memory.get("skills", {}).get(skill_name)

    if not isinstance(skill, dict):
        return None

    return skill.get("score", None)


def format_memory_source_summary(memory, source):
    profile = memory.get("profile", {})
    skills = memory.get("skills", {})

    lines = []

    lines.append(f"长期记忆来源：{source}")
    lines.append("")
    lines.append("Eric Profile：")
    lines.append(f"- 名字：{profile.get('name', 'Eric')}")
    lines.append(f"- 年龄：{profile.get('age', 13)}")
    lines.append(f"- 长期目标：{profile.get('goal', 'AI Systems Engineer')}")
    lines.append(f"- 当前项目：{profile.get('current_project', 'Atlas')}")
    lines.append(f"- 当前版本：{profile.get('current_version', 'Atlas 4.0')}")
    lines.append("")
    lines.append("技能状态：")

    for skill_name, skill_info in skills.items():
        lines.append(f"- {skill_name}：{skill_info.get('score', 0)} 分")

    lines.append("")
    lines.append(f"Project History 数量：{len(memory.get('project_history', []))}")
    lines.append(f"Learning Plan 数量：{len(memory.get('daily_learning_plans', []))}")
    lines.append(f"Emotion Memory 数量：{len(memory.get('emotion_records', []))}")
    lines.append(f"Recommendation 数量：{len(memory.get('recommendations', []))}")
    lines.append(f"Daily Task 数量：{len(memory.get('daily_tasks', []))}")
    lines.append(f"Bug 数量：{len(memory.get('bugs', []))}")

    return "\n".join(lines)


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

    lines = []
    lines.append(f"从 project_log.txt 找到 {yesterday} 的记录：")

    for index, block in enumerate(recent_blocks, start=1):
        short_block = block.replace("\n\n", "\n")
        if len(short_block) > 600:
            short_block = short_block[:600] + "..."
        lines.append(f"\n记录 {index}：\n{short_block}")

    return "\n".join(lines)


def get_yesterday_learning_plan_summary(memory):
    yesterday = get_yesterday_text()
    plans = memory.get("daily_learning_plans", [])

    matched = []

    for plan in plans:
        if plan.get("date") == yesterday:
            matched.append(plan)

    if not matched:
        return f"没有找到 {yesterday} 的 Learning Plan。"

    latest = matched[-1]

    return (
        f"昨天 Learning Plan：\n"
        f"- 日期：{latest.get('date', '')}\n"
        f"- 重点：{latest.get('today_focus', '')}\n"
        f"- 原因：{latest.get('reason', '')}\n"
        f"- 状态：{latest.get('status', '')}\n"
        f"- 复盘：{latest.get('evening_review', '') if latest.get('evening_review') else '暂无'}"
    )


def get_yesterday_emotion_summary(memory):
    yesterday = get_yesterday_text()
    records = memory.get("emotion_records", [])

    matched = []

    for record in records:
        if record.get("date") == yesterday:
            matched.append(record)

    if not matched:
        return f"没有找到 {yesterday} 的 Emotion Memory。"

    latest = matched[-1]

    return (
        f"昨天研发状态：\n"
        f"- 状态：{latest.get('feeling', '')}\n"
        f"- 连续调试：{latest.get('debug_hours', 0)} 小时\n"
        f"- 问题：{latest.get('problem', '')}\n"
        f"- 下一步：{latest.get('next_step', '')}"
    )


def summarize_yesterday(memory):
    lines = []

    lines.append("昨天工作总结")
    lines.append("")
    lines.append(get_yesterday_learning_plan_summary(memory))
    lines.append("")
    lines.append(get_yesterday_emotion_summary(memory))
    lines.append("")
    lines.append(get_project_log_yesterday_summary())

    return "\n".join(lines)


def decide_today_task(memory):
    profile = memory.get("profile", {})
    current_version = profile.get("current_version", "Atlas 4.0")

    ros2_score = get_skill_score(memory, "ROS2")
    yolo_score = get_skill_score(memory, "YOLO")
    python_score = get_skill_score(memory, "Python")

    if "4.0" in current_version or "Atlas 4.0" in current_version:
        return {
            "focus": "Atlas 4.0 Proactive Mentor",
            "reason": "Vision、Voice Input、Voice Output 和 Memory Integration 已经跑通，现在应该让 Atlas 主动总结昨天、建议今天、提醒未推进任务。",
            "task_1": "运行 atlas4_proactive_mentor.py。",
            "task_2": "生成一次主动导师 Morning Brief。",
            "task_3": "测试 Atlas 是否能说出主动提醒。",
            "estimated_time": "1.5 到 2 小时"
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
            "task_2": "画出 Vision、Voice、Memory 的模块关系。",
            "task_3": "准备后续整合版主程序。",
            "estimated_time": "2 小时"
        }

    return {
        "focus": "Atlas 4.0 Integration",
        "reason": "当前基础功能较完整，可以开始整合 Atlas 4.0 的视觉、语音和记忆系统。",
        "task_1": "检查 Stage 1 到 Stage 5 的日志。",
        "task_2": "确认每个阶段都能单独运行。",
        "task_3": "准备进入 Stage 6 Hardware Feedback。",
        "estimated_time": "2 小时"
    }


def check_inactive_tasks(memory, inactive_days=3):
    today = date.today()
    warnings = []

    plans = memory.get("daily_learning_plans", [])
    tasks = memory.get("daily_tasks", [])

    for plan in plans:
        plan_date = parse_date(plan.get("date", ""))

        if plan_date is None:
            continue

        age = (today - plan_date).days
        status = plan.get("status", "")

        if age >= inactive_days and status not in ["完成", "completed", "done"]:
            warnings.append(
                f"Learning Plan 已经 {age} 天没有完成闭环："
                f"{plan.get('today_focus', '未知重点')} | 状态：{status}"
            )

    for task in tasks:
        task_date = parse_date(task.get("date", ""))

        if task_date is None:
            continue

        age = (today - task_date).days
        status = task.get("status", "")

        if age >= inactive_days and status not in ["完成", "completed", "done"]:
            warnings.append(
                f"Daily Task 已经 {age} 天没有完成闭环："
                f"{task.get('today_plan', '未知任务')} | 状态：{status}"
            )

    if not warnings:
        return "目前没有发现超过 3 天未推进的任务。"

    lines = []
    lines.append("长期未推进任务提醒：")

    for warning in warnings:
        lines.append(f"- {warning}")

    lines.append("")
    lines.append("建议：今天不要新增太多功能，先关闭一个旧任务或补一次复盘。")

    return "\n".join(lines)


def generate_morning_brief(memory, source):
    profile = memory.get("profile", {})
    today_task = decide_today_task(memory)
    yesterday_summary = summarize_yesterday(memory)
    inactive_warning = check_inactive_tasks(memory)

    name = profile.get("name", "Eric")
    goal = profile.get("goal", "AI Systems Engineer")
    current_project = profile.get("current_project", "Atlas")
    current_version = profile.get("current_version", "Atlas 4.0")

    lines = []

    lines.append(f"Good morning, {name}.")
    lines.append("")
    lines.append("I am Atlas 4.0 Proactive Mentor.")
    lines.append("")
    lines.append("一、当前项目状态")
    lines.append(f"- 长期目标：{goal}")
    lines.append(f"- 当前项目：{current_project}")
    lines.append(f"- 当前版本：{current_version}")
    lines.append(f"- 记忆来源：{source}")
    lines.append("")
    lines.append("二、昨天总结")
    lines.append(yesterday_summary)
    lines.append("")
    lines.append("三、今天建议")
    lines.append(f"- 今日重点：{today_task['focus']}")
    lines.append(f"- 原因：{today_task['reason']}")
    lines.append(f"- 任务 1：{today_task['task_1']}")
    lines.append(f"- 任务 2：{today_task['task_2']}")
    lines.append(f"- 任务 3：{today_task['task_3']}")
    lines.append(f"- 预计时间：{today_task['estimated_time']}")
    lines.append("")
    lines.append("四、未推进任务提醒")
    lines.append(inactive_warning)
    lines.append("")
    lines.append("五、Atlas 主动导师提醒")
    lines.append("今天不要同时扩大太多功能。先完成一个最小测试，再写入 Project Log。")

    return "\n".join(lines)


def speak_text(text):
    if not TTS_AVAILABLE:
        message = "pyttsx3 不可用，无法语音输出。请先确认第三阶段 Voice Output 是否正常。"
        print("\n" + message)
        return False

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 155)
        engine.setProperty("volume", 1.0)

        engine.say(text)
        engine.runAndWait()
        return True

    except Exception as error:
        print(f"\n语音输出失败：{error}")
        return False


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
        f"This is Atlas 4.0 Proactive Mentor. "
        f"Today I suggest you focus on {focus}. "
        f"The reason is: {today_task['reason']} "
        f"Your first task is: {today_task['task_1']} "
        f"{warning_sentence} "
        f"Please finish one small test first, then update the project log."
    )


def generate_and_show_morning_brief():
    memory, source = load_memory()
    brief = generate_morning_brief(memory, source)

    save_proactive_record(
        record_type="morning_brief",
        content=brief,
        source=source
    )

    print("\nAtlas 4.0 Proactive Morning Brief：")
    print("-" * 70)
    print(brief)
    print("-" * 70)

    write_to_proactive_log(brief)
    write_to_project_log(
        "Atlas 4.0 Proactive Mentor 生成 Morning Brief",
        brief
    )


def generate_and_speak_morning_brief():
    memory, source = load_memory()
    brief = generate_morning_brief(memory, source)
    short_speech = build_short_speech(memory)

    spoken = speak_text(short_speech)
    status = "spoken" if spoken else "text_only"

    content = (
        f"语音状态：{status}\n\n"
        f"语音简版内容：\n{short_speech}\n\n"
        f"完整 Morning Brief：\n{brief}"
    )

    save_proactive_record(
        record_type="spoken_morning_brief",
        content=content,
        source=source
    )

    print("\nAtlas 4.0 Proactive Mentor 已生成语音版 Morning Brief：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_proactive_log(content)
    write_to_project_log(
        "Atlas 4.0 Proactive Mentor 语音 Morning Brief",
        content
    )


def show_yesterday_summary():
    memory, source = load_memory()
    content = summarize_yesterday(memory)

    print("\n昨天工作总结：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    save_proactive_record(
        record_type="yesterday_summary",
        content=content,
        source=source
    )

    write_to_proactive_log(content)
    write_to_project_log(
        "Atlas 4.0 Proactive Mentor 昨天总结",
        content
    )


def show_today_task():
    memory, source = load_memory()
    task = decide_today_task(memory)

    content = (
        f"今天建议任务：\n"
        f"- 今日重点：{task['focus']}\n"
        f"- 原因：{task['reason']}\n"
        f"- 任务 1：{task['task_1']}\n"
        f"- 任务 2：{task['task_2']}\n"
        f"- 任务 3：{task['task_3']}\n"
        f"- 预计时间：{task['estimated_time']}"
    )

    print("\n今天建议任务：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    save_proactive_record(
        record_type="today_task",
        content=content,
        source=source
    )

    write_to_proactive_log(content)
    write_to_project_log(
        "Atlas 4.0 Proactive Mentor 今日任务建议",
        content
    )


def show_inactive_task_warning():
    memory, source = load_memory()
    content = check_inactive_tasks(memory)

    print("\n未推进任务提醒：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    save_proactive_record(
        record_type="inactive_task_warning",
        content=content,
        source=source
    )

    write_to_proactive_log(content)
    write_to_project_log(
        "Atlas 4.0 Proactive Mentor 未推进任务提醒",
        content
    )


def show_memory_source():
    memory, source = load_memory()
    content = format_memory_source_summary(memory, source)

    print("\nProactive Mentor 读取记忆来源：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_proactive_log(content)
    write_to_project_log(
        "Atlas 4.0 Proactive Mentor 记忆来源检测",
        content
    )


def show_recent_proactive_records():
    data = load_proactive_data()
    records = data.get("proactive_records", [])

    if not records:
        message = "目前还没有 Proactive Mentor 记录。"
        print("\n" + message)
        write_to_proactive_log(message)
        return

    recent_records = records[-5:]
    lines = []

    print("\n最近 5 条 Proactive Mentor 记录：")
    print("-" * 70)

    for record in recent_records:
        text = (
            f"时间：{record.get('time', '')}\n"
            f"类型：{record.get('record_type', '')}\n"
            f"来源：{record.get('source', '')}\n"
            f"内容：\n{record.get('content', '')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    content = "\n\n".join(lines)

    write_to_proactive_log(content)
    write_to_project_log(
        "Atlas 4.0 Proactive Mentor 查看最近记录",
        content
    )


def test_log_write():
    content = (
        "这是 Atlas 4.0 Proactive Mentor 第五阶段的日志写入测试。\n"
        "如果你能看到这段记录，说明 proactive_mentor_log.txt 和 project_log.txt 都可以正常写入。"
    )

    write_to_proactive_log(content)
    write_to_project_log(
        "Atlas 4.0 Proactive Mentor 日志写入测试",
        content
    )


def show_intro():
    print("\n==============================")
    print("Atlas 4.0")
    print("Stage 5: Proactive Mentor")
    print("==============================")
    print("目标：让 Atlas 主动问候 Eric、总结昨天、建议今天、提醒未推进任务。")
    print("当前阶段只做 Proactive Mentor，不做 Arduino 硬件反馈。")
    print(f"Proactive Mentor Log 文件：{PROACTIVE_MENTOR_LOG_FILE}")
    print(f"Proactive Mentor Data 文件：{PROACTIVE_MENTOR_DATA_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")


def main():
    show_intro()

    write_to_project_log(
        "Atlas 4.0 Proactive Mentor 程序启动",
        "Atlas 4.0 第五阶段 Proactive Mentor 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 检测长期记忆来源")
        print("2. 生成主动导师 Morning Brief")
        print("3. 生成并语音播放 Morning Brief")
        print("4. 只查看昨天工作总结")
        print("5. 只查看今天任务建议")
        print("6. 检查长期未推进任务")
        print("7. 查看最近 Proactive Mentor 记录")
        print("8. 测试 proactive_mentor_log.txt 和 project_log.txt 写入")
        print("9. 退出")

        choice = input("请输入数字 1-9：").strip()

        if choice == "1":
            show_memory_source()

        elif choice == "2":
            generate_and_show_morning_brief()

        elif choice == "3":
            generate_and_speak_morning_brief()

        elif choice == "4":
            show_yesterday_summary()

        elif choice == "5":
            show_today_task()

        elif choice == "6":
            show_inactive_task_warning()

        elif choice == "7":
            show_recent_proactive_records()

        elif choice == "8":
            test_log_write()

        elif choice == "9":
            write_to_project_log(
                "Atlas 4.0 Proactive Mentor 程序退出",
                "Atlas 4.0 第五阶段 Proactive Mentor 程序已退出。"
            )

            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 9。")


if __name__ == "__main__":
    main()