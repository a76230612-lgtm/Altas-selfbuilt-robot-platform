import json
from datetime import datetime, date, timedelta
from pathlib import Path


# 固定文件路径，防止写到别的目录
BASE_DIR = Path(__file__).resolve().parent

TASKS_FILE = BASE_DIR / "daily_tasks.json"
PROJECTS_FILE = BASE_DIR / "projects.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


def get_now_text():
    """获取当前时间。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_today_text():
    """获取今天日期。"""
    return date.today().strftime("%Y-%m-%d")


def get_yesterday_text():
    """获取昨天日期。"""
    return (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")


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


def create_default_tasks_database():
    """如果 daily_tasks.json 不存在，就创建默认任务数据库。"""
    default_data = {
        "student_name": "Eric",
        "task_database_version": "Atlas 2.0 Daily Task v1",
        "daily_tasks": []
    }

    save_tasks_database(default_data)

    write_to_project_log(
        "Atlas 2.0 Daily Task 初始化",
        "已创建 daily_tasks.json 每日任务数据库。"
    )

    return default_data


def load_tasks_database():
    """读取每日任务数据库。"""
    if not TASKS_FILE.exists():
        return create_default_tasks_database()

    with open(TASKS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "task_database_version" not in data:
        data["task_database_version"] = "Atlas 2.0 Daily Task v1"

    if "daily_tasks" not in data:
        data["daily_tasks"] = []

    save_tasks_database(data)
    return data


def save_tasks_database(data):
    """保存每日任务数据库。"""
    with open(TASKS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_projects_database():
    """读取项目数据库，用于给任务选择项目。"""
    if not PROJECTS_FILE.exists():
        return []

    try:
        with open(PROJECTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("projects", [])

    except Exception:
        return []


def find_today_task(data):
    """查找今天的任务。"""
    today = get_today_text()

    for task in data["daily_tasks"]:
        if task["date"] == today:
            return task

    return None


def find_yesterday_task(data):
    """查找昨天的任务。"""
    yesterday = get_yesterday_text()

    for task in data["daily_tasks"]:
        if task["date"] == yesterday:
            return task

    return None


def show_project_options():
    """显示项目选项，帮助 Eric 选择今天任务属于哪个项目。"""
    projects = load_projects_database()

    if not projects:
        print("\n没有找到 projects.json，项目名称可以手动输入。")
        return

    print("\n当前项目数据库：")
    print("-" * 50)

    for project in projects:
        print(
            f"{project['id']}. {project['name']} | "
            f"状态：{project['status']} | "
            f"完成度：{project['progress']}%"
        )

    print("-" * 50)


def create_today_task(data):
    """创建或更新今天的任务。"""
    today_task = find_today_task(data)

    if today_task is not None:
        print("\n今天已经有任务：")
        print(f"项目：{today_task['project_name']}")
        print(f"今天计划：{today_task['today_plan']}")
        print(f"状态：{today_task['status']}")

        answer = input("\n是否覆盖今天的任务？输入 y 覆盖，其他键取消：").strip().lower()

        if answer != "y":
            print("已取消，本次没有修改今天任务。")
            return

        data["daily_tasks"].remove(today_task)

    print("\n开始创建今天的 Daily Task。")
    print("每一项写一句话即可。")

    show_project_options()

    project_name = input("\n今天任务属于哪个项目？").strip()
    today_plan = input("今天准备完成什么？").strip()
    estimated_hours_text = input("预计需要几个小时？例如 2：").strip()
    priority = input("优先级（高 / 中 / 低）：").strip()
    reason = input("为什么今天要做这件事？").strip()

    if not project_name:
        project_name = "Atlas 2.0"

    if not today_plan:
        today_plan = "完成 Atlas 2.0 Daily Task 每日任务功能"

    if estimated_hours_text.isdigit():
        estimated_hours = int(estimated_hours_text)
    else:
        estimated_hours = 1

    if estimated_hours <= 0:
        estimated_hours = 1

    if not priority:
        priority = "中"

    if not reason:
        reason = "这是 Atlas 2.0 第二阶段的核心功能。"

    now = datetime.now()

    new_task = {
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

    data["daily_tasks"].append(new_task)
    save_tasks_database(data)

    content = (
        f"日期：{new_task['date']}\n"
        f"项目：{project_name}\n"
        f"今天计划：{today_plan}\n"
        f"预计时间：{estimated_hours} 小时\n"
        f"优先级：{priority}\n"
        f"为什么做：{reason}\n"
        f"当前状态：未完成"
    )

    write_to_project_log(
        "Atlas 2.0 Daily Task 创建今日任务",
        content
    )

    print("\n今日任务已创建：")
    print("-" * 50)
    print(content)
    print("-" * 50)


def show_today_task(data):
    """查看今天的任务。"""
    task = find_today_task(data)

    if task is None:
        message = "今天还没有创建 Daily Task。请先选择 1 创建今天任务。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 2.0 Daily Task 查看今日任务",
            message
        )

        return

    content = format_task_detail(task)

    print("\n今天的 Daily Task：")
    print("-" * 50)
    print(content)
    print("-" * 50)

    write_to_project_log(
        "Atlas 2.0 Daily Task 查看今日任务",
        content
    )


def evening_review(data):
    """晚上检查今天是否完成。"""
    task = find_today_task(data)

    if task is None:
        print("\n今天还没有任务，无法做晚上复盘。")
        print("请先选择 1 创建今天任务。")
        return

    print("\n开始晚上复盘。")
    print("机器人问题：Eric，今天的任务完成了吗？")

    print("\n今天任务：")
    print(f"项目：{task['project_name']}")
    print(f"计划：{task['today_plan']}")

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

    mentor_comment = generate_mentor_comment(
        task["today_plan"],
        finished_status,
        finished_result,
        problem,
        next_step
    )

    task["status"] = finished_status
    task["evening_review_done"] = True
    task["finished_result"] = finished_result
    task["problem"] = problem
    task["next_step"] = next_step
    task["mentor_comment"] = mentor_comment

    save_tasks_database(data)

    content = (
        f"日期：{task['date']}\n"
        f"项目：{task['project_name']}\n"
        f"原计划：{task['today_plan']}\n"
        f"完成情况：{finished_status}\n"
        f"实际完成：{finished_result}\n"
        f"遇到的问题：{problem}\n"
        f"明天下一步：{next_step}\n"
        f"导师评价：{mentor_comment}"
    )

    write_to_project_log(
        "Atlas 2.0 Daily Task 晚上复盘",
        content
    )

    print("\n晚上复盘已保存：")
    print("-" * 50)
    print(content)
    print("-" * 50)


def generate_mentor_comment(today_plan, finished_status, finished_result, problem, next_step):
    """根据完成情况生成简单导师评价。"""
    if finished_status == "完成":
        return (
            "今天任务完成得很好。建议把关键截图、运行结果和日志保存下来，"
            "这样以后可以作为版本演进证据。"
        )

    if finished_status == "部分完成":
        return (
            "今天不是失败，而是完成了部分推进。建议明天不要扩大任务，"
            f"优先继续做：{next_step}。"
        )

    if finished_status == "未完成":
        return (
            "今天任务没有完成也要记录原因。真实研发过程包含延迟、失败和调整。"
            "明天建议把任务缩小到一个更容易完成的小动作。"
        )

    return "建议继续保持每日计划、晚上复盘的研发节奏。"


def show_all_tasks(data):
    """查看全部任务。"""
    tasks = data["daily_tasks"]

    if not tasks:
        print("\n目前还没有任何 Daily Task。")
        return

    print("\n全部 Daily Task：")
    print("-" * 50)

    lines = []

    for task in tasks:
        detail = format_task_short(task)
        print(detail)
        print("-" * 50)
        lines.append(detail)

    write_to_project_log(
        "Atlas 2.0 Daily Task 查看全部任务",
        "\n\n".join(lines)
    )


def show_unfinished_tasks(data):
    """查看未完成任务。"""
    unfinished_tasks = []

    for task in data["daily_tasks"]:
        if task["status"] != "完成":
            unfinished_tasks.append(task)

    if not unfinished_tasks:
        message = "目前没有未完成任务。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 2.0 Daily Task 查看未完成任务",
            message
        )

        return

    print("\n未完成任务：")
    print("-" * 50)

    lines = []

    for task in unfinished_tasks:
        detail = format_task_short(task)
        print(detail)
        print("-" * 50)
        lines.append(detail)

    write_to_project_log(
        "Atlas 2.0 Daily Task 查看未完成任务",
        "\n\n".join(lines)
    )


def ask_today_recommendation(data):
    """机器人根据昨天任务和未完成任务，建议今天做什么。"""
    today_task = find_today_task(data)
    yesterday_task = find_yesterday_task(data)

    unfinished_tasks = [
        task for task in data["daily_tasks"]
        if task["status"] != "完成"
    ]

    lines = []

    lines.append("机器人建议：")

    if today_task:
        lines.append("今天已经有 Daily Task。")
        lines.append(f"项目：{today_task['project_name']}")
        lines.append(f"今天计划：{today_task['today_plan']}")
        lines.append(f"预计时间：{today_task['estimated_hours']} 小时")
        lines.append("建议先完成今天已设定的任务，不要临时增加新任务。")

    elif yesterday_task and yesterday_task["status"] != "完成":
        lines.append("昨天的任务还没有完全完成。")
        lines.append(f"昨天计划：{yesterday_task['today_plan']}")
        lines.append(f"昨天完成情况：{yesterday_task['status']}")
        lines.append(f"建议今天优先继续做：{yesterday_task['next_step'] or yesterday_task['today_plan']}")

    elif unfinished_tasks:
        latest_unfinished = unfinished_tasks[-1]
        lines.append("目前有未完成任务。")
        lines.append(f"最近未完成任务：{latest_unfinished['today_plan']}")
        lines.append(f"所属项目：{latest_unfinished['project_name']}")
        lines.append("建议今天先处理这个未完成任务。")

    else:
        lines.append("目前没有未完成任务。")
        lines.append("建议今天创建一个新的 Daily Task。")
        lines.append("推荐任务：继续推进 Atlas 2.0 的 Daily Task 功能测试。")

    lines.append("")
    lines.append("今天最小完成标准：")
    lines.append("只要创建一个今日任务，并在晚上完成一次复盘，第二阶段就跑通了。")

    recommendation = "\n".join(lines)

    print("\n" + recommendation)

    write_to_project_log(
        "Atlas 2.0 Daily Task 今日建议",
        recommendation
    )


def format_task_detail(task):
    """格式化任务详情。"""
    return (
        f"日期：{task['date']}\n"
        f"创建时间：{task['created_time']}\n"
        f"项目：{task['project_name']}\n"
        f"今天计划：{task['today_plan']}\n"
        f"预计时间：{task['estimated_hours']} 小时\n"
        f"优先级：{task['priority']}\n"
        f"为什么做：{task['reason']}\n"
        f"当前状态：{task['status']}\n"
        f"是否已晚上复盘：{task['evening_review_done']}\n"
        f"实际完成：{task['finished_result']}\n"
        f"遇到的问题：{task['problem']}\n"
        f"下一步：{task['next_step']}\n"
        f"导师评价：{task['mentor_comment']}"
    )


def format_task_short(task):
    """格式化任务简短信息。"""
    return (
        f"日期：{task['date']}\n"
        f"项目：{task['project_name']}\n"
        f"计划：{task['today_plan']}\n"
        f"状态：{task['status']}\n"
        f"下一步：{task['next_step'] if task['next_step'] else '暂无'}"
    )


def test_log_write():
    """测试 project_log.txt 是否能写入。"""
    content = (
        "这是 Atlas 2.0 Daily Task 的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明 Daily Task 日志保存正常。"
    )

    write_to_project_log(
        "Atlas 2.0 Daily Task 日志写入测试",
        content
    )


def auto_morning_check(data):
    """程序启动时自动检查今天是否已有任务。"""
    today_task = find_today_task(data)

    if today_task is not None:
        print("\n机器人提醒：今天已经有 Daily Task。")
        print(f"今天计划：{today_task['today_plan']}")
        print(f"当前状态：{today_task['status']}")
        return

    print("\n机器人提醒：今天还没有 Daily Task。")
    print("Atlas 2.0 第二阶段要求每天形成 Todo。")
    answer = input("现在要创建今天任务吗？输入 y 创建，其他键跳过：").strip().lower()

    if answer == "y":
        create_today_task(data)
    else:
        print("已跳过。你可以稍后在菜单里选择 1 创建今天任务。")


def show_intro(data):
    """显示开头。"""
    print("\n==============================")
    print("Atlas 2.0")
    print("Daily Task 每日任务")
    print("==============================")
    print(f"学生：{data['student_name']}")
    print(f"任务数据库版本：{data['task_database_version']}")
    print(f"任务数据库文件：{TASKS_FILE}")
    print(f"项目日志文件：{PROJECT_LOG_FILE}")
    print("当前目标：每天自动形成 Todo，并在晚上复盘是否完成")
    print("==============================")


def main():
    data = load_tasks_database()
    show_intro(data)

    write_to_project_log(
        "Atlas 2.0 Daily Task 程序启动",
        "Atlas 2.0 Daily Task 程序已启动。"
    )

    auto_morning_check(data)

    while True:
        print("\n请选择功能：")
        print("1. 创建或更新今天的 Daily Task")
        print("2. 查看今天的 Daily Task")
        print("3. 晚上复盘：今天完成了吗")
        print("4. 查看全部 Daily Task")
        print("5. 查看未完成任务")
        print("6. 机器人建议：今天应该做什么")
        print("7. 测试 project_log.txt 是否能写入")
        print("8. 退出")

        choice = input("请输入数字 1-8：").strip()

        if choice == "1":
            create_today_task(data)

        elif choice == "2":
            show_today_task(data)

        elif choice == "3":
            evening_review(data)

        elif choice == "4":
            show_all_tasks(data)

        elif choice == "5":
            show_unfinished_tasks(data)

        elif choice == "6":
            ask_today_recommendation(data)

        elif choice == "7":
            test_log_write()

        elif choice == "8":
            write_to_project_log(
                "Atlas 2.0 Daily Task 程序退出",
                "Atlas 2.0 Daily Task 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            message = f"输入无效：{choice}"
            print("输入无效，请输入 1 到 8。")
            write_to_project_log("Atlas 2.0 Daily Task 无效输入记录", message)


if __name__ == "__main__":
    main()