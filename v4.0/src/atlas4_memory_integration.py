import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

# Atlas 4.0 本阶段文件
MEMORY_INTEGRATION_LOG_FILE = BASE_DIR / "memory_integration_log.txt"
MEMORY_INTEGRATION_DATA_FILE = BASE_DIR / "memory_integration_data.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"

# Voice Input 阶段生成的数据
VOICE_INPUT_DATA_FILE = BASE_DIR / "voice_input_data.json"

# Atlas 3.0 / 综合版可能存在的数据文件
ATLAS_UNIFIED_DATA_FILE = BASE_DIR / "atlas_unified_data.json"
ATLAS3_DATA_FILE = BASE_DIR / "atlas3_data.json"
ATLAS_FINAL_DATA_FILE = BASE_DIR / "atlas_final_data.json"
ATLAS_INTEGRATED_DATA_FILE = BASE_DIR / "atlas_integrated_data.json"

# Atlas 3.0 分散旧文件
PROFILE_FILE = BASE_DIR / "profile.json"
SKILLS_FILE = BASE_DIR / "skills.json"
HISTORY_FILE = BASE_DIR / "history.json"
LEARNING_PLAN_FILE = BASE_DIR / "learning_plan.json"
EMOTION_FILE = BASE_DIR / "emotion_memory.json"
MENTOR_RECOMMENDATION_FILE = BASE_DIR / "mentor_recommendation.json"


def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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


def write_to_memory_log(content):
    text = (
        "\n" + "=" * 70 + "\n"
        "Atlas 4.0 Memory Integration Log\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(MEMORY_INTEGRATION_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 memory_integration_log.txt")
    print(f"Memory Integration Log 位置：{MEMORY_INTEGRATION_LOG_FILE}")


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


def create_default_memory_integration_data():
    return {
        "student_name": "Eric",
        "memory_integration_version": "Atlas 4.0 Memory Integration v1",
        "memory_interactions": []
    }


def load_memory_integration_data():
    if not MEMORY_INTEGRATION_DATA_FILE.exists():
        data = create_default_memory_integration_data()
        save_json(MEMORY_INTEGRATION_DATA_FILE, data)
        return data

    data = safe_load_json(
        MEMORY_INTEGRATION_DATA_FILE,
        create_default_memory_integration_data()
    )

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "memory_integration_version" not in data:
        data["memory_integration_version"] = "Atlas 4.0 Memory Integration v1"

    if "memory_interactions" not in data:
        data["memory_interactions"] = []

    save_json(MEMORY_INTEGRATION_DATA_FILE, data)
    return data


def save_memory_interaction(question, answer, source):
    data = load_memory_integration_data()

    record = {
        "time": get_now_text(),
        "question": question,
        "answer": answer,
        "source": source
    }

    data["memory_interactions"].append(record)
    save_json(MEMORY_INTEGRATION_DATA_FILE, data)

    return record


def create_default_atlas_memory():
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
                "skills_learned": ["Profile", "Skill Database", "Project History", "Learning Planner", "Emotion Memory", "Mentor Recommendation"],
                "transfer_to_atlas": "Atlas 3.0 建立了 Eric Digital Twin 成长画像。"
            },
            {
                "project_name": "Atlas 4.0",
                "version": "4.0",
                "status": "in_progress",
                "skills_learned": ["Vision", "Voice Input", "Voice Output", "Memory Integration"],
                "transfer_to_atlas": "Atlas 4.0 正在把视觉、语音和长期记忆整合成多模态导师。"
            }
        ],
        "daily_learning_plans": [],
        "emotion_records": [],
        "recommendations": []
    }


def load_atlas_memory():
    """
    优先读取综合数据库。
    如果没有综合数据库，就读取 Atlas 3.0 分散文件。
    如果都没有，就使用默认数据。
    """

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

            if memory:
                return memory, str(file_path.name)

    # 如果没有综合数据库，就尝试读取分散文件
    profile = safe_load_json(PROFILE_FILE, {})
    skills_data = safe_load_json(SKILLS_FILE, {})
    history_data = safe_load_json(HISTORY_FILE, {})
    learning_plan_data = safe_load_json(LEARNING_PLAN_FILE, {})
    emotion_data = safe_load_json(EMOTION_FILE, {})
    recommendation_data = safe_load_json(MENTOR_RECOMMENDATION_FILE, {})

    if profile or skills_data or history_data:
        memory = create_default_atlas_memory()

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

    return create_default_atlas_memory(), "default memory"


