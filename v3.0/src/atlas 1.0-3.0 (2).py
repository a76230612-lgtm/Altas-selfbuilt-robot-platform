import json
from datetime import datetime, date, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "atlas_unified_data.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"
WEEKLY_REPORT_TXT_FILE = BASE_DIR / "weekly_report.txt"

# Old data sources. Keep old files. This program only reads and migrates them.
OLD_ATLAS2_FILE = BASE_DIR / "atlas2_data.json"
OLD_ATLAS3_FILE = BASE_DIR / "atlas3_data.json"
OLD_PROFILE_FILE = BASE_DIR / "profile.json"
OLD_SKILLS_FILE = BASE_DIR / "skills.json"
OLD_HISTORY_FILE = BASE_DIR / "history.json"
OLD_LEARNING_PLAN_FILE = BASE_DIR / "learning_plan.json"
OLD_EMOTION_FILE = BASE_DIR / "emotion_memory.json"
OLD_RECOMMENDATION_FILE = BASE_DIR / "mentor_recommendation.json"
OLD_PROJECTS_FILE = BASE_DIR / "projects.json"
OLD_TASKS_FILE = BASE_DIR / "daily_tasks.json"
OLD_BUGS_FILE = BASE_DIR / "bugs.json"
OLD_WEEKLY_REPORTS_FILE = BASE_DIR / "weekly_reports.json"


# ============================================================
# Basic utilities
# ============================================================

def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_today_text():
    return date.today().strftime("%Y-%m-%d")


def get_week_range():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def date_to_text(date_obj):
    return date_obj.strftime("%Y-%m-%d")


def parse_date(date_text):
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except Exception:
        return None


def is_in_this_week(date_text, week_start, week_end):
    parsed = parse_date(date_text)
    if parsed is None:
        return False
    return week_start <= parsed <= week_end


def safe_load_json(path, default_data):
    if not path.exists():
        return default_data
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default_data


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
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


def write_to_weekly_report_txt(content):
    text = (
        "\n" + "=" * 70 + "\n"
        "Atlas Unified Weekly Report\n"
        f"生成时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + str(content) + "\n"
        + "=" * 70 + "\n"
    )
    with open(WEEKLY_REPORT_TXT_FILE, "a", encoding="utf-8") as file:
        file.write(text)
    print("\n已写入 weekly_report.txt")
    print(f"周报文件位置：{WEEKLY_REPORT_TXT_FILE}")


def get_next_id(items):
    ids = []
    for item in items:
        if isinstance(item, dict) and isinstance(item.get("id"), int):
            ids.append(item["id"])
    if not ids:
        return 1
    return max(ids) + 1


def split_text_to_list(text):
    if not text:
        return []
    result = []
    for item in text.split(","):
        cleaned = item.strip()
        if cleaned:
            result.append(cleaned)
    return result


# ============================================================
# Default unified database
# ============================================================

def default_projects():
    return [
        {
            "id": 1,
            "name": "智能植物养护系统",
            "status": "完成",
            "progress": 100,
            "category": "AI + Hardware + Plant Care",
            "description": "Eric 已完成的科创项目，用于展示持续研发能力。",
            "next_step": "整理项目日志、Demo 视频和版本说明。"
        },
        {
            "id": 2,
            "name": "AI Research Mentor Robot / Atlas 1.0",
            "status": "完成",
            "progress": 100,
            "category": "AI Mentor Robot",
            "description": "已经完成长期记忆、Project Log、导师建议、情绪支持、Arduino、OLED 和摄像头检测。",
            "next_step": "作为 Atlas 3.0 的项目历史基础。"
        },
        {
            "id": 3,
            "name": "Atlas 2.0",
            "status": "完成",
            "progress": 100,
            "category": "Project Management Robot",
            "description": "项目数据库、每日任务、Bug Manager 和 Weekly Report。",
            "next_step": "已整合进 Atlas Unified。"
        },
        {
            "id": 4,
            "name": "Atlas 3.0",
            "status": "完成",
            "progress": 100,
            "category": "Digital Twin Mentor Robot",
            "description": "Profile、Skill Database、Project History、Learning Planner、Emotion Memory、Mentor Recommendation。",
            "next_step": "整合 2.0 与 3.0，准备 Demo 和 Version Note。"
        }
    ]


def default_profile():
    return {
        "name": "Eric",
        "age": 13,
        "goal": "AI Systems Engineer",
        "current_project": "Atlas",
        "current_version": "Atlas Unified 2.0 + 3.0",
        "interests": ["AI", "Robot", "Python", "Basketball"],
        "strengths": ["Arduino", "Python", "OpenCV", "Project Iteration", "Hardware Prototyping"],
        "weaknesses": ["ROS2", "Advanced Robot System Design", "Long-term Engineering Documentation"],
        "learning_style": "喜欢通过项目实战学习，不喜欢重复听很多理论。",
        "mentor_note": "Eric is building Atlas as a long-term AI research mentor robot."
    }


def default_skills():
    return {
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
    }


def default_project_history():
    return [
        {
            "id": 1,
            "project_name": "智能植物养护系统",
            "version": "1.0 - 1.1",
            "status": "completed",
            "project_type": "AI + Hardware + Plant Care",
            "main_goal": "Build a smart plant care system with sensors, watering, lighting, and basic monitoring.",
            "skills_learned": ["Arduino", "Sensors", "Serial Communication", "Hardware Wiring", "Project Iteration"],
            "key_problems": ["Hardware stability", "Sensor reading", "Camera recognition preparation"],
            "transfer_to_atlas": "Eric learned hardware control, serial communication, and project iteration. These skills help Atlas control hardware feedback.",
            "evidence": "Project logs, demo videos, hardware prototype"
        },
        {
            "id": 2,
            "project_name": "Atlas 1.0 / AI Research Mentor Robot",
            "version": "1.0",
            "status": "completed",
            "project_type": "AI Mentor Robot",
            "main_goal": "Build a basic AI research mentor robot with memory, project log, mentor advice, emotion support, Arduino/OLED feedback, and camera detection.",
            "skills_learned": ["Python", "JSON", "OpenCV", "Arduino Communication", "Project Log", "Debugging"],
            "key_problems": ["Camera false detection", "Project log file path issue", "Hardware and software integration"],
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
            "skills_learned": ["Project Database", "Daily Task Management", "Bug Manager", "Weekly Report", "JSON Database Design", "File Management"],
            "key_problems": ["Too many separate code files", "Need to merge functions into one main program", "Need to organize version evidence"],
            "transfer_to_atlas": "Eric learned how to manage engineering work systematically. This becomes the foundation for Atlas 3.0 long-term memory and personalized mentoring.",
            "evidence": "atlas2_main.py, atlas2_data.json, weekly_report.txt"
        },
        {
            "id": 4,
            "project_name": "Atlas 3.0",
            "version": "3.0",
            "status": "completed",
            "project_type": "Digital Twin Mentor Robot",
            "main_goal": "Build Eric Digital Twin so Atlas can understand Eric's profile, skills, project history, learning plan, emotion memory, and mentor recommendations.",
            "skills_learned": ["Profile Database", "Skill Database", "Project History", "Learning Planner", "Emotion Memory", "Mentor Recommendation"],
            "key_problems": ["Need to connect all six stages into one main program", "Need to merge all JSON files into one database"],
            "transfer_to_atlas": "Atlas 3.0 uses Eric's profile, skills, project history, learning plan, emotion memory, and mentor recommendation to generate personalized guidance.",
            "evidence": "atlas3_main.py, atlas3_data.json, project_log.txt"
        }
    ]


def create_default_data():
    return {
        "student_name": "Eric",
        "atlas_version": "Atlas Unified 2.0 + 3.0",
        "database_version": "Atlas Unified Database v1",
        "projects": default_projects(),
        "daily_tasks": [],
        "bugs": [],
        "weekly_reports": [],
        "profile": default_profile(),
        "skills": default_skills(),
        "next_learning_focus": "ROS2",
        "project_history": default_project_history(),
        "daily_learning_plans": [],
        "emotion_records": [],
        "recommendations": []
    }


