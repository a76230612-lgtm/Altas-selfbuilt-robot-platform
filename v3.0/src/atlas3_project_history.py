import json
from datetime import datetime
from pathlib import Path


# 固定路径，防止写到别的目录
BASE_DIR = Path(__file__).resolve().parent

HISTORY_FILE = BASE_DIR / "history.json"
PROFILE_FILE = BASE_DIR / "profile.json"
SKILLS_FILE = BASE_DIR / "skills.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


class ProjectHistory:
    """Atlas 3.0 第三阶段：Project History 项目历史"""

    def __init__(self, data):
        self.student_name = data.get("student_name", "Eric")
        self.history_database_version = data.get(
            "history_database_version",
            "Atlas 3.0 Project History v1"
        )
        self.project_history = data.get("project_history", [])

    def to_dict(self):
        return {
            "student_name": self.student_name,
            "history_database_version": self.history_database_version,
            "project_history": self.project_history
        }

    def get_all_projects(self):
        return self.project_history

    def find_project_by_name(self, keyword):
        matched_projects = []

        for project in self.project_history:
            project_name = project.get("project_name", "")

            if keyword.lower() in project_name.lower():
                matched_projects.append(project)

        return matched_projects

    def get_completed_projects(self):
        completed_projects = []

        for project in self.project_history:
            if project.get("status") == "completed":
                completed_projects.append(project)

        return completed_projects

    def get_current_projects(self):
        current_projects = []

        for project in self.project_history:
            if project.get("status") == "in_progress":
                current_projects.append(project)

        return current_projects

    def get_all_skills_from_history(self):
        all_skills = []

        for project in self.project_history:
            skills = project.get("skills_learned", [])

            for skill in skills:
                if skill not in all_skills:
                    all_skills.append(skill)

        return all_skills

    def generate_history_summary(self):
        completed_projects = self.get_completed_projects()
        current_projects = self.get_current_projects()
        all_skills = self.get_all_skills_from_history()

        lines = []

        lines.append(f"{self.student_name} 的 Project History 项目历史")
        lines.append(f"数据库版本：{self.history_database_version}")
        lines.append("")

        lines.append("一、项目数量总结")
        lines.append(f"项目总数：{len(self.project_history)} 个")
        lines.append(f"已完成项目：{len(completed_projects)} 个")
        lines.append(f"进行中项目：{len(current_projects)} 个")
        lines.append("")

        lines.append("二、项目演进路线")
        for project in self.project_history:
            lines.append(
                f"- {project.get('project_name', '未命名项目')} "
                f"({project.get('version', '无版本')}) | "
                f"状态：{project.get('status', 'unknown')}"
            )

        lines.append("")

        lines.append("三、历史项目累计技能")
        if all_skills:
            for skill in all_skills:
                lines.append(f"- {skill}")
        else:
            lines.append("- 暂时没有记录到技能。")

        lines.append("")

        lines.append("四、机器人判断")
        lines.append(
            "Eric 的项目不是孤立的。植物系统训练了硬件和串口通信，"
            "Atlas 1.0 训练了记忆、日志、硬件反馈和摄像头，"
            "Atlas 2.0 训练了项目管理、任务管理、Bug 管理和周报，"
            "Atlas 3.0 正在把这些历史经验整合成 Eric Digital Twin。"
        )

        return "\n".join(lines)

    def generate_transfer_advice(self):
        lines = []

        lines.append(f"{self.student_name}，我已经读取你的 Project History。")
        lines.append("")
        lines.append("机器人判断：")

        plant_projects = self.find_project_by_name("植物")
        atlas1_projects = self.find_project_by_name("Atlas 1")
        atlas2_projects = self.find_project_by_name("Atlas 2")
        atlas3_projects = self.find_project_by_name("Atlas 3")

        if plant_projects:
            lines.append(
                "- 你在智能植物养护系统里已经学过 Arduino、传感器、硬件接线和串口通信。"
            )
            lines.append(
                "  所以现在做 Atlas 时，不需要重新从基础 Arduino 开始。"
            )

        if atlas1_projects:
            lines.append(
                "- 你在 Atlas 1.0 里已经学过长期记忆、Project Log、导师建议、情绪支持、Arduino/OLED 和摄像头检测。"
            )
            lines.append(
                "  所以 Atlas 3.0 不应该继续只堆功能，而应该开始理解 Eric。"
            )

        if atlas2_projects:
            lines.append(
                "- 你在 Atlas 2.0 里已经学过 Project Database、Daily Task、Bug Manager 和 Weekly Report。"
            )
            lines.append(
                "  所以 Atlas 3.0 可以在这些管理能力上继续发展长期成长画像。"
            )

        if atlas3_projects:
            lines.append(
                "- 你现在正在做 Atlas 3.0。重点是 Profile、Skill Database、Project History、Learning Planner、Emotion Memory 和 Mentor Recommendation。"
            )

        lines.append("")
        lines.append("导师建议：")
        lines.append(
            "下一步不要重复做已经会的硬件反馈。你现在应该把历史项目变成可查询的成长证据。"
        )
        lines.append(
            "Atlas 3.0 的价值在于：机器人能根据 Eric 过去做过什么、学会什么、卡在哪里，给出更精准的下一步建议。"
        )

        lines.append("")
        lines.append("今天的最小完成标准：")
        lines.append(
            "只要机器人能说出：Eric 从植物系统到 Atlas 1.0、Atlas 2.0、Atlas 3.0 的成长路线，第三阶段就跑通。"
        )

        return "\n".join(lines)


