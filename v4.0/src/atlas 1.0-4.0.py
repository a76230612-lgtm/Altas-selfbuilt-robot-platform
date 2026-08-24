#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Atlas All Versions Main
Single-file integrated version for Atlas 1.0 + 2.0 + 3.0 + 4.0

来源：
1. atlas_unified_main.py：Atlas 2.0 + Atlas 3.0 深度整合版
2. atlas4_full_main.py：Atlas 4.0 六阶段整合版

运行：
python atlas_all_versions_main.py
或：
py atlas_all_versions_main.py
"""


# ============================================================
# Source Part A: Atlas Unified 2.0 + 3.0
# ============================================================

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


# ============================================================
# Source Part B: Atlas 4.0 Full Main
# ============================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Atlas 4.0 Full Main
Single-file integrated version

包含功能：
Stage 1  Vision：摄像头检测 Eric 是否在场
Stage 2  Voice Input：录音并转文字
Stage 3  Voice Output：文字转语音
Stage 4  Memory Integration：读取 Atlas 3.0 / 综合长期记忆并回答
Stage 5  Proactive Mentor：主动生成 Morning Brief、昨天总结、今天任务、未推进任务提醒
Stage 6  Hardware Feedback：Python 串口控制 Arduino 的 LED / 舵机 / OLED 反馈

运行：
python atlas4_full_main.py
或：
py atlas4_full_main.py
"""

import json
import tempfile
import time
from datetime import datetime, date, timedelta
from pathlib import Path


# ============================================================
# Optional imports
# ============================================================

try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False

try:
    import numpy as np
    import sounddevice as sd
    from scipy.io.wavfile import write as write_wav
    import speech_recognition as sr
    VOICE_INPUT_AVAILABLE = True
except Exception:
    VOICE_INPUT_AVAILABLE = False
    np = None
    sd = None
    write_wav = None
    sr = None

try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False
    pyttsx3 = None

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except Exception:
    SERIAL_AVAILABLE = False
    serial = None


# ============================================================
# Global paths and settings
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "atlas4_config.json"
FULL_DATA_FILE = BASE_DIR / "atlas4_full_data.json"

PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"
VISION_LOG_FILE = BASE_DIR / "vision_log.txt"
VOICE_INPUT_LOG_FILE = BASE_DIR / "voice_input_log.txt"
VOICE_OUTPUT_LOG_FILE = BASE_DIR / "voice_output_log.txt"
MEMORY_INTEGRATION_LOG_FILE = BASE_DIR / "memory_integration_log.txt"
PROACTIVE_MENTOR_LOG_FILE = BASE_DIR / "proactive_mentor_log.txt"
HARDWARE_LOG_FILE = BASE_DIR / "hardware_feedback_log.txt"

VOICE_INPUT_DATA_FILE = BASE_DIR / "voice_input_data.json"
VOICE_OUTPUT_DATA_FILE = BASE_DIR / "voice_output_data.json"
MEMORY_INTEGRATION_DATA_FILE = BASE_DIR / "memory_integration_data.json"
PROACTIVE_MENTOR_DATA_FILE = BASE_DIR / "proactive_mentor_data.json"

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

DEFAULT_CONFIG = {
    "serial_port": "COM6",
    "backup_serial_ports": ["COM4", "COM5", "COM3", "COM7", "COM8"],
    "baud_rate": 9600,
    "camera_index": 0,
    "voice_input_sample_rate": 16000,
    "default_voice_language": "en-US",
    "tts_rate": 160,
    "tts_volume": 1.0
}

VALID_HARDWARE_COMMANDS = [
    "PING",
    "STATUS",
    "TEST",
    "HAPPY",
    "THINKING",
    "WARNING",
    "ERROR",
    "NOD",
    "OFF"
]

EXPECTED_RESPONSES = {
    "PING": ["PONG", "OK:PING"],
    "STATUS": ["STATUS_OK", "OK:STATUS"],
    "TEST": ["FULL_TEST_DONE", "OK:TEST"],
    "HAPPY": ["HAPPY_OK", "OK:HAPPY"],
    "THINKING": ["THINKING_OK", "OK:THINKING"],
    "WARNING": ["WARNING_OK", "OK:WARNING"],
    "ERROR": ["ERROR_OK", "OK:ERROR"],
    "NOD": ["NOD_OK", "OK:NOD"],
    "OFF": ["OFF_OK", "OK:OFF"]
}

COMMAND_READ_SECONDS = {
    "PING": 2.0,
    "STATUS": 2.5,
    "TEST": 6.0,
    "HAPPY": 3.0,
    "THINKING": 4.0,
    "WARNING": 4.0,
    "ERROR": 3.0,
    "NOD": 4.0,
    "OFF": 2.0
}


# ============================================================
# Basic utilities
# ============================================================

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
            data = json.load(file)
        return data
    except Exception:
        return default_data


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def safe_write_text(file_path, text):
    try:
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(text)
    except Exception as error:
        print(f"\n日志写入失败：{file_path}")
        print(f"错误信息：{error}")


def write_block_log(file_path, title, content, echo=True):
    text = (
        "\n" + "=" * 70 + "\n"
        + title + "\n"
        + f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + str(content) + "\n"
        + "=" * 70 + "\n"
    )

    safe_write_text(file_path, text)

    if echo:
        print(f"\n已写入：{file_path.name}")
        print(f"位置：{file_path}")


def write_to_project_log(title, content):
    write_block_log(PROJECT_LOG_FILE, title, content)


def write_to_vision_log(content):
    write_block_log(VISION_LOG_FILE, "Atlas 4.0 Vision Log", content)


def write_to_voice_input_log(content):
    write_block_log(VOICE_INPUT_LOG_FILE, "Atlas 4.0 Voice Input Log", content)


def write_to_voice_output_log(content):
    write_block_log(VOICE_OUTPUT_LOG_FILE, "Atlas 4.0 Voice Output Log", content)


def write_to_memory_log(content):
    write_block_log(MEMORY_INTEGRATION_LOG_FILE, "Atlas 4.0 Memory Integration Log", content)


def write_to_proactive_log(content):
    write_block_log(PROACTIVE_MENTOR_LOG_FILE, "Atlas 4.0 Proactive Mentor Log", content)


def write_to_hardware_log(content):
    write_block_log(HARDWARE_LOG_FILE, "Atlas 4.0 Hardware Feedback Log", content)


def load_config():
    config = dict(DEFAULT_CONFIG)

    if CONFIG_FILE.exists():
        try:
            old_config = safe_load_json(CONFIG_FILE, {})
            if isinstance(old_config, dict):
                config.update(old_config)
        except Exception:
            pass

    save_json(CONFIG_FILE, config)
    return config


def save_config_value(key, value):
    config = load_config()
    config[key] = value
    save_json(CONFIG_FILE, config)
    return config


def record_full_event(event_type, content):
    data = safe_load_json(FULL_DATA_FILE, {
        "student_name": "Eric",
        "atlas4_full_version": "Atlas 4.0 Full Main v1",
        "events": []
    })

    if "events" not in data:
        data["events"] = []

    data["events"].append({
        "time": get_now_text(),
        "event_type": event_type,
        "content": content
    })

    save_json(FULL_DATA_FILE, data)


def pause():
    input("\n按回车继续...")


# ============================================================
# Status
# ============================================================

def show_system_status():
    config = load_config()

    lines = []
    lines.append("Atlas 4.0 系统状态")
    lines.append("")
    lines.append(f"Python 文件夹：{BASE_DIR}")
    lines.append(f"Config 文件：{CONFIG_FILE}")
    lines.append(f"Full Data 文件：{FULL_DATA_FILE}")
    lines.append("")
    lines.append("依赖库状态：")
    lines.append(f"- OpenCV / Vision：{'OK' if CV2_AVAILABLE else 'MISSING'}")
    lines.append(f"- Voice Input：{'OK' if VOICE_INPUT_AVAILABLE else 'MISSING'}")
    lines.append(f"- Voice Output / pyttsx3：{'OK' if TTS_AVAILABLE else 'MISSING'}")
    lines.append(f"- Hardware / pyserial：{'OK' if SERIAL_AVAILABLE else 'MISSING'}")
    lines.append("")
    lines.append("当前配置：")
    lines.append(f"- Arduino 串口：{config.get('serial_port')}")
    lines.append(f"- 备用串口：{config.get('backup_serial_ports')}")
    lines.append(f"- 波特率：{config.get('baud_rate')}")
    lines.append(f"- 摄像头编号：{config.get('camera_index')}")
    lines.append(f"- 语音识别采样率：{config.get('voice_input_sample_rate')}")
    lines.append(f"- 默认语音识别语言：{config.get('default_voice_language')}")
    lines.append(f"- TTS 语速：{config.get('tts_rate')}")
    lines.append(f"- TTS 音量：{config.get('tts_volume')}")
    lines.append("")
    lines.append("长期记忆文件检测：")

    for file_path in [
        ATLAS_UNIFIED_DATA_FILE,
        ATLAS_FINAL_DATA_FILE,
        ATLAS_INTEGRATED_DATA_FILE,
        ATLAS3_DATA_FILE,
        PROFILE_FILE,
        SKILLS_FILE,
        HISTORY_FILE,
        LEARNING_PLAN_FILE,
        EMOTION_FILE,
        MENTOR_RECOMMENDATION_FILE,
    ]:
        lines.append(f"- {file_path.name}：{'FOUND' if file_path.exists() else 'not found'}")

    content = "\n".join(lines)

    print("\n" + content)
    write_to_project_log("Atlas 4.0 Full Main 系统状态检查", content)
    record_full_event("system_status", content)


def test_all_logs():
    content = (
        "Atlas 4.0 Full Main 日志写入测试。\n"
        "如果你能看到这些记录，说明所有核心日志文件都可以正常写入。"
    )

    write_to_project_log("Atlas 4.0 Full Main 日志写入测试", content)
    write_to_vision_log(content)
    write_to_voice_input_log(content)
    write_to_voice_output_log(content)
    write_to_memory_log(content)
    write_to_proactive_log(content)
    write_to_hardware_log(content)
    record_full_event("log_test", content)


# ============================================================
# Stage 1: Vision
# ============================================================