def ensure_data_fields(data):
    default = create_default_data()

    for key, value in default.items():
        if key not in data:
            data[key] = value

    if not isinstance(data.get("projects"), list) or not data["projects"]:
        data["projects"] = default["projects"]

    if not isinstance(data.get("daily_tasks"), list):
        data["daily_tasks"] = []

    if not isinstance(data.get("bugs"), list):
        data["bugs"] = []

    if not isinstance(data.get("weekly_reports"), list):
        data["weekly_reports"] = []

    if not isinstance(data.get("profile"), dict):
        data["profile"] = default["profile"]

    if not isinstance(data.get("skills"), dict):
        data["skills"] = default["skills"]

    if not isinstance(data.get("project_history"), list) or not data["project_history"]:
        data["project_history"] = default["project_history"]

    if not isinstance(data.get("daily_learning_plans"), list):
        data["daily_learning_plans"] = []

    if not isinstance(data.get("emotion_records"), list):
        data["emotion_records"] = []

    if not isinstance(data.get("recommendations"), list):
        data["recommendations"] = []

    return data


def migrate_old_data():
    if DATA_FILE.exists():
        data = safe_load_json(DATA_FILE, create_default_data())
        data = ensure_data_fields(data)
        save_data(data)
        return data

    data = create_default_data()

    atlas2 = safe_load_json(OLD_ATLAS2_FILE, {})
    if atlas2:
        if isinstance(atlas2.get("projects"), list) and atlas2["projects"]:
            data["projects"] = atlas2["projects"]
        if isinstance(atlas2.get("daily_tasks"), list):
            data["daily_tasks"] = atlas2["daily_tasks"]
        if isinstance(atlas2.get("bugs"), list):
            data["bugs"] = atlas2["bugs"]
        if isinstance(atlas2.get("weekly_reports"), list):
            data["weekly_reports"] = atlas2["weekly_reports"]

    atlas3 = safe_load_json(OLD_ATLAS3_FILE, {})
    if atlas3:
        if isinstance(atlas3.get("profile"), dict):
            data["profile"] = atlas3["profile"]
        if isinstance(atlas3.get("skills"), dict):
            data["skills"] = atlas3["skills"]
        if atlas3.get("next_learning_focus"):
            data["next_learning_focus"] = atlas3["next_learning_focus"]
        if isinstance(atlas3.get("project_history"), list) and atlas3["project_history"]:
            data["project_history"] = atlas3["project_history"]
        if isinstance(atlas3.get("daily_learning_plans"), list):
            data["daily_learning_plans"] = atlas3["daily_learning_plans"]
        if isinstance(atlas3.get("emotion_records"), list):
            data["emotion_records"] = atlas3["emotion_records"]
        if isinstance(atlas3.get("recommendations"), list):
            data["recommendations"] = atlas3["recommendations"]

    # Fallback from separate old JSON files
    profile = safe_load_json(OLD_PROFILE_FILE, {})
    if profile:
        data["profile"] = profile

    skills = safe_load_json(OLD_SKILLS_FILE, {})
    if isinstance(skills.get("skills"), dict):
        data["skills"] = skills["skills"]
    if skills.get("next_learning_focus"):
        data["next_learning_focus"] = skills["next_learning_focus"]

    history = safe_load_json(OLD_HISTORY_FILE, {})
    if isinstance(history.get("project_history"), list) and history["project_history"]:
        data["project_history"] = history["project_history"]

    learning = safe_load_json(OLD_LEARNING_PLAN_FILE, {})
    if isinstance(learning.get("daily_learning_plans"), list):
        data["daily_learning_plans"] = learning["daily_learning_plans"]

    emotion = safe_load_json(OLD_EMOTION_FILE, {})
    if isinstance(emotion.get("emotion_records"), list):
        data["emotion_records"] = emotion["emotion_records"]

    recommendation = safe_load_json(OLD_RECOMMENDATION_FILE, {})
    if isinstance(recommendation.get("recommendations"), list):
        data["recommendations"] = recommendation["recommendations"]

    projects = safe_load_json(OLD_PROJECTS_FILE, {})
    if isinstance(projects.get("projects"), list) and projects["projects"]:
        data["projects"] = projects["projects"]

    tasks = safe_load_json(OLD_TASKS_FILE, {})
    if isinstance(tasks.get("daily_tasks"), list) and tasks["daily_tasks"]:
        data["daily_tasks"] = tasks["daily_tasks"]

    bugs = safe_load_json(OLD_BUGS_FILE, {})
    if isinstance(bugs.get("bugs"), list) and bugs["bugs"]:
        data["bugs"] = bugs["bugs"]

    reports = safe_load_json(OLD_WEEKLY_REPORTS_FILE, {})
    if isinstance(reports.get("weekly_reports"), list) and reports["weekly_reports"]:
        data["weekly_reports"] = reports["weekly_reports"]

    data = ensure_data_fields(data)
    save_data(data)

    write_to_project_log(
        "Atlas Unified 初始化",
        "已创建 atlas_unified_data.json，并尝试迁移 atlas2_data.json、atlas3_data.json 以及旧的分散 JSON 文件。"
    )

    return data


def load_data():
    return migrate_old_data()


def save_data(data):
    save_json(DATA_FILE, data)


# ============================================================
# Atlas 2.0 - Project Database
# ============================================================

def format_project(project):
    return (
        f"项目 ID：{project.get('id', '未知')}\n"
        f"项目名称：{project.get('name', project.get('project_name', '未命名项目'))}\n"
        f"状态：{project.get('status', '未知')}\n"
        f"完成度：{project.get('progress', 0)}%\n"
        f"类别：{project.get('category', project.get('project_type', '未分类'))}\n"
        f"说明：{project.get('description', project.get('main_goal', '暂无说明'))}\n"
        f"下一步：{project.get('next_step', '暂无下一步')}"
    )


def get_project_summary_text(data):
    projects = data["projects"]
    total = len(projects)
    completed = 0
    developing = 0
    other = 0
    atlas2_status = "未找到 Atlas 2.0"
    atlas2_progress = "未找到 Atlas 2.0"
    atlas2_next = "未找到 Atlas 2.0"
    lines = []

    for project in projects:
        name = project.get("name", project.get("project_name", "未命名项目"))
        status = project.get("status", "未知")
        progress = project.get("progress", 0)

        if status in ["完成", "completed"]:
            completed += 1
        elif status in ["开发中", "in_progress"]:
            developing += 1
        else:
            other += 1

        lines.append(f"- {name} | 状态：{status} | 完成度：{progress}%")

        if "Atlas 2.0" in name:
            atlas2_status = status
            atlas2_progress = f"{progress}%"
            atlas2_next = project.get("next_step", "暂无下一步")

    return (
        f"Eric 现在一共有 {total} 个项目。\n"
        f"已完成项目：{completed} 个。\n"
        f"开发中项目：{developing} 个。\n"
        f"其他状态项目：{other} 个。\n"
        f"Atlas 2.0 当前状态：{atlas2_status}。\n"
        f"Atlas 2.0 当前完成度：{atlas2_progress}。\n"
        f"Atlas 2.0 当前下一步：{atlas2_next}。\n\n"
        "项目列表：\n" + "\n".join(lines)
    )


def show_project_database(data):
    content = get_project_summary_text(data)
    print("\nAtlas 2.0 Project Database：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 查看 Project Database", content)


def show_project_options(data):
    print("\n当前项目：")
    print("-" * 50)
    for project in data["projects"]:
        print(
            f"{project.get('id', '未知')}. "
            f"{project.get('name', project.get('project_name', '未命名'))} | "
            f"状态：{project.get('status', '未知')} | "
            f"完成度：{project.get('progress', 0)}%"
        )
    print("-" * 50)


def find_project_by_keyword(data, keyword):
    for project in data["projects"]:
        name = project.get("name", project.get("project_name", ""))
        if keyword in name:
            return project
    return None