def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_to_project_log(title, content):
    """写入 project_log.txt。"""
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


def create_default_history_data():
    return {
        "student_name": "Eric",
        "history_database_version": "Atlas 3.0 Project History v1",
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
                    "Project History"
                ],
                "key_problems": [
                    "Need to connect profile, skills, and project history",
                    "Need to make Atlas give advice based on Eric's past experience"
                ],
                "transfer_to_atlas": "Atlas 3.0 will use Eric's profile, skills, and project history to generate personalized mentor advice.",
                "evidence": "profile.json, skills.json, history.json, project_log.txt"
            }
        ]
    }


def create_default_history_file():
    default_data = create_default_history_data()
    save_history_dict(default_data)

    write_to_project_log(
        "Atlas 3.0 Project History 初始化",
        "已创建 history.json，建立 Eric 的项目历史数据库。"
    )

    return default_data


def load_history_dict():
    if not HISTORY_FILE.exists():
        return create_default_history_file()

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        print("\nhistory.json 读取失败，将重新创建默认 Project History。")
        return create_default_history_file()

    default_data = create_default_history_data()

    if "student_name" not in data:
        data["student_name"] = default_data["student_name"]

    if "history_database_version" not in data:
        data["history_database_version"] = default_data["history_database_version"]

    if "project_history" not in data:
        data["project_history"] = default_data["project_history"]

    save_history_dict(data)
    return data


def save_history_dict(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_project_history():
    data = load_history_dict()
    return ProjectHistory(data)


def save_project_history(project_history):
    save_history_dict(project_history.to_dict())


def show_history_summary(project_history):
    summary = project_history.generate_history_summary()

    print("\nProject History 项目历史总结：")
    print("-" * 70)
    print(summary)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Project History 查看项目历史",
        summary
    )


def show_transfer_advice(project_history):
    advice = project_history.generate_transfer_advice()

    print("\n基于 Project History 的迁移建议：")
    print("-" * 70)
    print(advice)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Project History 项目迁移建议",
        advice
    )


def show_all_projects(project_history):
    projects = project_history.get_all_projects()

    print("\n全部历史项目：")
    print("-" * 70)

    lines = []

    for project in projects:
        content = format_project_detail(project)
        print(content)
        print("-" * 70)
        lines.append(content)

    write_to_project_log(
        "Atlas 3.0 Project History 查看全部项目",
        "\n\n".join(lines)
    )


def search_project(project_history):
    keyword = input("\n请输入搜索关键词，例如 植物 / Atlas 1 / Atlas 2：").strip()

    if not keyword:
        print("关键词不能为空。")
        return

    matched_projects = project_history.find_project_by_name(keyword)

    if not matched_projects:
        message = f"没有找到包含关键词「{keyword}」的项目。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 3.0 Project History 搜索项目",
            message
        )
        return

    print(f"\n找到 {len(matched_projects)} 个相关项目：")
    print("-" * 70)

    lines = []

    for project in matched_projects:
        content = format_project_detail(project)
        print(content)
        print("-" * 70)
        lines.append(content)

    write_to_project_log(
        "Atlas 3.0 Project History 搜索项目",
        f"搜索关键词：{keyword}\n\n" + "\n\n".join(lines)
    )


