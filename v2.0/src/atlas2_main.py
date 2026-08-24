import json
from datetime import datetime, date, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "atlas2_data.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"
WEEKLY_REPORT_TXT_FILE = BASE_DIR / "weekly_report.txt"

OLD_PROJECTS_FILE = BASE_DIR / "projects.json"
OLD_TASKS_FILE = BASE_DIR / "daily_tasks.json"
OLD_BUGS_FILE = BASE_DIR / "bugs.json"
OLD_WEEKLY_REPORTS_FILE = BASE_DIR / "weekly_reports.json"


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
    current_date = parse_date(date_text)

    if current_date is None:
        return False

    return week_start <= current_date <= week_end


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
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(PROJECT_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 project_log.txt")
    print(f"日志文件位置：{PROJECT_LOG_FILE}")


def write_to_weekly_report_txt(content):
    text = (
        "\n" + "=" * 70 + "\n"
        "Atlas 2.0 Weekly Report\n"
        f"生成时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(WEEKLY_REPORT_TXT_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 weekly_report.txt")
    print(f"周报文件位置：{WEEKLY_REPORT_TXT_FILE}")


def create_default_data():
    return {
        "student_name": "Eric",
        "atlas_version": "Atlas 2.0",
        "database_version": "Atlas 2.0 Unified Database v1",
        "projects": [
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
                "next_step": "整理最终 Demo 视频和项目说明。"
            },
            {
                "id": 3,
                "name": "Atlas 2.0",
                "status": "完成",
                "progress": 100,
                "category": "Project Management Robot",
                "description": "目标是让机器人学会管理项目、每日任务、Bug 和周报。",
                "next_step": "整理 Atlas 2.0 Demo 视频、Version Note 和下一版本规划。"
            }
        ],
        "daily_tasks": [],
        "bugs": [],
        "weekly_reports": []
    }


def migrate_old_data_if_needed():
    default_data = create_default_data()

    if DATA_FILE.exists():
        data = safe_load_json(DATA_FILE, default_data)
        return ensure_data_fields(data)

    data = default_data

    if OLD_PROJECTS_FILE.exists():
        old_projects_data = safe_load_json(OLD_PROJECTS_FILE, {})
        old_projects = old_projects_data.get("projects", [])

        if old_projects:
            data["projects"] = old_projects

    if OLD_TASKS_FILE.exists():
        old_tasks_data = safe_load_json(OLD_TASKS_FILE, {})
        old_tasks = old_tasks_data.get("daily_tasks", [])

        if old_tasks:
            data["daily_tasks"] = old_tasks

    if OLD_BUGS_FILE.exists():
        old_bugs_data = safe_load_json(OLD_BUGS_FILE, {})
        old_bugs = old_bugs_data.get("bugs", [])

        if old_bugs:
            data["bugs"] = old_bugs

    if OLD_WEEKLY_REPORTS_FILE.exists():
        old_reports_data = safe_load_json(OLD_WEEKLY_REPORTS_FILE, {})
        old_reports = old_reports_data.get("weekly_reports", [])

        if old_reports:
            data["weekly_reports"] = old_reports

    data = ensure_data_fields(data)
    save_data(data)

    write_to_project_log(
        "Atlas 2.0 合并版初始化",
        "已创建 atlas2_data.json，并尝试从旧的 projects.json、daily_tasks.json、bugs.json、weekly_reports.json 中迁移数据。"
    )

    return data


def ensure_data_fields(data):
    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "atlas_version" not in data:
        data["atlas_version"] = "Atlas 2.0"

    if "database_version" not in data:
        data["database_version"] = "Atlas 2.0 Unified Database v1"

    if "projects" not in data:
        data["projects"] = []

    if "daily_tasks" not in data:
        data["daily_tasks"] = []

    if "bugs" not in data:
        data["bugs"] = []

    if "weekly_reports" not in data:
        data["weekly_reports"] = []

    if not data["projects"]:
        default_projects = create_default_data()["projects"]
        data["projects"] = default_projects

    return data


def load_data():
    return migrate_old_data_if_needed()


def save_data(data):
    save_json(DATA_FILE, data)


def get_next_id(items):
    if not items:
        return 1

    ids = []

    for item in items:
        if "id" in item:
            ids.append(item["id"])

    if not ids:
        return 1

    return max(ids) + 1