def update_atlas2_progress(data):
    project = find_project_by_keyword(data, "Atlas 2.0")
    if project is None:
        print("\n没有找到 Atlas 2.0 项目。")
        return

    print("\n当前 Atlas 2.0：")
    print(format_project(project))

    old_status = project.get("status", "未知")
    old_progress = project.get("progress", 0)
    old_next = project.get("next_step", "暂无下一步")

    new_status = input("\n新的状态（不改直接回车）：").strip()
    new_progress_text = input("新的完成度数字（不改直接回车）：").strip()
    new_next = input("新的下一步（不改直接回车）：").strip()

    if new_status:
        project["status"] = new_status
    if new_progress_text:
        if new_progress_text.isdigit():
            project["progress"] = max(0, min(100, int(new_progress_text)))
        else:
            print("完成度不是数字，所以没有修改。")
    if new_next:
        project["next_step"] = new_next

    save_data(data)

    content = (
        f"状态：{old_status} → {project.get('status', '未知')}\n"
        f"完成度：{old_progress}% → {project.get('progress', 0)}%\n"
        f"下一步：{old_next} → {project.get('next_step', '暂无下一步')}"
    )

    print("\n已更新 Atlas 2.0：")
    print(content)
    write_to_project_log("Atlas Unified 更新 Atlas 2.0 进度", content)


# ============================================================
# Atlas 2.0 - Daily Task
# ============================================================

def find_today_task(data):
    today = get_today_text()
    for task in data["daily_tasks"]:
        if task.get("date") == today:
            return task
    return None


def format_daily_task(task):
    return (
        f"日期：{task.get('date', '无日期')}\n"
        f"创建时间：{task.get('created_time', '无时间')}\n"
        f"项目：{task.get('project_name', '未知项目')}\n"
        f"今天计划：{task.get('today_plan', '未填写')}\n"
        f"预计时间：{task.get('estimated_hours', 1)} 小时\n"
        f"优先级：{task.get('priority', '中')}\n"
        f"为什么做：{task.get('reason', '未填写')}\n"
        f"当前状态：{task.get('status', '未完成')}\n"
        f"是否已晚上复盘：{task.get('evening_review_done', False)}\n"
        f"实际完成：{task.get('finished_result', '')}\n"
        f"遇到的问题：{task.get('problem', '')}\n"
        f"下一步：{task.get('next_step', '')}\n"
        f"导师评价：{task.get('mentor_comment', '')}"
    )


def create_or_update_daily_task(data):
    old = find_today_task(data)
    if old is not None:
        print("\n今天已经有 Daily Task：")
        print(format_daily_task(old))
        answer = input("\n是否覆盖今天任务？输入 y 覆盖：").strip().lower()
        if answer != "y":
            print("已取消。")
            return
        data["daily_tasks"].remove(old)

    print("\n创建今天的 Daily Task。")
    show_project_options(data)

    project_name = input("\n今天任务属于哪个项目？").strip() or "Atlas Unified"
    today_plan = input("今天准备完成什么？").strip() or "测试 Atlas Unified 主程序"
    hours_text = input("预计需要几个小时？例如 2：").strip()
    priority = input("优先级（高 / 中 / 低）：").strip() or "中"
    reason = input("为什么今天要做这件事？").strip() or "这是整合版测试的重要任务。"

    hours = int(hours_text) if hours_text.isdigit() else 1
    hours = max(1, hours)

    task = {
        "date": get_today_text(),
        "created_time": datetime.now().strftime("%H:%M:%S"),
        "project_name": project_name,
        "today_plan": today_plan,
        "estimated_hours": hours,
        "priority": priority,
        "reason": reason,
        "status": "未完成",
        "evening_review_done": False,
        "finished_result": "",
        "problem": "",
        "next_step": "",
        "mentor_comment": ""
    }

    data["daily_tasks"].append(task)
    save_data(data)

    content = format_daily_task(task)
    print("\n今日任务已保存：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 创建 Daily Task", content)


def show_today_daily_task(data):
    task = find_today_task(data)
    if task is None:
        message = "今天还没有 Daily Task。"
        print("\n" + message)
        write_to_project_log("Atlas Unified 查看今日 Daily Task", message)
        return

    content = format_daily_task(task)
    print("\n今天的 Daily Task：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 查看今日 Daily Task", content)


def generate_task_mentor_comment(status, next_step):
    if status == "完成":
        return "今天任务完成。建议保存截图、运行结果和日志，作为研发证据。"
    if status == "部分完成":
        return f"今天已经有部分推进。明天建议优先继续做：{next_step}。"
    return "今天任务未完成也要记录原因。研发管理的重点是形成闭环。"


def review_daily_task(data):
    task = find_today_task(data)
    if task is None:
        print("\n今天还没有 Daily Task，无法复盘。")
        return

    print("\n晚上复盘 Daily Task。")
    print(f"今天计划：{task.get('today_plan', '')}")

    status = input("完成情况（完成 / 部分完成 / 未完成）：").strip()
    result = input("今天实际完成了什么？").strip()
    problem = input("今天遇到什么问题？没有就写 无：").strip()
    next_step = input("明天下一步做什么？").strip()

    if status not in ["完成", "部分完成", "未完成"]:
        status = "部分完成"
    if not result:
        result = "未填写"
    if not problem:
        problem = "无"
    if not next_step:
        next_step = "继续完成今天未完成的任务"

    task["status"] = status
    task["evening_review_done"] = True
    task["finished_result"] = result
    task["problem"] = problem
    task["next_step"] = next_step
    task["mentor_comment"] = generate_task_mentor_comment(status, next_step)

    save_data(data)

    content = format_daily_task(task)
    print("\nDaily Task 复盘已保存：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified Daily Task 复盘", content)


# ============================================================
# Atlas 2.0 - Bug Manager
# ============================================================

def generate_bug_mentor_comment(title, severity, next_step):
    lower = title.lower()
    if severity == "高":
        return "这是高优先级 Bug。建议先暂停新增功能，优先复现问题、记录报错、缩小排查范围。"
    if "opencv" in lower or "摄像头" in title or "识别" in title:
        return "这是视觉识别类 Bug。建议先确认摄像头、光线、距离、检测模型和判断阈值。"
    if "arduino" in lower or "oled" in lower or "舵机" in title or "灯" in title:
        return "这是硬件反馈类 Bug。建议先检查端口、接线、GND 是否共地，再检查 Python 指令发送。"
    if "json" in lower or "保存" in title or "日志" in title:
        return "这是数据保存类 Bug。建议先检查文件路径是否固定，再检查 JSON 格式是否正确。"
    return f"建议下一步先做最小复现，并执行：{next_step}。"


def format_bug(bug):
    return (
        f"Bug ID：{bug.get('id', '未知')}\n"
        f"日期：{bug.get('date', '无日期')}\n"
        f"创建时间：{bug.get('created_time', '无时间')}\n"
        f"项目：{bug.get('project_name', '未知项目')}\n"
        f"Bug 标题：{bug.get('bug_title', '未命名 Bug')}\n"
        f"Bug 现象：{bug.get('bug_description', '未填写')}\n"
        f"触发条件：{bug.get('trigger_condition', '未填写')}\n"
        f"已尝试方法：{bug.get('attempted_solution', '无')}\n"
        f"严重程度：{bug.get('severity', '中')}\n"
        f"状态：{bug.get('status', '未解决')}\n"
        f"解决方法：{bug.get('solution', '') if bug.get('solution', '') else '暂无'}\n"
        f"修复时间：{bug.get('fixed_time', '') if bug.get('fixed_time', '') else '未修复'}\n"
        f"下一步：{bug.get('next_step', '暂无')}\n"
        f"导师建议：{bug.get('mentor_comment', '')}"
    )


def add_bug(data):
    print("\n新增 Bug。")
    show_project_options(data)

    project_name = input("\nBug 属于哪个项目？").strip() or "Atlas Unified"
    title = input("Bug 标题：").strip()
    if not title:
        print("Bug 标题不能为空。")
        return
    description = input("Bug 现象描述：").strip() or "未填写具体 Bug 现象"
    trigger = input("什么时候会出现这个 Bug？").strip() or "未填写触发条件"
    attempted = input("已经尝试过什么解决方法？没有就写 无：").strip() or "无"
    severity = input("严重程度（高 / 中 / 低）：").strip()
    next_step = input("下一步准备怎么排查？").strip() or "继续复现 Bug，并记录报错信息"

    if severity not in ["高", "中", "低"]:
        severity = "中"

    bug = {
        "id": get_next_id(data["bugs"]),
        "date": get_today_text(),
        "created_time": datetime.now().strftime("%H:%M:%S"),
        "project_name": project_name,
        "bug_title": title,
        "bug_description": description,
        "trigger_condition": trigger,
        "attempted_solution": attempted,
        "severity": severity,
        "status": "未解决",
        "solution": "",
        "fixed_time": "",
        "next_step": next_step,
        "mentor_comment": generate_bug_mentor_comment(title, severity, next_step)
    }

    data["bugs"].append(bug)
    save_data(data)

    content = format_bug(bug)
    print("\nBug 已保存：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 新增 Bug", content)


