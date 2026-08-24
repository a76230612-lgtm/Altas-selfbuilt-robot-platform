import json
from datetime import datetime
from pathlib import Path


# 固定文件路径，防止写到别的目录
BASE_DIR = Path(__file__).resolve().parent

SKILLS_FILE = BASE_DIR / "skills.json"
PROFILE_FILE = BASE_DIR / "profile.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


class SkillDatabase:
    """Atlas 3.0 第二阶段：Skill Database 技能数据库"""

    def __init__(self, data):
        self.student_name = data.get("student_name", "Eric")
        self.skill_database_version = data.get(
            "skill_database_version",
            "Atlas 3.0 Skill Database v1"
        )
        self.skills = data.get("skills", {})
        self.next_learning_focus = data.get("next_learning_focus", "ROS2")

    def to_dict(self):
        """把 Class 转回 Dictionary，方便保存成 JSON。"""
        return {
            "student_name": self.student_name,
            "skill_database_version": self.skill_database_version,
            "skills": self.skills,
            "next_learning_focus": self.next_learning_focus
        }

    def get_skill_score(self, skill_name):
        """读取某项技能分数。"""
        skill = self.skills.get(skill_name)

        if skill is None:
            return None

        return skill.get("score", 0)

    def get_strong_skills(self):
        """找出强项技能：80分及以上。"""
        strong_skills = []

        for skill_name, skill_info in self.skills.items():
            score = skill_info.get("score", 0)

            if score >= 80:
                strong_skills.append({
                    "name": skill_name,
                    "score": score,
                    "note": skill_info.get("note", "")
                })

        return strong_skills

    def get_developing_skills(self):
        """找出发展中技能：40到79分。"""
        developing_skills = []

        for skill_name, skill_info in self.skills.items():
            score = skill_info.get("score", 0)

            if 40 <= score < 80:
                developing_skills.append({
                    "name": skill_name,
                    "score": score,
                    "note": skill_info.get("note", "")
                })

        return developing_skills

    def get_weak_skills(self):
        """找出薄弱技能：40分以下。"""
        weak_skills = []

        for skill_name, skill_info in self.skills.items():
            score = skill_info.get("score", 0)

            if score < 40:
                weak_skills.append({
                    "name": skill_name,
                    "score": score,
                    "note": skill_info.get("note", "")
                })

        return weak_skills

    def generate_skill_summary(self):
        """生成技能总结。"""
        strong_skills = self.get_strong_skills()
        developing_skills = self.get_developing_skills()
        weak_skills = self.get_weak_skills()

        lines = []

        lines.append(f"{self.student_name} 的 Skill Database 技能数据库")
        lines.append(f"数据库版本：{self.skill_database_version}")
        lines.append("")

        lines.append("一、全部技能：")

        for skill_name, skill_info in self.skills.items():
            score = skill_info.get("score", 0)
            level = skill_info.get("level", "unknown")
            note = skill_info.get("note", "")

            lines.append(
                f"- {skill_name}：{score} 分，level：{level}，说明：{note}"
            )

        lines.append("")

        lines.append("二、强项技能：")
        if strong_skills:
            for item in strong_skills:
                lines.append(f"- {item['name']}：{item['score']} 分")
        else:
            lines.append("- 暂时没有 80 分以上的强项技能。")

        lines.append("")

        lines.append("三、发展中技能：")
        if developing_skills:
            for item in developing_skills:
                lines.append(f"- {item['name']}：{item['score']} 分")
        else:
            lines.append("- 暂时没有发展中技能。")

        lines.append("")

        lines.append("四、需要补强技能：")
        if weak_skills:
            for item in weak_skills:
                lines.append(f"- {item['name']}：{item['score']} 分")
        else:
            lines.append("- 暂时没有明显薄弱技能。")

        lines.append("")

        lines.append(f"五、当前建议学习重点：{self.next_learning_focus}")

        return "\n".join(lines)

    def generate_next_learning_advice(self):
        """根据技能分数生成下一步学习建议。"""
        arduino_score = self.get_skill_score("Arduino")
        python_score = self.get_skill_score("Python")
        opencv_score = self.get_skill_score("OpenCV")
        yolo_score = self.get_skill_score("YOLO")
        ros2_score = self.get_skill_score("ROS2")

        lines = []

        lines.append(f"{self.student_name}，我已经读取你的技能数据库。")
        lines.append("")
        lines.append("机器人判断：")

        if arduino_score is not None and arduino_score >= 80:
            lines.append(f"- Arduino 已经达到 {arduino_score} 分，不需要继续重复基础 Arduino。")

        if python_score is not None and python_score >= 75:
            lines.append(f"- Python 已经达到 {python_score} 分，可以继续支持更复杂的机器人系统学习。")

        if opencv_score is not None and opencv_score >= 70:
            lines.append(f"- OpenCV 已经达到 {opencv_score} 分，说明你已经具备基础视觉感知能力。")

        if yolo_score is not None and 40 <= yolo_score < 80:
            lines.append(f"- YOLO 目前是 {yolo_score} 分，属于发展中技能，可以继续通过小项目练习。")

        if ros2_score is not None and ros2_score < 40:
            lines.append(f"- ROS2 目前是 {ros2_score} 分，是当前最明显的短板。")

        lines.append("")
        lines.append("导师建议：")

        if ros2_score is not None and ros2_score < 40:
            lines.append(
                "下一步建议开始学习 ROS2。原因是：如果 Eric 以后要做真正的机器人系统，"
                "ROS2 会比继续重复 Arduino 更重要。"
            )
        elif yolo_score is not None and yolo_score < 80:
            lines.append(
                "下一步建议继续提高 YOLO。原因是：机器人需要更强的视觉识别能力。"
            )
        elif python_score is not None and python_score < 90:
            lines.append(
                "下一步建议继续提高 Python 工程能力。原因是：Atlas 的长期记忆和规划系统都依赖 Python。"
            )
        else:
            lines.append(
                "目前基础技能状态较好，下一步可以进入 Project History 或 Learning Planner。"
            )

        lines.append("")
        lines.append("今天的最小完成标准：")
        lines.append("不要学习太多内容。只要确认 Skill Database 能读取技能分数，并能建议下一步学习 ROS2，就算第二阶段跑通。")

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