def show_intro(data):
    week_start, week_end = get_week_range()

    print("\n==============================")
    print("Atlas 2.0 Unified Main Program")
    print("合并版主程序")
    print("==============================")
    print(f"学生：{data['student_name']}")
    print(f"版本：{data['atlas_version']}")
    print(f"数据库文件：{DATA_FILE}")
    print(f"项目日志：{PROJECT_LOG_FILE}")
    print(f"周报文件：{WEEKLY_REPORT_TXT_FILE}")
    print(f"本周周期：{date_to_text(week_start)} 至 {date_to_text(week_end)}")
    print("==============================")
    print("功能：Project Database + Daily Task + Bug Manager + Weekly Report")
    print("==============================")


def format_project(project):
    return (
        f"项目 ID：{project.get('id', '未知')}\n"
        f"项目名称：{project.get('name', '未命名项目')}\n"
        f"状态：{project.get('status', '未知')}\n"
        f"完成度：{project.get('progress', 0)}%\n"
        f"类别：{project.get('category', '未分类')}\n"
        f"说明：{project.get('description', '暂无说明')}\n"
        f"下一步：{project.get('next_step', '暂无下一步')}"
    )


def get_project_summary_text(data):
    projects = data["projects"]

    total_projects = len(projects)
    completed_count = 0
    developing_count = 0
    other_count = 0

    atlas_status = "未找到 Atlas 2.0"
    atlas_progress = "未找到 Atlas 2.0"
    atlas_next_step = "未找到 Atlas 2.0"

    project_lines = []

    for project in projects:
        status = project.get("status", "未知")

        if status == "完成":
            completed_count += 1
        elif status == "开发中":
            developing_count += 1
        else:
            other_count += 1

        project_name = project.get("name", "未命名项目")
        progress = project.get("progress", 0)

        project_lines.append(
            f"- {project_name} | 状态：{status} | 完成度：{progress}%"
        )

        if "Atlas 2.0" in project_name:
            atlas_status = status
            atlas_progress = f"{progress}%"
            atlas_next_step = project.get("next_step", "暂无下一步")

    summary = (
        f"Eric 现在一共有 {total_projects} 个项目。\n"
        f"已完成项目：{completed_count} 个。\n"
        f"开发中项目：{developing_count} 个。\n"
        f"其他状态项目：{other_count} 个。\n"
        f"Atlas 2.0 当前状态：{atlas_status}。\n"
        f"Atlas 2.0 当前完成度：{atlas_progress}。\n"
        f"Atlas 2.0 当前下一步：{atlas_next_step}。\n\n"
        "项目列表：\n"
        + "\n".join(project_lines)
    )

    return summary


def show_project_summary(data):
    summary = get_project_summary_text(data)

    print("\nProject Database 项目总览：")
    print("-" * 60)
    print(summary)
    print("-" * 60)

    write_to_project_log(
        "Atlas 2.0 合并版 Project Database 项目总览",
        summary
    )


def find_atlas_project(data):
    for project in data["projects"]:
        if "Atlas 2.0" in project.get("name", ""):
            return project

    return None


def update_atlas_progress(data):
    atlas_project = find_atlas_project(data)

    if atlas_project is None:
        print("\n没有找到 Atlas 2.0 项目。")
        return

    print("\n当前 Atlas 2.0：")
    print(format_project(atlas_project))

    old_status = atlas_project.get("status", "未知")
    old_progress = atlas_project.get("progress", 0)
    old_next_step = atlas_project.get("next_step", "暂无下一步")

    new_status = input("\n新的状态（不改就直接回车）：").strip()
    new_progress_text = input("新的完成度数字（不改就直接回车）：").strip()
    new_next_step = input("新的下一步（不改就直接回车）：").strip()

    if new_status:
        atlas_project["status"] = new_status

    if new_progress_text:
        if new_progress_text.isdigit():
            new_progress = int(new_progress_text)

            if new_progress < 0:
                new_progress = 0

            if new_progress > 100:
                new_progress = 100

            atlas_project["progress"] = new_progress
        else:
            print("完成度不是数字，所以没有修改。")

    if new_next_step:
        atlas_project["next_step"] = new_next_step

    save_data(data)

    content = (
        "Atlas 2.0 进度更新：\n"
        f"状态：{old_status} → {atlas_project.get('status', '未知')}\n"
        f"完成度：{old_progress}% → {atlas_project.get('progress', 0)}%\n"
        f"下一步：{old_next_step} → {atlas_project.get('next_step', '暂无下一步')}"
    )

    print("\n已更新：")
    print(content)

    write_to_project_log(
        "Atlas 2.0 合并版 更新项目进度",
        content
    )


