import json
from datetime import datetime
from pathlib import Path


# 固定文件路径，防止写到别的目录
BASE_DIR = Path(__file__).resolve().parent

PROFILE_FILE = BASE_DIR / "profile.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


class EricProfile:
    """Atlas 3.0 第一阶段：Eric Profile 成长画像"""

    def __init__(self, data):
        self.name = data.get("name", "Eric")
        self.age = data.get("age", 13)
        self.goal = data.get("goal", "AI Systems Engineer")
        self.current_project = data.get("current_project", "Atlas")
        self.current_version = data.get("current_version", "Atlas 3.0")
        self.interests = data.get("interests", [])
        self.strengths = data.get("strengths", [])
        self.weaknesses = data.get("weaknesses", [])
        self.learning_style = data.get(
            "learning_style",
            "喜欢通过项目实战学习，不喜欢重复听很多理论。"
        )
        self.mentor_note = data.get(
            "mentor_note",
            "Eric is building Atlas as a long-term AI research mentor robot."
        )

    def to_dict(self):
        """把 Class 转回 Dictionary，方便保存成 JSON。"""
        return {
            "name": self.name,
            "age": self.age,
            "goal": self.goal,
            "current_project": self.current_project,
            "current_version": self.current_version,
            "interests": self.interests,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "learning_style": self.learning_style,
            "mentor_note": self.mentor_note
        }

    def generate_identity_reply(self):
        """生成机器人身份式回答。"""
        interests_text = "、".join(self.interests) if self.interests else "暂时没有记录"
        strengths_text = "、".join(self.strengths) if self.strengths else "暂时没有记录"
        weaknesses_text = "、".join(self.weaknesses) if self.weaknesses else "暂时没有记录"

        reply = (
            f"{self.name}，我已经读取了你的成长画像。\n\n"
            f"你现在 {self.age} 岁。\n"
            f"你的长期目标是：{self.goal}。\n"
            f"你目前正在开发：{self.current_project}。\n"
            f"当前版本是：{self.current_version}。\n\n"
            f"你的兴趣包括：{interests_text}。\n"
            f"你目前比较强的能力包括：{strengths_text}。\n"
            f"你下一步需要补强的能力包括：{weaknesses_text}。\n\n"
            f"我会根据这个成长画像来回答你，而不是只说普通的：你好。"
        )

        return reply

    def generate_simple_mentor_advice(self):
        """根据 Eric Profile 生成第一阶段导师建议。"""
        weaknesses_text = "、".join(self.weaknesses) if self.weaknesses else "暂时没有记录"

        advice = (
            f"{self.name}，根据你的成长画像，我的判断是：\n\n"
            f"你已经不是刚开始做机器人项目。\n"
            f"你已经有 Arduino、Python、OpenCV 和项目迭代经验。\n\n"
            f"但是你目前还需要补强：{weaknesses_text}。\n\n"
            f"所以 Atlas 3.0 的第一步不是继续加硬件，"
            f"而是先建立稳定的 Eric Profile。"
            f"以后 Atlas 的所有建议都应该基于你的成长画像。"
        )

        return advice


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


def create_default_profile():
    """如果 profile.json 不存在，就创建默认 Eric Profile。"""
    default_profile = {
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
    }

    save_profile_dict(default_profile)

    write_to_project_log(
        "Atlas 3.0 Eric Profile 初始化",
        "已创建 profile.json，建立 Eric 的基础成长画像。"
    )

    return default_profile


def load_profile_dict():
    """读取 profile.json。"""
    if not PROFILE_FILE.exists():
        return create_default_profile()

    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        print("\nprofile.json 读取失败，将重新创建默认 Profile。")
        return create_default_profile()

    default_data = create_default_profile_data()

    for key, value in default_data.items():
        if key not in data:
            data[key] = value

    save_profile_dict(data)
    return data


def create_default_profile_data():
    """默认 Profile 数据，不直接写文件。"""
    return {
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
    }