def test_camera_once():
    if not CV2_AVAILABLE:
        message = "OpenCV 不可用。请先运行：pip install opencv-python"
        print("\n" + message)
        write_to_vision_log(message)
        return False

    config = load_config()
    camera_index = int(config.get("camera_index", 0))

    print(f"\n正在测试摄像头是否可以打开，camera_index={camera_index} ...")

    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        message = (
            f"摄像头打开失败。当前 camera_index={camera_index}\n"
            "请检查：\n"
            "1. 摄像头是否被其他软件占用\n"
            "2. Windows 是否允许 Cursor / Python 使用摄像头\n"
            "3. 如果是外接 USB 摄像头，请重新插拔\n"
            "4. 可以在配置菜单把 camera_index 改成 1 或 2"
        )
        print(message)
        write_to_vision_log(message)
        write_to_project_log("Atlas 4.0 Vision 摄像头测试失败", message)
        return False

    success, frame = camera.read()
    camera.release()

    if not success:
        message = "摄像头可以打开，但无法读取画面。"
        print(message)
        write_to_vision_log(message)
        write_to_project_log("Atlas 4.0 Vision 摄像头读取失败", message)
        return False

    message = "摄像头测试成功。Atlas 4.0 可以读取摄像头画面。"
    print(message)
    write_to_vision_log(message)
    write_to_project_log("Atlas 4.0 Vision 摄像头测试成功", message)
    return True


def start_vision_detection():
    if not CV2_AVAILABLE:
        message = "OpenCV 不可用。请先运行：pip install opencv-python"
        print("\n" + message)
        write_to_vision_log(message)
        return

    config = load_config()
    camera_index = int(config.get("camera_index", 0))

    print("\n启动 Atlas 4.0 Vision 检测。")
    print("1. 摄像头窗口打开后，请让 Eric 面对摄像头。")
    print("2. 检测到人脸时，会显示 Eric is present。")
    print("3. 没检测到人脸时，会显示 Eric is not present。")
    print("4. 按 q 退出摄像头窗口。")
    print(f"当前 camera_index：{camera_index}")

    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        message = f"摄像头打开失败。当前 camera_index={camera_index}。"
        print(message)
        write_to_vision_log(message)
        write_to_project_log("Atlas 4.0 Vision 启动失败", message)
        return

    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_detector = cv2.CascadeClassifier(face_cascade_path)

    if face_detector.empty():
        message = "OpenCV 人脸检测模型加载失败。"
        print(message)
        write_to_vision_log(message)
        write_to_project_log("Atlas 4.0 Vision 人脸模型加载失败", message)
        camera.release()
        return

    last_status = None
    present_count = 0
    absent_count = 0

    write_to_vision_log("Atlas 4.0 Vision 检测已启动。")
    write_to_project_log(
        "Atlas 4.0 Vision 检测启动",
        "摄像头检测已启动。目标：判断 Eric 是否在画面前。"
    )

    while True:
        success, frame = camera.read()

        if not success:
            print("无法读取摄像头画面。")
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_detector.detectMultiScale(
            gray_frame,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )

        if len(faces) > 0:
            status = "Eric is present"
            present_count += 1
        else:
            status = "Eric is not present"
            absent_count += 1

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.putText(
            frame,
            status,
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0) if len(faces) > 0 else (0, 0, 255),
            2
        )

        cv2.putText(
            frame,
            "Press q to quit",
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.imshow("Atlas 4.0 Vision - Eric Presence Detection", frame)

        if status != last_status:
            log_message = f"Vision 状态变化：{status}"
            print(log_message)
            write_to_vision_log(log_message)
            last_status = status

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    summary = (
        "Atlas 4.0 Vision 检测结束。\n"
        f"检测到 Eric 在场的帧数：{present_count}\n"
        f"未检测到 Eric 的帧数：{absent_count}\n"
        "说明：这是 Atlas 4.0 第一阶段 Vision 的基础检测结果。"
    )

    print("\n" + summary)
    write_to_vision_log(summary)
    write_to_project_log("Atlas 4.0 Vision 检测结束", summary)


def set_camera_index():
    current = load_config().get("camera_index", 0)
    print(f"\n当前 camera_index：{current}")
    text = input("请输入新的摄像头编号，例如 0 / 1 / 2：").strip()

    if not text.isdigit():
        print("输入无效。")
        return

    index = int(text)
    save_config_value("camera_index", index)
    print(f"已保存 camera_index：{index}")


# ============================================================
# Stage 2: Voice Input
# ============================================================

def create_default_voice_data():
    return {
        "student_name": "Eric",
        "voice_input_version": "Atlas 4.0 Voice Input v1",
        "voice_records": []
    }


def load_voice_data():
    data = safe_load_json(VOICE_INPUT_DATA_FILE, create_default_voice_data())

    if not isinstance(data, dict):
        data = create_default_voice_data()

    data.setdefault("student_name", "Eric")
    data.setdefault("voice_input_version", "Atlas 4.0 Voice Input v1")
    data.setdefault("voice_records", [])

    save_json(VOICE_INPUT_DATA_FILE, data)
    return data


def save_voice_record(text, language, duration_seconds, status):
    data = load_voice_data()

    record = {
        "time": get_now_text(),
        "language": language,
        "duration_seconds": duration_seconds,
        "recognized_text": text,
        "status": status
    }

    data["voice_records"].append(record)
    save_json(VOICE_INPUT_DATA_FILE, data)
    return record


def list_audio_devices():
    if not VOICE_INPUT_AVAILABLE:
        message = (
            "Voice Input 依赖库不可用。\n"
            "请先运行：pip install numpy sounddevice scipy SpeechRecognition"
        )
        print("\n" + message)
        write_to_voice_input_log(message)
        return

    print("\n当前电脑音频设备：")
    print("-" * 70)

    try:
        devices = sd.query_devices()
        lines = []

        for index, device in enumerate(devices):
            name = device.get("name", "Unknown")
            max_input_channels = device.get("max_input_channels", 0)
            max_output_channels = device.get("max_output_channels", 0)

            line = (
                f"{index}. {name} | "
                f"输入通道：{max_input_channels} | "
                f"输出通道：{max_output_channels}"
            )

            print(line)
            lines.append(line)

        print("-" * 70)

        content = "已成功读取电脑音频设备列表：\n" + "\n".join(lines)
        write_to_voice_input_log(content)
        write_to_project_log("Atlas 4.0 Voice Input 音频设备检测成功", content)

    except Exception as error:
        message = f"音频设备读取失败：{error}"
        print(message)
        write_to_voice_input_log(message)
        write_to_project_log("Atlas 4.0 Voice Input 音频设备检测失败", message)


def record_audio_to_temp_wav(duration_seconds=5, sample_rate=16000):
    if not VOICE_INPUT_AVAILABLE:
        raise RuntimeError("Voice Input 依赖库不可用。请安装 numpy sounddevice scipy SpeechRecognition。")

    print("\n准备开始录音。")
    print(f"请 Eric 对着麦克风说话，录音时长：{duration_seconds} 秒。")
    print("开始录音...")

    try:
        audio_data = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()

    except Exception as error:
        raise RuntimeError(f"录音失败：{error}")

    print("录音结束。")

    audio_data = np.asarray(audio_data)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file_path = temp_file.name
    temp_file.close()

    write_wav(temp_file_path, sample_rate, audio_data)

    return temp_file_path


def recognize_speech_from_wav(wav_path, language):
    if not VOICE_INPUT_AVAILABLE:
        raise RuntimeError("SpeechRecognition 不可用。")

    recognizer = sr.Recognizer()

    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)

    try:
        recognized_text = recognizer.recognize_google(audio, language=language)
        return recognized_text

    except sr.UnknownValueError:
        return ""

    except sr.RequestError as error:
        raise RuntimeError(
            f"语音识别服务连接失败：{error}\n"
            "可能原因：网络不可用，或 Google Speech Recognition 暂时无法访问。"
        )


def record_and_recognize_once():
    if not VOICE_INPUT_AVAILABLE:
        message = (
            "Voice Input 依赖库不可用。\n"
            "请先运行：pip install numpy sounddevice scipy SpeechRecognition"
        )
        print("\n" + message)
        write_to_voice_input_log(message)
        return ""

    print("\n选择识别语言：")
    print("1. English")
    print("2. 中文")
    language_choice = input("请输入 1 或 2：").strip()

    if language_choice == "2":
        language = "zh-CN"
        language_name = "中文"
    else:
        language = "en-US"
        language_name = "English"

    duration_text = input("\n录音几秒？建议 5 秒，直接回车默认 5 秒：").strip()

    if duration_text.isdigit():
        duration_seconds = int(duration_text)
    else:
        duration_seconds = 5

    duration_seconds = max(2, min(15, duration_seconds))
    sample_rate = int(load_config().get("voice_input_sample_rate", 16000))

    try:
        wav_path = record_audio_to_temp_wav(
            duration_seconds=duration_seconds,
            sample_rate=sample_rate
        )
        recognized_text = recognize_speech_from_wav(wav_path, language=language)

        if recognized_text:
            status = "recognized"
            content = (
                f"识别语言：{language_name}\n"
                f"录音时长：{duration_seconds} 秒\n"
                f"识别结果：{recognized_text}"
            )
            print("\nAtlas 听到的内容：")
            print("-" * 70)
            print(recognized_text)
            print("-" * 70)

        else:
            status = "not_recognized"
            content = (
                f"识别语言：{language_name}\n"
                f"录音时长：{duration_seconds} 秒\n"
                "识别结果：没有识别到清楚语音。\n"
                "建议：靠近麦克风，说话慢一点，环境安静一点。"
            )
            print("\n没有识别到清楚语音。")
            print("建议：靠近麦克风，说话慢一点，环境安静一点。")

        save_voice_record(
            text=recognized_text,
            language=language_name,
            duration_seconds=duration_seconds,
            status=status
        )

        write_to_voice_input_log(content)
        write_to_project_log("Atlas 4.0 Voice Input 单次语音识别", content)
        return recognized_text

    except Exception as error:
        message = f"Voice Input 运行失败：{error}"

        print("\n" + message)

        save_voice_record(
            text="",
            language=language_name,
            duration_seconds=duration_seconds,
            status="error"
        )

        write_to_voice_input_log(message)
        write_to_project_log("Atlas 4.0 Voice Input 运行失败", message)
        return ""


def continuous_voice_test():
    print("\n连续语音识别测试。")
    print("每次录音 5 秒。")
    print("输入 q 可以退出连续测试。")

    while True:
        command = input("\n按回车开始一次录音，输入 q 退出：").strip().lower()

        if command == "q":
            print("已退出连续语音识别测试。")
            break

        record_and_recognize_once()