def normalize_memory_data(data):
    """
    兼容 atlas3_data.json、atlas_unified_data.json、atlas_final_data.json 等结构。
    """

    if not isinstance(data, dict):
        return None

    default_memory = create_default_atlas_memory()

    memory = {
        "student_name": data.get("student_name", "Eric"),
        "profile": data.get("profile", default_memory["profile"]),
        "skills": data.get("skills", default_memory["skills"]),
        "project_history": data.get("project_history", default_memory["project_history"]),
        "daily_learning_plans": data.get("daily_learning_plans", []),
        "emotion_records": data.get("emotion_records", []),
        "recommendations": data.get("recommendations", [])
    }

    # 有些 2.0 / 综合版用 projects，不用 project_history
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


def get_latest_voice_input_text():
    if not VOICE_INPUT_DATA_FILE.exists():
        return ""

    data = safe_load_json(VOICE_INPUT_DATA_FILE, {})
    records = data.get("voice_records", [])

    if not records:
        return ""

    for record in reversed(records):
        text = record.get("recognized_text", "")
        status = record.get("status", "")

        if text and status == "recognized":
            return text

    return ""


def format_profile_summary(memory):
    profile = memory.get("profile", {})

    interests = profile.get("interests", [])
    strengths = profile.get("strengths", [])
    weaknesses = profile.get("weaknesses", [])

    interests_text = "、".join(interests) if interests else "暂无"
    strengths_text = "、".join(strengths) if strengths else "暂无"
    weaknesses_text = "、".join(weaknesses) if weaknesses else "暂无"

    return (
        f"Eric 的当前成长画像：\n"
        f"- 年龄：{profile.get('age', 13)}\n"
        f"- 长期目标：{profile.get('goal', 'AI Systems Engineer')}\n"
        f"- 当前项目：{profile.get('current_project', 'Atlas')}\n"
        f"- 当前版本：{profile.get('current_version', 'Atlas 4.0')}\n"
        f"- 兴趣：{interests_text}\n"
        f"- 强项：{strengths_text}\n"
        f"- 需要补强：{weaknesses_text}\n"
        f"- 学习风格：{profile.get('learning_style', '喜欢通过项目实战学习')}"
    )


def format_skill_summary(memory):
    skills = memory.get("skills", {})

    lines = []

    lines.append("Eric 的技能状态：")

    for skill_name, skill_info in skills.items():
        lines.append(
            f"- {skill_name}：{skill_info.get('score', 0)} 分，level：{skill_info.get('level', 'unknown')}"
        )

    return "\n".join(lines)


def format_project_history_summary(memory):
    history = memory.get("project_history", [])

    if not history:
        return "目前没有 Project History。"

    lines = []

    lines.append("Eric 的项目历史：")

    for project in history:
        project_name = project.get("project_name", "未命名项目")
        version = project.get("version", "unknown")
        status = project.get("status", "unknown")
        skills = project.get("skills_learned", [])
        transfer = project.get("transfer_to_atlas", "")

        skills_text = "、".join(skills) if skills else "暂无技能记录"

        lines.append(
            f"- {project_name} ({version}) | 状态：{status} | 学到：{skills_text}"
        )

        if transfer:
            lines.append(f"  迁移价值：{transfer}")

    return "\n".join(lines)


def get_latest_learning_plan_text(memory):
    plans = memory.get("daily_learning_plans", [])

    if not plans:
        return "目前没有 Learning Plan 记录。"

    latest = plans[-1]

    return (
        f"最近一次 Learning Plan：\n"
        f"- 日期：{latest.get('date', '')}\n"
        f"- 今日重点：{latest.get('today_focus', '')}\n"
        f"- 原因：{latest.get('reason', '')}\n"
        f"- 任务 1：{latest.get('task_1', '')}\n"
        f"- 任务 2：{latest.get('task_2', '')}\n"
        f"- 任务 3：{latest.get('task_3', '')}\n"
        f"- 状态：{latest.get('status', '')}"
    )


def get_latest_emotion_text(memory):
    records = memory.get("emotion_records", [])

    if not records:
        return "目前没有 Emotion Memory 记录。"

    latest = records[-1]

    return (
        f"最近一次研发状态：\n"
        f"- 状态：{latest.get('feeling', '')}\n"
        f"- 连续调试时间：{latest.get('debug_hours', 0)} 小时\n"
        f"- 问题：{latest.get('problem', '')}\n"
        f"- 下一步：{latest.get('next_step', '')}"
    )