def show_or_search_bugs(data):
    keyword = input("\n直接回车查看全部 Bug；输入关键词可以搜索 Bug：").strip()
    matched = []

    if not keyword:
        matched = data["bugs"]
        title = "Atlas Unified 查看全部 Bug"
    else:
        title = "Atlas Unified 搜索 Bug"
        for bug in data["bugs"]:
            search_text = " ".join([
                bug.get("project_name", ""),
                bug.get("bug_title", ""),
                bug.get("bug_description", ""),
                bug.get("trigger_condition", ""),
                bug.get("attempted_solution", ""),
                bug.get("status", ""),
                bug.get("next_step", "")
            ])
            if keyword.lower() in search_text.lower():
                matched.append(bug)

    if not matched:
        message = f"没有找到包含关键词「{keyword}」的 Bug。" if keyword else "目前还没有 Bug。"
        print("\n" + message)
        write_to_project_log(title, message)
        return

    lines = []
    print("\nBug 记录：")
    print("-" * 70)
    for bug in matched:
        content = format_bug(bug)
        print(content)
        print("-" * 70)
        lines.append(content)
    write_to_project_log(title, "\n\n".join(lines))


def find_bug_by_id(data, bug_id):
    for bug in data["bugs"]:
        if bug.get("id") == bug_id:
            return bug
    return None


def update_bug_status(data):
    bug_id_text = input("\n请输入要更新的 Bug ID：").strip()
    if not bug_id_text.isdigit():
        print("请输入数字 Bug ID。")
        return

    bug = find_bug_by_id(data, int(bug_id_text))
    if bug is None:
        print("没有找到这个 Bug。")
        return

    print("\n当前 Bug：")
    print(format_bug(bug))

    old_status = bug.get("status", "未知")
    old_solution = bug.get("solution", "")
    old_next = bug.get("next_step", "")

    status = input("\n新的状态（未解决 / 排查中 / 已解决）：").strip()
    solution = input("解决方法或当前排查结果：").strip()
    next_step = input("下一步：").strip()

    if status not in ["未解决", "排查中", "已解决"]:
        status = old_status

    bug["status"] = status
    if solution:
        bug["solution"] = solution
    if next_step:
        bug["next_step"] = next_step
    if status == "已解决":
        bug["fixed_time"] = get_now_text()

    save_data(data)

    content = (
        f"更新 Bug ID：{bug.get('id')}\n"
        f"Bug 标题：{bug.get('bug_title')}\n"
        f"状态：{old_status} → {bug.get('status')}\n"
        f"解决方法：{old_solution if old_solution else '暂无'} → {bug.get('solution') if bug.get('solution') else '暂无'}\n"
        f"下一步：{old_next if old_next else '暂无'} → {bug.get('next_step') if bug.get('next_step') else '暂无'}\n"
        f"修复时间：{bug.get('fixed_time') if bug.get('fixed_time') else '未修复'}"
    )

    print("\nBug 已更新：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 更新 Bug", content)


def get_bug_summary_text(data):
    total = len(data["bugs"])
    open_count = 0
    checking_count = 0
    fixed_count = 0
    high_count = 0

    for bug in data["bugs"]:
        status = bug.get("status", "未知")
        severity = bug.get("severity", "未知")
        if status == "未解决":
            open_count += 1
        elif status == "排查中":
            checking_count += 1
        elif status == "已解决":
            fixed_count += 1
        if severity == "高":
            high_count += 1

    summary = (
        f"Bug 总数：{total} 个。\n"
        f"未解决 Bug：{open_count} 个。\n"
        f"排查中 Bug：{checking_count} 个。\n"
        f"已解决 Bug：{fixed_count} 个。\n"
        f"高严重程度 Bug：{high_count} 个。"
    )

    if open_count > 0 or checking_count > 0:
        summary += "\n建议：先处理未解决和排查中的 Bug，不要急着增加新功能。"
    else:
        summary += "\n建议：当前 Bug 状态较好，可以继续做版本收尾。"

    return summary


def show_bug_summary(data):
    content = get_bug_summary_text(data)
    print("\nBug Manager 总结：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified Bug 总结", content)


# ============================================================
# Atlas 2.0 - Weekly Report
# ============================================================

def summarize_tasks_this_week(data, week_start, week_end):
    tasks = []
    for task in data["daily_tasks"]:
        if is_in_this_week(task.get("date", ""), week_start, week_end):
            tasks.append(task)

    completed = [t for t in tasks if t.get("status") == "完成"]
    partial = [t for t in tasks if t.get("status") == "部分完成"]
    unfinished = [t for t in tasks if t.get("status") not in ["完成", "部分完成"]]

    lines = []
    for task in tasks:
        lines.append(
            f"- {task.get('date', '无日期')} | {task.get('project_name', '未知项目')} | "
            f"{task.get('today_plan', '未填写任务')} | 状态：{task.get('status', '未知')}"
        )

    return {
        "tasks": tasks,
        "completed": completed,
        "partial": partial,
        "unfinished": unfinished,
        "lines": lines
    }


def summarize_bugs_this_week(data, week_start, week_end):
    bugs = []
    for bug in data["bugs"]:
        if is_in_this_week(bug.get("date", ""), week_start, week_end):
            bugs.append(bug)

    open_bugs = [b for b in bugs if b.get("status") == "未解决"]
    checking_bugs = [b for b in bugs if b.get("status") == "排查中"]
    fixed_bugs = [b for b in bugs if b.get("status") == "已解决"]
    high_bugs = [b for b in bugs if b.get("severity") == "高"]

    lines = []
    for bug in bugs:
        lines.append(
            f"- Bug ID {bug.get('id', '未知')} | {bug.get('bug_title', '未命名 Bug')} | "
            f"状态：{bug.get('status', '未知')} | 严重程度：{bug.get('severity', '未知')}"
        )

    return {
        "bugs": bugs,
        "open_bugs": open_bugs,
        "checking_bugs": checking_bugs,
        "fixed_bugs": fixed_bugs,
        "high_bugs": high_bugs,
        "lines": lines
    }


def generate_weekly_report(data):
    week_start, week_end = get_week_range()
    task_summary = summarize_tasks_this_week(data, week_start, week_end)
    bug_summary = summarize_bugs_this_week(data, week_start, week_end)
    project_summary = get_project_summary_text(data)

    suggestions = []
    if bug_summary["open_bugs"] or bug_summary["checking_bugs"]:
        suggestions.append("下周优先处理未解决或排查中的 Bug。")
    if task_summary["unfinished"]:
        suggestions.append("下周优先完成未完成的 Daily Task。")
    if not suggestions:
        suggestions.append("下周可以继续整理 Atlas Unified Demo 视频、Version Note 和下一版本规划。")

    lines = []
    lines.append("Atlas Unified Weekly Report")
    lines.append(f"周报周期：{date_to_text(week_start)} 至 {date_to_text(week_end)}")
    lines.append("")
    lines.append("一、项目总览")
    lines.append(project_summary)
    lines.append("")
    lines.append("二、本周 Daily Task 总结")
    lines.append(f"本周任务总数：{len(task_summary['tasks'])} 个。")
    lines.append(f"完成任务：{len(task_summary['completed'])} 个。")
    lines.append(f"部分完成任务：{len(task_summary['partial'])} 个。")
    lines.append(f"未完成任务：{len(task_summary['unfinished'])} 个。")
    lines.append("任务列表：")
    lines.extend(task_summary["lines"] if task_summary["lines"] else ["- 本周还没有 Daily Task。"])
    lines.append("")
    lines.append("三、本周 Bug 总结")
    lines.append(f"本周 Bug 总数：{len(bug_summary['bugs'])} 个。")
    lines.append(f"未解决 Bug：{len(bug_summary['open_bugs'])} 个。")
    lines.append(f"排查中 Bug：{len(bug_summary['checking_bugs'])} 个。")
    lines.append(f"已解决 Bug：{len(bug_summary['fixed_bugs'])} 个。")
    lines.append(f"高严重程度 Bug：{len(bug_summary['high_bugs'])} 个。")
    lines.append("Bug 列表：")
    lines.extend(bug_summary["lines"] if bug_summary["lines"] else ["- 本周还没有 Bug。"])
    lines.append("")
    lines.append("四、下周建议")
    for index, suggestion in enumerate(suggestions, start=1):
        lines.append(f"{index}. {suggestion}")

    report = "\n".join(lines)

    record = {
        "week_start": date_to_text(week_start),
        "week_end": date_to_text(week_end),
        "created_date": get_today_text(),
        "created_time": datetime.now().strftime("%H:%M:%S"),
        "content": report
    }

    data["weekly_reports"].append(record)
    save_data(data)

    write_to_weekly_report_txt(report)
    write_to_project_log("Atlas Unified 生成 Weekly Report", report)

    print("\nWeekly Report 已生成：")
    print("-" * 70)
    print(report)
    print("-" * 70)