def create_default_skills_data():
    """默认技能数据库。"""
    return {
        "student_name": "Eric",
        "skill_database_version": "Atlas 3.0 Skill Database v1",
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
        "next_learning_focus": "ROS2"
    }


def create_default_skills_file():
    """如果 skills.json 不存在，就创建默认技能数据库。"""
    default_data = create_default_skills_data()

    save_skills_dict(default_data)

    write_to_project_log(
        "Atlas 3.0 Skill Database 初始化",
        "已创建 skills.json，建立 Eric 的技能数据库。"
    )

    return default_data


def load_skills_dict():
    """读取 skills.json。"""
    if not SKILLS_FILE.exists():
        return create_default_skills_file()

    try:
        with open(SKILLS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        print("\nskills.json 读取失败，将重新创建默认 Skill Database。")
        return create_default_skills_file()

    default_data = create_default_skills_data()

    if "student_name" not in data:
        data["student_name"] = default_data["student_name"]

    if "skill_database_version" not in data:
        data["skill_database_version"] = default_data["skill_database_version"]

    if "skills" not in data:
        data["skills"] = default_data["skills"]

    if "next_learning_focus" not in data:
        data["next_learning_focus"] = default_data["next_learning_focus"]

    for skill_name, skill_info in default_data["skills"].items():
        if skill_name not in data["skills"]:
            data["skills"][skill_name] = skill_info

    save_skills_dict(data)
    return data


def save_skills_dict(data):
    """保存 skills.json。"""
    with open(SKILLS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_skill_database():
    """读取技能数据库，并转成 Class。"""
    data = load_skills_dict()
    return SkillDatabase(data)


def save_skill_database(skill_database):
    """保存 SkillDatabase Class。"""
    save_skills_dict(skill_database.to_dict())


def show_skill_database(skill_database):
    """显示技能数据库。"""
    summary = skill_database.generate_skill_summary()

    print("\nSkill Database 技能数据库：")
    print("-" * 70)
    print(summary)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Skill Database 查看技能数据库",
        summary
    )


def show_next_learning_advice(skill_database):
    """显示下一步学习建议。"""
    advice = skill_database.generate_next_learning_advice()

    print("\n基于 Skill Database 的学习建议：")
    print("-" * 70)
    print(advice)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Skill Database 下一步学习建议",
        advice
    )