def answer_question_with_memory(question, memory):
    question_lower = question.lower()

    profile = memory.get("profile", {})
    skills = memory.get("skills", {})
    history = memory.get("project_history", [])

    ros2_score = skills.get("ROS2", {}).get("score", None)
    arduino_score = skills.get("Arduino", {}).get("score", None)
    python_score = skills.get("Python", {}).get("score", None)
    opencv_score = skills.get("OpenCV", {}).get("score", None)

    # 问下一步 / 今天做什么
    if (
        "下一步" in question
        or "今天" in question
        or "学什么" in question
        or "next" in question_lower
        or "today" in question_lower
        or "what should i do" in question_lower
    ):
        if ros2_score is not None and ros2_score < 40:
            return (
                "Eric，根据你的长期记忆，我建议你下一步继续补 ROS2。\n\n"
                f"原因是：Arduino 当前约 {arduino_score} 分，Python 当前约 {python_score} 分，OpenCV 当前约 {opencv_score} 分，"
                f"但 ROS2 目前只有 {ros2_score} 分。\n\n"
                "如果你未来要做真正的机器人系统，ROS2 是必须补上的能力。"
            )

        return (
            "Eric，根据你的长期记忆，下一步建议继续推进 Atlas 4.0 的多模态整合。\n"
            "现在你已经完成 Vision、Voice Input、Voice Output，当前重点是 Memory Integration。"
        )

    # 问 ROS2
    if "ros" in question_lower or "ros2" in question_lower:
        return (
            f"Eric，你现在需要关注 ROS2。\n\n"
            f"你的 ROS2 当前分数是 {ros2_score}。\n"
            "你的 Arduino、Python、OpenCV 已经有基础，所以你不需要继续重复基础 Arduino。\n"
            "如果未来要做真正的机器人系统，ROS2 是下一阶段必须补上的能力。"
        )

    # 问 Arduino
    if "arduino" in question_lower:
        return (
            f"Eric，你的 Arduino 当前分数是 {arduino_score}。\n\n"
            "这已经是你的强项。你可以继续用 Arduino 做硬件反馈，"
            "但不建议继续停留在基础 Arduino。下一步更应该进入 ROS2、视觉、语音和系统整合。"
        )

    # 问 Atlas 3.0
    if "3.0" in question or "atlas 3" in question_lower:
        return (
            "Eric，Atlas 3.0 的核心成果是 Eric Digital Twin。\n\n"
            "它包括 Profile、Skill Database、Project History、Learning Planner、Emotion Memory 和 Mentor Recommendation。\n"
            "这些长期记忆现在会成为 Atlas 4.0 Memory Integration 的基础。"
        )

    # 问 Atlas 4.0
    if "4.0" in question or "atlas 4" in question_lower:
        return (
            "Eric，Atlas 4.0 的目标是把 Atlas 从记忆和规划助手升级为多模态导师。\n\n"
            "目前已经完成 Vision、Voice Input、Voice Output，现在正在做 Memory Integration。\n"
            "下一步才是 Proactive Mentor。"
        )

    # 问植物项目
    if "植物" in question or "plant" in question_lower:
        return (
            "Eric，你的智能植物养护系统不是孤立项目。\n\n"
            "它训练了 Arduino、传感器、硬件接线和项目迭代能力。"
            "这些能力后来迁移到了 Atlas 的硬件反馈、摄像头检测和多模态系统设计里。"
        )

    # 问项目历史
    if "历史" in question or "project history" in question_lower or "past project" in question_lower:
        return format_project_history_summary(memory)

    # 问技能
    if "技能" in question or "skill" in question_lower:
        return format_skill_summary(memory)

    # 问画像 / profile
    if "画像" in question or "profile" in question_lower or "who am i" in question_lower:
        return format_profile_summary(memory)

    # 问计划
    if "计划" in question or "learning plan" in question_lower:
        return get_latest_learning_plan_text(memory)

    # 问调试 / 累 / debug
    if "debug" in question_lower or "调试" in question or "累" in question or "卡住" in question:
        emotion_text = get_latest_emotion_text(memory)

        return (
            f"{emotion_text}\n\n"
            "如果你已经连续调试很久，Atlas 建议先休息 15 到 20 分钟，"
            "然后回来只测试一个最小问题。"
        )

    # 默认回答
    return (
        f"Eric，我已经读取了你的长期记忆。\n\n"
        f"{format_profile_summary(memory)}\n\n"
        "如果你想让我更准确回答，可以问：\n"
        "1. 我下一步应该做什么？\n"
        "2. 为什么要学 ROS2？\n"
        "3. 我的项目历史是什么？\n"
        "4. 我现在的技能状态是什么？"
    )