def add_project_history(project_history):
    print("\n新增一个历史项目。")
    print("每一项写一句话即可。")

    project_name = input("项目名称：").strip()
    version = input("版本，例如 1.0：").strip()
    status = input("状态 completed / in_progress：").strip()
    project_type = input("项目类型：").strip()
    main_goal = input("项目目标：").strip()
    skills_text = input("学到的技能，用英文逗号分隔：").strip()
    problems_text = input("遇到的问题，用英文逗号分隔：").strip()
    transfer_to_atlas = input("这个项目如何迁移到 Atlas？").strip()
    evidence = input("项目证据，例如 Demo / Log / Code：").strip()

    if not project_name:
        print("项目名称不能为空，本次不保存。")
        return

    if not version:
        version = "unknown"

    if status not in ["completed", "in_progress"]:
        status = "completed"

    if not project_type:
        project_type = "Engineering Project"

    if not main_goal:
        main_goal = "暂无项目目标"

    skills_learned = split_text_to_list(skills_text)
    key_problems = split_text_to_list(problems_text)

    if not skills_learned:
        skills_learned = ["Project Experience"]

    if not key_problems:
        key_problems = ["暂无记录"]

    if not transfer_to_atlas:
        transfer_to_atlas = "这个项目为 Atlas 提供了历史经验。"

    if not evidence:
        evidence = "Project Log"

    new_project = {
        "id": get_next_project_id(project_history),
        "project_name": project_name,
        "version": version,
        "status": status,
        "project_type": project_type,
        "main_goal": main_goal,
        "skills_learned": skills_learned,
        "key_problems": key_problems,
        "transfer_to_atlas": transfer_to_atlas,
        "evidence": evidence
    }

    project_history.project_history.append(new_project)
    save_project_history(project_history)

    content = format_project_detail(new_project)

    print("\n历史项目已新增：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Project History 新增历史项目",
        content
    )


def update_project_status(project_history):
    project_id_text = input("\n请输入要更新的项目 ID：").strip()

    if not project_id_text.isdigit():
        print("请输入数字 ID。")
        return

    project_id = int(project_id_text)
    project = find_project_by_id(project_history, project_id)

    if project is None:
        print("没有找到这个项目。")
        return

    print("\n当前项目：")
    print(format_project_detail(project))

    old_status = project.get("status", "unknown")
    old_transfer = project.get("transfer_to_atlas", "")

    new_status = input("\n新的状态 completed / in_progress（不改直接回车）：").strip()
    new_transfer = input("新的迁移说明（不改直接回车）：").strip()

    if new_status in ["completed", "in_progress"]:
        project["status"] = new_status

    if new_transfer:
        project["transfer_to_atlas"] = new_transfer

    save_project_history(project_history)

    content = (
        f"项目 ID：{project_id}\n"
        f"项目名称：{project.get('project_name', '')}\n"
        f"状态：{old_status} → {project.get('status', '')}\n"
        f"迁移说明：{old_transfer} → {project.get('transfer_to_atlas', '')}"
    )

    print("\n项目已更新：")
    print(content)

    write_to_project_log(
        "Atlas 3.0 Project History 更新项目",
        content
    )


def robot_answer_history_question(project_history):
    question = input("\n请输入问题，例如：以前项目对现在有什么帮助？").strip()

    if not question:
        question = "以前项目对现在有什么帮助？"

    question_lower = question.lower()

    if "植物" in question:
        matched_projects = project_history.find_project_by_name("植物")

        if matched_projects:
            project = matched_projects[0]
            answer = (
                "你在智能植物养护系统里已经学过："
                + "、".join(project.get("skills_learned", []))
                + "。\n所以现在做 Atlas 时，不需要重新从基础 Arduino 和串口通信开始。"
            )
        else:
            answer = "我还没有在 Project History 里找到植物项目。"

    elif "atlas 1" in question_lower or "1.0" in question:
        matched_projects = project_history.find_project_by_name("Atlas 1")

        if matched_projects:
            project = matched_projects[0]
            answer = (
                "Atlas 1.0 让你学会了："
                + "、".join(project.get("skills_learned", []))
                + "。\n所以 Atlas 3.0 应该继续使用这些能力，而不是重新做基础聊天机器人。"
            )
        else:
            answer = "我还没有找到 Atlas 1.0 的历史记录。"

    elif "atlas 2" in question_lower or "2.0" in question:
        matched_projects = project_history.find_project_by_name("Atlas 2")

        if matched_projects:
            project = matched_projects[0]
            answer = (
                "Atlas 2.0 让你学会了："
                + "、".join(project.get("skills_learned", []))
                + "。\n这些能力会成为 Atlas 3.0 的管理层基础。"
            )
        else:
            answer = "我还没有找到 Atlas 2.0 的历史记录。"

    elif "帮助" in question or "以前" in question or "过去" in question:
        answer = project_history.generate_transfer_advice()

    else:
        answer = (
            "我会根据 Eric 的 Project History 来回答。\n"
            "目前最重要的判断是：Eric 的植物系统、Atlas 1.0、Atlas 2.0 都不是孤立项目，"
            "它们共同构成 Atlas 3.0 的长期记忆基础。"
        )

    print("\n机器人回答：")
    print("-" * 70)
    print(answer)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Project History 历史问题回答",
        f"Eric 的问题：{question}\n\n机器人回答：\n{answer}"
    )


