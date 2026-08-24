import json
from datetime import datetime, date
from pathlib import Path


# 固定路径，防止写到别的目录
BASE_DIR = Path(__file__).resolve().parent

BUGS_FILE = BASE_DIR / "bugs.json"
PROJECTS_FILE = BASE_DIR / "projects.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


def get_now_text():
    """获取当前时间。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_today_text():
    """获取今天日期。"""
    return date.today().strftime("%Y-%m-%d")


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


def save_bug_database(data):
    """保存 Bug 数据库。"""
    with open(BUGS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def create_default_bug_database():
    """如果 bugs.json 不存在，就自动创建默认 Bug 数据库。"""
    default_data = {
        "student_name": "Eric",
        "bug_database_version": "Atlas 2.0 Bug Manager v1",
        "bugs": []
    }

    save_bug_database(default_data)

    write_to_project_log(
        "Atlas 2.0 Bug Manager 初始化",
        "已创建 bugs.json Bug 数据库。"
    )

    return default_data


def load_bug_database():
    """读取 Bug 数据库。"""
    if not BUGS_FILE.exists():
        return create_default_bug_database()

    with open(BUGS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "bug_database_version" not in data:
        data["bug_database_version"] = "Atlas 2.0 Bug Manager v1"

    if "bugs" not in data:
        data["bugs"] = []

    save_bug_database(data)
    return data


def load_projects_database():
    """读取项目数据库，用于选择 Bug 所属项目。"""
    if not PROJECTS_FILE.exists():
        return []

    try:
        with open(PROJECTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("projects", [])

    except Exception:
        return []


def show_project_options():
    """显示项目选项。"""
    projects = load_projects_database()

    if not projects:
        print("\n没有找到 projects.json，可以手动输入项目名称。")
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


def get_next_bug_id(data):
    """生成新的 Bug ID。"""
    if not data["bugs"]:
        return 1

    existing_ids = [bug["id"] for bug in data["bugs"]]
    return max(existing_ids) + 1


def add_bug(data):
    """新增 Bug。"""
    print("\n开始记录一个新的 Bug。")
    print("每一项写一句话即可。")

    show_project_options()

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
        write_to_project_log(
            "Atlas 2.0 Bug Manager 新增 Bug 失败",
            "Bug 标题为空，本次没有保存。"
        )
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

    new_bug = {
        "id": get_next_bug_id(data),
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
        "mentor_comment": generate_bug_mentor_comment(
            bug_title,
            bug_description,
            severity,
            next_step
        )
    }

    data["bugs"].append(new_bug)
    save_bug_database(data)

    content = format_bug_detail(new_bug)

    write_to_project_log(
        "Atlas 2.0 Bug Manager 新增 Bug",
        content
    )

    print("\nBug 已保存：")
    print("-" * 50)
    print(content)
    print("-" * 50)


def generate_bug_mentor_comment(bug_title, bug_description, severity, next_step):
    """生成简单导师建议。"""
    if severity == "高":
        return (
            "这是高优先级 Bug。建议先暂停新增功能，优先复现问题、记录报错、缩小排查范围。"
        )

    if "摄像头" in bug_title or "OpenCV" in bug_title or "识别" in bug_title:
        return (
            "这是视觉识别类 Bug。建议先确认摄像头能否打开，再确认光线、距离、检测模型和阈值。"
        )

    if "Arduino" in bug_title or "舵机" in bug_title or "OLED" in bug_title or "灯" in bug_title:
        return (
            "这是硬件反馈类 Bug。建议先检查端口、接线、GND 是否共地，再检查 Python 是否成功发送指令。"
        )

    if "保存" in bug_title or "日志" in bug_title or "json" in bug_title.lower():
        return (
            "这是数据保存类 Bug。建议先检查文件路径是否固定，再检查 JSON 格式是否正确。"
        )

    return (
        f"建议下一步先做最小复现：只测试一个功能，并执行：{next_step}。"
    )


def show_all_bugs(data):
    """查看全部 Bug。"""
    bugs = data["bugs"]

    if not bugs:
        message = "目前还没有任何 Bug 记录。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 2.0 Bug Manager 查看全部 Bug",
            message
        )
        return

    print("\n全部 Bug：")
    print("-" * 50)

    lines = []

    for bug in bugs:
        detail = format_bug_short(bug)
        print(detail)
        print("-" * 50)
        lines.append(detail)

    write_to_project_log(
        "Atlas 2.0 Bug Manager 查看全部 Bug",
        "\n\n".join(lines)
    )


def show_open_bugs(data):
    """查看未解决 Bug。"""
    open_bugs = []

    for bug in data["bugs"]:
        if bug["status"] != "已解决":
            open_bugs.append(bug)

    if not open_bugs:
        message = "目前没有未解决 Bug。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 2.0 Bug Manager 查看未解决 Bug",
            message
        )
        return

    print("\n未解决 Bug：")
    print("-" * 50)

    lines = []

    for bug in open_bugs:
        detail = format_bug_short(bug)
        print(detail)
        print("-" * 50)
        lines.append(detail)

    write_to_project_log(
        "Atlas 2.0 Bug Manager 查看未解决 Bug",
        "\n\n".join(lines)
    )


def find_bug_by_id(data, bug_id):
    """根据 ID 查找 Bug。"""
    for bug in data["bugs"]:
        if bug["id"] == bug_id:
            return bug

    return None


def show_one_bug(data):
    """查看单个 Bug 详情。"""
    bug_id_text = input("\n请输入 Bug ID：").strip()

    if not bug_id_text.isdigit():
        message = "输入错误，请输入数字 Bug ID。"
        print(message)

        write_to_project_log(
            "Atlas 2.0 Bug Manager 查看 Bug 失败",
            message
        )
        return

    bug_id = int(bug_id_text)
    bug = find_bug_by_id(data, bug_id)

    if bug is None:
        message = f"没有找到 ID 为 {bug_id} 的 Bug。"
        print(message)

        write_to_project_log(
            "Atlas 2.0 Bug Manager 查看 Bug 失败",
            message
        )
        return

    content = format_bug_detail(bug)

    print("\nBug 详情：")
    print("-" * 50)
    print(content)
    print("-" * 50)

    write_to_project_log(
        "Atlas 2.0 Bug Manager 查看单个 Bug",
        content
    )


def update_bug_status(data):
    """更新 Bug 状态。"""
    bug_id_text = input("\n请输入要更新的 Bug ID：").strip()

    if not bug_id_text.isdigit():
        message = "输入错误，请输入数字 Bug ID。"
        print(message)

        write_to_project_log(
            "Atlas 2.0 Bug Manager 更新 Bug 失败",
            message
        )
        return

    bug_id = int(bug_id_text)
    bug = find_bug_by_id(data, bug_id)

    if bug is None:
        message = f"没有找到 ID 为 {bug_id} 的 Bug。"
        print(message)

        write_to_project_log(
            "Atlas 2.0 Bug Manager 更新 Bug 失败",
            message
        )
        return

    print("\n当前 Bug：")
    print(f"Bug 标题：{bug['bug_title']}")
    print(f"当前状态：{bug['status']}")
    print(f"当前下一步：{bug['next_step']}")

    old_status = bug["status"]
    old_solution = bug["solution"]
    old_next_step = bug["next_step"]

    new_status = input("\n新的状态（未解决 / 排查中 / 已解决）：").strip()
    solution = input("解决方法或当前排查结果：").strip()
    next_step = input("下一步：").strip()

    if new_status not in ["未解决", "排查中", "已解决"]:
        new_status = bug["status"]

    if solution:
        bug["solution"] = solution

    if next_step:
        bug["next_step"] = next_step

    bug["status"] = new_status

    if new_status == "已解决":
        bug["fixed_time"] = get_now_text()

    save_bug_database(data)

    content = (
        f"更新 Bug ID：{bug['id']}\n"
        f"Bug 标题：{bug['bug_title']}\n"
        f"状态：{old_status} → {bug['status']}\n"
        f"解决方法：{old_solution} → {bug['solution']}\n"
        f"下一步：{old_next_step} → {bug['next_step']}\n"
        f"修复时间：{bug['fixed_time'] if bug['fixed_time'] else '未修复'}"
    )

    write_to_project_log(
        "Atlas 2.0 Bug Manager 更新 Bug 状态",
        content
    )

    print("\nBug 已更新：")
    print("-" * 50)
    print(content)
    print("-" * 50)


def search_bugs(data):
    """搜索 Bug。"""
    keyword = input("\n请输入搜索关键词：").strip()

    if not keyword:
        print("关键词不能为空。")
        return

    matched_bugs = []

    for bug in data["bugs"]:
        search_text = (
            bug["project_name"] + " "
            + bug["bug_title"] + " "
            + bug["bug_description"] + " "
            + bug["trigger_condition"] + " "
            + bug["attempted_solution"] + " "
            + bug["status"] + " "
            + bug["next_step"]
        )

        if keyword.lower() in search_text.lower():
            matched_bugs.append(bug)

    if not matched_bugs:
        message = f"没有找到包含关键词「{keyword}」的 Bug。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 2.0 Bug Manager 搜索 Bug",
            message
        )
        return

    print(f"\n找到 {len(matched_bugs)} 个相关 Bug：")
    print("-" * 50)

    lines = []

    for bug in matched_bugs:
        detail = format_bug_short(bug)
        print(detail)
        print("-" * 50)
        lines.append(detail)

    write_to_project_log(
        "Atlas 2.0 Bug Manager 搜索 Bug",
        f"搜索关键词：{keyword}\n\n" + "\n\n".join(lines)
    )


def ask_bug_summary(data):
    """机器人总结当前 Bug 情况。"""
    bugs = data["bugs"]

    total_count = len(bugs)
    open_count = 0
    checking_count = 0
    fixed_count = 0
    high_count = 0

    for bug in bugs:
        if bug["status"] == "未解决":
            open_count += 1
        elif bug["status"] == "排查中":
            checking_count += 1
        elif bug["status"] == "已解决":
            fixed_count += 1

        if bug["severity"] == "高":
            high_count += 1

    summary = (
        f"Eric 当前一共有 {total_count} 个 Bug 记录。\n"
        f"未解决 Bug：{open_count} 个。\n"
        f"排查中 Bug：{checking_count} 个。\n"
        f"已解决 Bug：{fixed_count} 个。\n"
        f"高严重程度 Bug：{high_count} 个。\n"
    )

    if open_count > 0 or checking_count > 0:
        summary += "建议：下一步不要急着新增功能，先处理未解决和排查中的 Bug。"
    else:
        summary += "建议：当前 Bug 状态较好，可以继续推进下一阶段功能。"

    print("\n机器人 Bug 总结：")
    print(summary)

    write_to_project_log(
        "Atlas 2.0 Bug Manager Bug 总结",
        summary
    )


def format_bug_short(bug):
    """简短格式显示 Bug。"""
    return (
        f"Bug ID：{bug['id']}\n"
        f"日期：{bug['date']}\n"
        f"项目：{bug['project_name']}\n"
        f"标题：{bug['bug_title']}\n"
        f"状态：{bug['status']}\n"
        f"严重程度：{bug['severity']}\n"
        f"下一步：{bug['next_step']}"
    )


def format_bug_detail(bug):
    """详细格式显示 Bug。"""
    return (
        f"Bug ID：{bug['id']}\n"
        f"日期：{bug['date']}\n"
        f"创建时间：{bug['created_time']}\n"
        f"项目：{bug['project_name']}\n"
        f"Bug 标题：{bug['bug_title']}\n"
        f"Bug 现象：{bug['bug_description']}\n"
        f"触发条件：{bug['trigger_condition']}\n"
        f"已尝试方法：{bug['attempted_solution']}\n"
        f"严重程度：{bug['severity']}\n"
        f"状态：{bug['status']}\n"
        f"解决方法：{bug['solution'] if bug['solution'] else '暂无'}\n"
        f"修复时间：{bug['fixed_time'] if bug['fixed_time'] else '未修复'}\n"
        f"下一步：{bug['next_step']}\n"
        f"导师建议：{bug['mentor_comment']}"
    )


def test_log_write():
    """测试 project_log.txt 是否能写入。"""
    content = (
        "这是 Atlas 2.0 Bug Manager 的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明 Bug Manager 日志保存正常。"
    )

    write_to_project_log(
        "Atlas 2.0 Bug Manager 日志写入测试",
        content
    )


def show_intro(data):
    """显示开头。"""
    print("\n==============================")
    print("Atlas 2.0")
    print("Bug Manager")
    print("==============================")
    print(f"学生：{data['student_name']}")
    print(f"Bug 数据库版本：{data['bug_database_version']}")
    print(f"Bug 数据库文件：{BUGS_FILE}")
    print(f"项目日志文件：{PROJECT_LOG_FILE}")
    print("当前目标：记录、查询、更新、总结 Bug")
    print("==============================")


def main():
    data = load_bug_database()
    show_intro(data)

    write_to_project_log(
        "Atlas 2.0 Bug Manager 程序启动",
        "Atlas 2.0 Bug Manager 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 新增 Bug")
        print("2. 查看全部 Bug")
        print("3. 查看未解决 Bug")
        print("4. 查看单个 Bug 详情")
        print("5. 更新 Bug 状态")
        print("6. 搜索 Bug")
        print("7. 机器人总结当前 Bug 情况")
        print("8. 测试 project_log.txt 是否能写入")
        print("9. 退出")

        choice = input("请输入数字 1-9：").strip()

        if choice == "1":
            add_bug(data)

        elif choice == "2":
            show_all_bugs(data)

        elif choice == "3":
            show_open_bugs(data)

        elif choice == "4":
            show_one_bug(data)

        elif choice == "5":
            update_bug_status(data)

        elif choice == "6":
            search_bugs(data)

        elif choice == "7":
            ask_bug_summary(data)

        elif choice == "8":
            test_log_write()

        elif choice == "9":
            write_to_project_log(
                "Atlas 2.0 Bug Manager 程序退出",
                "Atlas 2.0 Bug Manager 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            message = f"输入无效：{choice}"
            print("输入无效，请输入 1 到 9。")
            write_to_project_log("Atlas 2.0 Bug Manager 无效输入记录", message)


if __name__ == "__main__":
    main()