def show_latest_weekly_report(data):
    if not data["weekly_reports"]:
        message = "目前还没有 Weekly Report。请先生成周报。"
        print("\n" + message)
        write_to_project_log("Atlas Unified 查看最新 Weekly Report", message)
        return

    content = data["weekly_reports"][-1].get("content", "")
    print("\n最新 Weekly Report：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 查看最新 Weekly Report", content)


# ============================================================
# Atlas 3.0 - Profile
# ============================================================

def profile_identity_text(data):
    profile = data["profile"]
    interests = "、".join(profile.get("interests", [])) if profile.get("interests") else "暂无"
    strengths = "、".join(profile.get("strengths", [])) if profile.get("strengths") else "暂无"
    weaknesses = "、".join(profile.get("weaknesses", [])) if profile.get("weaknesses") else "暂无"

    return (
        f"{profile.get('name', 'Eric')}，我已经读取了你的成长画像。\n\n"
        f"你现在 {profile.get('age', 13)} 岁。\n"
        f"你的长期目标是：{profile.get('goal', 'AI Systems Engineer')}。\n"
        f"你目前正在开发：{profile.get('current_project', 'Atlas')}。\n"
        f"当前版本是：{profile.get('current_version', 'Atlas Unified 2.0 + 3.0')}。\n\n"
        f"你的兴趣包括：{interests}。\n"
        f"你的强项包括：{strengths}。\n"
        f"你需要补强的能力包括：{weaknesses}。\n\n"
        f"学习风格：{profile.get('learning_style', '')}\n"
        f"导师备注：{profile.get('mentor_note', '')}"
    )


def show_profile(data):
    content = profile_identity_text(data)
    print("\nEric Profile 成长画像：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 查看 Eric Profile", content)


def robot_profile_intro(data):
    profile = data["profile"]
    reply = (
        f"{profile.get('name', 'Eric')}，目前你正在开发 {profile.get('current_project', 'Atlas')}。\n"
        f"当前版本是 {profile.get('current_version', 'Atlas Unified 2.0 + 3.0')}。\n"
        f"你的目标是成为 {profile.get('goal', 'AI Systems Engineer')}。\n"
        f"所以我会根据你的成长画像来回答，而不是只说普通的你好。"
    )
    print("\n机器人回答：")
    print("-" * 70)
    print(reply)
    print("-" * 70)
    write_to_project_log("Atlas Unified Profile 身份回答", reply)


def update_profile(data):
    profile = data["profile"]
    print("\n开始更新 Eric Profile。不想修改的地方直接回车。")

    old = profile_identity_text(data)

    name = input(f"名字（当前：{profile.get('name', 'Eric')}）：").strip()
    age = input(f"年龄（当前：{profile.get('age', 13)}）：").strip()
    goal = input(f"长期目标（当前：{profile.get('goal', '')}）：").strip()
    project = input(f"当前项目（当前：{profile.get('current_project', '')}）：").strip()
    version = input(f"当前版本（当前：{profile.get('current_version', '')}）：").strip()
    learning_style = input(f"学习风格（当前：{profile.get('learning_style', '')}）：").strip()

    if name:
        profile["name"] = name
    if age:
        if age.isdigit():
            profile["age"] = int(age)
        else:
            print("年龄不是数字，所以没有修改。")
    if goal:
        profile["goal"] = goal
    if project:
        profile["current_project"] = project
    if version:
        profile["current_version"] = version
    if learning_style:
        profile["learning_style"] = learning_style

    save_data(data)

    new = profile_identity_text(data)
    content = "更新前：\n" + old + "\n\n更新后：\n" + new

    print("\nProfile 已更新：")
    print("-" * 70)
    print(new)
    print("-" * 70)
    write_to_project_log("Atlas Unified 更新 Eric Profile", content)


# ============================================================
# Atlas 3.0 - Skill Database
# ============================================================

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
    return [name for name, info in data["skills"].items() if info.get("score", 0) >= 80]


def get_developing_skills(data):
    return [name for name, info in data["skills"].items() if 40 <= info.get("score", 0) < 80]


def get_weak_skills(data):
    return [name for name, info in data["skills"].items() if info.get("score", 0) < 40]


def skill_summary_text(data):
    lines = []
    lines.append("Eric 的 Skill Database 技能数据库")
    lines.append("")
    lines.append("一、全部技能")
    for name, info in data["skills"].items():
        lines.append(f"- {name}：{info.get('score', 0)} 分，level：{info.get('level', 'unknown')}，说明：{info.get('note', '')}")
    lines.append("")
    lines.append("二、强项技能")
    lines.append("、".join(get_strong_skills(data)) if get_strong_skills(data) else "暂无")
    lines.append("")
    lines.append("三、发展中技能")
    lines.append("、".join(get_developing_skills(data)) if get_developing_skills(data) else "暂无")
    lines.append("")
    lines.append("四、需要补强技能")
    lines.append("、".join(get_weak_skills(data)) if get_weak_skills(data) else "暂无")
    lines.append("")
    lines.append(f"五、当前学习重点：{data.get('next_learning_focus', 'ROS2')}")
    return "\n".join(lines)


def show_skill_database(data):
    content = skill_summary_text(data)
    print("\nSkill Database 技能数据库：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 查看 Skill Database", content)


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
        lines.append("目前基础技能状态较好，下一步可以进行 Atlas Unified Demo。")
    return "\n".join(lines)


def show_next_learning_advice(data):
    content = next_learning_advice_text(data)
    print("\n基于 Skill Database 的学习建议：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 技能学习建议", content)


def update_skill(data):
    print("\n当前技能：")
    for name, info in data["skills"].items():
        print(f"- {name}：{info.get('score', 0)} 分")

    skill_name = input("\n请输入要更新的技能名称，例如 ROS2：").strip()
    if not skill_name:
        print("技能名称不能为空。")
        return

    if skill_name not in data["skills"]:
        answer = input("这个技能不存在，是否新增？输入 y 新增：").strip().lower()
        if answer != "y":
            print("已取消。")
            return
        data["skills"][skill_name] = {"score": 0, "level": "not_started", "note": "New skill added by Eric."}

    old_score = data["skills"][skill_name].get("score", 0)
    old_level = data["skills"][skill_name].get("level", "unknown")
    old_note = data["skills"][skill_name].get("note", "")

    score_text = input(f"新的分数 0-100（当前：{old_score}）：").strip()
    note = input(f"新的说明（当前：{old_note}）：").strip()

    if score_text:
        if score_text.isdigit():
            score = max(0, min(100, int(score_text)))
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
    write_to_project_log("Atlas Unified 更新技能", content)


# ============================================================
# Atlas 3.0 - Project History
# ============================================================

def format_history_project(project):
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


def project_history_text(data):
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
        lines.append(f"- {project.get('project_name', '未命名')} ({project.get('version', '无版本')}) | 状态：{project.get('status', 'unknown')}")
    lines.append("")
    lines.append("历史项目累计技能：")
    lines.append("、".join(all_skills) if all_skills else "暂无")
    lines.append("")
    lines.append("机器人判断：")
    lines.append("Eric 的项目不是孤立的。植物系统训练了硬件和串口通信，Atlas 1.0 训练了记忆、日志、硬件反馈和摄像头，Atlas 2.0 训练了项目管理，Atlas 3.0 正在把这些历史经验整合成 Eric Digital Twin。")
    return "\n".join(lines)