def show_recent_voice_records():
    data = load_voice_data()
    records = data.get("voice_records", [])

    if not records:
        message = "目前还没有语音识别记录。"
        print("\n" + message)
        write_to_voice_input_log(message)
        return

    recent_records = records[-5:]
    lines = []

    print("\n最近 5 条语音识别记录：")
    print("-" * 70)

    for record in recent_records:
        text = (
            f"时间：{record.get('time', '')}\n"
            f"语言：{record.get('language', '')}\n"
            f"录音时长：{record.get('duration_seconds', '')} 秒\n"
            f"状态：{record.get('status', '')}\n"
            f"识别结果：{record.get('recognized_text', '')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    content = "\n\n".join(lines)
    write_to_voice_input_log(content)
    write_to_project_log("Atlas 4.0 Voice Input 查看最近语音记录", content)


def get_latest_voice_input_text():
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


# ============================================================
# Stage 3: Voice Output
# ============================================================

def create_default_voice_output_data():
    return {
        "student_name": "Eric",
        "voice_output_version": "Atlas 4.0 Voice Output v1",
        "voice_output_records": []
    }


def load_voice_output_data():
    data = safe_load_json(VOICE_OUTPUT_DATA_FILE, create_default_voice_output_data())

    if not isinstance(data, dict):
        data = create_default_voice_output_data()

    data.setdefault("student_name", "Eric")
    data.setdefault("voice_output_version", "Atlas 4.0 Voice Output v1")
    data.setdefault("voice_output_records", [])

    save_json(VOICE_OUTPUT_DATA_FILE, data)
    return data


def save_voice_output_record(text, voice_name, rate, volume, status):
    data = load_voice_output_data()

    record = {
        "time": get_now_text(),
        "text": text,
        "voice_name": voice_name,
        "rate": rate,
        "volume": volume,
        "status": status
    }

    data["voice_output_records"].append(record)
    save_json(VOICE_OUTPUT_DATA_FILE, data)
    return record


def create_tts_engine():
    if not TTS_AVAILABLE:
        raise RuntimeError("pyttsx3 不可用。请先运行：pip install pyttsx3")

    try:
        engine = pyttsx3.init()
        return engine
    except Exception as error:
        raise RuntimeError(f"pyttsx3 初始化失败：{error}")


def list_voices():
    print("\n正在读取电脑可用语音列表...")

    if not TTS_AVAILABLE:
        message = "pyttsx3 不可用。请先运行：pip install pyttsx3"
        print("\n" + message)
        write_to_voice_output_log(message)
        return

    try:
        engine = create_tts_engine()
        voices = engine.getProperty("voices")

        print("\n电脑可用语音：")
        print("-" * 70)

        if not voices:
            print("没有读取到语音。")
            return

        lines = []

        for index, voice in enumerate(voices):
            voice_name = getattr(voice, "name", "Unknown")
            voice_id = getattr(voice, "id", "Unknown")
            languages = getattr(voice, "languages", [])

            text = (
                f"{index}. 语音名称：{voice_name}\n"
                f"   语音 ID：{voice_id}\n"
                f"   languages：{languages}"
            )

            print(text)
            print("-" * 70)
            lines.append(text)

        content = "已成功读取电脑可用语音列表：\n\n" + "\n\n".join(lines)

        write_to_voice_output_log(content)
        write_to_project_log("Atlas 4.0 Voice Output 查看语音列表", content)

    except Exception as error:
        message = f"读取语音列表失败：{error}"
        print("\n" + message)
        write_to_voice_output_log(message)
        write_to_project_log("Atlas 4.0 Voice Output 读取语音列表失败", message)


def speak_text(text, rate=None, volume=None, voice_index=None, log=True):
    if not text:
        text = "Hello Eric. This is Atlas."

    config = load_config()
    if rate is None:
        rate = int(config.get("tts_rate", 160))
    if volume is None:
        volume = float(config.get("tts_volume", 1.0))

    if not TTS_AVAILABLE:
        message = "pyttsx3 不可用，无法语音输出。请运行：pip install pyttsx3"
        print("\n" + message)
        if log:
            write_to_voice_output_log(message)
        return False

    try:
        engine = create_tts_engine()

        voices = engine.getProperty("voices")
        selected_voice_name = "default"

        if voice_index is not None and voices:
            if 0 <= voice_index < len(voices):
                selected_voice = voices[voice_index]
                engine.setProperty("voice", selected_voice.id)
                selected_voice_name = getattr(selected_voice, "name", "selected_voice")
            else:
                selected_voice_name = "default"

        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)

        print("\nAtlas 正在说：")
        print("-" * 70)
        print(text)
        print("-" * 70)

        engine.say(text)
        engine.runAndWait()

        content = (
            f"语音输出成功。\n"
            f"文本：{text}\n"
            f"语音：{selected_voice_name}\n"
            f"语速：{rate}\n"
            f"音量：{volume}"
        )

        save_voice_output_record(
            text=text,
            voice_name=selected_voice_name,
            rate=rate,
            volume=volume,
            status="spoken"
        )

        if log:
            write_to_voice_output_log(content)
            write_to_project_log("Atlas 4.0 Voice Output 语音输出成功", content)

        return True

    except Exception as error:
        message = f"语音输出失败：{error}"
        print("\n" + message)

        save_voice_output_record(
            text=text,
            voice_name="unknown",
            rate=rate,
            volume=volume,
            status="error"
        )

        if log:
            write_to_voice_output_log(message)
            write_to_project_log("Atlas 4.0 Voice Output 语音输出失败", message)

        return False


def test_basic_speech():
    return speak_text("Hello Eric. I am Atlas. I can speak now.")


def test_chinese_speech():
    return speak_text("你好 Eric，我是 Atlas。现在我已经可以说话了。", rate=150)


def custom_speech():
    print("\n自定义语音输出。")
    text = input("请输入想让 Atlas 说的话：").strip()

    if not text:
        text = "Hello Eric. This is Atlas."

    rate_text = input("语速，建议 150 到 180，直接回车默认配置值：").strip()

    if rate_text.isdigit():
        rate = int(rate_text)
    else:
        rate = int(load_config().get("tts_rate", 160))

    rate = max(80, min(260, rate))

    volume_text = input("音量 0.0 到 1.0，直接回车默认配置值：").strip()

    try:
        volume = float(volume_text) if volume_text else float(load_config().get("tts_volume", 1.0))
    except Exception:
        volume = 1.0

    volume = max(0, min(1, volume))

    voice_index_text = input("语音编号，直接回车使用默认语音：").strip()

    if voice_index_text.isdigit():
        voice_index = int(voice_index_text)
    else:
        voice_index = None

    return speak_text(text=text, rate=rate, volume=volume, voice_index=voice_index)


def atlas_greeting():
    text = (
        "Hello Eric. I am Atlas. "
        "I can see you, hear you, and now I can speak to you. "
        "Today, I will help you continue your AI mentor robot project."
    )
    return speak_text(text, rate=160)


def atlas_task_reminder():
    text = (
        "Eric, here is your task reminder. "
        "Do not add too many new features at once. "
        "Test one function, record the result, and then continue."
    )
    return speak_text(text, rate=160)


def atlas_debug_reminder():
    text = (
        "Eric, if you have been debugging for a long time, "
        "take a short break first. "
        "Then come back and test only one small problem."
    )
    return speak_text(text, rate=155)


def show_recent_voice_output_records():
    data = load_voice_output_data()
    records = data.get("voice_output_records", [])

    if not records:
        message = "目前还没有 Voice Output 记录。"
        print("\n" + message)
        write_to_voice_output_log(message)
        return

    recent_records = records[-5:]
    lines = []

    print("\n最近 5 条 Voice Output 记录：")
    print("-" * 70)

    for record in recent_records:
        text = (
            f"时间：{record.get('time', '')}\n"
            f"文本：{record.get('text', '')}\n"
            f"语音：{record.get('voice_name', '')}\n"
            f"语速：{record.get('rate', '')}\n"
            f"音量：{record.get('volume', '')}\n"
            f"状态：{record.get('status', '')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    content = "\n\n".join(lines)
    write_to_voice_output_log(content)
    write_to_project_log("Atlas 4.0 Voice Output 查看最近语音输出记录", content)


# ============================================================
# Stage 4 / 5: Memory shared functions
# ============================================================

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
                    "Proactive Mentor",
                    "Hardware Feedback"
                ],
                "transfer_to_atlas": "Atlas 4.0 正在把视觉、语音、长期记忆、主动导师和硬件反馈能力整合起来。"
            }
        ],
        "daily_learning_plans": [],
        "emotion_records": [],
        "recommendations": [],
        "daily_tasks": [],
        "bugs": [],
        "weekly_reports": []
    }


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
    lines = ["Eric 的技能状态："]

    for skill_name, skill_info in skills.items():
        if isinstance(skill_info, dict):
            lines.append(
                f"- {skill_name}：{skill_info.get('score', 0)} 分，level：{skill_info.get('level', 'unknown')}"
            )
        else:
            lines.append(f"- {skill_name}：{skill_info}")

    return "\n".join(lines)


def format_project_history_summary(memory):
    history = memory.get("project_history", [])

    if not history:
        return "目前没有 Project History。"

    lines = ["Eric 的项目历史："]

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

    skills = memory.get("skills", {})

    ros2_score = skills.get("ROS2", {}).get("score", None) if isinstance(skills.get("ROS2"), dict) else None
    arduino_score = skills.get("Arduino", {}).get("score", None) if isinstance(skills.get("Arduino"), dict) else None
    python_score = skills.get("Python", {}).get("score", None) if isinstance(skills.get("Python"), dict) else None
    opencv_score = skills.get("OpenCV", {}).get("score", None) if isinstance(skills.get("OpenCV"), dict) else None

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
            "现在你已经完成 Vision、Voice Input、Voice Output、Memory Integration、Proactive Mentor，当前重点是 Hardware Feedback 和总集成。"
        )

    if "ros" in question_lower or "ros2" in question_lower:
        return (
            f"Eric，你现在需要关注 ROS2。\n\n"
            f"你的 ROS2 当前分数是 {ros2_score}。\n"
            "你的 Arduino、Python、OpenCV 已经有基础，所以你不需要继续重复基础 Arduino。\n"
            "如果未来要做真正的机器人系统，ROS2 是下一阶段必须补上的能力。"
        )

    if "arduino" in question_lower:
        return (
            f"Eric，你的 Arduino 当前分数是 {arduino_score}。\n\n"
            "这已经是你的强项。你可以继续用 Arduino 做硬件反馈，"
            "但不建议继续停留在基础 Arduino。下一步更应该进入 ROS2、视觉、语音和系统整合。"
        )

    if "3.0" in question or "atlas 3" in question_lower:
        return (
            "Eric，Atlas 3.0 的核心成果是 Eric Digital Twin。\n\n"
            "它包括 Profile、Skill Database、Project History、Learning Planner、Emotion Memory 和 Mentor Recommendation。\n"
            "这些长期记忆现在会成为 Atlas 4.0 Memory Integration 的基础。"
        )

    if "4.0" in question or "atlas 4" in question_lower:
        return (
            "Eric，Atlas 4.0 的目标是把 Atlas 从记忆和规划助手升级为多模态导师。\n\n"
            "它包含 Vision、Voice Input、Voice Output、Memory Integration、Proactive Mentor 和 Hardware Feedback。"
        )

    if "植物" in question or "plant" in question_lower:
        return (
            "Eric，你的智能植物养护系统不是孤立项目。\n\n"
            "它训练了 Arduino、传感器、硬件接线和项目迭代能力。"
            "这些能力后来迁移到了 Atlas 的硬件反馈、摄像头检测和多模态系统设计里。"
        )

    if "历史" in question or "project history" in question_lower or "past project" in question_lower:
        return format_project_history_summary(memory)

    if "技能" in question or "skill" in question_lower:
        return format_skill_summary(memory)

    if "画像" in question or "profile" in question_lower or "who am i" in question_lower:
        return format_profile_summary(memory)

    if "计划" in question or "learning plan" in question_lower:
        return get_latest_learning_plan_text(memory)

    if "debug" in question_lower or "调试" in question or "累" in question or "卡住" in question:
        emotion_text = get_latest_emotion_text(memory)

        return (
            f"{emotion_text}\n\n"
            "如果你已经连续调试很久，Atlas 建议先休息 15 到 20 分钟，"
            "然后回来只测试一个最小问题。"
        )

    return (
        f"Eric，我已经读取了你的长期记忆。\n\n"
        f"{format_profile_summary(memory)}\n\n"
        "你可以继续问：\n"
        "1. 我下一步应该做什么？\n"
        "2. 为什么要学 ROS2？\n"
        "3. 我的项目历史是什么？\n"
        "4. 我现在的技能状态是什么？"
    )