def show_project_options(data):
    print("\n当前项目：")
    print("-" * 50)

    for project in data["projects"]:
        print(
            f"{project.get('id', '未知')}. "
            f"{project.get('name', '未命名')} | "
            f"状态：{project.get('status', '未知')} | "
            f"完成度：{project.get('progress', 0)}%"
        )

    print("-" * 50)


def find_today_task(data):
    today = get_today_text()

    for task in data["daily_tasks"]:
        if task.get("date") == today:
            return task

    return None


def format_task(task):
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


def create_or_update_today_task(data):
    today_task = find_today_task(data)

    if today_task is not None:
        print("\n今天已经有 Daily Task：")
        print(format_task(today_task))

        answer = input("\n是否覆盖今天的任务？输入 y 覆盖，其他键取消：").strip().lower()

        if answer != "y":
            print("已取消，没有修改今天任务。")
            return

        data["daily_tasks"].remove(today_task)

    print("\n创建今天的 Daily Task。")
    show_project_options(data)

    project_name = input("\n今天任务属于哪个项目？").strip()
    today_plan = input("今天准备完成什么？").strip()
    estimated_hours_text = input("预计需要几个小时？例如 2：").strip()
    priority = input("优先级（高 / 中 / 低）：").strip()
    reason = input("为什么今天要做这件事？").strip()

    if not project_name:
        project_name = "Atlas 2.0"

    if not today_plan:
        today_plan = "整理 Atlas 2.0 合并版 Demo"

    if estimated_hours_text.isdigit():
        estimated_hours = int(estimated_hours_text)
    else:
        estimated_hours = 1

    if estimated_hours <= 0:
        estimated_hours = 1

    if not priority:
        priority = "中"

    if not reason:
        reason = "这是 Atlas 2.0 版本收尾的重要任务。"

    now = datetime.now()

    task = {
        "date": get_today_text(),
        "created_time": now.strftime("%H:%M:%S"),
        "project_name": project_name,
        "today_plan": today_plan,
        "estimated_hours": estimated_hours,
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

    content = format_task(task)

    print("\n今日任务已保存：")
    print("-" * 60)
    print(content)
    print("-" * 60)

    write_to_project_log(
        "Atlas 2.0 合并版 Daily Task 创建今日任务",
        content
    )


def show_today_task(data):
    task = find_today_task(data)

    if task is None:
        message = "今天还没有 Daily Task。请先创建今天任务。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 2.0 合并版 Daily Task 查看今日任务",
            message
        )
        return

    content = format_task(task)

    print("\n今天的 Daily Task：")
    print("-" * 60)
    print(content)
    print("-" * 60)

    write_to_project_log(
        "Atlas 2.0 合并版 Daily Task 查看今日任务",
        content
    )


def generate_task_mentor_comment(status, next_step):
    if status == "完成":
        return "今天任务完成。建议保存截图、运行结果和日志，作为 Atlas 2.0 的研发证据。"

    if status == "部分完成":
        return f"今天已经有部分推进。明天建议优先继续做：{next_step}。"

    return "今天任务未完成也要记录原因。研发管理的重点是形成闭环，而不是每天都假装顺利。"