def update_one_skill(skill_database):
    """更新单项技能分数。"""
    print("\n当前技能：")

    for skill_name, skill_info in skill_database.skills.items():
        print(f"- {skill_name}：{skill_info.get('score', 0)} 分")

    skill_name = input("\n请输入要更新的技能名称，例如 ROS2：").strip()

    if not skill_name:
        print("技能名称不能为空，本次不修改。")
        return

    if skill_name not in skill_database.skills:
        print("\n这个技能目前不在数据库里。")
        answer = input("是否新增这个技能？输入 y 新增，其他键取消：").strip().lower()

        if answer != "y":
            print("已取消。")
            return

        skill_database.skills[skill_name] = {
            "score": 0,
            "level": "not_started",
            "note": "New skill added by Eric."
        }

    old_score = skill_database.skills[skill_name].get("score", 0)
    old_level = skill_database.skills[skill_name].get("level", "unknown")
    old_note = skill_database.skills[skill_name].get("note", "")

    new_score_text = input(f"新的分数（当前：{old_score}）：").strip()
    new_note = input(f"新的说明（当前：{old_note}）：").strip()

    if new_score_text:
        if new_score_text.isdigit():
            new_score = int(new_score_text)

            if new_score < 0:
                new_score = 0

            if new_score > 100:
                new_score = 100

            skill_database.skills[skill_name]["score"] = new_score
            skill_database.skills[skill_name]["level"] = score_to_level(new_score)
        else:
            print("分数不是数字，所以没有修改分数。")

    if new_note:
        skill_database.skills[skill_name]["note"] = new_note

    save_skill_database(skill_database)

    new_score = skill_database.skills[skill_name].get("score", 0)
    new_level = skill_database.skills[skill_name].get("level", "unknown")
    new_note_after = skill_database.skills[skill_name].get("note", "")

    content = (
        f"技能名称：{skill_name}\n"
        f"分数：{old_score} → {new_score}\n"
        f"level：{old_level} → {new_level}\n"
        f"说明：{old_note} → {new_note_after}"
    )

    write_to_project_log(
        "Atlas 3.0 Skill Database 更新技能",
        content
    )

    print("\n技能已更新：")
    print("-" * 70)
    print(content)
    print("-" * 70)


def score_to_level(score):
    """根据分数自动判断 level。"""
    if score >= 90:
        return "strong"

    if score >= 75:
        return "good"

    if score >= 40:
        return "developing"

    if score > 0:
        return "beginner"

    return "not_started"


def update_next_learning_focus(skill_database):
    """更新下一步学习重点。"""
    old_focus = skill_database.next_learning_focus

    print(f"\n当前下一步学习重点：{old_focus}")
    new_focus = input("请输入新的下一步学习重点，例如 ROS2：").strip()

    if not new_focus:
        print("没有输入，本次不修改。")
        return

    skill_database.next_learning_focus = new_focus
    save_skill_database(skill_database)

    content = (
        f"下一步学习重点：{old_focus} → {new_focus}"
    )

    write_to_project_log(
        "Atlas 3.0 Skill Database 更新下一步学习重点",
        content
    )

    print("\n下一步学习重点已更新：")
    print(content)


def add_new_skill(skill_database):
    """新增技能。"""
    print("\n新增技能。")

    skill_name = input("技能名称：").strip()
    score_text = input("技能分数 0-100：").strip()
    note = input("技能说明：").strip()

    if not skill_name:
        print("技能名称不能为空，本次不保存。")
        return

    if score_text.isdigit():
        score = int(score_text)
    else:
        score = 0

    if score < 0:
        score = 0

    if score > 100:
        score = 100

    if not note:
        note = "暂无说明"

    skill_database.skills[skill_name] = {
        "score": score,
        "level": score_to_level(score),
        "note": note
    }

    save_skill_database(skill_database)

    content = (
        f"新增技能：{skill_name}\n"
        f"分数：{score}\n"
        f"level：{score_to_level(score)}\n"
        f"说明：{note}"
    )

    write_to_project_log(
        "Atlas 3.0 Skill Database 新增技能",
        content
    )

    print("\n技能已新增：")
    print(content)