# ============================================================
# Stage 4: Memory Integration
# ============================================================

def create_default_memory_integration_data():
    return {
        "student_name": "Eric",
        "memory_integration_version": "Atlas 4.0 Memory Integration v1",
        "memory_interactions": []
    }


def load_memory_integration_data():
    data = safe_load_json(MEMORY_INTEGRATION_DATA_FILE, create_default_memory_integration_data())

    if not isinstance(data, dict):
        data = create_default_memory_integration_data()

    data.setdefault("student_name", "Eric")
    data.setdefault("memory_integration_version", "Atlas 4.0 Memory Integration v1")
    data.setdefault("memory_interactions", [])

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


def show_memory_source():
    memory, source = load_memory()

    content = (
        f"Atlas 4.0 当前读取到的长期记忆来源：{source}\n\n"
        f"{format_profile_summary(memory)}\n\n"
        f"{format_skill_summary(memory)}\n\n"
        f"Project History 数量：{len(memory.get('project_history', []))} 个\n"
        f"Learning Plan 数量：{len(memory.get('daily_learning_plans', []))} 条\n"
        f"Emotion Memory 数量：{len(memory.get('emotion_records', []))} 条\n"
        f"Mentor Recommendation 数量：{len(memory.get('recommendations', []))} 条\n"
        f"Daily Task 数量：{len(memory.get('daily_tasks', []))} 条\n"
        f"Bug 数量：{len(memory.get('bugs', []))} 条"
    )

    print("\n长期记忆来源检测结果：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_memory_log(content)
    write_to_project_log("Atlas 4.0 Memory Integration 检测长期记忆来源", content)
    record_full_event("memory_source", content)


def answer_latest_voice_input():
    memory, source = load_memory()
    question = get_latest_voice_input_text()

    if not question:
        message = (
            "没有找到最近一次有效语音识别文本。\n"
            "请先录音并成功识别一句话；或者手动输入问题测试 Memory Integration。"
        )

        print("\n" + message)
        write_to_memory_log(message)
        write_to_project_log("Atlas 4.0 Memory Integration 读取语音失败", message)
        return ""

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
    write_to_project_log("Atlas 4.0 Memory Integration 语音问题记忆回答", content)
    record_full_event("memory_answer_latest_voice", content)

    return answer


def answer_manual_question():
    memory, source = load_memory()

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
    write_to_project_log("Atlas 4.0 Memory Integration 手动问题记忆回答", content)
    record_full_event("memory_answer_manual", content)

    return answer


def answer_question_direct(question, source_label="direct input"):
    memory, source = load_memory()
    answer = answer_question_with_memory(question, memory)

    save_memory_interaction(
        question=question,
        answer=answer,
        source=source_label + " + " + source
    )

    content = (
        f"长期记忆来源：{source}\n\n"
        f"问题：\n{question}\n\n"
        f"回答：\n{answer}"
    )

    write_to_memory_log(content)
    write_to_project_log("Atlas 4.0 Memory Integration 直接问答", content)
    record_full_event("memory_answer_direct", content)

    return answer


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
    write_to_project_log("Atlas 4.0 Memory Integration 查看最近问答记录", content)


# ============================================================
# Stage 5: Proactive Mentor
# ============================================================

def create_default_proactive_data():
    return {
        "student_name": "Eric",
        "proactive_mentor_version": "Atlas 4.0 Proactive Mentor v1",
        "proactive_records": []
    }


def load_proactive_data():
    data = safe_load_json(PROACTIVE_MENTOR_DATA_FILE, create_default_proactive_data())

    if not isinstance(data, dict):
        data = create_default_proactive_data()

    data.setdefault("student_name", "Eric")
    data.setdefault("proactive_mentor_version", "Atlas 4.0 Proactive Mentor v1")
    data.setdefault("proactive_records", [])

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
    lines = [f"从 project_log.txt 找到 {yesterday} 的记录："]

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
            "focus": "Atlas 4.0 Full Integration",
            "reason": "Vision、Voice Input、Voice Output、Memory Integration、Proactive Mentor 和 Hardware Feedback 已经分阶段建立，现在应该让它们进入同一个主程序并测试完整链路。",
            "task_1": "运行 atlas4_full_main.py。",
            "task_2": "先测试系统状态、摄像头、语音输出和硬件 PING。",
            "task_3": "最后测试 Voice → Memory → Voice Output → Hardware Feedback 完整链路。",
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
        "task_1": "检查 Stage 1 到 Stage 6 的日志。",
        "task_2": "确认每个阶段都能单独运行。",
        "task_3": "准备运行 Full Demo。",
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
    write_to_project_log("Atlas 4.0 Proactive Mentor 生成 Morning Brief", brief)
    record_full_event("morning_brief", brief)

    return brief


def generate_and_speak_morning_brief():
    memory, source = load_memory()
    brief = generate_morning_brief(memory, source)
    short_speech = build_short_speech(memory)

    spoken = speak_text(short_speech, rate=155)
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
    write_to_project_log("Atlas 4.0 Proactive Mentor 语音 Morning Brief", content)
    record_full_event("spoken_morning_brief", content)

    return brief


def show_yesterday_summary():
    memory, source = load_memory()
    content = summarize_yesterday(memory)

    print("\n昨天工作总结：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    save_proactive_record("yesterday_summary", content, source)
    write_to_proactive_log(content)
    write_to_project_log("Atlas 4.0 Proactive Mentor 昨天总结", content)


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

    save_proactive_record("today_task", content, source)
    write_to_proactive_log(content)
    write_to_project_log("Atlas 4.0 Proactive Mentor 今日任务建议", content)


def show_inactive_task_warning():
    memory, source = load_memory()
    content = check_inactive_tasks(memory)

    print("\n未推进任务提醒：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    save_proactive_record("inactive_task_warning", content, source)
    write_to_proactive_log(content)
    write_to_project_log("Atlas 4.0 Proactive Mentor 未推进任务提醒", content)


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
    write_to_project_log("Atlas 4.0 Proactive Mentor 查看最近记录", content)


# ============================================================
# Stage 6: Hardware Feedback
# ============================================================

def get_serial_ports():
    if not SERIAL_AVAILABLE:
        return []

    return list(serial.tools.list_ports.comports())


def list_serial_ports():
    if not SERIAL_AVAILABLE:
        message = "pyserial 不可用。请先运行：pip install pyserial"
        print("\n" + message)
        write_to_hardware_log(message)
        return []

    ports = get_serial_ports()

    if not ports:
        message = "没有检测到串口设备。请检查 Arduino 是否插入电脑。"
        print("\n" + message)
        write_to_hardware_log(message)
        write_to_project_log("Atlas 4.0 Hardware Feedback 串口检测", message)
        return []

    lines = ["当前检测到的串口设备："]

    print("\n当前检测到的串口设备：")
    print("-" * 70)

    for index, port in enumerate(ports):
        line = f"{index}. 端口：{port.device} | 名称：{port.description}"
        print(line)
        lines.append(line)

    print("-" * 70)

    content = "\n".join(lines)

    write_to_hardware_log(content)
    write_to_project_log("Atlas 4.0 Hardware Feedback 串口设备列表", content)

    return ports


def build_candidate_ports(preferred_port=None):
    ports = get_serial_ports()
    detected_ports = [port.device for port in ports]
    config = load_config()

    candidates = []

    if preferred_port:
        candidates.append(preferred_port)

    configured_port = config.get("serial_port", "")
    if configured_port:
        candidates.append(configured_port)

    for backup in config.get("backup_serial_ports", []):
        candidates.append(backup)

    for port_name in detected_ports:
        candidates.append(port_name)

    final_candidates = []
    seen = set()

    for item in candidates:
        if not item:
            continue

        name = str(item).strip()

        if not name:
            continue

        upper_name = name.upper()

        if upper_name not in seen:
            final_candidates.append(name)
            seen.add(upper_name)

    return final_candidates


def read_serial_lines(arduino, seconds=2.0):
    lines = []
    end_time = time.time() + seconds

    while time.time() < end_time:
        try:
            if arduino.in_waiting > 0:
                raw_line = arduino.readline()
                line = raw_line.decode("utf-8", errors="ignore").strip()

                if line:
                    lines.append(line)
                    print(f"Arduino 返回：{line}")
            else:
                time.sleep(0.05)

        except Exception as error:
            lines.append(f"READ_ERROR:{error}")
            break

    return lines


def response_contains(lines, expected_tokens):
    joined_text = "\n".join(lines)

    for token in expected_tokens:
        if token in joined_text:
            return True

    return False


def explain_serial_error(error):
    error_text = str(error)

    if "Access is denied" in error_text or "PermissionError" in error_text:
        return (
            "串口被占用。最常见原因：Arduino IDE 串口监视器、串口绘图器、"
            "另一个 Python 程序、另一个 Cursor 终端还在占用 Arduino。"
        )

    if "FileNotFoundError" in error_text or "could not open port" in error_text:
        return "这个 COM 端口不存在或已经变化。请先查看串口设备列表。"

    if "ClearCommError" in error_text or "GetOverlappedResult" in error_text:
        return "Windows 串口状态异常。建议拔掉 Arduino，等待 3 秒后重新插入，再运行程序。"

    return "未知串口错误。请检查 Arduino 是否插入、端口是否正确、是否被其他程序占用。"


def open_port(port_name):
    config = load_config()
    baud_rate = int(config.get("baud_rate", 9600))

    arduino = serial.Serial(
        port=port_name,
        baudrate=baud_rate,
        timeout=0.2,
        write_timeout=1
    )

    return arduino


def connect_arduino(preferred_port=None):
    if not SERIAL_AVAILABLE:
        message = "pyserial 没有安装。请运行：pip install pyserial"
        print("\n" + message)
        write_to_hardware_log(message)
        return None, None

    ports = get_serial_ports()

    if not ports:
        message = (
            "没有检测到任何串口设备。\n"
            "请确认：\n"
            "1. Arduino 已经插入电脑\n"
            "2. USB 数据线不是只能充电的线\n"
            "3. Windows 设备管理器里能看到 COM 端口"
        )
        print("\n" + message)
        write_to_hardware_log(message)
        write_to_project_log("Atlas 4.0 Hardware Feedback Arduino 连接失败", message)
        return None, None

    candidates = build_candidate_ports(preferred_port)

    print("\n准备自动连接 Arduino。")
    print("候选端口：")
    for item in candidates:
        print(f"- {item}")

    all_errors = []

    for port_name in candidates:
        arduino = None

        try:
            print(f"\n正在尝试连接端口：{port_name}")

            arduino = open_port(port_name)

            # Arduino UNO / Nano 打开串口后通常会自动重启。
            # 必须等待，否则 Python 可能在 Arduino 未准备好时就发指令。
            time.sleep(2.8)

            print("读取 Arduino 启动信息...")
            boot_lines = read_serial_lines(arduino, seconds=1.2)

            try:
                arduino.reset_input_buffer()
                arduino.reset_output_buffer()
            except Exception:
                pass

            print("发送握手指令：PING")
            arduino.write(b"PING\n")
            arduino.flush()

            response_lines = read_serial_lines(arduino, seconds=2.5)

            all_lines = boot_lines + response_lines

            if response_contains(all_lines, ["PONG", "OK:PING"]):
                message = (
                    f"Arduino 连接成功：{port_name}\n"
                    "握手成功：Python 已发送 PING，Arduino 已返回 PONG。"
                )

                print("\n" + message)

                save_config_value("serial_port", port_name)

                write_to_hardware_log(
                    message + "\n\nArduino 返回内容：\n" + "\n".join(all_lines)
                )

                write_to_project_log("Atlas 4.0 Hardware Feedback Arduino 连接成功", message)
                record_full_event("hardware_connected", message)

                return arduino, port_name

            detail = (
                f"{port_name} 可以打开，但没有收到 PONG。\n"
                "这说明该端口可能不是 Atlas Arduino，或者 Arduino 代码没有正确上传。\n"
                "返回内容：\n"
                + ("\n".join(all_lines) if all_lines else "无返回")
            )

            print("\n" + detail)
            all_errors.append(detail)

            try:
                arduino.close()
            except Exception:
                pass

        except Exception as error:
            reason = explain_serial_error(error)
            detail = (
                f"{port_name} 连接失败。\n"
                f"原始错误：{error}\n"
                f"判断：{reason}"
            )

            print("\n" + detail)
            all_errors.append(detail)

            if arduino is not None:
                try:
                    arduino.close()
                except Exception:
                    pass

    final_message = (
        "Arduino 自动连接失败。\n\n"
        "已经尝试过以下端口：\n"
        + "\n".join([f"- {item}" for item in candidates])
        + "\n\n详细错误：\n"
        + "\n\n".join(all_errors)
        + "\n\n最可信处理方式：\n"
        "1. 关闭 Arduino IDE 串口监视器\n"
        "2. 关闭 Arduino 串口绘图器\n"
        "3. 关闭所有正在运行的 Python / Cursor 终端\n"
        "4. 拔掉 Arduino，等待 3 秒，再插回电脑\n"
        "5. 重新运行本程序，先查看串口，再自动连接\n"
    )

    print("\n" + final_message)

    write_to_hardware_log(final_message)
    write_to_project_log("Atlas 4.0 Hardware Feedback Arduino 自动连接失败", final_message)
    record_full_event("hardware_connection_failed", final_message)

    return None, None


def close_arduino(arduino):
    if arduino is not None:
        try:
            arduino.close()
            print("\nArduino 连接已关闭。")
        except Exception:
            pass


def send_hardware_command(arduino, command):
    command = command.strip().upper()

    if command not in VALID_HARDWARE_COMMANDS:
        message = (
            f"无效指令：{command}\n"
            f"可用指令：{', '.join(VALID_HARDWARE_COMMANDS)}"
        )
        print("\n" + message)
        write_to_hardware_log(message)
        return False

    if arduino is None:
        message = "Arduino 未连接，不能发送指令。"
        print("\n" + message)
        write_to_hardware_log(message)
        return False

    try:
        print(f"\n发送硬件指令：{command}")

        try:
            arduino.reset_input_buffer()
        except Exception:
            pass

        arduino.write((command + "\n").encode("utf-8"))
        arduino.flush()

        wait_seconds = COMMAND_READ_SECONDS.get(command, 3.0)
        response_lines = read_serial_lines(arduino, seconds=wait_seconds)

        expected_tokens = EXPECTED_RESPONSES.get(command, [])
        success = response_contains(response_lines, expected_tokens)

        result = "成功" if success else "未确认成功"

        message = (
            f"已发送硬件指令：{command}\n"
            f"执行结果：{result}\n"
            f"期望返回：{expected_tokens}\n"
            "Arduino 返回内容：\n"
            + ("\n".join(response_lines) if response_lines else "无返回")
        )

        print("\n" + message)

        write_to_hardware_log(message)
        write_to_project_log("Atlas 4.0 Hardware Feedback 发送指令", message)
        record_full_event("hardware_command", message)

        return success

    except Exception as error:
        message = (
            f"发送指令失败：{error}\n"
            f"判断：{explain_serial_error(error)}"
        )

        print("\n" + message)

        write_to_hardware_log(message)
        write_to_project_log("Atlas 4.0 Hardware Feedback 发送指令失败", message)
        record_full_event("hardware_command_failed", message)

        return False


def connect_send_close(command):
    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is None:
            return False

        return send_hardware_command(arduino, command)

    finally:
        close_arduino(arduino)


def manual_set_serial_port():
    ports = list_serial_ports()

    if not ports:
        return

    choice = input("\n请输入 Arduino 对应的编号，例如 0 / 1 / 2：").strip()

    if not choice.isdigit():
        print("输入无效。")
        return

    index = int(choice)

    if index < 0 or index >= len(ports):
        print("编号超出范围。")
        return

    selected_port = ports[index].device
    save_config_value("serial_port", selected_port)

    message = f"已手动设置 Arduino 串口：{selected_port}"
    print("\n" + message)

    write_to_hardware_log(message)
    write_to_project_log("Atlas 4.0 Hardware Feedback 手动设置串口", message)


def test_single_hardware_command():
    print("\n单个指令测试。")
    print(f"可用指令：{', '.join(VALID_HARDWARE_COMMANDS)}")
    print("建议先测试：PING")
    print("然后测试：STATUS")
    print("最后测试：HAPPY / THINKING / WARNING / NOD / OFF")

    command = input("\n请输入要发送的指令：").strip().upper()

    if command not in VALID_HARDWARE_COMMANDS:
        print("指令无效。")
        return

    connect_send_close(command)


def run_basic_hardware_feedback_test():
    print("\n开始基础硬件反馈测试。")
    print("将依次发送：PING / STATUS / HAPPY / THINKING / WARNING / ERROR / NOD / OFF")

    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is None:
            return

        commands = [
            ("PING", "确认 Python 与 Arduino 是否真正连通"),
            ("STATUS", "读取 Arduino 硬件状态"),
            ("HAPPY", "任务成功 / 开心反馈"),
            ("THINKING", "Atlas 正在思考"),
            ("WARNING", "提醒 Eric 注意"),
            ("ERROR", "出现错误"),
            ("NOD", "舵机点头"),
            ("OFF", "关闭反馈")
        ]

        lines = []

        for command, description in commands:
            line = f"{command} - {description}"
            print("\n测试：" + line)
            lines.append(line)

            send_hardware_command(arduino, command)
            time.sleep(0.8)

        content = (
            "基础硬件反馈测试完成。\n"
            "已测试：\n"
            + "\n".join(lines)
        )

        write_to_hardware_log(content)
        write_to_project_log("Atlas 4.0 Hardware Feedback 基础测试完成", content)

    finally:
        close_arduino(arduino)


def run_full_hardware_test():
    print("\n开始 Arduino 全硬件 TEST。")
    print("将发送 TEST，让 Arduino 自动测试绿灯、黄灯、红灯、舵机、OLED。")
    connect_send_close("TEST")


def run_atlas_scene_hardware_test():
    print("\n开始 Atlas 场景反馈测试。")
    print("这一步模拟 Atlas 4.0 的真实使用场景。")

    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is None:
            return

        scenes = [
            ("THINKING", "Atlas 正在读取 Eric 的长期记忆。"),
            ("HAPPY", "Atlas 成功生成 Morning Brief。"),
            ("NOD", "Atlas 点头确认今天任务。"),
            ("WARNING", "Atlas 发现任务长期未推进，提醒 Eric。"),
            ("HAPPY", "Eric 完成一个最小测试，Atlas 给出成功反馈。"),
            ("OFF", "测试结束，关闭硬件反馈。")
        ]

        lines = []

        for command, description in scenes:
            line = f"{description} → 发送 {command}"
            print("\n" + line)
            lines.append(line)

            send_hardware_command(arduino, command)
            time.sleep(1.0)

        content = "Atlas 4.0 场景反馈测试完成。\n\n" + "\n".join(lines)

        write_to_hardware_log(content)
        write_to_project_log("Atlas 4.0 Hardware Feedback 场景测试完成", content)

    finally:
        close_arduino(arduino)


# ============================================================
# Integrated demos
# ============================================================

def run_morning_brief_with_voice_and_hardware():
    print("\n开始完整 Demo：Morning Brief + Voice Output + Hardware Feedback")
    print("流程：Hardware THINKING → 生成 Morning Brief → 语音播放 → Hardware HAPPY + NOD → OFF")

    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is not None:
            send_hardware_command(arduino, "THINKING")

        memory, source = load_memory()
        brief = generate_morning_brief(memory, source)
        short_speech = build_short_speech(memory)

        save_proactive_record("full_demo_morning_brief", brief, source)

        print("\n完整 Morning Brief：")
        print("-" * 70)
        print(brief)
        print("-" * 70)

        spoken = speak_text(short_speech, rate=155)

        if arduino is not None:
            if spoken:
                send_hardware_command(arduino, "HAPPY")
                send_hardware_command(arduino, "NOD")
            else:
                send_hardware_command(arduino, "WARNING")

            send_hardware_command(arduino, "OFF")

        content = (
            f"完整 Demo 完成。\n"
            f"记忆来源：{source}\n"
            f"语音状态：{'spoken' if spoken else 'text_only'}\n\n"
            f"Morning Brief：\n{brief}"
        )

        write_to_proactive_log(content)
        write_to_project_log("Atlas 4.0 Full Demo：Morning Brief + Voice + Hardware", content)
        record_full_event("full_demo_morning_brief_voice_hardware", content)

    finally:
        close_arduino(arduino)


def run_voice_memory_voice_hardware_chain():
    print("\n开始完整链路 Demo：Voice Input → Memory Integration → Voice Output → Hardware Feedback")
    print("流程：录音 → 转文字 → 长期记忆回答 → 语音输出 → Arduino 硬件反馈")

    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is not None:
            send_hardware_command(arduino, "THINKING")

        question = record_and_recognize_once()

        if not question:
            print("\n没有得到有效语音文本，改为手动输入问题。")
            question = input("请输入 Eric 的问题，例如：我下一步应该做什么？").strip()

        if not question:
            question = "我下一步应该做什么？"

        answer = answer_question_direct(question, source_label="voice/full chain")

        print("\nAtlas 回答：")
        print("-" * 70)
        print(answer)
        print("-" * 70)

        spoken = speak_text(answer, rate=155)

        if arduino is not None:
            if spoken:
                send_hardware_command(arduino, "HAPPY")
                send_hardware_command(arduino, "NOD")
            else:
                send_hardware_command(arduino, "WARNING")

            send_hardware_command(arduino, "OFF")

        content = (
            "完整链路 Demo 完成。\n\n"
            f"问题：{question}\n\n"
            f"回答：{answer}\n\n"
            f"语音状态：{'spoken' if spoken else 'text_only'}"
        )

        write_to_project_log("Atlas 4.0 Full Chain：Voice → Memory → Voice → Hardware", content)
        record_full_event("full_chain_voice_memory_voice_hardware", content)

    finally:
        close_arduino(arduino)


def run_proactive_mentor_hardware_demo():
    print("\n开始 Proactive Mentor + Hardware Feedback Demo。")
    print("这一步模拟第五阶段主动导师和第六阶段硬件反馈的连接。")

    arduino = None

    try:
        arduino, port_name = connect_arduino()

        if arduino is None:
            return

        steps = [
            ("THINKING", "Atlas 正在思考今天的任务。"),
            ("HAPPY", "Atlas 生成主动导师 Morning Brief 成功。"),
            ("NOD", "Atlas 点头确认：今天先完成一个最小测试。"),
            ("WARNING", "Atlas 提醒：不要一次增加太多功能。"),
            ("OFF", "硬件反馈结束。")
        ]

        lines = []

        for command, description in steps:
            line = f"{description} → {command}"
            print("\n" + line)
            lines.append(line)

            send_hardware_command(arduino, command)
            time.sleep(1.0)

        content = "Proactive Mentor + Hardware Feedback Demo 完成。\n\n" + "\n".join(lines)

        write_to_hardware_log(content)
        write_to_project_log("Atlas 4.0 Proactive Mentor + Hardware Feedback Demo", content)
        record_full_event("proactive_hardware_demo", content)

    finally:
        close_arduino(arduino)


# ============================================================
# Config menu
# ============================================================

def configure_tts():
    config = load_config()
    print(f"\n当前 TTS 语速：{config.get('tts_rate')}")
    print(f"当前 TTS 音量：{config.get('tts_volume')}")

    rate_text = input("输入新语速，建议 150-180，回车不修改：").strip()
    if rate_text.isdigit():
        rate = int(rate_text)
        rate = max(80, min(260, rate))
        save_config_value("tts_rate", rate)
        print(f"已保存 TTS 语速：{rate}")

    volume_text = input("输入新音量 0.0-1.0，回车不修改：").strip()
    if volume_text:
        try:
            volume = float(volume_text)
            volume = max(0, min(1, volume))
            save_config_value("tts_volume", volume)
            print(f"已保存 TTS 音量：{volume}")
        except Exception:
            print("音量输入无效。")


def show_current_config():
    config = load_config()
    print("\n当前 atlas4_config.json：")
    print("-" * 70)
    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("-" * 70)


# ============================================================
# Menus
# ============================================================

def show_intro():
    print("\n==============================")
    print("Atlas 4.0 Full Main")
    print("Single-file Integrated Version")
    print("==============================")
    print("包含：Vision / Voice Input / Voice Output / Memory Integration / Proactive Mentor / Hardware Feedback")
    print("重点：先单项测试，再运行完整 Demo。")
    print(f"程序文件夹：{BASE_DIR}")
    print("==============================")


def config_menu():
    while True:
        print("\n配置菜单：")
        print("1. 查看当前配置")
        print("2. 查看电脑串口设备")
        print("3. 手动选择 Arduino 串口")
        print("4. 自动连接 Arduino，并用 PING/PONG 验证")
        print("5. 设置摄像头编号 camera_index")
        print("6. 查看电脑可用语音列表")
        print("7. 设置 TTS 语速和音量")
        print("8. 返回主菜单")

        choice = input("请输入数字 1-8：").strip()

        if choice == "1":
            show_current_config()

        elif choice == "2":
            list_serial_ports()

        elif choice == "3":
            manual_set_serial_port()

        elif choice == "4":
            arduino = None
            try:
                arduino, port_name = connect_arduino()
                if arduino is not None:
                    print(f"\n最终确认：Arduino 已连接，端口：{port_name}")
            finally:
                close_arduino(arduino)

        elif choice == "5":
            set_camera_index()

        elif choice == "6":
            list_voices()

        elif choice == "7":
            configure_tts()

        elif choice == "8":
            break

        else:
            print("输入无效。")


def vision_menu():
    while True:
        print("\nStage 1 Vision 菜单：")
        print("1. 测试摄像头是否能打开")
        print("2. 启动 Eric 是否在场检测")
        print("3. 设置摄像头编号 camera_index")
        print("4. 返回主菜单")

        choice = input("请输入数字 1-4：").strip()

        if choice == "1":
            test_camera_once()
        elif choice == "2":
            start_vision_detection()
        elif choice == "3":
            set_camera_index()
        elif choice == "4":
            break
        else:
            print("输入无效。")


def voice_input_menu():
    while True:
        print("\nStage 2 Voice Input 菜单：")
        print("1. 查看电脑音频设备")
        print("2. 录音一次并转换成文字")
        print("3. 连续语音识别测试")
        print("4. 查看最近语音识别记录")
        print("5. 返回主菜单")

        choice = input("请输入数字 1-5：").strip()

        if choice == "1":
            list_audio_devices()
        elif choice == "2":
            record_and_recognize_once()
        elif choice == "3":
            continuous_voice_test()
        elif choice == "4":
            show_recent_voice_records()
        elif choice == "5":
            break
        else:
            print("输入无效。")


def voice_output_menu():
    while True:
        print("\nStage 3 Voice Output 菜单：")
        print("1. 查看电脑可用语音列表")
        print("2. 测试英文语音输出")
        print("3. 测试中文语音输出")
        print("4. 自定义让 Atlas 说一句话")
        print("5. Atlas 问候语 Greeting")
        print("6. Atlas 任务提醒 Task Reminder")
        print("7. Atlas Debug 提醒")
        print("8. 查看最近 Voice Output 记录")
        print("9. 返回主菜单")

        choice = input("请输入数字 1-9：").strip()

        if choice == "1":
            list_voices()
        elif choice == "2":
            test_basic_speech()
        elif choice == "3":
            test_chinese_speech()
        elif choice == "4":
            custom_speech()
        elif choice == "5":
            atlas_greeting()
        elif choice == "6":
            atlas_task_reminder()
        elif choice == "7":
            atlas_debug_reminder()
        elif choice == "8":
            show_recent_voice_output_records()
        elif choice == "9":
            break
        else:
            print("输入无效。")


def memory_menu():
    while True:
        print("\nStage 4 Memory Integration 菜单：")
        print("1. 检测 Atlas 3.0 / 综合长期记忆来源")
        print("2. 读取最近一次语音识别文本，并根据长期记忆回答")
        print("3. 手动输入问题，并根据长期记忆回答")
        print("4. 查看最近 Memory Integration 问答记录")
        print("5. 返回主菜单")

        choice = input("请输入数字 1-5：").strip()

        if choice == "1":
            show_memory_source()
        elif choice == "2":
            answer_latest_voice_input()
        elif choice == "3":
            answer_manual_question()
        elif choice == "4":
            show_recent_memory_interactions()
        elif choice == "5":
            break
        else:
            print("输入无效。")


def proactive_menu():
    while True:
        print("\nStage 5 Proactive Mentor 菜单：")
        print("1. 检测长期记忆来源")
        print("2. 生成主动导师 Morning Brief")
        print("3. 生成并语音播放 Morning Brief")
        print("4. 只查看昨天工作总结")
        print("5. 只查看今天任务建议")
        print("6. 检查长期未推进任务")
        print("7. 查看最近 Proactive Mentor 记录")
        print("8. Proactive Mentor + Hardware Feedback Demo")
        print("9. 返回主菜单")

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
            run_proactive_mentor_hardware_demo()
        elif choice == "9":
            break
        else:
            print("输入无效。")


def hardware_menu():
    while True:
        print("\nStage 6 Hardware Feedback 菜单：")
        print("1. 查看电脑串口设备")
        print("2. 自动连接 Arduino，并用 PING/PONG 验证")
        print("3. 手动选择 Arduino 串口，并保存到 atlas4_config.json")
        print("4. 发送单个硬件指令")
        print("5. 基础硬件反馈测试")
        print("6. Arduino 全硬件 TEST")
        print("7. Atlas 场景反馈测试")
        print("8. Proactive Mentor + Hardware Feedback Demo")
        print("9. 返回主菜单")

        choice = input("请输入数字 1-9：").strip()

        if choice == "1":
            list_serial_ports()

        elif choice == "2":
            arduino = None
            try:
                arduino, port_name = connect_arduino()
                if arduino is not None:
                    print(f"\n最终确认：Arduino 已连接，端口：{port_name}")
            finally:
                close_arduino(arduino)

        elif choice == "3":
            manual_set_serial_port()

        elif choice == "4":
            test_single_hardware_command()

        elif choice == "5":
            run_basic_hardware_feedback_test()

        elif choice == "6":
            run_full_hardware_test()

        elif choice == "7":
            run_atlas_scene_hardware_test()

        elif choice == "8":
            run_proactive_mentor_hardware_demo()

        elif choice == "9":
            break

        else:
            print("输入无效。")


def show_main_menu():
    print("\n请选择功能：")
    print("1. 系统状态总览")
    print("2. 配置菜单：串口 / 摄像头 / 语音")
    print("3. Stage 1 Vision：摄像头检测 Eric 是否在场")
    print("4. Stage 2 Voice Input：录音并转文字")
    print("5. Stage 3 Voice Output：文字转语音")
    print("6. Stage 4 Memory Integration：长期记忆问答")
    print("7. Stage 5 Proactive Mentor：主动导师")
    print("8. Stage 6 Hardware Feedback：Arduino 硬件反馈")
    print("9. 完整 Demo：Morning Brief + Voice Output + Hardware Feedback")
    print("10. 完整链路：Voice Input → Memory → Voice Output → Hardware")
    print("11. 测试所有日志写入")
    print("12. 退出")


def main():
    show_intro()

    load_config()

    write_to_project_log(
        "Atlas 4.0 Full Main 程序启动",
        "Atlas 4.0 六阶段整合版主程序已启动。"
    )

    record_full_event("program_start", "Atlas 4.0 Full Main started.")

    while True:
        show_main_menu()

        choice = input("请输入数字 1-12：").strip()

        if choice == "1":
            show_system_status()

        elif choice == "2":
            config_menu()

        elif choice == "3":
            vision_menu()

        elif choice == "4":
            voice_input_menu()

        elif choice == "5":
            voice_output_menu()

        elif choice == "6":
            memory_menu()

        elif choice == "7":
            proactive_menu()

        elif choice == "8":
            hardware_menu()

        elif choice == "9":
            run_morning_brief_with_voice_and_hardware()

        elif choice == "10":
            run_voice_memory_voice_hardware_chain()

        elif choice == "11":
            test_all_logs()

        elif choice == "12":
            write_to_project_log(
                "Atlas 4.0 Full Main 程序退出",
                "Atlas 4.0 六阶段整合版主程序已退出。"
            )
            record_full_event("program_exit", "Atlas 4.0 Full Main exited.")
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 12。")


# ============================================================
# Atlas All Versions Master Integration Layer
# Atlas 1.0 + 2.0 + 3.0 + 4.0
# ============================================================

ALL_VERSIONS_NAME = "Atlas Unified 1.0 + 2.0 + 3.0 + 4.0"
ALL_VERSIONS_DATA_FILE = DATA_FILE


def ensure_all_versions_data(data):
    """Ensure the unified database contains Atlas 1.0, 2.0, 3.0 and 4.0 records."""
    data = ensure_data_fields(data)
    data["atlas_version"] = ALL_VERSIONS_NAME
    data["database_version"] = "Atlas All Versions Unified Database v1"

    profile = data.get("profile", {})
    if isinstance(profile, dict):
        profile.setdefault("name", "Eric")
        profile.setdefault("goal", "AI Systems Engineer")
        profile.setdefault("current_project", "Atlas")
        profile["current_version"] = ALL_VERSIONS_NAME
        data["profile"] = profile

    project_names = []
    for project in data.get("projects", []):
        if isinstance(project, dict):
            project_names.append(project.get("name", project.get("project_name", "")))

    def project_exists(keyword):
        return any(keyword in name for name in project_names)

    if not project_exists("Atlas 4.0"):
        data["projects"].append({
            "id": get_next_id(data.get("projects", [])),
            "name": "Atlas 4.0",
            "status": "开发中",
            "progress": 90,
            "category": "Multimodal AI Mentor Robot",
            "description": "Vision、Voice Input、Voice Output、Memory Integration、Proactive Mentor、Hardware Feedback 六阶段整合。",
            "next_step": "测试全链路 Demo：Voice Input → Memory → Voice Output → Hardware Feedback。"
        })

    history_names = []
    for item in data.get("project_history", []):
        if isinstance(item, dict):
            history_names.append(item.get("project_name", ""))

    def history_exists(keyword):
        return any(keyword in name for name in history_names)

    if not history_exists("Atlas 4.0"):
        data["project_history"].append({
            "id": get_next_id(data.get("project_history", [])),
            "project_name": "Atlas 4.0",
            "version": "4.0",
            "status": "in_progress",
            "project_type": "Multimodal AI Mentor Robot",
            "main_goal": "Upgrade Atlas into a multimodal mentor robot that can see, hear, speak, remember, proactively advise, and control hardware feedback.",
            "skills_learned": [
                "OpenCV Vision",
                "Voice Input",
                "Voice Output",
                "Memory Integration",
                "Proactive Mentor",
                "Serial Communication",
                "Arduino Hardware Feedback"
            ],
            "key_problems": [
                "Need to integrate six separate Stage 4.0 files into one main program",
                "Need robust Arduino serial connection with PING/PONG validation",
                "Need all version functions under one master menu"
            ],
            "transfer_to_atlas": "Atlas 4.0 connects the earlier project management and digital twin system with real multimodal interaction and physical hardware feedback.",
            "evidence": "atlas4_full_main.py, atlas4_config.json, hardware_feedback_log.txt, voice logs, vision logs, proactive mentor records"
        })

    save_data(data)
    return data


def load_all_versions_data():
    data = load_data()
    return ensure_all_versions_data(data)


def show_atlas1_overview(data):
    """Atlas 1.0 was the basic AI mentor robot foundation."""
    lines = []
    lines.append("Atlas 1.0 基础能力总览")
    lines.append("")
    lines.append("定位：AI Research Mentor Robot 基础版。")
    lines.append("核心能力：长期记忆雏形、Project Log、导师建议、情绪支持、摄像头基础检测、Arduino/OLED/硬件反馈基础。")
    lines.append("")
    lines.append("在当前总程序里，Atlas 1.0 不再单独作为旧代码运行，而是被整理为以下基础入口：")
    lines.append("1. Project Log 写入测试")
    lines.append("2. 基础导师问候 / 机器人身份回答")
    lines.append("3. 摄像头基础测试")
    lines.append("4. Arduino PING / STATUS 基础通信测试")
    lines.append("5. 项目历史中的 Atlas 1.0 证据记录")
    lines.append("")
    lines.append("项目历史摘录：")

    matched = []
    for project in data.get("project_history", []):
        name = project.get("project_name", "")
        if "Atlas 1" in name or "AI Research Mentor" in name:
            matched.append(project)

    if not matched:
        lines.append("- 没有在 project_history 中找到 Atlas 1.0 记录。")
    else:
        for project in matched:
            lines.append(f"- {project.get('project_name', '')} | 版本：{project.get('version', '')} | 状态：{project.get('status', '')}")
            lines.append(f"  目标：{project.get('main_goal', project.get('transfer_to_atlas', ''))}")
            lines.append(f"  证据：{project.get('evidence', '暂无')}")

    content = "\n".join(lines)
    print("\n" + "-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas 1.0 基础能力总览", content)


def atlas1_project_log_test():
    content = (
        "Atlas 1.0 Project Log 基础测试。\n"
        "如果这条记录能写入 project_log.txt，说明 Atlas 最基础的研发记录能力正常。"
    )
    write_to_project_log("Atlas 1.0 Project Log 测试", content)


def atlas1_basic_mentor_reply(data):
    print("\nAtlas 1.0 基础导师回答：")
    print("-" * 70)
    robot_profile_intro(data)
    print("-" * 70)


def atlas1_basic_camera_test():
    print("\nAtlas 1.0 摄像头基础测试。")
    test_camera_once()


def atlas1_basic_hardware_test():
    print("\nAtlas 1.0 Arduino 基础通信测试。")
    print("将依次测试 PING 和 STATUS。")
    arduino = None
    try:
        arduino, port_name = connect_arduino()
        if arduino is None:
            return
        send_hardware_command(arduino, "PING")
        send_hardware_command(arduino, "STATUS")
    finally:
        close_arduino(arduino)


def atlas1_menu(data):
    while True:
        print("\nAtlas 1.0 基础机器人菜单：")
        print("1. 查看 Atlas 1.0 基础能力总览")
        print("2. 测试 Project Log 写入")
        print("3. 基础导师身份回答")
        print("4. 摄像头基础测试")
        print("5. Arduino 基础 PING / STATUS 测试")
        print("6. Atlas 语音问候 Greeting")
        print("7. 返回主菜单")

        choice = input("请输入数字 1-7：").strip()

        if choice == "1":
            show_atlas1_overview(data)
        elif choice == "2":
            atlas1_project_log_test()
        elif choice == "3":
            atlas1_basic_mentor_reply(data)
        elif choice == "4":
            atlas1_basic_camera_test()
        elif choice == "5":
            atlas1_basic_hardware_test()
        elif choice == "6":
            atlas_greeting()
        elif choice == "7":
            break
        else:
            print("输入无效。")


def atlas2_menu(data):
    while True:
        print("\nAtlas 2.0 项目管理菜单：")
        print("1. Project Database 项目总览")
        print("2. 更新 Atlas 2.0 进度")
        print("3. 创建或更新 Daily Task")
        print("4. 查看今日 Daily Task")
        print("5. 复盘 Daily Task")
        print("6. 新增 Bug")
        print("7. 查看 / 搜索 Bug")
        print("8. 更新 Bug 状态")
        print("9. Bug 总结")
        print("10. 生成 Weekly Report")
        print("11. 查看最新 Weekly Report")
        print("12. 返回主菜单")

        choice = input("请输入数字 1-12：").strip()

        if choice == "1":
            show_project_database(data)
        elif choice == "2":
            update_atlas2_progress(data)
        elif choice == "3":
            create_or_update_daily_task(data)
        elif choice == "4":
            show_today_daily_task(data)
        elif choice == "5":
            review_daily_task(data)
        elif choice == "6":
            add_bug(data)
        elif choice == "7":
            show_or_search_bugs(data)
        elif choice == "8":
            update_bug_status(data)
        elif choice == "9":
            show_bug_summary(data)
        elif choice == "10":
            generate_weekly_report(data)
        elif choice == "11":
            show_latest_weekly_report(data)
        elif choice == "12":
            break
        else:
            print("输入无效。")

        data = ensure_all_versions_data(data)


def atlas3_menu(data):
    while True:
        print("\nAtlas 3.0 Digital Twin 菜单：")
        print("1. 查看 Eric Profile")
        print("2. 机器人身份回答")
        print("3. 更新 Eric Profile")
        print("4. 查看 Skill Database")
        print("5. 下一步学习建议")
        print("6. 更新技能分数")
        print("7. 查看 Project History")
        print("8. 项目迁移建议")
        print("9. 开机主动提醒")
        print("10. 生成今日 Learning Plan")
        print("11. 查看今日 Learning Plan")
        print("12. 解释 Learning Planner 判断逻辑")
        print("13. 复盘 Learning Plan")
        print("14. 新增 Emotion Memory")
        print("15. 查看最近 Emotion Memory")
        print("16. Emotion Memory 总结")
        print("17. Emotion Memory 提醒")
        print("18. 生成 Mentor Recommendation")
        print("19. 查看最新 Mentor Recommendation")
        print("20. 解释 Mentor Recommendation 逻辑")
        print("21. 返回主菜单")

        choice = input("请输入数字 1-21：").strip()

        if choice == "1":
            show_profile(data)
        elif choice == "2":
            robot_profile_intro(data)
        elif choice == "3":
            update_profile(data)
        elif choice == "4":
            show_skill_database(data)
        elif choice == "5":
            show_next_learning_advice(data)
        elif choice == "6":
            update_skill(data)
        elif choice == "7":
            show_project_history(data)
        elif choice == "8":
            show_transfer_advice(data)
        elif choice == "9":
            show_morning_message(data)
        elif choice == "10":
            generate_learning_plan(data)
        elif choice == "11":
            show_today_learning_plan(data)
        elif choice == "12":
            show_learning_logic(data)
        elif choice == "13":
            review_learning_plan(data)
        elif choice == "14":
            add_emotion_record(data)
        elif choice == "15":
            show_emotion_records(data)
        elif choice == "16":
            show_emotion_summary(data)
        elif choice == "17":
            show_emotion_reminder(data)
        elif choice == "18":
            generate_mentor_recommendation(data)
        elif choice == "19":
            show_latest_recommendation(data)
        elif choice == "20":
            show_recommendation_logic(data)
        elif choice == "21":
            break
        else:
            print("输入无效。")

        data = ensure_all_versions_data(data)


def atlas4_menu():
    while True:
        print("\nAtlas 4.0 多模态机器人菜单：")
        print("1. 系统状态总览")
        print("2. 配置菜单：串口 / 摄像头 / 语音")
        print("3. Stage 1 Vision：摄像头检测 Eric 是否在场")
        print("4. Stage 2 Voice Input：录音并转文字")
        print("5. Stage 3 Voice Output：文字转语音")
        print("6. Stage 4 Memory Integration：长期记忆问答")
        print("7. Stage 5 Proactive Mentor：主动导师")
        print("8. Stage 6 Hardware Feedback：Arduino 硬件反馈")
        print("9. 完整 Demo：Morning Brief + Voice Output + Hardware Feedback")
        print("10. 完整链路：Voice Input → Memory → Voice Output → Hardware")
        print("11. 返回主菜单")

        choice = input("请输入数字 1-11：").strip()

        if choice == "1":
            show_system_status()
        elif choice == "2":
            config_menu()
        elif choice == "3":
            vision_menu()
        elif choice == "4":
            voice_input_menu()
        elif choice == "5":
            voice_output_menu()
        elif choice == "6":
            memory_menu()
        elif choice == "7":
            proactive_menu()
        elif choice == "8":
            hardware_menu()
        elif choice == "9":
            run_morning_brief_with_voice_and_hardware()
        elif choice == "10":
            run_voice_memory_voice_hardware_chain()
        elif choice == "11":
            break
        else:
            print("输入无效。")


def show_all_versions_overview(data):
    content = (
        f"总程序：{ALL_VERSIONS_NAME}\n"
        f"总数据库文件：{ALL_VERSIONS_DATA_FILE}\n"
        f"学生：{data.get('student_name', 'Eric')}\n"
        f"当前版本：{data.get('atlas_version', ALL_VERSIONS_NAME)}\n"
        f"数据库版本：{data.get('database_version', '')}\n\n"
        "版本能力：\n"
        "- Atlas 1.0：基础 AI Mentor Robot、Project Log、基础导师回答、摄像头/硬件基础能力。\n"
        "- Atlas 2.0：Project Database、Daily Task、Bug Manager、Weekly Report。\n"
        "- Atlas 3.0：Eric Profile、Skill Database、Project History、Learning Planner、Emotion Memory、Mentor Recommendation。\n"
        "- Atlas 4.0：Vision、Voice Input、Voice Output、Memory Integration、Proactive Mentor、Hardware Feedback。\n\n"
        f"数据统计：\n"
        f"- projects：{len(data.get('projects', []))} 个\n"
        f"- daily_tasks：{len(data.get('daily_tasks', []))} 条\n"
        f"- bugs：{len(data.get('bugs', []))} 条\n"
        f"- weekly_reports：{len(data.get('weekly_reports', []))} 份\n"
        f"- skills：{len(data.get('skills', {}))} 项\n"
        f"- project_history：{len(data.get('project_history', []))} 个\n"
        f"- daily_learning_plans：{len(data.get('daily_learning_plans', []))} 条\n"
        f"- emotion_records：{len(data.get('emotion_records', []))} 条\n"
        f"- recommendations：{len(data.get('recommendations', []))} 条"
    )

    print("\nAtlas 1.0 + 2.0 + 3.0 + 4.0 总览：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    write_to_project_log("Atlas 全版本总览", content)
    record_full_event("all_versions_overview", content)


def run_all_versions_demo(data):
    print("\n开始 Atlas 1.0 + 2.0 + 3.0 + 4.0 一键总 Demo。")
    print("这一步会展示文字版总能力，不强制打开摄像头、不强制录音。")

    lines = []
    lines.append("Atlas All Versions Demo")
    lines.append("")
    lines.append("一、Atlas 1.0 基础机器人")
    lines.append("- Project Log：可记录研发过程。")
    lines.append("- Basic Mentor：可基于 Eric 画像进行基础回答。")
    lines.append("- Camera / Arduino：作为基础感知与硬件反馈入口。")
    lines.append("")
    lines.append("二、Atlas 2.0 项目管理")
    lines.append(get_project_summary_text(data))
    lines.append("")
    lines.append("三、Atlas 3.0 Digital Twin")
    lines.append(profile_identity_text(data))
    lines.append("")
    lines.append(skill_summary_text(data))
    lines.append("")
    lines.append("四、Atlas 4.0 多模态导师")
    memory, source = load_memory()
    brief = generate_morning_brief(memory, source)
    lines.append(brief)
    lines.append("")
    lines.append("五、总判断")
    lines.append("当前总程序已把 1.0 基础机器人、2.0 项目管理、3.0 数字画像、4.0 多模态交互整合到一个主程序。")

    content = "\n".join(lines)
    print("\n" + "=" * 70)
    print(content)
    print("=" * 70)

    write_to_project_log("Atlas 1.0 + 2.0 + 3.0 + 4.0 一键总 Demo", content)
    record_full_event("all_versions_demo", content)

    speak_choice = input("\n是否语音播放简短总结？输入 y 播放，直接回车跳过：").strip().lower()
    if speak_choice == "y":
        speak_text(
            "Hello Eric. This is Atlas. Version one, two, three, and four are now integrated into one main program. Please test one function at a time.",
            rate=155
        )

    hardware_choice = input("是否发送 Arduino HAPPY + NOD 硬件反馈？输入 y 发送，直接回车跳过：").strip().lower()
    if hardware_choice == "y":
        arduino = None
        try:
            arduino, port_name = connect_arduino()
            if arduino is not None:
                send_hardware_command(arduino, "HAPPY")
                send_hardware_command(arduino, "NOD")
                send_hardware_command(arduino, "OFF")
        finally:
            close_arduino(arduino)


def test_all_versions_logs():
    data = load_all_versions_data()
    content = (
        "Atlas 全版本日志测试。\n"
        "如果你能看到这段记录，说明 1.0/2.0/3.0/4.0 总主程序的日志系统正常。"
    )
    write_to_project_log("Atlas 全版本日志测试", content)
    write_to_vision_log(content)
    write_to_voice_input_log(content)
    write_to_voice_output_log(content)
    write_to_memory_log(content)
    write_to_proactive_log(content)
    write_to_hardware_log(content)
    record_full_event("all_versions_log_test", content)
    show_all_versions_overview(data)


def show_all_versions_intro(data):
    profile = data.get("profile", {})
    print("\n==============================")
    print("Atlas All Versions Main Program")
    print("Atlas 1.0 + 2.0 + 3.0 + 4.0 总整合版")
    print("==============================")
    print(f"学生：{profile.get('name', 'Eric')}")
    print(f"目标：{profile.get('goal', '')}")
    print(f"当前项目：{profile.get('current_project', 'Atlas')}")
    print(f"当前版本：{profile.get('current_version', ALL_VERSIONS_NAME)}")
    print(f"总数据库文件：{ALL_VERSIONS_DATA_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")
    print("功能：1.0 Basic Robot + 2.0 Project Management + 3.0 Digital Twin + 4.0 Multimodal Robot")
    print("==============================")


def show_all_versions_main_menu():
    print("\n请选择功能：")
    print("1. Atlas 全版本总览")
    print("2. Atlas 1.0：基础机器人功能")
    print("3. Atlas 2.0：项目管理功能")
    print("4. Atlas 3.0：Digital Twin 导师功能")
    print("5. Atlas 4.0：视觉 / 语音 / 记忆 / 主动导师 / 硬件反馈")
    print("6. 配置菜单：串口 / 摄像头 / 语音")
    print("7. 一键总 Demo：展示 1.0 + 2.0 + 3.0 + 4.0")
    print("8. 完整链路 Demo：Voice Input → Memory → Voice Output → Hardware")
    print("9. 测试所有日志写入")
    print("10. 退出")


def main():
    data = load_all_versions_data()
    load_config()
    show_all_versions_intro(data)

    write_to_project_log(
        "Atlas 全版本总主程序启动",
        "atlas_all_versions_main.py 已启动，包含 Atlas 1.0、2.0、3.0、4.0 的主要功能。"
    )
    record_full_event("all_versions_program_start", "Atlas All Versions Main started.")

    print("\n机器人开机主动提醒：")
    print("-" * 70)
    print(morning_message_text(data))
    print("-" * 70)

    while True:
        data = load_all_versions_data()
        show_all_versions_main_menu()
        choice = input("请输入数字 1-10：").strip()

        if choice == "1":
            show_all_versions_overview(data)
        elif choice == "2":
            atlas1_menu(data)
        elif choice == "3":
            atlas2_menu(data)
        elif choice == "4":
            atlas3_menu(data)
        elif choice == "5":
            atlas4_menu()
        elif choice == "6":
            config_menu()
        elif choice == "7":
            run_all_versions_demo(data)
        elif choice == "8":
            run_voice_memory_voice_hardware_chain()
        elif choice == "9":
            test_all_versions_logs()
        elif choice == "10":
            write_to_project_log(
                "Atlas 全版本总主程序退出",
                "atlas_all_versions_main.py 已退出。"
            )
            record_full_event("all_versions_program_exit", "Atlas All Versions Main exited.")
            print("\n程序已退出。")
            break
        else:
            print("输入无效，请输入 1 到 10。")
            write_to_project_log("Atlas 全版本无效输入", f"用户输入了无效菜单数字：{choice}")


if __name__ == "__main__":
    main()