def evening_review(data):
    task = find_today_task(data)

    if task is None:
        print("\n今天还没有 Daily Task，无法复盘。")
        return

    print("\n晚上复盘：Eric，今天完成了吗？")
    print("\n今天任务：")
    print(f"项目：{task.get('project_name', '未知项目')}")
    print(f"计划：{task.get('today_plan', '未填写')}")

    finished_status = input("\n完成情况（完成 / 部分完成 / 未完成）：").strip()
    finished_result = input("今天实际完成了什么？").strip()
    problem = input("今天遇到什么问题？没有就写 无：").strip()
    next_step = input("明天下一步做什么？").strip()

    if finished_status not in ["完成", "部分完成", "未完成"]:
        finished_status = "部分完成"

    if not finished_result:
        finished_result = "未填写"

    if not problem:
        problem = "无"

    if not next_step:
        next_step = "继续完成今天未完成的任务"

    mentor_comment = generate_task_mentor_comment(finished_status, next_step)

    task["status"] = finished_status
    task["evening_review_done"] = True
    task["finished_result"] = finished_result
    task["problem"] = problem
    task["next_step"] = next_step
    task["mentor_comment"] = mentor_comment

    save_data(data)

    content = format_task(task)

    print("\n晚上复盘已保存：")
    print("-" * 60)
    print(content)
    print("-" * 60)

    write_to_project_log(
        "Atlas 2.0 合并版 Daily Task 晚上复盘",
        content
    )


def generate_bug_mentor_comment(bug_title, severity, next_step):
    title_lower = bug_title.lower()

    if severity == "高":
        return "这是高优先级 Bug。建议先暂停新增功能，优先复现问题、记录报错、缩小排查范围。"

    if "opencv" in title_lower or "摄像头" in bug_title or "识别" in bug_title:
        return "这是视觉识别类 Bug。建议先确认摄像头、光线、距离、检测模型和判断阈值。"

    if "arduino" in title_lower or "oled" in title_lower or "舵机" in bug_title or "灯" in bug_title:
        return "这是硬件反馈类 Bug。建议先检查端口、接线、GND 是否共地，再检查 Python 指令发送。"

    if "json" in title_lower or "保存" in bug_title or "日志" in bug_title:
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

    project_name = input("\nBug 属于哪个项目？").strip()
    bug_title = input("Bug 标题：").strip()
    bug_description = input("Bug 现象描述：").strip()
    trigger_condition = input("什么时候会出现这个 Bug？").strip()
    attempted_solution = input("已经尝试过什么解决方法？没有就写 无：").strip()
    severity = input("严重程度（高 / 中 / 低）：").strip()
    next_step = input("下一步准备怎么排查？").strip()

    if not project_name:
        project_name = "Atlas 2.0"

    if not bug_title:
        print("Bug 标题不能为空，本次没有保存。")
        return

    if not bug_description:
        bug_description = "未填写具体 Bug 现象"

    if not trigger_condition:
        trigger_condition = "未填写触发条件"

    if not attempted_solution:
        attempted_solution = "无"

    if severity not in ["高", "中", "低"]:
        severity = "中"

    if not next_step:
        next_step = "继续复现 Bug，并记录报错信息"

    now = datetime.now()

    bug = {
        "id": get_next_id(data["bugs"]),
        "date": get_today_text(),
        "created_time": now.strftime("%H:%M:%S"),
        "project_name": project_name,
        "bug_title": bug_title,
        "bug_description": bug_description,
        "trigger_condition": trigger_condition,
        "attempted_solution": attempted_solution,
        "severity": severity,
        "status": "未解决",
        "solution": "",
        "fixed_time": "",
        "next_step": next_step,
        "mentor_comment": generate_bug_mentor_comment(bug_title, severity, next_step)
    }

    data["bugs"].append(bug)
    save_data(data)

    content = format_bug(bug)

    print("\nBug 已保存：")
    print("-" * 60)
    print(content)
    print("-" * 60)

    write_to_project_log(
        "Atlas 2.0 合并版 Bug Manager 新增 Bug",
        content
    )


