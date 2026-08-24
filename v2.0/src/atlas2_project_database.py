import json
from datetime import datetime
from pathlib import Path


# 关键修复：
# 所有文件都固定保存在当前这个 Python 文件所在的文件夹里
BASE_DIR = Path(__file__).resolve().parent

PROJECTS_FILE = BASE_DIR / "projects.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


def get_now_text():
    """获取当前时间。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_to_project_log(title, content):
    """写入 project_log.txt，并在终端显示准确路径。"""
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


def save_database(data):
    """保存项目数据库。"""
    with open(PROJECTS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def create_default_database():
    """如果没有 projects.json，就自动创建默认项目数据库。"""
    default_data = {
        "student_name": "Eric",
        "project_database_version": "Atlas 2.0 Project Database v1",
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
                "status": "开发中",
                "progress": 20,
                "category": "Project Management Robot",
                "description": "目标是让机器人学会管理项目、每日任务、Bug 和周报。",
                "next_step": "完成 Project Database 项目数据库。"
            }
        ]
    }

    save_database(default_data)

    write_to_project_log(
        "Atlas 2.0 Project Database 初始化",
        "已自动创建 projects.json 项目数据库。"
    )

    return default_data


def load_database():
    """读取项目数据库。"""
    if not PROJECTS_FILE.exists():
        return create_default_database()

    with open(PROJECTS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "project_database_version" not in data:
        data["project_database_version"] = "Atlas 2.0 Project Database v1"

    if "projects" not in data:
        data["projects"] = []

    save_database(data)
    return data


def generate_project_summary(data):
    """生成项目数据库总结。"""
    projects = data["projects"]
    total_projects = len(projects)

    completed_count = 0
    developing_count = 0
    other_count = 0

    atlas_progress = "未找到 Atlas 2.0 项目"

    for project in projects:
        if project["status"] == "完成":
            completed_count += 1
        elif project["status"] == "开发中":
            developing_count += 1
        else:
            other_count += 1

        if "Atlas 2.0" in project["name"]:
            atlas_progress = f"{project['progress']}%"

    summary = (
        f"Eric 现在一共有 {total_projects} 个项目。\n"
        f"已完成项目：{completed_count} 个。\n"
        f"开发中项目：{developing_count} 个。\n"
        f"其他状态项目：{other_count} 个。\n"
        f"目前 Atlas 2.0 完成度：{atlas_progress}。"
    )

    return summary


def show_all_projects(data):
    """显示所有项目。"""
    projects = data["projects"]

    if not projects:
        print("\n目前还没有项目。")
        write_to_project_log(
            "Atlas 2.0 Project Database 查看全部项目",
            "目前还没有项目。"
        )
        return

    print("\nEric 的项目数据库：")
    print("-" * 50)

    lines = []

    for project in projects:
        text = (
            f"项目 ID：{project['id']}\n"
            f"项目名称：{project['name']}\n"
            f"状态：{project['status']}\n"
            f"完成度：{project['progress']}%\n"
            f"类别：{project['category']}\n"
            f"说明：{project['description']}\n"
            f"下一步：{project['next_step']}"
        )

        print(text)
        print("-" * 50)

        lines.append(text)

    content = "\n\n".join(lines)

    write_to_project_log(
        "Atlas 2.0 Project Database 查看全部项目",
        content
    )


def ask_project_summary(data):
    """让机器人回答项目总览。"""
    summary = generate_project_summary(data)

    print("\n机器人回答：")
    print(summary)

    write_to_project_log(
        "Atlas 2.0 Project Database 项目总览回答",
        summary
    )


def find_project_by_id(data, project_id):
    """根据 ID 找项目。"""
    for project in data["projects"]:
        if project["id"] == project_id:
            return project

    return None


def show_one_project(data):
    """查看单个项目。"""
    project_id_text = input("\n请输入项目 ID：").strip()

    if not project_id_text.isdigit():
        message = "输入错误，请输入数字 ID。"
        print(message)
        write_to_project_log("Atlas 2.0 查看单个项目失败", message)
        return

    project_id = int(project_id_text)
    project = find_project_by_id(data, project_id)

    if project is None:
        message = f"没有找到 ID 为 {project_id} 的项目。"
        print(message)
        write_to_project_log("Atlas 2.0 查看单个项目失败", message)
        return

    content = (
        f"项目 ID：{project['id']}\n"
        f"项目名称：{project['name']}\n"
        f"状态：{project['status']}\n"
        f"完成度：{project['progress']}%\n"
        f"类别：{project['category']}\n"
        f"说明：{project['description']}\n"
        f"下一步：{project['next_step']}"
    )

    print("\n项目详情：")
    print("-" * 50)
    print(content)
    print("-" * 50)

    write_to_project_log(
        "Atlas 2.0 Project Database 查看单个项目",
        content
    )


def add_new_project(data):
    """新增项目。"""
    print("\n开始新增项目。")

    name = input("项目名称：").strip()
    status = input("项目状态（完成 / 开发中 / 暂停）：").strip()
    progress_text = input("完成度数字，例如 20：").strip()
    category = input("项目类别：").strip()
    description = input("项目说明：").strip()
    next_step = input("下一步：").strip()

    if not name:
        message = "项目名称不能为空，本次没有新增。"
        print(message)
        write_to_project_log("Atlas 2.0 新增项目失败", message)
        return

    if not status:
        status = "开发中"

    if progress_text.isdigit():
        progress = int(progress_text)
    else:
        progress = 0

    if progress < 0:
        progress = 0

    if progress > 100:
        progress = 100

    if not category:
        category = "未分类"

    if not description:
        description = "暂无说明"

    if not next_step:
        next_step = "继续推进项目"

    existing_ids = [project["id"] for project in data["projects"]]

    if existing_ids:
        new_id = max(existing_ids) + 1
    else:
        new_id = 1

    new_project = {
        "id": new_id,
        "name": name,
        "status": status,
        "progress": progress,
        "category": category,
        "description": description,
        "next_step": next_step
    }

    data["projects"].append(new_project)
    save_database(data)

    content = (
        f"新增项目 ID：{new_id}\n"
        f"项目名称：{name}\n"
        f"状态：{status}\n"
        f"完成度：{progress}%\n"
        f"类别：{category}\n"
        f"说明：{description}\n"
        f"下一步：{next_step}"
    )

    write_to_project_log(
        "Atlas 2.0 Project Database 新增项目",
        content
    )

    print("\n项目已新增。")
    print(content)


def update_project_progress(data):
    """更新项目状态和完成度。"""
    project_id_text = input("\n请输入要更新的项目 ID：").strip()

    if not project_id_text.isdigit():
        message = "输入错误，请输入数字 ID。"
        print(message)
        write_to_project_log("Atlas 2.0 更新项目失败", message)
        return

    project_id = int(project_id_text)
    project = find_project_by_id(data, project_id)

    if project is None:
        message = f"没有找到 ID 为 {project_id} 的项目。"
        print(message)
        write_to_project_log("Atlas 2.0 更新项目失败", message)
        return

    print("\n当前项目：")
    print(f"项目名称：{project['name']}")
    print(f"当前状态：{project['status']}")
    print(f"当前完成度：{project['progress']}%")
    print(f"当前下一步：{project['next_step']}")

    old_status = project["status"]
    old_progress = project["progress"]
    old_next_step = project["next_step"]

    new_status = input("\n新的状态（不改就直接回车）：").strip()
    new_progress_text = input("新的完成度数字（不改就直接回车）：").strip()
    new_next_step = input("新的下一步（不改就直接回车）：").strip()

    if new_status:
        project["status"] = new_status

    if new_progress_text:
        if new_progress_text.isdigit():
            new_progress = int(new_progress_text)

            if new_progress < 0:
                new_progress = 0

            if new_progress > 100:
                new_progress = 100

            project["progress"] = new_progress
        else:
            print("完成度不是数字，所以没有修改完成度。")

    if new_next_step:
        project["next_step"] = new_next_step

    save_database(data)

    content = (
        f"更新项目：{project['name']}\n"
        f"状态：{old_status} → {project['status']}\n"
        f"完成度：{old_progress}% → {project['progress']}%\n"
        f"下一步：{old_next_step} → {project['next_step']}"
    )

    write_to_project_log(
        "Atlas 2.0 Project Database 更新项目",
        content
    )

    print("\n项目已更新。")
    print(content)


def ask_atlas_progress(data):
    """查询 Atlas 2.0 完成度。"""
    atlas_project = None

    for project in data["projects"]:
        if "Atlas 2.0" in project["name"]:
            atlas_project = project
            break

    if atlas_project is None:
        answer = "我没有在项目数据库里找到 Atlas 2.0。"
        print(answer)
        write_to_project_log("Atlas 2.0 完成度查询", answer)
        return

    answer = (
        f"Atlas 2.0 当前状态是：{atlas_project['status']}。\n"
        f"当前完成度是：{atlas_project['progress']}%。\n"
        f"当前下一步是：{atlas_project['next_step']}。"
    )

    print("\n机器人回答：")
    print(answer)

    write_to_project_log(
        "Atlas 2.0 完成度查询",
        answer
    )


def test_log_write():
    """专门测试 project_log.txt 是否能写入。"""
    content = (
        "这是一次日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明日志保存功能已经正常。"
    )

    write_to_project_log(
        "Atlas 2.0 Project Log 写入测试",
        content
    )

    print("\n请打开下面这个文件检查：")
    print(PROJECT_LOG_FILE)


def show_intro(data):
    """显示程序开头。"""
    print("\n==============================")
    print("Atlas 2.0")
    print("Project Database 项目数据库")
    print("==============================")
    print(f"学生：{data['student_name']}")
    print(f"数据库版本：{data['project_database_version']}")
    print(f"项目数据库文件：{PROJECTS_FILE}")
    print(f"项目日志文件：{PROJECT_LOG_FILE}")
    print("==============================")


def main():
    data = load_database()
    show_intro(data)

    write_to_project_log(
        "Atlas 2.0 Project Database 程序启动",
        "Atlas 2.0 Project Database 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 查看全部项目")
        print("2. 机器人回答：Eric 现在有几个项目")
        print("3. 查看单个项目")
        print("4. 新增项目")
        print("5. 更新项目状态和完成度")
        print("6. 查询 Atlas 2.0 当前完成度")
        print("7. 测试 project_log.txt 是否能写入")
        print("8. 退出")

        choice = input("请输入数字 1-8：").strip()

        if choice == "1":
            show_all_projects(data)

        elif choice == "2":
            ask_project_summary(data)

        elif choice == "3":
            show_one_project(data)

        elif choice == "4":
            add_new_project(data)

        elif choice == "5":
            update_project_progress(data)

        elif choice == "6":
            ask_atlas_progress(data)

        elif choice == "7":
            test_log_write()

        elif choice == "8":
            write_to_project_log(
                "Atlas 2.0 Project Database 程序退出",
                "Atlas 2.0 Project Database 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            message = f"输入无效：{choice}"
            print("输入无效，请输入 1 到 8。")
            write_to_project_log("Atlas 2.0 无效输入记录", message)


if __name__ == "__main__":
    main()