def show_memory_source():
    memory, source = load_atlas_memory()

    content = (
        f"Atlas 4.0 当前读取到的长期记忆来源：{source}\n\n"
        f"{format_profile_summary(memory)}\n\n"
        f"{format_skill_summary(memory)}\n\n"
        f"Project History 数量：{len(memory.get('project_history', []))} 个\n"
        f"Learning Plan 数量：{len(memory.get('daily_learning_plans', []))} 条\n"
        f"Emotion Memory 数量：{len(memory.get('emotion_records', []))} 条\n"
        f"Mentor Recommendation 数量：{len(memory.get('recommendations', []))} 条"
    )

    print("\n长期记忆来源检测结果：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_memory_log(content)
    write_to_project_log(
        "Atlas 4.0 Memory Integration 检测长期记忆来源",
        content
    )


def answer_latest_voice_input():
    memory, source = load_atlas_memory()
    question = get_latest_voice_input_text()

    if not question:
        message = (
            "没有找到最近一次有效语音识别文本。\n"
            "请先运行 atlas4_voice_input.py，录音并成功识别一句话；"
            "或者在本程序选择 3，手动输入问题测试 Memory Integration。"
        )

        print("\n" + message)

        write_to_memory_log(message)
        write_to_project_log(
            "Atlas 4.0 Memory Integration 读取语音失败",
            message
        )

        return

    answer = answer_question_with_memory(question, memory)

    content = (
        f"长期记忆来源：{source}\n\n"
        f"Eric 最近语音问题：\n{question}\n\n"
        f"Atlas 基于长期记忆的回答：\n{answer}"
    )

    save_memory_interaction(
        question=question,
        answer=answer,
        source="latest voice input + " + source
    )

    print("\nAtlas 读取最近语音，并根据长期记忆回答：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_memory_log(content)
    write_to_project_log(
        "Atlas 4.0 Memory Integration 语音问题记忆回答",
        content
    )


def answer_manual_question():
    memory, source = load_atlas_memory()

    question = input("\n请输入 Eric 的问题，例如：我下一步应该做什么？").strip()

    if not question:
        question = "我下一步应该做什么？"

    answer = answer_question_with_memory(question, memory)

    content = (
        f"长期记忆来源：{source}\n\n"
        f"Eric 手动输入问题：\n{question}\n\n"
        f"Atlas 基于长期记忆的回答：\n{answer}"
    )

    save_memory_interaction(
        question=question,
        answer=answer,
        source="manual input + " + source
    )

    print("\nAtlas 基于长期记忆的回答：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_memory_log(content)
    write_to_project_log(
        "Atlas 4.0 Memory Integration 手动问题记忆回答",
        content
    )


def show_recent_memory_interactions():
    data = load_memory_integration_data()
    records = data.get("memory_interactions", [])

    if not records:
        message = "目前还没有 Memory Integration 问答记录。"
        print("\n" + message)
        write_to_memory_log(message)
        return

    recent_records = records[-5:]

    lines = []

    print("\n最近 5 条 Memory Integration 问答记录：")
    print("-" * 70)

    for record in recent_records:
        text = (
            f"时间：{record.get('time', '')}\n"
            f"来源：{record.get('source', '')}\n"
            f"问题：{record.get('question', '')}\n"
            f"回答：{record.get('answer', '')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    content = "\n\n".join(lines)

    write_to_memory_log(content)
    write_to_project_log(
        "Atlas 4.0 Memory Integration 查看最近问答记录",
        content
    )


def test_log_write():
    content = (
        "这是 Atlas 4.0 Memory Integration 第四阶段的日志写入测试。\n"
        "如果你能看到这段记录，说明 memory_integration_log.txt 和 project_log.txt 都可以正常写入。"
    )

    write_to_memory_log(content)
    write_to_project_log(
        "Atlas 4.0 Memory Integration 日志写入测试",
        content
    )


def show_intro():
    print("\n==============================")
    print("Atlas 4.0")
    print("Stage 4: Memory Integration")
    print("==============================")
    print("目标：把 Eric 的语音问题和 Atlas 3.0 长期记忆连接起来。")
    print("当前阶段只做 Memory Integration，不做主动导师、不做 Arduino 反馈。")
    print(f"Memory Integration Log 文件：{MEMORY_INTEGRATION_LOG_FILE}")
    print(f"Memory Integration Data 文件：{MEMORY_INTEGRATION_DATA_FILE}")
    print(f"Voice Input Data 文件：{VOICE_INPUT_DATA_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")


def main():
    show_intro()

    write_to_project_log(
        "Atlas 4.0 Memory Integration 程序启动",
        "Atlas 4.0 第四阶段 Memory Integration 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 检测 Atlas 3.0 长期记忆来源")
        print("2. 读取最近一次语音识别文本，并根据长期记忆回答")
        print("3. 手动输入问题，并根据长期记忆回答")
        print("4. 查看最近 Memory Integration 问答记录")
        print("5. 测试 memory_integration_log.txt 和 project_log.txt 写入")
        print("6. 退出")

        choice = input("请输入数字 1-6：").strip()

        if choice == "1":
            show_memory_source()

        elif choice == "2":
            answer_latest_voice_input()

        elif choice == "3":
            answer_manual_question()

        elif choice == "4":
            show_recent_memory_interactions()

        elif choice == "5":
            test_log_write()

        elif choice == "6":
            write_to_project_log(
                "Atlas 4.0 Memory Integration 程序退出",
                "Atlas 4.0 第四阶段 Memory Integration 程序已退出。"
            )

            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 6。")


if __name__ == "__main__":
    main()