def format_project_detail(project):
    skills_text = "、".join(project.get("skills_learned", []))
    problems_text = "、".join(project.get("key_problems", []))

    return (
        f"项目 ID：{project.get('id', '未知')}\n"
        f"项目名称：{project.get('project_name', '未命名项目')}\n"
        f"版本：{project.get('version', '无版本')}\n"
        f"状态：{project.get('status', 'unknown')}\n"
        f"项目类型：{project.get('project_type', '未知类型')}\n"
        f"项目目标：{project.get('main_goal', '暂无目标')}\n"
        f"学到的技能：{skills_text}\n"
        f"遇到的问题：{problems_text}\n"
        f"迁移到 Atlas：{project.get('transfer_to_atlas', '暂无说明')}\n"
        f"项目证据：{project.get('evidence', '暂无证据')}"
    )


def split_text_to_list(text):
    result = []

    if not text:
        return result

    for item in text.split(","):
        clean_item = item.strip()
        if clean_item:
            result.append(clean_item)

    return result


def get_next_project_id(project_history):
    ids = []

    for project in project_history.project_history:
        project_id = project.get("id")

        if isinstance(project_id, int):
            ids.append(project_id)

    if not ids:
        return 1

    return max(ids) + 1


def find_project_by_id(project_history, project_id):
    for project in project_history.project_history:
        if project.get("id") == project_id:
            return project

    return None


def test_log_write():
    content = (
        "这是 Atlas 3.0 Project History 的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明第三阶段日志保存正常。"
    )

    write_to_project_log(
        "Atlas 3.0 Project History 日志写入测试",
        content
    )


def show_intro(project_history):
    print("\n==============================")
    print("Atlas 3.0")
    print("Stage 3: Project History")
    print("==============================")
    print(f"学生：{project_history.student_name}")
    print(f"数据库版本：{project_history.history_database_version}")
    print(f"项目历史数据库文件：{HISTORY_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")
    print("当前目标：让机器人理解 Eric 的项目成长路线")
    print("==============================")


def main():
    project_history = load_project_history()
    show_intro(project_history)

    write_to_project_log(
        "Atlas 3.0 Project History 程序启动",
        "Atlas 3.0 第三阶段 Project History 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 查看 Project History 总结")
        print("2. 查看全部历史项目")
        print("3. 机器人建议：以前项目如何帮助现在")
        print("4. 搜索历史项目")
        print("5. 新增历史项目")
        print("6. 更新历史项目状态")
        print("7. 回答项目历史相关问题")
        print("8. 测试 project_log.txt 是否能写入")
        print("9. 退出")

        choice = input("请输入数字 1-9：").strip()

        if choice == "1":
            show_history_summary(project_history)

        elif choice == "2":
            show_all_projects(project_history)

        elif choice == "3":
            show_transfer_advice(project_history)

        elif choice == "4":
            search_project(project_history)

        elif choice == "5":
            add_project_history(project_history)

        elif choice == "6":
            update_project_status(project_history)

        elif choice == "7":
            robot_answer_history_question(project_history)

        elif choice == "8":
            test_log_write()

        elif choice == "9":
            write_to_project_log(
                "Atlas 3.0 Project History 程序退出",
                "Atlas 3.0 第三阶段 Project History 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 9。")
            write_to_project_log(
                "Atlas 3.0 Project History 无效输入",
                f"用户输入了无效菜单数字：{choice}"
            )


if __name__ == "__main__":
    main()