def robot_answer_skill_question(skill_database):
    """让机器人回答技能相关问题。"""
    question = input("\n请输入问题，例如：我下一步应该学什么？").strip()

    if not question:
        question = "我下一步应该学什么？"

    question_lower = question.lower()

    if "ros" in question_lower or "ros2" in question_lower:
        ros2_score = skill_database.get_skill_score("ROS2")

        if ros2_score is None:
            answer = "我还没有在 Skill Database 里找到 ROS2。建议先把 ROS2 加入技能数据库。"
        elif ros2_score < 40:
            answer = (
                f"Eric，ROS2 目前只有 {ros2_score} 分，属于明显短板。\n"
                f"如果你以后要做真正的机器人系统，下一步应该开始学习 ROS2。"
            )
        else:
            answer = (
                f"Eric，ROS2 目前是 {ros2_score} 分。\n"
                f"你可以继续通过小型机器人项目练习 ROS2。"
            )

    elif "arduino" in question_lower:
        arduino_score = skill_database.get_skill_score("Arduino")

        if arduino_score is not None and arduino_score >= 80:
            answer = (
                f"Eric，Arduino 目前是 {arduino_score} 分，已经是强项。\n"
                f"不建议继续重复基础 Arduino。下一步应该学习更系统的机器人技术，例如 ROS2。"
            )
        else:
            answer = (
                "Arduino 还可以继续补强，但不要只停留在基础接线，"
                "要把它放进机器人系统里使用。"
            )

    elif "下一步" in question or "学什么" in question:
        answer = skill_database.generate_next_learning_advice()

    else:
        answer = (
            "我会根据 Eric 的 Skill Database 来回答。\n"
            "目前最重要的判断是：Arduino、Python、OpenCV 已经有基础，"
            "下一步应该开始补强 ROS2。"
        )

    print("\n机器人回答：")
    print("-" * 70)
    print(answer)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Skill Database 技能问题回答",
        f"Eric 的问题：{question}\n\n机器人回答：\n{answer}"
    )


def test_log_write():
    """测试日志写入。"""
    content = (
        "这是 Atlas 3.0 Skill Database 的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明第二阶段日志保存正常。"
    )

    write_to_project_log(
        "Atlas 3.0 Skill Database 日志写入测试",
        content
    )


def show_intro(skill_database):
    """显示程序开头。"""
    print("\n==============================")
    print("Atlas 3.0")
    print("Stage 2: Skill Database")
    print("==============================")
    print(f"学生：{skill_database.student_name}")
    print(f"数据库版本：{skill_database.skill_database_version}")
    print(f"技能数据库文件：{SKILLS_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print(f"当前学习重点：{skill_database.next_learning_focus}")
    print("==============================")
    print("当前目标：让机器人知道 Eric 的技能强弱，并判断下一步应该学什么")
    print("==============================")


def main():
    skill_database = load_skill_database()
    show_intro(skill_database)

    write_to_project_log(
        "Atlas 3.0 Skill Database 程序启动",
        "Atlas 3.0 第二阶段 Skill Database 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 查看完整 Skill Database")
        print("2. 机器人建议：下一步应该学什么")
        print("3. 更新一个技能分数")
        print("4. 新增一个技能")
        print("5. 更新下一步学习重点")
        print("6. 回答技能相关问题")
        print("7. 测试 project_log.txt 是否能写入")
        print("8. 退出")

        choice = input("请输入数字 1-8：").strip()

        if choice == "1":
            show_skill_database(skill_database)

        elif choice == "2":
            show_next_learning_advice(skill_database)

        elif choice == "3":
            update_one_skill(skill_database)

        elif choice == "4":
            add_new_skill(skill_database)

        elif choice == "5":
            update_next_learning_focus(skill_database)

        elif choice == "6":
            robot_answer_skill_question(skill_database)

        elif choice == "7":
            test_log_write()

        elif choice == "8":
            write_to_project_log(
                "Atlas 3.0 Skill Database 程序退出",
                "Atlas 3.0 第二阶段 Skill Database 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 8。")
            write_to_project_log(
                "Atlas 3.0 Skill Database 无效输入",
                f"用户输入了无效菜单数字：{choice}"
            )


if __name__ == "__main__":
    main()