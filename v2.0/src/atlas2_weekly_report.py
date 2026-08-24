import json
from datetime import datetime, date, timedelta
from pathlib import Path


# 固定路径，防止写到别的目录
BASE_DIR = Path(__file__).resolve().parent

PROJECTS_FILE = BASE_DIR / "projects.json"
TASKS_FILE = BASE_DIR / "daily_tasks.json"
BUGS_FILE = BASE_DIR / "bugs.json"
WEEKLY_REPORTS_FILE = BASE_DIR / "weekly_reports.json"
WEEKLY_REPORT_TXT_FILE = BASE_DIR / "weekly_report.txt"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


def get_now_text():
    """获取当前时间。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_today_date():
    """获取今天日期对象。"""
    return date.today()


def get_week_range():
    """获取本周周一到周日日期。"""
    today = get_today_date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def date_to_text(date_obj):
    """日期对象转文字。"""
    return date_obj.strftime("%Y-%m-%d")


def parse_date(date_text):
    """文字日期转日期对象。"""
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except Exception:
        return None


def is_in_this_week(date_text, week_start, week_end):
    """判断某个日期是否属于本周。"""
    current_date = parse_date(date_text)

    if current_date is None:
        return False

    return week_start <= current_date <= week_end


def write_to_project_log(title, content):
    """写入 project_log.txt。"""
    text = (
        "\n" + "=" * 60 + "\n"
        f"{title}\n"
        f"时间：{get_now_text()}\n"
        + "=" * 60 + "\n"
        + content + "\n"
        + "=" * 60 + "\n"
    )

    with open(PROJECT_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 project_log.txt")
    print(f"日志文件位置：{PROJECT_LOG_FILE}")


def write_to_weekly_report_txt(content):
    """写入 weekly_report.txt。"""
    text = (
        "\n" + "=" * 70 + "\n"
        f"Atlas 2.0 Weekly Report\n"
        f"生成时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(WEEKLY_REPORT_TXT_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 weekly_report.txt")
    print(f"周报文件位置：{WEEKLY_REPORT_TXT_FILE}")


def load_json_file(file_path, default_data):
    """安全读取 JSON 文件。"""
    if not file_path.exists():
        return default_data

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception:
        return default_data


def save_json_file(file_path, data):
    """保存 JSON 文件。"""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_projects():
    """读取 projects.json。"""
    default_data = {
        "student_name": "Eric",
        "project_database_version": "Atlas 2.0 Project Database v1",
        "projects": []
    }

    data = load_json_file(PROJECTS_FILE, default_data)
    return data.get("projects", [])


def load_tasks():
    """读取 daily_tasks.json。"""
    default_data = {
        "student_name": "Eric",
        "task_database_version": "Atlas 2.0 Daily Task v1",
        "daily_tasks": []
    }

    data = load_json_file(TASKS_FILE, default_data)
    return data.get("daily_tasks", [])


def load_bugs():
    """读取 bugs.json。"""
    default_data = {
        "student_name": "Eric",
        "bug_database_version": "Atlas 2.0 Bug Manager v1",
        "bugs": []
    }

    data = load_json_file(BUGS_FILE, default_data)
    return data.get("bugs", [])


def load_weekly_reports_database():
    """读取 weekly_reports.json。"""
    default_data = {
        "student_name": "Eric",
        "weekly_report_version": "Atlas 2.0 Weekly Report v1",
        "weekly_reports": []
    }

    data = load_json_file(WEEKLY_REPORTS_FILE, default_data)

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "weekly_report_version" not in data:
        data["weekly_report_version"] = "Atlas 2.0 Weekly Report v1"

    if "weekly_reports" not in data:
        data["weekly_reports"] = []

    save_json_file(WEEKLY_REPORTS_FILE, data)
    return data


def summarize_projects(projects):
    """总结项目数据库。"""
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
        progress = project.get("progress", 0)

        if status == "完成":
            completed_count += 1
        elif status == "开发中":
            developing_count += 1
        else:
            other_count += 1

        project_name = project.get("name", "未命名项目")

        project_lines.append(
            f"- {project_name} | 状态：{status} | 完成度：{progress}%"
        )

        if "Atlas 2.0" in project_name:
            atlas_status = status
            atlas_progress = f"{progress}%"
            atlas_next_step = project.get("next_step", "暂无下一步")

    return {
        "total_projects": total_projects,
        "completed_count": completed_count,
        "developing_count": developing_count,
        "other_count": other_count,
        "atlas_status": atlas_status,
        "atlas_progress": atlas_progress,
        "atlas_next_step": atlas_next_step,
        "project_lines": project_lines
    }


def summarize_tasks(tasks, week_start, week_end):
    """总结本周任务。"""
    this_week_tasks = []

    for task in tasks:
        task_date = task.get("date", "")
        if is_in_this_week(task_date, week_start, week_end):
            this_week_tasks.append(task)

    completed_tasks = []
    partial_tasks = []
    unfinished_tasks = []

    task_lines = []

    for task in this_week_tasks:
        status = task.get("status", "未知")

        if status == "完成":
            completed_tasks.append(task)
        elif status == "部分完成":
            partial_tasks.append(task)
        else:
            unfinished_tasks.append(task)

        task_lines.append(
            f"- {task.get('date', '无日期')} | "
            f"{task.get('project_name', '未知项目')} | "
            f"{task.get('today_plan', '未填写任务')} | "
            f"状态：{status}"
        )

    return {
        "this_week_tasks": this_week_tasks,
        "completed_tasks": completed_tasks,
        "partial_tasks": partial_tasks,
        "unfinished_tasks": unfinished_tasks,
        "task_lines": task_lines
    }


def summarize_bugs(bugs, week_start, week_end):
    """总结本周 Bug。"""
    this_week_bugs = []

    for bug in bugs:
        bug_date = bug.get("date", "")
        if is_in_this_week(bug_date, week_start, week_end):
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


def generate_next_week_suggestion(project_summary, task_summary, bug_summary):
    """生成下周建议。"""
    suggestions = []

    open_bug_count = len(bug_summary["open_bugs"])
    checking_bug_count = len(bug_summary["checking_bugs"])
    unfinished_task_count = len(task_summary["unfinished_tasks"])

    if open_bug_count > 0 or checking_bug_count > 0:
        suggestions.append(
            "下周优先处理未解决或排查中的 Bug，不要急着增加复杂新功能。"
        )

    if unfinished_task_count > 0:
        suggestions.append(
            "下周优先完成未完成的 Daily Task，保持任务闭环。"
        )

    atlas_progress_text = project_summary["atlas_progress"]

    if atlas_progress_text != "未找到 Atlas 2.0":
        try:
            atlas_progress_number = int(atlas_progress_text.replace("%", ""))
        except Exception:
            atlas_progress_number = 0

        if atlas_progress_number < 100:
            suggestions.append(
                "继续推进 Atlas 2.0，完成 Weekly Report 后可以更新 Atlas 2.0 进度。"
            )
        else:
            suggestions.append(
                "Atlas 2.0 已接近完成，下周可以开始整理 Demo 视频、Version Note 和下一版本规划。"
            )

    if not suggestions:
        suggestions.append(
            "下周建议整理 Atlas 2.0 的 Demo 视频、Project Log、Version Note，并准备进入下一版本。"
        )

    return suggestions


def build_weekly_report_content(project_summary, task_summary, bug_summary, week_start, week_end):
    """生成周报正文。"""
    week_start_text = date_to_text(week_start)
    week_end_text = date_to_text(week_end)

    suggestions = generate_next_week_suggestion(
        project_summary,
        task_summary,
        bug_summary
    )

    lines = []

    lines.append("Atlas 2.0 Weekly Report")
    lines.append(f"周报周期：{week_start_text} 至 {week_end_text}")
    lines.append("")

    lines.append("一、本周项目总览")
    lines.append(f"Eric 当前一共有 {project_summary['total_projects']} 个项目。")
    lines.append(f"已完成项目：{project_summary['completed_count']} 个。")
    lines.append(f"开发中项目：{project_summary['developing_count']} 个。")
    lines.append(f"其他状态项目：{project_summary['other_count']} 个。")
    lines.append(f"Atlas 2.0 当前状态：{project_summary['atlas_status']}。")
    lines.append(f"Atlas 2.0 当前完成度：{project_summary['atlas_progress']}。")
    lines.append(f"Atlas 2.0 当前下一步：{project_summary['atlas_next_step']}。")
    lines.append("")

    lines.append("项目列表：")
    if project_summary["project_lines"]:
        lines.extend(project_summary["project_lines"])
    else:
        lines.append("- 本周没有项目数据库记录。")
    lines.append("")

    lines.append("二、本周 Daily Task 总结")
    lines.append(f"本周任务总数：{len(task_summary['this_week_tasks'])} 个。")
    lines.append(f"完成任务：{len(task_summary['completed_tasks'])} 个。")
    lines.append(f"部分完成任务：{len(task_summary['partial_tasks'])} 个。")
    lines.append(f"未完成任务：{len(task_summary['unfinished_tasks'])} 个。")
    lines.append("")

    lines.append("任务列表：")
    if task_summary["task_lines"]:
        lines.extend(task_summary["task_lines"])
    else:
        lines.append("- 本周还没有 Daily Task 记录。")
    lines.append("")

    lines.append("三、本周 Bug 总结")
    lines.append(f"本周 Bug 总数：{len(bug_summary['this_week_bugs'])} 个。")
    lines.append(f"未解决 Bug：{len(bug_summary['open_bugs'])} 个。")
    lines.append(f"排查中 Bug：{len(bug_summary['checking_bugs'])} 个。")
    lines.append(f"已解决 Bug：{len(bug_summary['fixed_bugs'])} 个。")
    lines.append(f"高严重程度 Bug：{len(bug_summary['high_bugs'])} 个。")
    lines.append("")

    lines.append("Bug 列表：")
    if bug_summary["bug_lines"]:
        lines.extend(bug_summary["bug_lines"])
    else:
        lines.append("- 本周还没有 Bug 记录。")
    lines.append("")

    lines.append("四、机器人导师判断")
    if len(task_summary["completed_tasks"]) > 0:
        lines.append("本周已经有可记录的研发产出。")
    else:
        lines.append("本周 Daily Task 记录偏少，下周要加强每日任务闭环。")

    if len(bug_summary["fixed_bugs"]) > 0:
        lines.append("本周有 Bug 修复记录，这是很重要的真实研发证据。")
    elif len(bug_summary["this_week_bugs"]) > 0:
        lines.append("本周已经开始记录 Bug，但还需要继续推动 Bug 关闭。")
    else:
        lines.append("本周没有 Bug 记录。如果确实没有 Bug，可以继续推进；如果有问题，建议及时记录。")
    lines.append("")

    lines.append("五、下周建议")
    for index, suggestion in enumerate(suggestions, start=1):
        lines.append(f"{index}. {suggestion}")

    lines.append("")
    lines.append("六、本周最低完成判断")
    lines.append("如果本周已经完成 Project Database、Daily Task、Bug Manager，并生成本周报告，Atlas 2.0 的核心管理能力已经跑通。")

    return "\n".join(lines)


def save_weekly_report(data, report_content, week_start, week_end):
    """保存周报到 weekly_reports.json。"""
    now = datetime.now()

    report_record = {
        "week_start": date_to_text(week_start),
        "week_end": date_to_text(week_end),
        "created_date": now.strftime("%Y-%m-%d"),
        "created_time": now.strftime("%H:%M:%S"),
        "content": report_content
    }

    data["weekly_reports"].append(report_record)
    save_json_file(WEEKLY_REPORTS_FILE, data)


def generate_weekly_report():
    """生成本周周报。"""
    weekly_data = load_weekly_reports_database()

    projects = load_projects()
    tasks = load_tasks()
    bugs = load_bugs()

    week_start, week_end = get_week_range()

    project_summary = summarize_projects(projects)
    task_summary = summarize_tasks(tasks, week_start, week_end)
    bug_summary = summarize_bugs(bugs, week_start, week_end)

    report_content = build_weekly_report_content(
        project_summary,
        task_summary,
        bug_summary,
        week_start,
        week_end
    )

    save_weekly_report(
        weekly_data,
        report_content,
        week_start,
        week_end
    )

    write_to_weekly_report_txt(report_content)

    write_to_project_log(
        "Atlas 2.0 Weekly Report 自动生成周报",
        report_content
    )

    print("\n本周 Weekly Report 已生成：")
    print("-" * 60)
    print(report_content)
    print("-" * 60)


def show_latest_weekly_report():
    """查看最新周报。"""
    data = load_weekly_reports_database()
    reports = data["weekly_reports"]

    if not reports:
        message = "目前还没有 Weekly Report。请先选择 1 生成本周周报。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 2.0 Weekly Report 查看最新周报",
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
        "Atlas 2.0 Weekly Report 查看最新周报",
        content
    )


def show_all_weekly_reports():
    """查看全部周报。"""
    data = load_weekly_reports_database()
    reports = data["weekly_reports"]

    if not reports:
        message = "目前还没有 Weekly Report。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 2.0 Weekly Report 查看全部周报",
            message
        )
        return

    print("\n全部 Weekly Report：")
    print("-" * 60)

    lines = []

    for index, report in enumerate(reports, start=1):
        short_text = (
            f"{index}. 周期：{report['week_start']} 至 {report['week_end']} | "
            f"生成时间：{report['created_date']} {report['created_time']}"
        )

        print(short_text)
        lines.append(short_text)

    write_to_project_log(
        "Atlas 2.0 Weekly Report 查看全部周报",
        "\n".join(lines)
    )


def test_log_write():
    """测试日志写入。"""
    content = (
        "这是 Atlas 2.0 Weekly Report 的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明 Weekly Report 日志保存正常。"
    )

    write_to_project_log(
        "Atlas 2.0 Weekly Report 日志写入测试",
        content
    )


def show_intro():
    """显示开头。"""
    week_start, week_end = get_week_range()

    print("\n==============================")
    print("Atlas 2.0")
    print("Weekly Report")
    print("==============================")
    print("学生：Eric")
    print(f"本周周期：{date_to_text(week_start)} 至 {date_to_text(week_end)}")
    print(f"项目数据库：{PROJECTS_FILE}")
    print(f"每日任务数据库：{TASKS_FILE}")
    print(f"Bug 数据库：{BUGS_FILE}")
    print(f"周报数据库：{WEEKLY_REPORTS_FILE}")
    print(f"周报文本：{WEEKLY_REPORT_TXT_FILE}")
    print(f"项目日志：{PROJECT_LOG_FILE}")
    print("当前目标：自动总结本周项目、任务、Bug，并生成下周建议")
    print("==============================")


def main():
    show_intro()

    load_weekly_reports_database()

    write_to_project_log(
        "Atlas 2.0 Weekly Report 程序启动",
        "Atlas 2.0 Weekly Report 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 生成本周 Weekly Report")
        print("2. 查看最新 Weekly Report")
        print("3. 查看全部 Weekly Report")
        print("4. 测试 project_log.txt 是否能写入")
        print("5. 退出")

        choice = input("请输入数字 1-5：").strip()

        if choice == "1":
            generate_weekly_report()

        elif choice == "2":
            show_latest_weekly_report()

        elif choice == "3":
            show_all_weekly_reports()

        elif choice == "4":
            test_log_write()

        elif choice == "5":
            write_to_project_log(
                "Atlas 2.0 Weekly Report 程序退出",
                "Atlas 2.0 Weekly Report 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            message = f"输入无效：{choice}"
            print("输入无效，请输入 1 到 5。")
            write_to_project_log("Atlas 2.0 Weekly Report 无效输入记录", message)


if __name__ == "__main__":
    main()