def show_project_history(data):
    content = project_history_text(data)
    print("\nProject History 项目历史：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 查看 Project History", content)


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
    write_to_project_log("Atlas Unified 项目迁移建议", content)


# ============================================================
# Atlas 3.0 - Learning Planner
# ============================================================

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
            "task_3": "把 ROS2 加入 Atlas 未来长期学习计划。",
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
            "reason": "Python 已经能支持 JSON、文件读写和 OpenCV，但 Atlas 需要更清晰的类、模块和数据结构。",
            "task_1": "复习 Python Class 的基本结构。",
            "task_2": "把 Profile、Skill、History 的关系画出来。",
            "task_3": "整理代码模块，让 Atlas 更像工程项目。",
            "estimated_time": "2 小时"
        }

    return {
        "focus": "Atlas Unified Demo",
        "reason": "当前基础技能状态较好，可以开始整理 Atlas Unified Demo。",
        "task_1": "测试一键 Demo 总览。",
        "task_2": "检查 atlas_unified_data.json 是否完整。",
        "task_3": "准备 Demo 视频和 Version Note。",
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
    print("\nAtlas 主动提醒：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 开机主动提醒", content)


def format_learning_plan(plan):
    strong = "、".join(plan.get("strong_skills", [])) if plan.get("strong_skills") else "暂无"
    developing = "、".join(plan.get("developing_skills", [])) if plan.get("developing_skills") else "暂无"
    weak = "、".join(plan.get("weak_skills", [])) if plan.get("weak_skills") else "暂无"
    return (
        f"日期：{plan.get('date', '')}\n"
        f"创建时间：{plan.get('created_time', '')}\n"
        f"学生：{plan.get('student_name', 'Eric')}\n"
        f"当前项目：{plan.get('current_project', 'Atlas')}\n"
        f"当前版本：{plan.get('current_version', 'Atlas Unified')}\n"
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


def generate_learning_plan(data):
    profile = data["profile"]
    focus = decide_today_focus(data)

    plan = {
        "date": get_today_text(),
        "created_time": datetime.now().strftime("%H:%M:%S"),
        "student_name": profile.get("name", "Eric"),
        "current_project": profile.get("current_project", "Atlas"),
        "current_version": profile.get("current_version", "Atlas Unified 2.0 + 3.0"),
        "goal": profile.get("goal", "AI Systems Engineer"),
        "today_focus": focus["focus"],
        "reason": focus["reason"],
        "task_1": focus["task_1"],
        "task_2": focus["task_2"],
        "task_3": focus["task_3"],
        "estimated_time": focus["estimated_time"],
        "strong_skills": get_strong_skills(data),
        "developing_skills": get_developing_skills(data),
        "weak_skills": get_weak_skills(data),
        "learning_style": profile.get("learning_style", ""),
        "status": "planned",
        "evening_review": ""
    }

    today = get_today_text()
    new_plans = [p for p in data["daily_learning_plans"] if p.get("date") != today]
    new_plans.append(plan)
    data["daily_learning_plans"] = new_plans

    save_data(data)

    content = format_learning_plan(plan)
    print("\n今日 Learning Plan 已生成：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 生成 Learning Plan", content)


def show_today_learning_plan(data):
    today = get_today_text()
    for plan in data["daily_learning_plans"]:
        if plan.get("date") == today:
            content = format_learning_plan(plan)
            print("\n今天的 Learning Plan：")
            print("-" * 70)
            print(content)
            print("-" * 70)
            write_to_project_log("Atlas Unified 查看今日 Learning Plan", content)
            return

    message = "今天还没有 Learning Plan。请先生成今日 Learning Plan。"
    print("\n" + message)
    write_to_project_log("Atlas Unified 查看今日 Learning Plan", message)


def show_learning_logic(data):
    profile = data["profile"]
    focus = decide_today_focus(data)
    lines = []
    lines.append("Atlas Learning Planner 判断逻辑：")
    lines.append("")
    lines.append("1. 先读取 Eric Profile")
    lines.append(f"   - 当前目标：{profile.get('goal', '')}")
    lines.append(f"   - 当前项目：{profile.get('current_project', '')}")
    lines.append(f"   - 学习风格：{profile.get('learning_style', '')}")
    lines.append("")
    lines.append("2. 再读取 Skill Database")
    for name, info in data["skills"].items():
        lines.append(f"   - {name}：{info.get('score', 0)} 分")
    lines.append("")
    lines.append("3. 再读取 Project History")
    lines.append("   - Eric 已经完成植物系统、Atlas 1.0、Atlas 2.0，并完成 Atlas 3.0 六阶段。")
    lines.append("")
    lines.append("4. 最后生成今日建议")
    lines.append(f"   - 今日建议：{focus['focus']}")
    lines.append(f"   - 判断原因：{focus['reason']}")

    content = "\n".join(lines)
    print("\nLearning Planner 判断逻辑：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified Learning Planner 判断逻辑", content)


def review_learning_plan(data):
    today = get_today_text()
    plan = None
    for item in data["daily_learning_plans"]:
        if item.get("date") == today:
            plan = item
            break

    if plan is None:
        print("\n今天还没有 Learning Plan，无法复盘。")
        return

    print("\n开始复盘今日 Learning Plan。")
    print(f"今日重点：{plan.get('today_focus', '')}")

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

    plan["status"] = status
    plan["evening_review"] = review
    save_data(data)

    content = format_learning_plan(plan)
    print("\nLearning Plan 复盘已保存：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified Learning Plan 复盘", content)


# ============================================================
# Atlas 3.0 - Emotion Memory
# ============================================================

def emotion_advice_text(record):
    feeling = record.get("feeling", "")
    hours = record.get("debug_hours", 0)
    problem = record.get("problem", "")
    next_step = record.get("next_step", "")

    lines = []
    lines.append("先说明：我不是心理医生。我只作为研发导师，帮助 Eric 调整 Debug 节奏。")
    lines.append("")
    lines.append("机器人判断：")

    if hours >= 4:
        lines.append(f"你今天已经连续调试 {hours} 小时，时间偏长。")
        lines.append("现在不建议继续硬撑。建议先休息 15 到 20 分钟，再回来只测试一个最小问题。")
    elif hours >= 2:
        lines.append(f"你今天已经调试 {hours} 小时。")
        lines.append("建议不要继续扩大功能，只保留一个最小测试目标。")
    else:
        lines.append(f"你今天调试时间是 {hours} 小时，还在可控范围。")

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


def add_emotion_record(data):
    print("\n开始记录今天的研发状态。")
    print("注意：这不是心理诊断，只是研发节奏记录。")

    feeling = input("今天的研发状态，例如：调试失败、有点卡住、连续 Debug 很久：").strip() or "今天有点卡住。"
    hours_text = input("今天连续调试了几个小时？例如 4：").strip()
    problem = input("今天主要卡在哪个问题？").strip() or "未填写具体问题"
    attempted = input("已经尝试过什么方法？").strip() or "未填写已尝试方法"
    next_step = input("下一步准备怎么做？").strip() or "先把问题缩小，再做最小复现测试。"

    hours = int(hours_text) if hours_text.isdigit() else 1
    hours = max(0, hours)

    record = {
        "date": get_today_text(),
        "time": datetime.now().strftime("%H:%M:%S"),
        "feeling": feeling,
        "debug_hours": hours,
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
        f"连续调试时间：{hours} 小时\n"
        f"卡住的问题：{problem}\n"
        f"已尝试方法：{attempted}\n"
        f"下一步：{next_step}\n\n"
        f"机器人提醒：\n{advice}"
    )

    print("\n研发状态记录已保存：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 新增 Emotion Memory", content)


def show_emotion_records(data):
    records = data["emotion_records"][-5:]
    if not records:
        message = "目前还没有研发状态记录。"
        print("\n" + message)
        write_to_project_log("Atlas Unified 查看 Emotion Memory", message)
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
    write_to_project_log("Atlas Unified 查看最近 Emotion Memory", "\n\n".join(lines))


def emotion_summary_text(data):
    records = data["emotion_records"]
    if not records:
        return "目前还没有研发状态记录。"

    tired = 0
    stuck = 0
    failed = 0
    long_debug = 0

    for record in records:
        feeling = record.get("feeling", "")
        hours = record.get("debug_hours", 0)
        if "累" in feeling or "疲惫" in feeling:
            tired += 1
        if "卡住" in feeling or "不知道" in feeling:
            stuck += 1
        if "失败" in feeling or "报错" in feeling:
            failed += 1
        if hours >= 3:
            long_debug += 1

    return (
        f"Eric 目前一共有 {len(records)} 条研发状态记录。\n"
        f"疲惫记录：{tired} 次。\n"
        f"卡住记录：{stuck} 次。\n"
        f"失败或报错记录：{failed} 次。\n"
        f"连续调试 3 小时以上记录：{long_debug} 次。\n\n"
        "机器人判断：这些记录不是心理诊断，而是研发节奏记录。"
    )


def show_emotion_summary(data):
    content = emotion_summary_text(data)
    print("\nEmotion Memory 总结：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified Emotion Memory 总结", content)


def show_emotion_reminder(data):
    if not data["emotion_records"]:
        content = "目前还没有研发状态记录。建议先记录一次 Debug 状态。"
    else:
        content = emotion_advice_text(data["emotion_records"][-1])

    print("\n机器人提醒：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified Emotion Memory 提醒", content)


# ============================================================
# Atlas 3.0 - Mentor Recommendation
# ============================================================

def analyze_state(data):
    completed = []
    in_progress = []
    for project in data["project_history"]:
        if project.get("status") == "completed":
            completed.append(project.get("project_name", "未命名项目"))
        elif project.get("status") == "in_progress":
            in_progress.append(project.get("project_name", "未命名项目"))

    return {
        "arduino_score": get_skill_score(data, "Arduino"),
        "python_score": get_skill_score(data, "Python"),
        "opencv_score": get_skill_score(data, "OpenCV"),
        "yolo_score": get_skill_score(data, "YOLO"),
        "ros2_score": get_skill_score(data, "ROS2"),
        "latest_learning_plan": data["daily_learning_plans"][-1] if data["daily_learning_plans"] else None,
        "latest_emotion": data["emotion_records"][-1] if data["emotion_records"] else None,
        "completed_projects": completed,
        "in_progress_projects": in_progress
    }


def decide_mentor_recommendation(data):
    state = analyze_state(data)
    emotion = state["latest_emotion"]

    if emotion is not None:
        hours = emotion.get("debug_hours", 0)
        feeling = emotion.get("feeling", "")
        if hours >= 4:
            return {
                "main_focus": "Debug Rhythm Control",
                "recommendation": "今天不要继续硬撑新功能。先休息 15 到 20 分钟，再回来只测试一个最小问题。",
                "reason": f"Emotion Memory 显示 Eric 最近连续调试 {hours} 小时，时间偏长。此时继续加功能容易制造更多 Bug。",
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

    ros2 = state["ros2_score"]
    yolo = state["yolo_score"]
    python_score = state["python_score"]

    if ros2 is not None and ros2 < 40:
        return {
            "main_focus": "ROS2",
            "recommendation": "下一步建议 Eric 开始学习 ROS2，而不是继续重复基础 Arduino。",
            "reason": "Skill Database 显示 Arduino、Python、OpenCV 已经有基础，但 ROS2 还没有开始。如果 Eric 未来要做真正的机器人系统，ROS2 是必须补上的能力。",
            "action_1": "了解 ROS2 是什么，以及它为什么用于机器人系统。",
            "action_2": "整理一页 ROS2 笔记：Node、Topic、Message。",
            "action_3": "把 ROS2 作为 Atlas 后续长期学习重点。",
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
            "recommendation": "下一步建议提高 Python 工程化能力，把 Atlas 的代码整理成更清晰的模块。",
            "reason": "Atlas 已经有 2.0 和 3.0 多个模块。如果继续发展，必须把代码结构整理清楚，否则会越来越难维护。",
            "action_1": "整理 Atlas 的所有文件清单。",
            "action_2": "画出 2.0 和 3.0 模块关系图。",
            "action_3": "继续优化 atlas_unified_main.py。",
            "estimated_time": "2 小时",
            "priority": "medium"
        }

    return {
        "main_focus": "Atlas Unified Demo",
        "recommendation": "下一步建议准备 Atlas Unified Demo 和版本说明。",
        "reason": "2.0 和 3.0 已经整合到一个主程序，下一步重点是展示证据，而不是继续加功能。",
        "action_1": "测试一键 Demo 总览。",
        "action_2": "录制 3 分钟 Demo 视频。",
        "action_3": "写 Atlas Unified Version Note。",
        "estimated_time": "2 小时",
        "priority": "medium"
    }


def mentor_recommendation_text(data):
    profile = data["profile"]
    state = analyze_state(data)
    decision = decide_mentor_recommendation(data)

    completed = "、".join(state["completed_projects"]) if state["completed_projects"] else "暂无"
    in_progress = "、".join(state["in_progress_projects"]) if state["in_progress_projects"] else "暂无"

    latest_plan = state["latest_learning_plan"]
    latest_emotion = state["latest_emotion"]

    lines = []
    lines.append(f"{profile.get('name', 'Eric')}，这是 Atlas 生成的导师推荐。")
    lines.append("")
    lines.append("一、Eric 画像")
    lines.append(f"年龄：{profile.get('age', 13)}")
    lines.append(f"长期目标：{profile.get('goal', '')}")
    lines.append(f"当前项目：{profile.get('current_project', '')}")
    lines.append(f"当前版本：{profile.get('current_version', '')}")
    lines.append(f"学习风格：{profile.get('learning_style', '')}")
    lines.append("")
    lines.append("二、技能状态")
    for name, info in data["skills"].items():
        lines.append(f"- {name}：{info.get('score', 0)} 分，level：{info.get('level', 'unknown')}")
    lines.append("")
    lines.append("三、项目历史")
    lines.append(f"已完成项目：{completed}")
    lines.append(f"进行中项目：{in_progress}")
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

    print("\nAtlas 导师推荐：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 生成导师推荐", content)


def show_latest_recommendation(data):
    if not data["recommendations"]:
        message = "目前还没有导师推荐。请先生成导师推荐。"
        print("\n" + message)
        write_to_project_log("Atlas Unified 查看最新导师推荐", message)
        return

    content = data["recommendations"][-1].get("full_text", "")
    print("\n最新导师推荐：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 查看最新导师推荐", content)


def show_recommendation_logic(data):
    state = analyze_state(data)
    decision = decide_mentor_recommendation(data)
    profile = data["profile"]

    lines = []
    lines.append("Atlas Mentor Recommendation 判断逻辑：")
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
    lines.append("   判断 Eric 不是零基础，而是已经完成植物系统、Atlas 1.0、Atlas 2.0 和 Atlas 3.0。")
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
    write_to_project_log("Atlas Unified 导师推荐判断逻辑", content)


# ============================================================
# Unified overview and menu
# ============================================================

def show_database_overview(data):
    content = (
        f"总数据库文件：{DATA_FILE}\n"
        f"学生：{data.get('student_name', 'Eric')}\n"
        f"版本：{data.get('atlas_version', 'Atlas Unified 2.0 + 3.0')}\n"
        f"数据库版本：{data.get('database_version', '')}\n\n"
        f"Atlas 2.0 数据：\n"
        f"- projects：{len(data.get('projects', []))} 个\n"
        f"- daily_tasks：{len(data.get('daily_tasks', []))} 条\n"
        f"- bugs：{len(data.get('bugs', []))} 条\n"
        f"- weekly_reports：{len(data.get('weekly_reports', []))} 份\n\n"
        f"Atlas 3.0 数据：\n"
        f"- profile：已整合\n"
        f"- skills：{len(data.get('skills', {}))} 项技能\n"
        f"- project_history：{len(data.get('project_history', []))} 个历史项目\n"
        f"- daily_learning_plans：{len(data.get('daily_learning_plans', []))} 条\n"
        f"- emotion_records：{len(data.get('emotion_records', []))} 条\n"
        f"- recommendations：{len(data.get('recommendations', []))} 条\n\n"
        "说明：Atlas 2.0 和 Atlas 3.0 已经整合为一个代码文件和一个 JSON 数据库。"
    )

    print("\nAtlas Unified 总数据库概览：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas Unified 总数据库概览", content)


def one_click_demo(data):
    profile = data["profile"]
    focus = decide_today_focus(data)
    decision = decide_mentor_recommendation(data)

    lines = []
    lines.append("Atlas Unified 2.0 + 3.0 Demo Overview")
    lines.append("")
    lines.append("一、Atlas 2.0 项目管理能力")
    lines.append(f"项目数量：{len(data['projects'])} 个")
    lines.append(f"Daily Task 数量：{len(data['daily_tasks'])} 条")
    lines.append(f"Bug 数量：{len(data['bugs'])} 条")
    lines.append(f"Weekly Report 数量：{len(data['weekly_reports'])} 份")
    lines.append("")
    lines.append("二、Atlas 3.0 Digital Twin 能力")
    lines.append(f"Eric Profile：{profile.get('name', 'Eric')}，目标：{profile.get('goal', '')}")
    lines.append(f"强项技能：{'、'.join(get_strong_skills(data)) if get_strong_skills(data) else '暂无'}")
    lines.append(f"需要补强：{'、'.join(get_weak_skills(data)) if get_weak_skills(data) else '暂无'}")
    lines.append(f"项目历史数量：{len(data['project_history'])} 个")
    lines.append("")
    lines.append("三、Learning Planner")
    lines.append(f"今日建议重点：{focus['focus']}")
    lines.append(f"原因：{focus['reason']}")
    lines.append("")
    lines.append("四、Emotion Memory")
    lines.append(f"研发状态记录数量：{len(data['emotion_records'])} 条")
    if data["emotion_records"]:
        latest = data["emotion_records"][-1]
        lines.append(f"最近状态：{latest.get('feeling', '')}")
        lines.append(f"最近调试时间：{latest.get('debug_hours', 0)} 小时")
    else:
        lines.append("最近状态：暂无记录")
    lines.append("")
    lines.append("五、Mentor Recommendation")
    lines.append(f"推荐重点：{decision['main_focus']}")
    lines.append(f"推荐内容：{decision['recommendation']}")
    lines.append("")
    lines.append("机器人总结：")
    lines.append("Atlas Unified 已经把 Atlas 2.0 的项目管理能力和 Atlas 3.0 的个性化导师能力整合成一个主程序和一个总数据库。")

    content = "\n".join(lines)
    print("\n" + "=" * 70)
    print(content)
    print("=" * 70)
    write_to_project_log("Atlas Unified 一键 Demo 总览", content)


def test_log_write():
    content = (
        "这是 Atlas Unified 主程序的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明整合版日志保存正常。"
    )
    write_to_project_log("Atlas Unified 日志写入测试", content)


def show_intro(data):
    profile = data["profile"]
    print("\n==============================")
    print("Atlas Unified Main Program")
    print("Atlas 2.0 + Atlas 3.0 深度整合版")
    print("==============================")
    print(f"学生：{profile.get('name', 'Eric')}")
    print(f"目标：{profile.get('goal', '')}")
    print(f"当前项目：{profile.get('current_project', '')}")
    print(f"当前版本：{profile.get('current_version', 'Atlas Unified 2.0 + 3.0')}")
    print(f"总数据库文件：{DATA_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")
    print("功能：Project Management + Digital Twin Mentor")
    print("==============================")


def main():
    data = load_data()
    show_intro(data)

    write_to_project_log("Atlas Unified 主程序启动", "atlas_unified_main.py 已启动。")

    print("\n机器人开机主动提醒：")
    print("-" * 70)
    print(morning_message_text(data))
    print("-" * 70)

    while True:
        print("\n请选择功能：")
        print("1. 一键 Demo 总览")
        print("2. 查看总数据库概览")
        print("3. Atlas 2.0：Project Database 项目总览")
        print("4. Atlas 2.0：更新 Atlas 2.0 进度")
        print("5. Atlas 2.0：创建或更新 Daily Task")
        print("6. Atlas 2.0：查看今日 Daily Task")
        print("7. Atlas 2.0：复盘 Daily Task")
        print("8. Atlas 2.0：新增 Bug")
        print("9. Atlas 2.0：查看 / 搜索 Bug")
        print("10. Atlas 2.0：更新 Bug 状态")
        print("11. Atlas 2.0：Bug 总结")
        print("12. Atlas 2.0：生成 Weekly Report")
        print("13. Atlas 2.0：查看最新 Weekly Report")
        print("14. Atlas 3.0：查看 Eric Profile")
        print("15. Atlas 3.0：机器人身份回答")
        print("16. Atlas 3.0：更新 Eric Profile")
        print("17. Atlas 3.0：查看 Skill Database")
        print("18. Atlas 3.0：下一步学习建议")
        print("19. Atlas 3.0：更新技能分数")
        print("20. Atlas 3.0：查看 Project History")
        print("21. Atlas 3.0：项目迁移建议")
        print("22. Atlas 3.0：开机主动提醒")
        print("23. Atlas 3.0：生成今日 Learning Plan")
        print("24. Atlas 3.0：查看今日 Learning Plan")
        print("25. Atlas 3.0：解释 Learning Planner 判断逻辑")
        print("26. Atlas 3.0：复盘 Learning Plan")
        print("27. Atlas 3.0：新增 Emotion Memory")
        print("28. Atlas 3.0：查看最近 Emotion Memory")
        print("29. Atlas 3.0：Emotion Memory 总结")
        print("30. Atlas 3.0：Emotion Memory 提醒")
        print("31. Atlas 3.0：生成 Mentor Recommendation")
        print("32. Atlas 3.0：查看最新 Mentor Recommendation")
        print("33. Atlas 3.0：解释 Mentor Recommendation 逻辑")
        print("34. 测试 project_log.txt 是否能写入")
        print("35. 退出")

        choice = input("请输入数字 1-35：").strip()

        if choice == "1":
            one_click_demo(data)
        elif choice == "2":
            show_database_overview(data)
        elif choice == "3":
            show_project_database(data)
        elif choice == "4":
            update_atlas2_progress(data)
        elif choice == "5":
            create_or_update_daily_task(data)
        elif choice == "6":
            show_today_daily_task(data)
        elif choice == "7":
            review_daily_task(data)
        elif choice == "8":
            add_bug(data)
        elif choice == "9":
            show_or_search_bugs(data)
        elif choice == "10":
            update_bug_status(data)
        elif choice == "11":
            show_bug_summary(data)
        elif choice == "12":
            generate_weekly_report(data)
        elif choice == "13":
            show_latest_weekly_report(data)
        elif choice == "14":
            show_profile(data)
        elif choice == "15":
            robot_profile_intro(data)
        elif choice == "16":
            update_profile(data)
        elif choice == "17":
            show_skill_database(data)
        elif choice == "18":
            show_next_learning_advice(data)
        elif choice == "19":
            update_skill(data)
        elif choice == "20":
            show_project_history(data)
        elif choice == "21":
            show_transfer_advice(data)
        elif choice == "22":
            show_morning_message(data)
        elif choice == "23":
            generate_learning_plan(data)
        elif choice == "24":
            show_today_learning_plan(data)
        elif choice == "25":
            show_learning_logic(data)
        elif choice == "26":
            review_learning_plan(data)
        elif choice == "27":
            add_emotion_record(data)
        elif choice == "28":
            show_emotion_records(data)
        elif choice == "29":
            show_emotion_summary(data)
        elif choice == "30":
            show_emotion_reminder(data)
        elif choice == "31":
            generate_mentor_recommendation(data)
        elif choice == "32":
            show_latest_recommendation(data)
        elif choice == "33":
            show_recommendation_logic(data)
        elif choice == "34":
            test_log_write()
        elif choice == "35":
            write_to_project_log("Atlas Unified 主程序退出", "atlas_unified_main.py 已退出。")
            print("\n程序已退出。")
            break
        else:
            print("输入无效，请输入 1 到 35。")
            write_to_project_log("Atlas Unified 无效输入", f"用户输入了无效菜单数字：{choice}")


if __name__ == "__main__":
    main()