def save_profile_dict(data):
    """保存 profile.json。"""
    with open(PROFILE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_profile():
    """读取 Profile，并转换成 EricProfile Class。"""
    data = load_profile_dict()
    return EricProfile(data)


def show_profile(profile):
    """显示完整 Eric Profile。"""
    content = profile.generate_identity_reply()

    print("\nEric Profile 成长画像：")
    print("-" * 60)
    print(content)
    print("-" * 60)

    write_to_project_log(
        "Atlas 3.0 Eric Profile 查看成长画像",
        content
    )


def robot_introduction(profile):
    """机器人基于 Profile 做自我式回答。"""
    reply = (
        f"{profile.name}，目前你正在开发 {profile.current_project}。\n"
        f"当前版本是 {profile.current_version}。\n"
        f"你的目标是成为 {profile.goal}。\n"
        f"所以我以后不会只把你当普通用户，而会根据你的成长画像给你建议。"
    )

    print("\n机器人回答：")
    print("-" * 60)
    print(reply)
    print("-" * 60)

    write_to_project_log(
        "Atlas 3.0 Eric Profile 机器人身份回答",
        reply
    )


def profile_based_mentor_advice(profile):
    """根据 Profile 生成导师建议。"""
    advice = profile.generate_simple_mentor_advice()

    print("\n基于 Eric Profile 的导师建议：")
    print("-" * 60)
    print(advice)
    print("-" * 60)

    write_to_project_log(
        "Atlas 3.0 Eric Profile 导师建议",
        advice
    )


def update_profile(profile):
    """更新 Eric Profile。"""
    print("\n开始更新 Eric Profile。")
    print("不想修改的地方，直接按回车。")

    new_name = input(f"名字（当前：{profile.name}）：").strip()
    new_age_text = input(f"年龄（当前：{profile.age}）：").strip()
    new_goal = input(f"长期目标（当前：{profile.goal}）：").strip()
    new_current_project = input(f"当前项目（当前：{profile.current_project}）：").strip()
    new_current_version = input(f"当前版本（当前：{profile.current_version}）：").strip()
    new_learning_style = input(f"学习风格（当前：{profile.learning_style}）：").strip()
    new_mentor_note = input(f"导师备注（当前：{profile.mentor_note}）：").strip()

    old_profile_text = profile.generate_identity_reply()

    if new_name:
        profile.name = new_name

    if new_age_text:
        if new_age_text.isdigit():
            profile.age = int(new_age_text)
        else:
            print("年龄不是数字，所以没有修改年龄。")

    if new_goal:
        profile.goal = new_goal

    if new_current_project:
        profile.current_project = new_current_project

    if new_current_version:
        profile.current_version = new_current_version

    if new_learning_style:
        profile.learning_style = new_learning_style

    if new_mentor_note:
        profile.mentor_note = new_mentor_note

    save_profile_dict(profile.to_dict())

    new_profile_text = profile.generate_identity_reply()

    content = (
        "Eric Profile 已更新。\n\n"
        "更新前：\n"
        f"{old_profile_text}\n\n"
        "更新后：\n"
        f"{new_profile_text}"
    )

    write_to_project_log(
        "Atlas 3.0 Eric Profile 更新成长画像",
        content
    )

    print("\nEric Profile 已更新。")
    print("-" * 60)
    print(new_profile_text)
    print("-" * 60)


def update_interests(profile):
    """更新兴趣列表。"""
    print("\n当前兴趣：")
    print(profile.interests)

    interests_text = input("请输入新的兴趣，用英文逗号分隔，例如 AI,Robot,Basketball：").strip()

    if not interests_text:
        print("没有输入，本次不修改。")
        return

    new_interests = []

    for item in interests_text.split(","):
        clean_item = item.strip()
        if clean_item:
            new_interests.append(clean_item)

    if not new_interests:
        print("没有有效兴趣，本次不修改。")
        return

    old_interests = profile.interests
    profile.interests = new_interests

    save_profile_dict(profile.to_dict())

    content = (
        f"兴趣更新前：{old_interests}\n"
        f"兴趣更新后：{profile.interests}"
    )

    write_to_project_log(
        "Atlas 3.0 Eric Profile 更新兴趣",
        content
    )

    print("\n兴趣已更新：")
    print(profile.interests)


def update_strengths_and_weaknesses(profile):
    """更新强项和弱项。"""
    print("\n当前强项：")
    print(profile.strengths)
    print("\n当前需要补强：")
    print(profile.weaknesses)

    strengths_text = input("\n请输入新的强项，用英文逗号分隔：").strip()
    weaknesses_text = input("请输入新的需要补强项，用英文逗号分隔：").strip()

    old_strengths = profile.strengths
    old_weaknesses = profile.weaknesses

    if strengths_text:
        new_strengths = []
        for item in strengths_text.split(","):
            clean_item = item.strip()
            if clean_item:
                new_strengths.append(clean_item)

        if new_strengths:
            profile.strengths = new_strengths

    if weaknesses_text:
        new_weaknesses = []
        for item in weaknesses_text.split(","):
            clean_item = item.strip()
            if clean_item:
                new_weaknesses.append(clean_item)

        if new_weaknesses:
            profile.weaknesses = new_weaknesses

    save_profile_dict(profile.to_dict())

    content = (
        f"强项更新前：{old_strengths}\n"
        f"强项更新后：{profile.strengths}\n\n"
        f"需要补强更新前：{old_weaknesses}\n"
        f"需要补强更新后：{profile.weaknesses}"
    )

    write_to_project_log(
        "Atlas 3.0 Eric Profile 更新强项和弱项",
        content
    )

    print("\n强项和需要补强项已更新。")
    print(f"当前强项：{profile.strengths}")
    print(f"当前需要补强：{profile.weaknesses}")


def test_log_write():
    """测试日志写入。"""
    content = (
        "这是 Atlas 3.0 Eric Profile 的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明第一阶段日志保存正常。"
    )

    write_to_project_log(
        "Atlas 3.0 Eric Profile 日志写入测试",
        content
    )


def show_intro(profile):
    """显示程序开头。"""
    print("\n==============================")
    print("Atlas 3.0")
    print("Stage 1: Eric Profile")
    print("==============================")
    print(f"学生：{profile.name}")
    print(f"年龄：{profile.age}")
    print(f"目标：{profile.goal}")
    print(f"当前项目：{profile.current_project}")
    print(f"当前版本：{profile.current_version}")
    print(f"Profile 文件：{PROFILE_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")
    print("当前目标：建立 Eric Digital Twin 的第一层成长画像")
    print("==============================")


def main():
    profile = load_profile()
    show_intro(profile)

    write_to_project_log(
        "Atlas 3.0 Eric Profile 程序启动",
        "Atlas 3.0 第一阶段 Eric Profile 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 查看 Eric Profile 成长画像")
        print("2. 机器人回答：Eric 目前正在开发什么")
        print("3. 根据 Eric Profile 生成导师建议")
        print("4. 更新基础 Profile")
        print("5. 更新兴趣 interests")
        print("6. 更新强项 strengths 和需要补强 weaknesses")
        print("7. 测试 project_log.txt 是否能写入")
        print("8. 退出")

        choice = input("请输入数字 1-8：").strip()

        if choice == "1":
            show_profile(profile)

        elif choice == "2":
            robot_introduction(profile)

        elif choice == "3":
            profile_based_mentor_advice(profile)

        elif choice == "4":
            update_profile(profile)

        elif choice == "5":
            update_interests(profile)

        elif choice == "6":
            update_strengths_and_weaknesses(profile)

        elif choice == "7":
            test_log_write()

        elif choice == "8":
            write_to_project_log(
                "Atlas 3.0 Eric Profile 程序退出",
                "Atlas 3.0 第一阶段 Eric Profile 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 8。")
            write_to_project_log(
                "Atlas 3.0 Eric Profile 无效输入",
                f"用户输入了无效菜单数字：{choice}"
            )


if __name__ == "__main__":
    main()