def show_or_search_bugs(data):
    keyword = input("\n直接回车查看全部 Bug；输入关键词可以搜索 Bug：").strip()

    matched_bugs = []

    if not keyword:
        matched_bugs = data["bugs"]
        title = "Atlas 2.0 合并版 Bug Manager 查看全部 Bug"
    else:
        title = "Atlas 2.0 合并版 Bug Manager 搜索 Bug"

        for bug in data["bugs"]:
            search_text = (
                bug.get("project_name", "") + " "
                + bug.get("bug_title", "") + " "
                + bug.get("bug_description", "") + " "
                + bug.get("trigger_condition", "") + " "
                + bug.get("attempted_solution", "") + " "
                + bug.get("status", "") + " "
                + bug.get("next_step", "")
            )

            if keyword.lower() in search_text.lower():
                matched_bugs.append(bug)

    if not matched_bugs:
        if keyword:
            message = f"没有找到包含关键词「{keyword}」的 Bug。"
        else:
            message = "目前还没有 Bug。"

        print("\n" + message)

        write_to_project_log(title, message)
        return

    lines = []

    print("\nBug 记录：")
    print("-" * 60)

    for bug in matched_bugs:
        content = format_bug(bug)
        print(content)
        print("-" * 60)
        lines.append(content)

    write_to_project_log(
        title,
        "\n\n".join(lines)
    )


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

    bug_id = int(bug_id_text)
    bug = find_bug_by_id(data, bug_id)

    if bug is None:
        print("没有找到这个 Bug。")
        return

    print("\n当前 Bug：")
    print(format_bug(bug))

    old_status = bug.get("status", "未知")
    old_solution = bug.get("solution", "")
    old_next_step = bug.get("next_step", "")

    new_status = input("\n新的状态（未解决 / 排查中 / 已解决）：").strip()
    solution = input("解决方法或当前排查结果：").strip()
    next_step = input("下一步：").strip()

    if new_status not in ["未解决", "排查中", "已解决"]:
        new_status = old_status

    bug["status"] = new_status

    if solution:
        bug["solution"] = solution

    if next_step:
        bug["next_step"] = next_step

    if new_status == "已解决":
        bug["fixed_time"] = get_now_text()

    save_data(data)

    content = (
        f"更新 Bug ID：{bug.get('id', '未知')}\n"
        f"Bug 标题：{bug.get('bug_title', '未命名 Bug')}\n"
        f"状态：{old_status} → {bug.get('status', '未知')}\n"
        f"解决方法：{old_solution if old_solution else '暂无'} → {bug.get('solution', '') if bug.get('solution', '') else '暂无'}\n"
        f"下一步：{old_next_step if old_next_step else '暂无'} → {bug.get('next_step', '') if bug.get('next_step', '') else '暂无'}\n"
        f"修复时间：{bug.get('fixed_time', '') if bug.get('fixed_time', '') else '未修复'}"
    )

    print("\nBug 已更新：")
    print("-" * 60)
    print(content)
    print("-" * 60)

    write_to_project_log(
        "Atlas 2.0 合并版 Bug Manager 更新 Bug",
        content
    )


def get_bug_summary_text(data):
    bugs = data["bugs"]

    total_count = len(bugs)
    open_count = 0
    checking_count = 0
    fixed_count = 0
    high_count = 0

    for bug in bugs:
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
        f"Bug 总数：{total_count} 个。\n"
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


def summarize_tasks_this_week(data, week_start, week_end):
    tasks = data["daily_tasks"]
    this_week_tasks = []

    for task in tasks:
        if is_in_this_week(task.get("date", ""), week_start, week_end):
            this_week_tasks.append(task)

    completed = []
    partial = []
    unfinished = []

    task_lines = []

    for task in this_week_tasks:
        status = task.get("status", "未知")

        if status == "完成":
            completed.append(task)
        elif status == "部分完成":
            partial.append(task)
        else:
            unfinished.append(task)

        task_lines.append(
            f"- {task.get('date', '无日期')} | "
            f"{task.get('project_name', '未知项目')} | "
            f"{task.get('today_plan', '未填写任务')} | "
            f"状态：{status}"
        )

    return {
        "this_week_tasks": this_week_tasks,
        "completed": completed,
        "partial": partial,
        "unfinished": unfinished,
        "task_lines": task_lines
    }


def summarize_bugs_this_week(data, week_start, week_end):
    bugs = data["bugs"]
    this_week_bugs = []

    for bug in bugs:
        if is_in_this_week(bug.get("date", ""), week_start, week_end):
            this_week_bugs.append(bug)

    open_bugs = []
    checking_bugs = []
    fixed_bugs = []
    high_bugs = []

    bug_lines = []

    for bug in this_week_bugs:
        status = bug.get("status", "未知")
        severity = bug.get("severity", "未知")

        if status == "未解决":
            open_bugs.append(bug)
        elif status == "排查中":
            checking_bugs.append(bug)
        elif status == "已解决":
            fixed_bugs.append(bug)

        if severity == "高":
            high_bugs.append(bug)

        bug_lines.append(
            f"- Bug ID {bug.get('id', '未知')} | "
            f"{bug.get('bug_title', '未命名 Bug')} | "
            f"状态：{status} | 严重程度：{severity}"
        )

    return {
        "this_week_bugs": this_week_bugs,
        "open_bugs": open_bugs,
        "checking_bugs": checking_bugs,
        "fixed_bugs": fixed_bugs,
        "high_bugs": high_bugs,
        "bug_lines": bug_lines
    }


