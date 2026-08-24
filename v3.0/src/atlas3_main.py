import json
from datetime import datetime, date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "atlas3_data.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"

OLD_PROFILE_FILE = BASE_DIR / "profile.json"
OLD_SKILLS_FILE = BASE_DIR / "skills.json"
OLD_HISTORY_FILE = BASE_DIR / "history.json"
OLD_LEARNING_PLAN_FILE = BASE_DIR / "learning_plan.json"
OLD_EMOTION_FILE = BASE_DIR / "emotion_memory.json"
OLD_RECOMMENDATION_FILE = BASE_DIR / "mentor_recommendation.json"


# =========================
# 基础工具
# =========================

def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_today_text():
    return date.today().strftime("%Y-%m-%d")


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


def write_to_project_log(title, content):
    text = (
        "\n" + "=" * 70 + "\n"
        f"{title}\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + str(content) + "\n"
        + "=" * 70 + "\n"
    )

    with open(PROJECT_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 project_log.txt")
    print(f"日志文件位置：{PROJECT_LOG_FILE}")


def get_next_id(items):
    ids = []

    for item in items:
        if isinstance(item, dict) and isinstance(item.get("id"), int):
            ids.append(item["id"])

    if not ids:
        return 1

    return max(ids) + 1


def split_text_to_list(text):
    result = []

    if not text:
        return result

    for item in text.split(","):
        clean_item = item.strip()
        if clean_item:
            result.append(clean_item)

    return result


# =========================
# 默认总数据库
# =========================

def create_default_data():
    return {
        "student_name": "Eric",
        "atlas_version": "Atlas 3.0",
        "database_version": "Atlas 3.0 Unified Database v1",
        "profile": {
            "name": "Eric",
            "age": 13,
            "goal": "AI Systems Engineer",
            "current_project": "Atlas",
            "current_version": "Atlas 3.0",
            "interests": [
                "AI",
                "Robot",
                "Python",
                "Basketball"
            ],
            "strengths": [
                "Arduino",
                "Python",
                "OpenCV",
                "Project Iteration",
                "Hardware Prototyping"
            ],
            "weaknesses": [
                "ROS2",
                "Advanced Robot System Design",
                "Long-term Engineering Documentation"
            ],
            "learning_style": "喜欢通过项目实战学习，不喜欢重复听很多理论。",
            "mentor_note": "Eric is building Atlas as a long-term AI research mentor robot."
        },
        "skills": {
            "Arduino": {
                "score": 95,
                "level": "strong",
                "note": "Eric can already use Arduino for hardware feedback, LEDs, servo, and OLED."
            },
            "Python": {
                "score": 80,
                "level": "good",
                "note": "Eric can use Python for JSON, file reading and writing, OpenCV, and project management logic."
            },
            "OpenCV": {
                "score": 75,
                "level": "good",
                "note": "Eric can use OpenCV for camera detection and face presence checking."
            },
            "YOLO": {
                "score": 60,
                "level": "developing",
                "note": "Eric has basic direction for object detection but still needs more practice."
            },
            "ROS2": {
                "score": 0,
                "level": "not_started",
                "note": "Eric has not started ROS2 yet. This is important for future robot systems."
            }
        },
        "next_learning_focus": "ROS2",
        "project_history": [
            {
                "id": 1,
                "project_name": "智能植物养护系统",
                "version": "1.0 - 1.1",
                "status": "completed",
                "project_type": "AI + Hardware + Plant Care",
                "main_goal": "Build a smart plant care system with sensors, watering, lighting, and basic monitoring.",
                "skills_learned": [
                    "Arduino",
                    "Sensors",
                    "Serial Communication",
                    "Hardware Wiring",
                    "Project Iteration"
                ],
                "key_problems": [
                    "Hardware stability",
                    "Sensor reading",
                    "Camera recognition preparation"
                ],
                "transfer_to_atlas": "Eric learned hardware control, serial communication, and project iteration. These skills help Atlas control Arduino, OLED, servo, and hardware feedback.",
                "evidence": "Project logs, demo videos, hardware prototype"
            },
            {
                "id": 2,
                "project_name": "Atlas 1.0 / AI Research Mentor Robot",
                "version": "1.0",
                "status": "completed",
                "project_type": "AI Mentor Robot",
                "main_goal": "Build a basic AI research mentor robot with memory, project log, mentor advice, emotion support, Arduino/OLED feedback, and camera detection.",
                "skills_learned": [
                    "Python",
                    "JSON",
                    "OpenCV",
                    "Arduino Communication",
                    "Project Log",
                    "Debugging"
                ],
                "key_problems": [
                    "Camera false detection",
                    "Project log file path issue",
                    "Hardware and software integration"
                ],
                "transfer_to_atlas": "Eric learned how to combine software, hardware, memory, and camera sensing into one mentor robot.",
                "evidence": "atlas_full_main.py, memory records, camera logs, project_log.txt"
            },
            {
                "id": 3,
                "project_name": "Atlas 2.0",
                "version": "2.0",
                "status": "completed",
                "project_type": "Project Management Robot",
                "main_goal": "Upgrade Atlas from a chatbot into a project management mentor that can manage projects, daily tasks, bugs, and weekly reports.",
                "skills_learned": [
                    "Project Database",
                    "Daily Task Management",
                    "Bug Manager",
                    "Weekly Report",
                    "JSON Database Design",
                    "File Management"
                ],
                "key_problems": [
                    "Too many separate code files",
                    "Need to merge functions into one main program",
                    "Need to organize version evidence"
                ],
                "transfer_to_atlas": "Eric learned how to manage engineering work systematically. This becomes the foundation for Atlas 3.0 long-term memory and personalized mentoring.",
                "evidence": "atlas2_main.py, atlas_full_main.py, atlas2_data.json, weekly_report.txt"
            },
            {
                "id": 4,
                "project_name": "Atlas 3.0",
                "version": "3.0",
                "status": "in_progress",
                "project_type": "Digital Twin Mentor Robot",
                "main_goal": "Build Eric Digital Twin so Atlas can understand Eric's profile, skills, project history, learning plan, emotion memory, and mentor recommendations.",
                "skills_learned": [
                    "Profile Database",
                    "Skill Database",
                    "Project History",
                    "Learning Planner",
                    "Emotion Memory",
                    "Mentor Recommendation"
                ],
                "key_problems": [
                    "Need to connect all six stages into one main program",
                    "Need to merge all JSON files into one database"
                ],
                "transfer_to_atlas": "Atlas 3.0 uses Eric's profile, skills, project history, learning plan, emotion memory, and mentor recommendation to generate personalized guidance.",
                "evidence": "atlas3_main.py, atlas3_data.json, project_log.txt"
            }
        ],
        "daily_learning_plans": [],
        "emotion_records": [],
        "recommendations": []
    }


def ensure_data_fields(data):
    default_data = create_default_data()

    for key, value in default_data.items():
        if key not in data:
            data[key] = value

    if not isinstance(data.get("profile"), dict):
        data["profile"] = default_data["profile"]

    if not isinstance(data.get("skills"), dict):
        data["skills"] = default_data["skills"]

    if not isinstance(data.get("project_history"), list):
        data["project_history"] = default_data["project_history"]

    if not isinstance(data.get("daily_learning_plans"), list):
        data["daily_learning_plans"] = []

    if not isinstance(data.get("emotion_records"), list):
        data["emotion_records"] = []

    if not isinstance(data.get("recommendations"), list):
        data["recommendations"] = []

    return data


def migrate_old_json_files():
    if DATA_FILE.exists():
        data = safe_load_json(DATA_FILE, create_default_data())
        data = ensure_data_fields(data)
        save_data(data)
        return data

    data = create_default_data()

    old_profile = safe_load_json(OLD_PROFILE_FILE, {})
    if old_profile:
        data["profile"] = old_profile

    old_skills = safe_load_json(OLD_SKILLS_FILE, {})
    if old_skills:
        if isinstance(old_skills.get("skills"), dict):
            data["skills"] = old_skills["skills"]

        if old_skills.get("next_learning_focus"):
            data["next_learning_focus"] = old_skills["next_learning_focus"]

    old_history = safe_load_json(OLD_HISTORY_FILE, {})
    if old_history:
        if isinstance(old_history.get("project_history"), list) and old_history["project_history"]:
            data["project_history"] = old_history["project_history"]

    old_learning_plan = safe_load_json(OLD_LEARNING_PLAN_FILE, {})
    if old_learning_plan:
        if isinstance(old_learning_plan.get("daily_learning_plans"), list):
            data["daily_learning_plans"] = old_learning_plan["daily_learning_plans"]

    old_emotion = safe_load_json(OLD_EMOTION_FILE, {})
    if old_emotion:
        if isinstance(old_emotion.get("emotion_records"), list):
            data["emotion_records"] = old_emotion["emotion_records"]

    old_recommendation = safe_load_json(OLD_RECOMMENDATION_FILE, {})
    if old_recommendation:
        if isinstance(old_recommendation.get("recommendations"), list):
            data["recommendations"] = old_recommendation["recommendations"]

    data = ensure_data_fields(data)
    save_data(data)

    write_to_project_log(
        "Atlas 3.0 总数据库初始化",
        "已创建 atlas3_data.json，并尝试从 profile.json、skills.json、history.json、learning_plan.json、emotion_memory.json、mentor_recommendation.json 迁移数据。"
    )

    return data


def load_data():
    return migrate_old_json_files()


def save_data(data):
    save_json(DATA_FILE, data)


# =========================
# Profile
# =========================

def profile_identity_text(data):
    profile = data["profile"]

    interests_text = "、".join(profile.get("interests", [])) if profile.get("interests") else "暂无"
    strengths_text = "、".join(profile.get("strengths", [])) if profile.get("strengths") else "暂无"
    weaknesses_text = "、".join(profile.get("weaknesses", [])) if profile.get("weaknesses") else "暂无"

    return (
        f"{profile.get('name', 'Eric')}，我已经读取了你的成长画像。\n\n"
        f"你现在 {profile.get('age', 13)} 岁。\n"
        f"你的长期目标是：{profile.get('goal', 'AI Systems Engineer')}。\n"
        f"你目前正在开发：{profile.get('current_project', 'Atlas')}。\n"
        f"当前版本是：{profile.get('current_version', 'Atlas 3.0')}。\n\n"
        f"你的兴趣包括：{interests_text}。\n"
        f"你的强项包括：{strengths_text}。\n"
        f"你需要补强的能力包括：{weaknesses_text}。\n\n"
        f"学习风格：{profile.get('learning_style', '')}\n"
        f"导师备注：{profile.get('mentor_note', '')}"
    )


def show_profile(data):
    content = profile_identity_text(data)

    print("\nEric Profile 成长画像：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 查看 Eric Profile", content)


def robot_profile_intro(data):
    profile = data["profile"]

    reply = (
        f"{profile.get('name', 'Eric')}，目前你正在开发 {profile.get('current_project', 'Atlas')}。\n"
        f"当前版本是 {profile.get('current_version', 'Atlas 3.0')}。\n"
        f"你的目标是成为 {profile.get('goal', 'AI Systems Engineer')}。\n"
        f"所以我会根据你的成长画像来回答，而不是只说普通的你好。"
    )

    print("\n机器人回答：")
    print("-" * 70)
    print(reply)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 Profile 身份回答", reply)


def update_profile(data):
    profile = data["profile"]

    print("\n开始更新 Eric Profile。")
    print("不想修改的地方直接回车。")

    old_text = profile_identity_text(data)

    new_name = input(f"名字（当前：{profile.get('name', 'Eric')}）：").strip()
    new_age = input(f"年龄（当前：{profile.get('age', 13)}）：").strip()
    new_goal = input(f"长期目标（当前：{profile.get('goal', '')}）：").strip()
    new_project = input(f"当前项目（当前：{profile.get('current_project', '')}）：").strip()
    new_version = input(f"当前版本（当前：{profile.get('current_version', '')}）：").strip()
    new_learning_style = input(f"学习风格（当前：{profile.get('learning_style', '')}）：").strip()

    if new_name:
        profile["name"] = new_name

    if new_age:
        if new_age.isdigit():
            profile["age"] = int(new_age)
        else:
            print("年龄不是数字，所以没有修改。")

    if new_goal:
        profile["goal"] = new_goal

    if new_project:
        profile["current_project"] = new_project

    if new_version:
        profile["current_version"] = new_version

    if new_learning_style:
        profile["learning_style"] = new_learning_style

    save_data(data)

    new_text = profile_identity_text(data)

    content = (
        "更新前：\n"
        f"{old_text}\n\n"
        "更新后：\n"
        f"{new_text}"
    )

    print("\nProfile 已更新：")
    print("-" * 70)
    print(new_text)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 更新 Eric Profile", content)


# =========================
# Skills
# =========================

def score_to_level(score):
    if score >= 90:
        return "strong"
    if score >= 75:
        return "good"
    if score >= 40:
        return "developing"
    if score > 0:
        return "beginner"
    return "not_started"


def get_skill_score(data, skill_name):
    skill = data["skills"].get(skill_name)

    if skill is None:
        return None

    return skill.get("score", 0)


def get_strong_skills(data):
    result = []

    for skill_name, skill_info in data["skills"].items():
        if skill_info.get("score", 0) >= 80:
            result.append(skill_name)

    return result


def get_developing_skills(data):
    result = []

    for skill_name, skill_info in data["skills"].items():
        score = skill_info.get("score", 0)
        if 40 <= score < 80:
            result.append(skill_name)

    return result


def get_weak_skills(data):
    result = []

    for skill_name, skill_info in data["skills"].items():
        if skill_info.get("score", 0) < 40:
            result.append(skill_name)

    return result


def skill_summary_text(data):
    lines = []

    lines.append("Eric 的 Skill Database 技能数据库")
    lines.append("")

    lines.append("一、全部技能")
    for skill_name, skill_info in data["skills"].items():
        lines.append(
            f"- {skill_name}：{skill_info.get('score', 0)} 分，"
            f"level：{skill_info.get('level', 'unknown')}，"
            f"说明：{skill_info.get('note', '')}"
        )

    lines.append("")
    lines.append("二、强项技能")
    strong_skills = get_strong_skills(data)
    lines.append("、".join(strong_skills) if strong_skills else "暂无")

    lines.append("")
    lines.append("三、发展中技能")
    developing_skills = get_developing_skills(data)
    lines.append("、".join(developing_skills) if developing_skills else "暂无")

    lines.append("")
    lines.append("四、需要补强技能")
    weak_skills = get_weak_skills(data)
    lines.append("、".join(weak_skills) if weak_skills else "暂无")

    lines.append("")
    lines.append(f"五、当前学习重点：{data.get('next_learning_focus', 'ROS2')}")

    return "\n".join(lines)


def show_skill_database(data):
    content = skill_summary_text(data)

    print("\nSkill Database 技能数据库：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 查看 Skill Database", content)


def next_learning_advice_text(data):
    arduino = get_skill_score(data, "Arduino")
    python_score = get_skill_score(data, "Python")
    opencv = get_skill_score(data, "OpenCV")
    yolo = get_skill_score(data, "YOLO")
    ros2 = get_skill_score(data, "ROS2")

    lines = []

    lines.append("Eric，我已经读取你的技能数据库。")
    lines.append("")

    if arduino is not None and arduino >= 80:
        lines.append(f"- Arduino 已经达到 {arduino} 分，不需要继续重复基础 Arduino。")

    if python_score is not None and python_score >= 75:
        lines.append(f"- Python 已经达到 {python_score} 分，可以支持更复杂的机器人系统学习。")

    if opencv is not None and opencv >= 70:
        lines.append(f"- OpenCV 已经达到 {opencv} 分，说明你具备基础视觉感知能力。")

    if yolo is not None and 40 <= yolo < 80:
        lines.append(f"- YOLO 目前是 {yolo} 分，属于发展中技能。")

    if ros2 is not None and ros2 < 40:
        lines.append(f"- ROS2 目前是 {ros2} 分，是最明显的短板。")

    lines.append("")
    lines.append("导师建议：")

    if ros2 is not None and ros2 < 40:
        lines.append("下一步建议开始学习 ROS2。原因是：如果 Eric 以后要做真正的机器人系统，ROS2 会比继续重复 Arduino 更重要。")
    elif yolo is not None and yolo < 80:
        lines.append("下一步建议继续提高 YOLO。原因是：机器人需要更强的视觉识别能力。")
    elif python_score is not None and python_score < 90:
        lines.append("下一步建议继续提高 Python 工程能力。原因是：Atlas 的长期记忆和规划系统都依赖 Python。")
    else:
        lines.append("目前基础技能状态较好，下一步可以进行 Atlas 3.0 整合和 Demo。")

    return "\n".join(lines)


def show_next_learning_advice(data):
    content = next_learning_advice_text(data)

    print("\n基于 Skill Database 的学习建议：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 技能学习建议", content)


def update_skill(data):
    print("\n当前技能：")
    for skill_name, skill_info in data["skills"].items():
        print(f"- {skill_name}：{skill_info.get('score', 0)} 分")

    skill_name = input("\n请输入要更新的技能名称，例如 ROS2：").strip()

    if not skill_name:
        print("技能名称不能为空。")
        return

    if skill_name not in data["skills"]:
        answer = input("这个技能不存在，是否新增？输入 y 新增：").strip().lower()
        if answer != "y":
            print("已取消。")
            return

        data["skills"][skill_name] = {
            "score": 0,
            "level": "not_started",
            "note": "New skill added by Eric."
        }

    old_score = data["skills"][skill_name].get("score", 0)
    old_level = data["skills"][skill_name].get("level", "unknown")
    old_note = data["skills"][skill_name].get("note", "")

    score_text = input(f"新的分数 0-100（当前：{old_score}）：").strip()
    note = input(f"新的说明（当前：{old_note}）：").strip()

    if score_text:
        if score_text.isdigit():
            score = int(score_text)
            score = max(0, min(100, score))
            data["skills"][skill_name]["score"] = score
            data["skills"][skill_name]["level"] = score_to_level(score)
        else:
            print("分数不是数字，所以没有修改分数。")

    if note:
        data["skills"][skill_name]["note"] = note

    save_data(data)

    content = (
        f"技能名称：{skill_name}\n"
        f"分数：{old_score} → {data['skills'][skill_name].get('score', 0)}\n"
        f"level：{old_level} → {data['skills'][skill_name].get('level', 'unknown')}\n"
        f"说明：{old_note} → {data['skills'][skill_name].get('note', '')}"
    )

    print("\n技能已更新：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 更新技能", content)


# =========================
# Project History
# =========================

def format_project(project):
    skills = "、".join(project.get("skills_learned", [])) if project.get("skills_learned") else "暂无"
    problems = "、".join(project.get("key_problems", [])) if project.get("key_problems") else "暂无"

    return (
        f"项目 ID：{project.get('id', '未知')}\n"
        f"项目名称：{project.get('project_name', '未命名')}\n"
        f"版本：{project.get('version', '无版本')}\n"
        f"状态：{project.get('status', 'unknown')}\n"
        f"项目类型：{project.get('project_type', '未知')}\n"
        f"项目目标：{project.get('main_goal', '暂无')}\n"
        f"学到的技能：{skills}\n"
        f"遇到的问题：{problems}\n"
        f"迁移到 Atlas：{project.get('transfer_to_atlas', '暂无')}\n"
        f"项目证据：{project.get('evidence', '暂无')}"
    )


def history_summary_text(data):
    projects = data["project_history"]

    completed = [p for p in projects if p.get("status") == "completed"]
    in_progress = [p for p in projects if p.get("status") == "in_progress"]

    all_skills = []

    for project in projects:
        for skill in project.get("skills_learned", []):
            if skill not in all_skills:
                all_skills.append(skill)

    lines = []

    lines.append("Eric 的 Project History 项目历史")
    lines.append("")
    lines.append(f"项目总数：{len(projects)} 个")
    lines.append(f"已完成项目：{len(completed)} 个")
    lines.append(f"进行中项目：{len(in_progress)} 个")
    lines.append("")

    lines.append("项目演进路线：")
    for project in projects:
        lines.append(
            f"- {project.get('project_name', '未命名')} "
            f"({project.get('version', '无版本')}) | 状态：{project.get('status', 'unknown')}"
        )

    lines.append("")
    lines.append("历史项目累计技能：")
    lines.append("、".join(all_skills) if all_skills else "暂无")

    lines.append("")
    lines.append("机器人判断：")
    lines.append(
        "Eric 的项目不是孤立的。植物系统训练了硬件和串口通信，"
        "Atlas 1.0 训练了记忆、日志、硬件反馈和摄像头，"
        "Atlas 2.0 训练了项目管理、任务管理、Bug 管理和周报，"
        "Atlas 3.0 正在把这些历史经验整合成 Eric Digital Twin。"
    )

    return "\n".join(lines)


def show_project_history(data):
    content = history_summary_text(data)

    print("\nProject History 项目历史：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 查看 Project History", content)


def transfer_advice_text(data):
    names = [p.get("project_name", "") for p in data["project_history"]]

    lines = []

    lines.append("Eric，我已经读取你的 Project History。")
    lines.append("")
    lines.append("机器人判断：")

    if any("植物" in name for name in names):
        lines.append("- 你在智能植物养护系统里已经学过 Arduino、传感器、硬件接线和串口通信。")
        lines.append("  所以现在做 Atlas 时，不需要重新从基础 Arduino 开始。")

    if any("Atlas 1" in name for name in names):
        lines.append("- 你在 Atlas 1.0 里已经学过长期记忆、Project Log、导师建议、情绪支持、Arduino/OLED 和摄像头检测。")
        lines.append("  所以 Atlas 3.0 不应该继续只堆功能，而应该开始理解 Eric。")

    if any("Atlas 2" in name for name in names):
        lines.append("- 你在 Atlas 2.0 里已经学过 Project Database、Daily Task、Bug Manager 和 Weekly Report。")
        lines.append("  所以 Atlas 3.0 可以在这些管理能力上继续发展长期成长画像。")

    lines.append("")
    lines.append("导师建议：")
    lines.append("下一步不要重复做已经会的硬件反馈。你现在应该把历史项目变成可查询的成长证据。")

    return "\n".join(lines)


def show_transfer_advice(data):
    content = transfer_advice_text(data)

    print("\n基于 Project History 的迁移建议：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 项目迁移建议", content)


def search_project(data):
    keyword = input("\n请输入搜索关键词，例如 植物 / Atlas 1 / Atlas 2：").strip()

    if not keyword:
        print("关键词不能为空。")
        return

    matched = []

    for project in data["project_history"]:
        if keyword.lower() in project.get("project_name", "").lower():
            matched.append(project)

    if not matched:
        message = f"没有找到包含关键词「{keyword}」的项目。"
        print("\n" + message)
        write_to_project_log("Atlas 3.0 主程序 搜索历史项目", message)
        return

    lines = []

    print(f"\n找到 {len(matched)} 个项目：")
    print("-" * 70)

    for project in matched:
        content = format_project(project)
        print(content)
        print("-" * 70)
        lines.append(content)

    write_to_project_log(
        "Atlas 3.0 主程序 搜索历史项目",
        f"关键词：{keyword}\n\n" + "\n\n".join(lines)
    )


def add_project_history(data):
    print("\n新增历史项目。每一项写一句话即可。")

    project_name = input("项目名称：").strip()
    version = input("版本，例如 1.0：").strip()
    status = input("状态 completed / in_progress：").strip()
    project_type = input("项目类型：").strip()
    main_goal = input("项目目标：").strip()
    skills_text = input("学到的技能，用英文逗号分隔：").strip()
    problems_text = input("遇到的问题，用英文逗号分隔：").strip()
    transfer = input("这个项目如何迁移到 Atlas？").strip()
    evidence = input("项目证据，例如 Demo / Log / Code：").strip()

    if not project_name:
        print("项目名称不能为空。")
        return

    if status not in ["completed", "in_progress"]:
        status = "completed"

    new_project = {
        "id": get_next_id(data["project_history"]),
        "project_name": project_name,
        "version": version if version else "unknown",
        "status": status,
        "project_type": project_type if project_type else "Engineering Project",
        "main_goal": main_goal if main_goal else "暂无目标",
        "skills_learned": split_text_to_list(skills_text) if skills_text else ["Project Experience"],
        "key_problems": split_text_to_list(problems_text) if problems_text else ["暂无记录"],
        "transfer_to_atlas": transfer if transfer else "这个项目为 Atlas 提供了历史经验。",
        "evidence": evidence if evidence else "Project Log"
    }

    data["project_history"].append(new_project)
    save_data(data)

    content = format_project(new_project)

    print("\n历史项目已新增：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 新增历史项目", content)


# =========================
# Learning Planner
# =========================

def decide_today_focus(data):
    ros2 = get_skill_score(data, "ROS2")
    yolo = get_skill_score(data, "YOLO")
    python_score = get_skill_score(data, "Python")

    if ros2 is not None and ros2 < 40:
        return {
            "focus": "ROS2",
            "reason": "Arduino、Python、OpenCV 已经有基础，但 ROS2 还没开始。如果 Eric 未来要做真正的机器人系统，ROS2 是下一阶段必须补上的能力。",
            "task_1": "了解 ROS2 是什么，以及它为什么用于机器人系统。",
            "task_2": "整理一页 ROS2 学习笔记：Node、Topic、Message。",
            "task_3": "把 ROS2 加入 Atlas 3.0 的长期学习计划。",
            "estimated_time": "2 小时"
        }

    if yolo is not None and yolo < 80:
        return {
            "focus": "YOLO",
            "reason": "OpenCV 已经有基础，但 YOLO 还在发展中。如果机器人以后要理解真实世界，需要更强的目标识别能力。",
            "task_1": "复习 YOLO 的目标检测用途。",
            "task_2": "准备一个简单的 YOLO 测试素材。",
            "task_3": "记录 YOLO 和 OpenCV 的区别。",
            "estimated_time": "2 小时"
        }

    if python_score is not None and python_score < 90:
        return {
            "focus": "Python Engineering",
            "reason": "Python 已经能支持 JSON、文件读写和 OpenCV，但 Atlas 3.0 需要更清晰的类、模块和数据结构。",
            "task_1": "复习 Python Class 的基本结构。",
            "task_2": "把 Profile、Skill、History 的 Class 关系画出来。",
            "task_3": "整理代码模块，让 Atlas 3.0 更像工程项目。",
            "estimated_time": "2 小时"
        }

    return {
        "focus": "Atlas 3.0 Integration",
        "reason": "当前基础技能状态较好，可以开始把六个阶段整合成一个完整主程序。",
        "task_1": "检查 atlas3_data.json 是否完整。",
        "task_2": "测试六个功能模块。",
        "task_3": "准备 Atlas 3.0 Demo 视频。",
        "estimated_time": "2 小时"
    }


def morning_message_text(data):
    profile = data["profile"]
    focus = decide_today_focus(data)

    return (
        f"{profile.get('name', 'Eric')}，早上好。\n"
        f"我已经读取了你的 Profile、Skill Database 和 Project History。\n\n"
        f"你目前正在开发：{profile.get('current_project', 'Atlas')}。\n"
        f"你的长期目标是：{profile.get('goal', 'AI Systems Engineer')}。\n\n"
        f"今天我建议你重点做：{focus['focus']}。\n"
        f"原因：{focus['reason']}\n\n"
        f"预计时间：{focus['estimated_time']}。\n"
        f"这不是随机建议，而是根据你的成长画像、技能短板和项目历史生成的。"
    )


def show_morning_message(data):
    content = morning_message_text(data)

    print("\nAtlas 3.0 主动提醒：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 开机主动提醒", content)


def generate_learning_plan(data):
    profile = data["profile"]
    focus = decide_today_focus(data)

    strong_skills = get_strong_skills(data)
    developing_skills = get_developing_skills(data)
    weak_skills = get_weak_skills(data)

    plan = {
        "date": get_today_text(),
        "created_time": datetime.now().strftime("%H:%M:%S"),
        "student_name": profile.get("name", "Eric"),
        "current_project": profile.get("current_project", "Atlas"),
        "current_version": profile.get("current_version", "Atlas 3.0"),
        "goal": profile.get("goal", "AI Systems Engineer"),
        "today_focus": focus["focus"],
        "reason": focus["reason"],
        "task_1": focus["task_1"],
        "task_2": focus["task_2"],
        "task_3": focus["task_3"],
        "estimated_time": focus["estimated_time"],
        "strong_skills": strong_skills,
        "developing_skills": developing_skills,
        "weak_skills": weak_skills,
        "learning_style": profile.get("learning_style", ""),
        "status": "planned",
        "evening_review": ""
    }

    today = get_today_text()
    new_plans = []

    for old_plan in data["daily_learning_plans"]:
        if old_plan.get("date") != today:
            new_plans.append(old_plan)

    new_plans.append(plan)
    data["daily_learning_plans"] = new_plans

    save_data(data)

    content = format_learning_plan(plan)

    print("\n今日 Learning Plan 已生成：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 生成今日 Learning Plan", content)


def format_learning_plan(plan):
    strong = "、".join(plan.get("strong_skills", [])) if plan.get("strong_skills") else "暂无"
    developing = "、".join(plan.get("developing_skills", [])) if plan.get("developing_skills") else "暂无"
    weak = "、".join(plan.get("weak_skills", [])) if plan.get("weak_skills") else "暂无"

    return (
        f"日期：{plan.get('date', '')}\n"
        f"创建时间：{plan.get('created_time', '')}\n"
        f"学生：{plan.get('student_name', 'Eric')}\n"
        f"当前项目：{plan.get('current_project', 'Atlas')}\n"
        f"当前版本：{plan.get('current_version', 'Atlas 3.0')}\n"
        f"目标：{plan.get('goal', '')}\n"
        f"今日重点：{plan.get('today_focus', '')}\n"
        f"原因：{plan.get('reason', '')}\n"
        f"任务 1：{plan.get('task_1', '')}\n"
        f"任务 2：{plan.get('task_2', '')}\n"
        f"任务 3：{plan.get('task_3', '')}\n"
        f"预计时间：{plan.get('estimated_time', '')}\n"
        f"强项技能：{strong}\n"
        f"发展中技能：{developing}\n"
        f"需要补强：{weak}\n"
        f"学习风格：{plan.get('learning_style', '')}\n"
        f"状态：{plan.get('status', 'planned')}\n"
        f"晚上复盘：{plan.get('evening_review', '') if plan.get('evening_review') else '暂无'}"
    )


def show_today_learning_plan(data):
    today = get_today_text()
    today_plan = None

    for plan in data["daily_learning_plans"]:
        if plan.get("date") == today:
            today_plan = plan
            break

    if today_plan is None:
        message = "今天还没有 Learning Plan。请先生成今日 Learning Plan。"
        print("\n" + message)
        write_to_project_log("Atlas 3.0 主程序 查看今日 Learning Plan", message)
        return

    content = format_learning_plan(today_plan)

    print("\n今天的 Learning Plan：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 查看今日 Learning Plan", content)


def show_learning_logic(data):
    profile = data["profile"]
    focus = decide_today_focus(data)

    lines = []

    lines.append("Atlas 3.0 Learning Planner 判断逻辑：")
    lines.append("")
    lines.append("1. 先读取 Eric Profile")
    lines.append(f"   - 当前目标：{profile.get('goal', '')}")
    lines.append(f"   - 当前项目：{profile.get('current_project', '')}")
    lines.append(f"   - 学习风格：{profile.get('learning_style', '')}")
    lines.append("")
    lines.append("2. 再读取 Skill Database")
    for skill_name, skill_info in data["skills"].items():
        lines.append(f"   - {skill_name}：{skill_info.get('score', 0)} 分")
    lines.append("")
    lines.append("3. 再读取 Project History")
    lines.append("   - Eric 已经完成植物系统、Atlas 1.0、Atlas 2.0，正在做 Atlas 3.0。")
    lines.append("")
    lines.append("4. 最后生成今日建议")
    lines.append(f"   - 今日建议：{focus['focus']}")
    lines.append(f"   - 判断原因：{focus['reason']}")

    content = "\n".join(lines)

    print("\nLearning Planner 判断逻辑：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 Learning Planner 判断逻辑", content)


def review_learning_plan(data):
    today = get_today_text()
    today_plan = None

    for plan in data["daily_learning_plans"]:
        if plan.get("date") == today:
            today_plan = plan
            break

    if today_plan is None:
        print("\n今天还没有 Learning Plan，无法复盘。")
        return

    print("\n开始复盘今日 Learning Plan。")
    print(f"今日重点：{today_plan.get('today_focus', '')}")

    status = input("完成情况（完成 / 部分完成 / 未完成）：").strip()
    completed = input("今天实际完成了什么？").strip()
    problem = input("遇到什么问题？没有就写 无：").strip()
    next_step = input("明天下一步做什么？").strip()

    if status not in ["完成", "部分完成", "未完成"]:
        status = "部分完成"

    if not completed:
        completed = "未填写"

    if not problem:
        problem = "无"

    if not next_step:
        next_step = "继续完成今天的学习重点"

    review = (
        f"完成情况：{status}\n"
        f"实际完成：{completed}\n"
        f"遇到的问题：{problem}\n"
        f"明天下一步：{next_step}"
    )

    today_plan["status"] = status
    today_plan["evening_review"] = review

    save_data(data)

    content = format_learning_plan(today_plan)

    print("\nLearning Plan 复盘已保存：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 Learning Plan 复盘", content)


# =========================
# Emotion Memory
# =========================

def add_emotion_record(data):
    print("\n开始记录今天的研发状态。")
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

    debug_hours = max(0, debug_hours)

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

    data["emotion_records"].append(record)
    save_data(data)

    advice = emotion_advice_text(record)

    content = (
        f"日期：{record['date']} {record['time']}\n"
        f"研发状态：{feeling}\n"
        f"连续调试时间：{debug_hours} 小时\n"
        f"卡住的问题：{problem}\n"
        f"已尝试方法：{attempted}\n"
        f"下一步：{next_step}\n\n"
        f"机器人提醒：\n{advice}"
    )

    print("\n研发状态记录已保存：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 新增 Emotion Memory", content)


def emotion_advice_text(record):
    feeling = record.get("feeling", "")
    debug_hours = record.get("debug_hours", 0)
    problem = record.get("problem", "")
    next_step = record.get("next_step", "")

    lines = []

    lines.append("先说明：我不是心理医生。我只作为研发导师，帮助 Eric 调整 Debug 节奏。")
    lines.append("")
    lines.append("机器人判断：")

    if debug_hours >= 4:
        lines.append(f"你今天已经连续调试 {debug_hours} 小时，时间偏长。")
        lines.append("现在不建议继续硬撑。建议先休息 15 到 20 分钟，再回来只测试一个最小问题。")
    elif debug_hours >= 2:
        lines.append(f"你今天已经调试 {debug_hours} 小时。")
        lines.append("建议不要继续扩大功能，只保留一个最小测试目标。")
    else:
        lines.append(f"你今天调试时间是 {debug_hours} 小时，还在可控范围。")

    if "失败" in feeling or "报错" in feeling:
        lines.append("失败和报错是研发过程的一部分。最重要的是记录触发条件和尝试过的方法。")

    if "卡住" in feeling or "不知道" in feeling:
        lines.append("卡住通常不是能力问题，而是任务太大。下一步要把任务缩小。")

    lines.append("")
    lines.append("当前问题：")
    lines.append(problem if problem else "未填写具体问题。")
    lines.append("")
    lines.append("建议下一步：")
    lines.append(next_step if next_step else "先记录 Bug，再做一个最小复现测试。")

    return "\n".join(lines)


def show_emotion_records(data):
    records = data["emotion_records"][-5:]

    if not records:
        message = "目前还没有研发状态记录。"
        print("\n" + message)
        write_to_project_log("Atlas 3.0 主程序 查看 Emotion Memory", message)
        return

    lines = []

    print("\n最近研发状态记录：")
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

    write_to_project_log("Atlas 3.0 主程序 查看最近 Emotion Memory", "\n\n".join(lines))


def emotion_summary_text(data):
    records = data["emotion_records"]

    if not records:
        return "目前还没有研发状态记录。"

    tired_count = 0
    stuck_count = 0
    failed_count = 0
    long_debug_count = 0

    for record in records:
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

    return (
        f"Eric 目前一共有 {len(records)} 条研发状态记录。\n"
        f"疲惫记录：{tired_count} 次。\n"
        f"卡住记录：{stuck_count} 次。\n"
        f"失败或报错记录：{failed_count} 次。\n"
        f"连续调试 3 小时以上记录：{long_debug_count} 次。\n\n"
        "机器人判断：这些记录不是心理诊断，而是研发节奏记录。"
    )


def show_emotion_summary(data):
    content = emotion_summary_text(data)

    print("\nEmotion Memory 总结：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 Emotion Memory 总结", content)


def show_emotion_reminder(data):
    if not data["emotion_records"]:
        content = "目前还没有研发状态记录。建议先记录一次 Debug 状态。"
    else:
        content = emotion_advice_text(data["emotion_records"][-1])

    print("\n机器人提醒：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 Emotion Memory 提醒", content)


# =========================
# Mentor Recommendation
# =========================

def analyze_state(data):
    completed_projects = []
    in_progress_projects = []

    for project in data["project_history"]:
        if project.get("status") == "completed":
            completed_projects.append(project.get("project_name", "未命名项目"))
        elif project.get("status") == "in_progress":
            in_progress_projects.append(project.get("project_name", "未命名项目"))

    state = {
        "arduino_score": get_skill_score(data, "Arduino"),
        "python_score": get_skill_score(data, "Python"),
        "opencv_score": get_skill_score(data, "OpenCV"),
        "yolo_score": get_skill_score(data, "YOLO"),
        "ros2_score": get_skill_score(data, "ROS2"),
        "latest_learning_plan": data["daily_learning_plans"][-1] if data["daily_learning_plans"] else None,
        "latest_emotion": data["emotion_records"][-1] if data["emotion_records"] else None,
        "completed_projects": completed_projects,
        "in_progress_projects": in_progress_projects
    }

    return state


def decide_mentor_recommendation(data):
    state = analyze_state(data)

    latest_emotion = state["latest_emotion"]
    ros2 = state["ros2_score"]
    yolo = state["yolo_score"]
    python_score = state["python_score"]

    if latest_emotion is not None:
        debug_hours = latest_emotion.get("debug_hours", 0)
        feeling = latest_emotion.get("feeling", "")

        if debug_hours >= 4:
            return {
                "main_focus": "Debug Rhythm Control",
                "recommendation": "今天不要继续硬撑新功能。先休息 15 到 20 分钟，再回来只测试一个最小问题。",
                "reason": f"Emotion Memory 显示 Eric 最近连续调试 {debug_hours} 小时，时间偏长。此时继续加功能容易制造更多 Bug。",
                "action_1": "休息 15 到 20 分钟。",
                "action_2": "回来后只打开一个文件，只测试一个功能。",
                "action_3": "把问题写入 Bug 或 Project Log，不要同时改多个功能。",
                "estimated_time": "30 分钟",
                "priority": "high"
            }

        if "崩溃" in feeling or "不想做" in feeling:
            return {
                "main_focus": "Reduce Task Size",
                "recommendation": "今天不要扩大任务。只保留一个最小动作：查看最近一次 Learning Plan，并完成其中一个小任务。",
                "reason": "Emotion Memory 显示 Eric 当前研发状态波动较大。此时应该缩小任务，而不是扩大项目范围。",
                "action_1": "查看最近一次 Learning Plan。",
                "action_2": "只选择其中一个最小任务。",
                "action_3": "完成后写入 Project Log。",
                "estimated_time": "30 到 45 分钟",
                "priority": "high"
            }

    if ros2 is not None and ros2 < 40:
        return {
            "main_focus": "ROS2",
            "recommendation": "下一步建议 Eric 开始学习 ROS2，而不是继续重复基础 Arduino。",
            "reason": "Skill Database 显示 Arduino、Python、OpenCV 已经有基础，但 ROS2 还没有开始。如果 Eric 未来要做真正的机器人系统，ROS2 是必须补上的能力。",
            "action_1": "了解 ROS2 是什么，以及它为什么用于机器人系统。",
            "action_2": "整理一页 ROS2 笔记：Node、Topic、Message。",
            "action_3": "把 ROS2 作为 Atlas 3.0 后续长期学习重点。",
            "estimated_time": "2 小时",
            "priority": "high"
        }

    if yolo is not None and yolo < 80:
        return {
            "main_focus": "YOLO",
            "recommendation": "下一步建议继续补强 YOLO，让机器人视觉识别能力更接近真实应用。",
            "reason": "OpenCV 已经有基础，但 YOLO 仍处于发展中。如果机器人以后要识别物体、场景和人，YOLO 会比普通图像处理更重要。",
            "action_1": "复习 YOLO 的目标检测用途。",
            "action_2": "准备一个简单图片或摄像头测试素材。",
            "action_3": "记录 YOLO 和 OpenCV 的区别。",
            "estimated_time": "2 小时",
            "priority": "medium"
        }

    if python_score is not None and python_score < 90:
        return {
            "main_focus": "Python Engineering",
            "recommendation": "下一步建议提高 Python 工程化能力，把 Atlas 3.0 的代码整理成更清晰的模块。",
            "reason": "Atlas 3.0 已经有六个模块。如果继续发展，必须把代码结构整理清楚，否则会越来越难维护。",
            "action_1": "整理 Atlas 3.0 的所有文件清单。",
            "action_2": "画出 Profile、Skills、History、Learning Plan、Emotion Memory、Recommendation 的关系图。",
            "action_3": "继续优化 atlas3_main.py。",
            "estimated_time": "2 小时",
            "priority": "medium"
        }

    return {
        "main_focus": "Atlas 3.0 Demo",
        "recommendation": "下一步建议准备 Atlas 3.0 Demo 和版本说明。",
        "reason": "六个阶段已经整合到主程序，下一步的重点是展示证据，而不是继续加功能。",
        "action_1": "测试一键 Demo 总览。",
        "action_2": "录制 3 分钟 Demo 视频。",
        "action_3": "写 Atlas 3.0 Version Note。",
        "estimated_time": "2 小时",
        "priority": "medium"
    }


def mentor_recommendation_text(data):
    profile = data["profile"]
    state = analyze_state(data)
    decision = decide_mentor_recommendation(data)

    completed_text = "、".join(state["completed_projects"]) if state["completed_projects"] else "暂无"
    in_progress_text = "、".join(state["in_progress_projects"]) if state["in_progress_projects"] else "暂无"

    latest_plan = state["latest_learning_plan"]
    latest_emotion = state["latest_emotion"]

    lines = []

    lines.append(f"{profile.get('name', 'Eric')}，这是 Atlas 3.0 生成的导师推荐。")
    lines.append("")
    lines.append("一、Eric 画像")
    lines.append(f"年龄：{profile.get('age', 13)}")
    lines.append(f"长期目标：{profile.get('goal', '')}")
    lines.append(f"当前项目：{profile.get('current_project', '')}")
    lines.append(f"当前版本：{profile.get('current_version', '')}")
    lines.append(f"学习风格：{profile.get('learning_style', '')}")
    lines.append("")

    lines.append("二、技能状态")
    for skill_name, skill_info in data["skills"].items():
        lines.append(
            f"- {skill_name}：{skill_info.get('score', 0)} 分，level：{skill_info.get('level', 'unknown')}"
        )
    lines.append("")

    lines.append("三、项目历史")
    lines.append(f"已完成项目：{completed_text}")
    lines.append(f"进行中项目：{in_progress_text}")
    lines.append("")

    lines.append("四、最新 Learning Plan")
    if latest_plan:
        lines.append(f"最近学习重点：{latest_plan.get('today_focus', '未知')}")
        lines.append(f"计划状态：{latest_plan.get('status', 'unknown')}")
        lines.append(f"预计时间：{latest_plan.get('estimated_time', '未知')}")
    else:
        lines.append("暂时没有 Learning Plan。")
    lines.append("")

    lines.append("五、最新 Emotion Memory")
    if latest_emotion:
        lines.append(f"最近状态：{latest_emotion.get('feeling', '')}")
        lines.append(f"连续调试时间：{latest_emotion.get('debug_hours', 0)} 小时")
        lines.append(f"主要问题：{latest_emotion.get('problem', '')}")
    else:
        lines.append("暂时没有 Emotion Memory 记录。")
    lines.append("")

    lines.append("六、导师推荐")
    lines.append(f"推荐重点：{decision['main_focus']}")
    lines.append(f"推荐内容：{decision['recommendation']}")
    lines.append(f"推荐原因：{decision['reason']}")
    lines.append(f"优先级：{decision['priority']}")
    lines.append("")

    lines.append("七、今天具体动作")
    lines.append(f"1. {decision['action_1']}")
    lines.append(f"2. {decision['action_2']}")
    lines.append(f"3. {decision['action_3']}")
    lines.append("")

    lines.append("八、预计时间")
    lines.append(decision["estimated_time"])
    lines.append("")

    lines.append("九、导师判断")
    lines.append("这不是随机建议。它综合读取了 Eric Profile、Skill Database、Project History、Learning Planner 和 Emotion Memory。")

    return "\n".join(lines), decision


def generate_mentor_recommendation(data):
    content, decision = mentor_recommendation_text(data)

    record = {
        "date": get_today_text(),
        "time": datetime.now().strftime("%H:%M:%S"),
        "main_focus": decision["main_focus"],
        "priority": decision["priority"],
        "recommendation": decision["recommendation"],
        "reason": decision["reason"],
        "action_1": decision["action_1"],
        "action_2": decision["action_2"],
        "action_3": decision["action_3"],
        "estimated_time": decision["estimated_time"],
        "full_text": content
    }

    data["recommendations"].append(record)
    save_data(data)

    print("\nAtlas 3.0 导师推荐：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 生成导师推荐", content)


def show_latest_recommendation(data):
    if not data["recommendations"]:
        message = "目前还没有导师推荐。请先生成导师推荐。"
        print("\n" + message)
        write_to_project_log("Atlas 3.0 主程序 查看最新导师推荐", message)
        return

    content = data["recommendations"][-1].get("full_text", "")

    print("\n最新导师推荐：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 查看最新导师推荐", content)


def show_recommendation_logic(data):
    state = analyze_state(data)
    decision = decide_mentor_recommendation(data)
    profile = data["profile"]

    lines = []

    lines.append("Atlas 3.0 Mentor Recommendation 判断逻辑：")
    lines.append("")
    lines.append("1. 先读取 Eric Profile")
    lines.append(f"   目标：{profile.get('goal', '')}")
    lines.append(f"   当前项目：{profile.get('current_project', '')}")
    lines.append("")
    lines.append("2. 再读取 Skill Database")
    lines.append(f"   Arduino：{state['arduino_score']} 分")
    lines.append(f"   Python：{state['python_score']} 分")
    lines.append(f"   OpenCV：{state['opencv_score']} 分")
    lines.append(f"   YOLO：{state['yolo_score']} 分")
    lines.append(f"   ROS2：{state['ros2_score']} 分")
    lines.append("")
    lines.append("3. 再读取 Project History")
    lines.append("   判断 Eric 不是零基础，而是已经完成植物系统、Atlas 1.0 和 Atlas 2.0。")
    lines.append("")
    lines.append("4. 再读取 Learning Planner")
    if state["latest_learning_plan"]:
        lines.append(f"   最近学习重点：{state['latest_learning_plan'].get('today_focus', '未知')}")
    else:
        lines.append("   暂时没有 Learning Plan。")
    lines.append("")
    lines.append("5. 再读取 Emotion Memory")
    if state["latest_emotion"]:
        lines.append(f"   最近状态：{state['latest_emotion'].get('feeling', '')}")
        lines.append(f"   连续调试时间：{state['latest_emotion'].get('debug_hours', 0)} 小时")
    else:
        lines.append("   暂时没有 Emotion Memory。")
    lines.append("")
    lines.append("6. 最后生成导师推荐")
    lines.append(f"   推荐重点：{decision['main_focus']}")
    lines.append(f"   推荐原因：{decision['reason']}")

    content = "\n".join(lines)

    print("\n导师推荐判断逻辑：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 导师推荐判断逻辑", content)


# =========================
# 一键 Demo
# =========================

def one_click_demo(data):
    profile = data["profile"]
    focus = decide_today_focus(data)
    decision = decide_mentor_recommendation(data)

    lines = []

    lines.append("Atlas 3.0 Unified Demo Overview")
    lines.append("")
    lines.append("一、Eric Profile")
    lines.append(f"姓名：{profile.get('name', 'Eric')}")
    lines.append(f"年龄：{profile.get('age', 13)}")
    lines.append(f"目标：{profile.get('goal', '')}")
    lines.append(f"当前项目：{profile.get('current_project', '')}")
    lines.append(f"当前版本：{profile.get('current_version', '')}")
    lines.append("")

    lines.append("二、Skill Database")
    lines.append(f"强项技能：{'、'.join(get_strong_skills(data)) if get_strong_skills(data) else '暂无'}")
    lines.append(f"发展中技能：{'、'.join(get_developing_skills(data)) if get_developing_skills(data) else '暂无'}")
    lines.append(f"需要补强：{'、'.join(get_weak_skills(data)) if get_weak_skills(data) else '暂无'}")
    lines.append("")

    lines.append("三、Project History")
    lines.append(f"项目历史数量：{len(data['project_history'])} 个")
    lines.append("项目路线：")
    for project in data["project_history"]:
        lines.append(f"- {project.get('project_name', '')} | {project.get('status', '')}")
    lines.append("")

    lines.append("四、Learning Planner")
    lines.append(f"今日建议重点：{focus['focus']}")
    lines.append(f"原因：{focus['reason']}")
    lines.append("")

    lines.append("五、Emotion Memory")
    lines.append(f"研发状态记录数量：{len(data['emotion_records'])} 条")
    if data["emotion_records"]:
        latest = data["emotion_records"][-1]
        lines.append(f"最近状态：{latest.get('feeling', '')}")
        lines.append(f"最近调试时间：{latest.get('debug_hours', 0)} 小时")
    else:
        lines.append("最近状态：暂无记录")
    lines.append("")

    lines.append("六、Mentor Recommendation")
    lines.append(f"推荐重点：{decision['main_focus']}")
    lines.append(f"推荐内容：{decision['recommendation']}")
    lines.append("")

    lines.append("机器人总结：")
    lines.append("Atlas 3.0 已经把 Eric Profile、Skill Database、Project History、Learning Planner、Emotion Memory 和 Mentor Recommendation 整合成一个主程序和一个总数据库。")

    content = "\n".join(lines)

    print("\n" + "=" * 70)
    print(content)
    print("=" * 70)

    write_to_project_log("Atlas 3.0 主程序 一键 Demo 总览", content)


def show_database_overview(data):
    content = (
        f"总数据库文件：{DATA_FILE}\n"
        f"学生：{data.get('student_name', 'Eric')}\n"
        f"版本：{data.get('atlas_version', 'Atlas 3.0')}\n"
        f"数据库版本：{data.get('database_version', '')}\n\n"
        f"profile：已整合\n"
        f"skills：{len(data.get('skills', {}))} 项技能\n"
        f"project_history：{len(data.get('project_history', []))} 个项目\n"
        f"daily_learning_plans：{len(data.get('daily_learning_plans', []))} 条\n"
        f"emotion_records：{len(data.get('emotion_records', []))} 条\n"
        f"recommendations：{len(data.get('recommendations', []))} 条\n\n"
        "说明：Atlas 3.0 已经从多个 JSON 文件整合为 atlas3_data.json。"
    )

    print("\nAtlas 3.0 总数据库概览：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log("Atlas 3.0 主程序 总数据库概览", content)


def test_log_write():
    content = (
        "这是 Atlas 3.0 主程序 atlas3_main.py 的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明综合版日志保存正常。"
    )

    write_to_project_log("Atlas 3.0 主程序 日志写入测试", content)


# =========================
# 主菜单
# =========================

def show_intro(data):
    profile = data["profile"]

    print("\n==============================")
    print("Atlas 3.0 Unified Main Program")
    print("六阶段整合版")
    print("==============================")
    print(f"学生：{profile.get('name', 'Eric')}")
    print(f"目标：{profile.get('goal', '')}")
    print(f"当前项目：{profile.get('current_project', '')}")
    print(f"当前版本：{profile.get('current_version', '')}")
    print(f"总数据库文件：{DATA_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")
    print("功能：Profile + Skills + History + Learning Planner + Emotion Memory + Mentor Recommendation")
    print("==============================")


def main():
    data = load_data()
    show_intro(data)

    write_to_project_log(
        "Atlas 3.0 主程序启动",
        "atlas3_main.py 已启动。"
    )

    print("\n机器人开机主动提醒：")
    print("-" * 70)
    print(morning_message_text(data))
    print("-" * 70)

    while True:
        print("\n请选择功能：")
        print("1. 一键 Demo 总览")
        print("2. 查看总数据库概览")
        print("3. Profile：查看 Eric 成长画像")
        print("4. Profile：机器人身份回答")
        print("5. Profile：更新 Eric Profile")
        print("6. Skill Database：查看技能数据库")
        print("7. Skill Database：下一步学习建议")
        print("8. Skill Database：更新技能分数")
        print("9. Project History：查看项目历史")
        print("10. Project History：项目迁移建议")
        print("11. Project History：搜索历史项目")
        print("12. Project History：新增历史项目")
        print("13. Learning Planner：开机主动提醒")
        print("14. Learning Planner：生成今日 Learning Plan")
        print("15. Learning Planner：查看今日 Learning Plan")
        print("16. Learning Planner：解释判断逻辑")
        print("17. Learning Planner：晚上复盘")
        print("18. Emotion Memory：新增研发状态记录")
        print("19. Emotion Memory：查看最近研发状态")
        print("20. Emotion Memory：查看研发状态总结")
        print("21. Emotion Memory：机器人提醒")
        print("22. Mentor Recommendation：生成导师推荐")
        print("23. Mentor Recommendation：查看最新推荐")
        print("24. Mentor Recommendation：解释推荐逻辑")
        print("25. 测试 project_log.txt 是否能写入")
        print("26. 退出")

        choice = input("请输入数字 1-26：").strip()

        if choice == "1":
            one_click_demo(data)

        elif choice == "2":
            show_database_overview(data)

        elif choice == "3":
            show_profile(data)

        elif choice == "4":
            robot_profile_intro(data)

        elif choice == "5":
            update_profile(data)

        elif choice == "6":
            show_skill_database(data)

        elif choice == "7":
            show_next_learning_advice(data)

        elif choice == "8":
            update_skill(data)

        elif choice == "9":
            show_project_history(data)

        elif choice == "10":
            show_transfer_advice(data)

        elif choice == "11":
            search_project(data)

        elif choice == "12":
            add_project_history(data)

        elif choice == "13":
            show_morning_message(data)

        elif choice == "14":
            generate_learning_plan(data)

        elif choice == "15":
            show_today_learning_plan(data)

        elif choice == "16":
            show_learning_logic(data)

        elif choice == "17":
            review_learning_plan(data)

        elif choice == "18":
            add_emotion_record(data)

        elif choice == "19":
            show_emotion_records(data)

        elif choice == "20":
            show_emotion_summary(data)

        elif choice == "21":
            show_emotion_reminder(data)

        elif choice == "22":
            generate_mentor_recommendation(data)

        elif choice == "23":
            show_latest_recommendation(data)

        elif choice == "24":
            show_recommendation_logic(data)

        elif choice == "25":
            test_log_write()

        elif choice == "26":
            write_to_project_log(
                "Atlas 3.0 主程序退出",
                "atlas3_main.py 已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 26。")
            write_to_project_log(
                "Atlas 3.0 主程序无效输入",
                f"用户输入了无效菜单数字：{choice}"
            )


if __name__ == "__main__":
    main()