def generate_weekly_report(data):
    week_start, week_end = get_week_range()

    project_summary = get_project_summary_text(data)
    task_summary = summarize_tasks_this_week(data, week_start, week_end)
    bug_summary = summarize_bugs_this_week(data, week_start, week_end)

    suggestions = []

    if len(bug_summary["open_bugs"]) > 0 or len(bug_summary["checking_bugs"]) > 0:
        suggestions.append("下周优先处理未解决或排查中的 Bug。")

    if len(task_summary["unfinished"]) > 0:
        suggestions.append("下周优先完成未完成的 Daily Task。")

    if not suggestions:
        suggestions.append("下周可以整理 Atlas 2.0 Demo 视频、Version Note 和下一版本规划。")

    lines = []

    lines.append("Atlas 2.0 Weekly Report")
    lines.append(f"周报周期：{date_to_text(week_start)} 至 {date_to_text(week_end)}")
    lines.append("")

    lines.append("一、本周项目总览")
    lines.append(project_summary)
    lines.append("")

    lines.append("二、本周 Daily Task 总结")
    lines.append(f"本周任务总数：{len(task_summary['this_week_tasks'])} 个。")
    lines.append(f"完成任务：{len(task_summary['completed'])} 个。")
    lines.append(f"部分完成任务：{len(task_summary['partial'])} 个。")
    lines.append(f"未完成任务：{len(task_summary['unfinished'])} 个。")
    lines.append("任务列表：")

    if task_summary["task_lines"]:
        lines.extend(task_summary["task_lines"])
    else:
        lines.append("- 本周还没有 Daily Task。")

    lines.append("")

    lines.append("三、本周 Bug 总结")
    lines.append(f"本周 Bug 总数：{len(bug_summary['this_week_bugs'])} 个。")
    lines.append(f"未解决 Bug：{len(bug_summary['open_bugs'])} 个。")
    lines.append(f"排查中 Bug：{len(bug_summary['checking_bugs'])} 个。")
    lines.append(f"已解决 Bug：{len(bug_summary['fixed_bugs'])} 个。")
    lines.append(f"高严重程度 Bug：{len(bug_summary['high_bugs'])} 个。")
    lines.append("Bug 列表：")

    if bug_summary["bug_lines"]:
        lines.extend(bug_summary["bug_lines"])
    else:
        lines.append("- 本周还没有 Bug。")

    lines.append("")

    lines.append("四、机器人导师判断")

    if len(task_summary["completed"]) > 0:
        lines.append("本周已经形成 Daily Task 完成记录，说明 Atlas 2.0 具备任务管理能力。")
    else:
        lines.append("本周任务记录偏少，后续需要继续保持每日计划和晚上复盘。")

    if len(bug_summary["fixed_bugs"]) > 0:
        lines.append("本周有 Bug 修复记录，这是非常重要的真实研发证据。")
    elif len(bug_summary["this_week_bugs"]) > 0:
        lines.append("本周已经开始记录 Bug，但还需要继续推动 Bug 关闭。")
    else:
        lines.append("本周没有 Bug 记录。如果实际调试中有问题，建议及时记录。")

    lines.append("")

    lines.append("五、下周建议")

    for index, suggestion in enumerate(suggestions, start=1):
        lines.append(f"{index}. {suggestion}")

    lines.append("")

    lines.append("六、版本判断")
    lines.append("如果 Project Database、Daily Task、Bug Manager 和 Weekly Report 都能运行，Atlas 2.0 的核心管理能力已经完成。")

    report_content = "\n".join(lines)

    now = datetime.now()

    report_record = {
        "week_start": date_to_text(week_start),
        "week_end": date_to_text(week_end),
        "created_date": now.strftime("%Y-%m-%d"),
        "created_time": now.strftime("%H:%M:%S"),
        "content": report_content
    }

    data["weekly_reports"].append(report_record)
    save_data(data)

    write_to_weekly_report_txt(report_content)

    write_to_project_log(
        "Atlas 2.0 合并版 Weekly Report 自动生成周报",
        report_content
    )

    print("\nWeekly Report 已生成：")
    print("-" * 60)
    print(report_content)
    print("-" * 60)


def show_latest_weekly_report(data):
    reports = data["weekly_reports"]

    if not reports:
        message = "目前还没有 Weekly Report，请先生成周报。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 2.0 合并版 Weekly Report 查看最新周报",
            message
        )
        return

    latest_report = reports[-1]
    content = latest_report["content"]

    print("\n最新 Weekly Report：")
    print("-" * 60)
    print(content)
    print("-" * 60)

    write_to_project_log(
        "Atlas 2.0 合并版 Weekly Report 查看最新周报",
        content
    )


def one_click_demo_overview(data):
    today_task = find_today_task(data)
    bug_summary = get_bug_summary_text(data)

    if data["weekly_reports"]:
        latest_report_status = "已有 Weekly Report"
    else:
        latest_report_status = "还没有 Weekly Report"

    lines = []

    lines.append("Atlas 2.0 Demo Overview")
    lines.append("")
    lines.append("一、Project Database")
    lines.append(get_project_summary_text(data))
    lines.append("")

    lines.append("二、Daily Task")
    if today_task:
        lines.append("今天已有 Daily Task：")
        lines.append(format_task(today_task))
    else:
        lines.append("今天还没有 Daily Task。")
    lines.append("")

    lines.append("三、Bug Manager")
    lines.append(bug_summary)
    lines.append("")

    lines.append("四、Weekly Report")
    lines.append(latest_report_status)
    lines.append("")

    lines.append("机器人总结：")
    lines.append("Atlas 2.0 已经从单纯聊天机器人，升级为可以管理项目、每日任务、Bug 和周报的研发管理机器人。")

    overview = "\n".join(lines)

    print("\n" + "=" * 60)
    print(overview)
    print("=" * 60)

    write_to_project_log(
        "Atlas 2.0 合并版 一键 Demo 总览",
        overview
    )


def test_log_write():
    content = (
        "这是 Atlas 2.0 合并版的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明合并版日志保存正常。"
    )

    write_to_project_log(
        "Atlas 2.0 合并版 日志写入测试",
        content
    )


def main():
    data = load_data()
    show_intro(data)

    write_to_project_log(
        "Atlas 2.0 合并版程序启动",
        "atlas2_main.py 已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 一键 Demo 总览")
        print("2. Project Database：查看项目总览")
        print("3. Project Database：更新 Atlas 2.0 进度")
        print("4. Daily Task：创建或更新今天任务")
        print("5. Daily Task：查看今天任务")
        print("6. Daily Task：晚上复盘")
        print("7. Bug Manager：新增 Bug")
        print("8. Bug Manager：查看全部 Bug / 搜索 Bug")
        print("9. Bug Manager：更新 Bug 状态")
        print("10. Weekly Report：生成本周周报")
        print("11. Weekly Report：查看最新周报")
        print("12. 测试 project_log.txt 是否能写入")
        print("13. 退出")

        choice = input("请输入数字 1-13：").strip()

        if choice == "1":
            one_click_demo_overview(data)

        elif choice == "2":
            show_project_summary(data)

        elif choice == "3":
            update_atlas_progress(data)

        elif choice == "4":
            create_or_update_today_task(data)

        elif choice == "5":
            show_today_task(data)

        elif choice == "6":
            evening_review(data)

        elif choice == "7":
            add_bug(data)

        elif choice == "8":
            show_or_search_bugs(data)

        elif choice == "9":
            update_bug_status(data)

        elif choice == "10":
            generate_weekly_report(data)

        elif choice == "11":
            show_latest_weekly_report(data)

        elif choice == "12":
            test_log_write()

        elif choice == "13":
            write_to_project_log(
                "Atlas 2.0 合并版程序退出",
                "atlas2_main.py 已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            message = f"输入无效：{choice}"
            print("输入无效，请输入 1 到 13。")

            write_to_project_log(
                "Atlas 2.0 合并版无效输入",
                message
            )


if __name__ == "__main__":
    main()