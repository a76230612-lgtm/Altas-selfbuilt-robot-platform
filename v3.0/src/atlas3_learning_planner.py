import json
from datetime import datetime, date, timedelta
from pathlib import Path


# 固定路径，防止写到别的目录
BASE_DIR = Path(__file__).resolve().parent

PROFILE_FILE = BASE_DIR / "profile.json"
SKILLS_FILE = BASE_DIR / "skills.json"
HISTORY_FILE = BASE_DIR / "history.json"
LEARNING_PLAN_FILE = BASE_DIR / "learning_plan.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


class LearningPlanner:
    """Atlas 3.0 第四阶段：Learning Planner 学习规划器"""

    def __init__(self, profile_data, skills_data, history_data, plan_data):
        self.profile_data = profile_data
        self.skills_data = skills_data
        self.history_data = history_data
        self.plan_data = plan_data

        self.student_name = profile_data.get("name", "Eric")
        self.current_project = profile_data.get("current_project", "Atlas")
        self.current_version = profile_data.get("current_version", "Atlas 3.0")
        self.goal = profile_data.get("goal", "AI Systems Engineer")
        self.interests = profile_data.get("interests", [])
        self.learning_style = profile_data.get(
            "learning_style",
            "喜欢通过项目实战学习，不喜欢重复听很多理论。"
        )

        self.skills = skills_data.get("skills", {})
        self.project_history = history_data.get("project_history", [])
        self.daily_learning_plans = plan_data.get("daily_learning_plans", [])

    def get_skill_score(self, skill_name):
        skill = self.skills.get(skill_name)

        if skill is None:
            return None

        return skill.get("score", 0)

    def get_strong_skills(self):
        strong_skills = []

        for skill_name, skill_info in self.skills.items():
            score = skill_info.get("score", 0)

            if score >= 80:
                strong_skills.append(skill_name)

        return strong_skills

    def get_weak_skills(self):
        weak_skills = []

        for skill_name, skill_info in self.skills.items():
            score = skill_info.get("score", 0)

            if score < 40:
                weak_skills.append(skill_name)

        return weak_skills

    def get_developing_skills(self):
        developing_skills = []

        for skill_name, skill_info in self.skills.items():
            score = skill_info.get("score", 0)

            if 40 <= score < 80:
                developing_skills.append(skill_name)

        return developing_skills

    def get_recent_project_history_summary(self):
        if not self.project_history:
            return "暂时没有项目历史记录。"

        lines = []

        for project in self.project_history:
            project_name = project.get("project_name", "未命名项目")
            version = project.get("version", "无版本")
            status = project.get("status", "unknown")
            skills = project.get("skills_learned", [])

            skills_text = "、".join(skills) if skills else "暂无技能记录"

            lines.append(
                f"- {project_name} ({version}) | 状态：{status} | 学到：{skills_text}"
            )

        return "\n".join(lines)

    def decide_today_focus(self):
        """根据 Profile + Skills + History 决定今天最应该做什么。"""
        arduino_score = self.get_skill_score("Arduino")
        python_score = self.get_skill_score("Python")
        opencv_score = self.get_skill_score("OpenCV")
        yolo_score = self.get_skill_score("YOLO")
        ros2_score = self.get_skill_score("ROS2")

        # 第一优先级：ROS2
        if ros2_score is not None and ros2_score < 40:
            return {
                "focus": "ROS2",
                "reason": (
                    "Arduino、Python、OpenCV 已经有基础，但 ROS2 还没开始。"
                    "如果 Eric 未来要做真正的机器人系统，ROS2 是下一阶段必须补上的能力。"
                ),
                "task_1": "了解 ROS2 是什么，以及它为什么用于机器人系统。",
                "task_2": "整理一页 ROS2 学习笔记：节点、话题、消息这三个概念。",
                "task_3": "把 ROS2 加入 Atlas 3.0 的长期学习计划。",
                "estimated_time": "2 小时"
            }

        # 第二优先级：YOLO
        if yolo_score is not None and yolo_score < 80:
            return {
                "focus": "YOLO",
                "reason": (
                    "OpenCV 已经有基础，但 YOLO 还在发展中。"
                    "如果机器人以后要理解真实世界，需要更强的目标识别能力。"
                ),
                "task_1": "复习 YOLO 的基本用途：目标检测。",
                "task_2": "准备一个简单的 YOLO 测试素材。",
                "task_3": "记录 YOLO 和 OpenCV 的区别。",
                "estimated_time": "2 小时"
            }

        # 第三优先级：Python 工程能力
        if python_score is not None and python_score < 90:
            return {
                "focus": "Python Engineering",
                "reason": (
                    "Python 已经能支持 JSON、文件读写和 OpenCV，"
                    "但 Atlas 3.0 需要更清晰的类、模块和数据结构。"
                ),
                "task_1": "复习 Python Class 的基本结构。",
                "task_2": "把 Profile、Skill、History 的 Class 关系画出来。",
                "task_3": "整理代码模块，让 Atlas 3.0 更像工程项目。",
                "estimated_time": "2 小时"
            }

        # 默认：项目整理
        return {
            "focus": "Atlas 3.0 Integration",
            "reason": (
                "当前基础技能状态较好，可以开始把 Profile、Skill Database、Project History "
                "整合成更完整的 Learning Planner。"
            ),
            "task_1": "测试 Profile、Skills、History 是否都能读取。",
            "task_2": "生成今天的 Learning Plan。",
            "task_3": "把 Learning Plan 保存到 project_log.txt。",
            "estimated_time": "1.5 小时"
        }

    def generate_today_learning_plan(self):
        """生成今天的主动学习规划。"""
        today_focus = self.decide_today_focus()

        strong_skills = self.get_strong_skills()
        developing_skills = self.get_developing_skills()
        weak_skills = self.get_weak_skills()

        strong_text = "、".join(strong_skills) if strong_skills else "暂时没有明显强项"
        developing_text = "、".join(developing_skills) if developing_skills else "暂时没有发展中技能"
        weak_text = "、".join(weak_skills) if weak_skills else "暂时没有明显短板"

        plan = {
            "date": get_today_text(),
            "created_time": datetime.now().strftime("%H:%M:%S"),
            "student_name": self.student_name,
            "current_project": self.current_project,
            "current_version": self.current_version,
            "goal": self.goal,
            "today_focus": today_focus["focus"],
            "reason": today_focus["reason"],
            "task_1": today_focus["task_1"],
            "task_2": today_focus["task_2"],
            "task_3": today_focus["task_3"],
            "estimated_time": today_focus["estimated_time"],
            "strong_skills": strong_skills,
            "developing_skills": developing_skills,
            "weak_skills": weak_skills,
            "learning_style": self.learning_style,
            "status": "planned",
            "evening_review": ""
        }

        lines = []

        lines.append(f"{self.student_name}，这是 Atlas 3.0 主动生成的今日学习计划。")
        lines.append("")
        lines.append("一、当前画像")
        lines.append(f"目标：{self.goal}")
        lines.append(f"当前项目：{self.current_project}")
        lines.append(f"当前版本：{self.current_version}")
        lines.append(f"学习风格：{self.learning_style}")
        lines.append("")

        lines.append("二、技能判断")
        lines.append(f"强项技能：{strong_text}")
        lines.append(f"发展中技能：{developing_text}")
        lines.append(f"需要补强：{weak_text}")
        lines.append("")

        lines.append("三、今天建议学习重点")
        lines.append(f"今日重点：{today_focus['focus']}")
        lines.append(f"原因：{today_focus['reason']}")
        lines.append("")

        lines.append("四、今天具体任务")
        lines.append(f"1. {today_focus['task_1']}")
        lines.append(f"2. {today_focus['task_2']}")
        lines.append(f"3. {today_focus['task_3']}")
        lines.append("")

        lines.append("五、预计时间")
        lines.append(today_focus["estimated_time"])
        lines.append("")

        lines.append("六、机器人导师提醒")
        lines.append(
            "今天不要同时做太多内容。只要完成这三个小任务，"
            "并把结果写入 Project Log，就算 Learning Planner 跑通。"
        )

        plan_text = "\n".join(lines)

        return plan, plan_text

    def generate_morning_message(self):
        """生成开机主动提醒。"""
        today_focus = self.decide_today_focus()

        message = (
            f"{self.student_name}，早上好。\n"
            f"我已经读取了你的 Profile、Skill Database 和 Project History。\n\n"
            f"你目前正在开发：{self.current_project}。\n"
            f"你的长期目标是：{self.goal}。\n\n"
            f"今天我建议你重点做：{today_focus['focus']}。\n"
            f"原因：{today_focus['reason']}\n\n"
            f"预计时间：{today_focus['estimated_time']}。\n"
            f"这不是随机建议，而是根据你的成长画像、技能短板和项目历史生成的。"
        )

        return message

    def generate_learning_logic_explanation(self):
        """解释机器人为什么这样建议。"""
        today_focus = self.decide_today_focus()

        lines = []

        lines.append("Atlas 3.0 Learning Planner 判断逻辑：")
        lines.append("")
        lines.append("1. 先读取 Eric Profile")
        lines.append(f"   - 当前目标：{self.goal}")
        lines.append(f"   - 当前项目：{self.current_project}")
        lines.append(f"   - 学习风格：{self.learning_style}")
        lines.append("")

        lines.append("2. 再读取 Skill Database")
        for skill_name, skill_info in self.skills.items():
            lines.append(
                f"   - {skill_name}：{skill_info.get('score', 0)} 分"
            )
        lines.append("")

        lines.append("3. 再读取 Project History")
        lines.append(
            "   - Eric 已经完成植物系统、Atlas 1.0、Atlas 2.0，"
            "说明他已经有硬件、Python、OpenCV、项目管理和 Bug 管理经验。"
        )
        lines.append("")

        lines.append("4. 最后生成今日建议")
        lines.append(f"   - 今日建议：{today_focus['focus']}")
        lines.append(f"   - 判断原因：{today_focus['reason']}")
        lines.append("")

        lines.append("结论：")
        lines.append(
            "Learning Planner 的意义不是随机安排任务，"
            "而是根据 Eric 的长期画像、技能水平和项目历史，主动生成下一步学习计划。"
        )

        return "\n".join(lines)


def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_today_text():
    return date.today().strftime("%Y-%m-%d")


def get_yesterday_text():
    return (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")


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


def safe_load_json(file_path, default_data):
    """安全读取 JSON。"""
    if not file_path.exists():
        return default_data

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default_data


def save_json(file_path, data):
    """保存 JSON。"""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def create_default_profile():
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


def create_default_skills():
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


def create_default_history():
    return {
        "student_name": "Eric",
        "history_database_version": "Atlas 3.0 Project History v1",
        "project_history": []
    }


def create_default_learning_plan():
    return {
        "student_name": "Eric",
        "learning_planner_version": "Atlas 3.0 Learning Planner v1",
        "daily_learning_plans": []
    }


def load_profile_data():
    data = safe_load_json(PROFILE_FILE, create_default_profile())

    if not PROFILE_FILE.exists():
        save_json(PROFILE_FILE, data)

    return data


def load_skills_data():
    data = safe_load_json(SKILLS_FILE, create_default_skills())

    if not SKILLS_FILE.exists():
        save_json(SKILLS_FILE, data)

    return data


def load_history_data():
    data = safe_load_json(HISTORY_FILE, create_default_history())

    if not HISTORY_FILE.exists():
        save_json(HISTORY_FILE, data)

    return data


def load_learning_plan_data():
    data = safe_load_json(LEARNING_PLAN_FILE, create_default_learning_plan())

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "learning_planner_version" not in data:
        data["learning_planner_version"] = "Atlas 3.0 Learning Planner v1"

    if "daily_learning_plans" not in data:
        data["daily_learning_plans"] = []

    save_json(LEARNING_PLAN_FILE, data)
    return data


def save_learning_plan_data(data):
    save_json(LEARNING_PLAN_FILE, data)


def load_learning_planner():
    profile_data = load_profile_data()
    skills_data = load_skills_data()
    history_data = load_history_data()
    plan_data = load_learning_plan_data()

    return LearningPlanner(profile_data, skills_data, history_data, plan_data)


def save_plan_to_database(planner, plan):
    plan_data = load_learning_plan_data()

    # 如果今天已经有计划，先移除旧的，避免重复太多
    today = get_today_text()
    new_daily_plans = []

    for old_plan in plan_data["daily_learning_plans"]:
        if old_plan.get("date") != today:
            new_daily_plans.append(old_plan)

    new_daily_plans.append(plan)
    plan_data["daily_learning_plans"] = new_daily_plans

    save_learning_plan_data(plan_data)

    # 同步更新 planner 内部数据
    planner.plan_data = plan_data
    planner.daily_learning_plans = plan_data["daily_learning_plans"]


def generate_and_save_today_plan(planner):
    """生成并保存今日学习计划。"""
    plan, plan_text = planner.generate_today_learning_plan()

    save_plan_to_database(planner, plan)

    print("\nAtlas 3.0 今日学习计划：")
    print("-" * 70)
    print(plan_text)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Learning Planner 生成今日学习计划",
        plan_text
    )


def show_morning_message(planner):
    """显示开机主动提醒。"""
    message = planner.generate_morning_message()

    print("\nAtlas 3.0 主动提醒：")
    print("-" * 70)
    print(message)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Learning Planner 开机主动提醒",
        message
    )


def show_learning_logic(planner):
    """显示判断逻辑。"""
    explanation = planner.generate_learning_logic_explanation()

    print("\nLearning Planner 判断逻辑：")
    print("-" * 70)
    print(explanation)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Learning Planner 判断逻辑",
        explanation
    )


def show_today_plan():
    """查看今天的学习计划。"""
    plan_data = load_learning_plan_data()
    today = get_today_text()

    today_plan = None

    for plan in plan_data["daily_learning_plans"]:
        if plan.get("date") == today:
            today_plan = plan
            break

    if today_plan is None:
        message = "今天还没有 Learning Plan。请先选择 2 生成今日学习计划。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 3.0 Learning Planner 查看今日计划",
            message
        )
        return

    content = format_learning_plan(today_plan)

    print("\n今天的 Learning Plan：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Learning Planner 查看今日计划",
        content
    )


def show_all_learning_plans():
    """查看全部学习计划。"""
    plan_data = load_learning_plan_data()
    plans = plan_data.get("daily_learning_plans", [])

    if not plans:
        message = "目前还没有任何 Learning Plan。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 3.0 Learning Planner 查看全部计划",
            message
        )
        return

    print("\n全部 Learning Plan：")
    print("-" * 70)

    lines = []

    for plan in plans:
        short_text = (
            f"日期：{plan.get('date', '无日期')} | "
            f"重点：{plan.get('today_focus', '无重点')} | "
            f"状态：{plan.get('status', 'unknown')} | "
            f"预计时间：{plan.get('estimated_time', '未知')}"
        )

        print(short_text)
        lines.append(short_text)

    write_to_project_log(
        "Atlas 3.0 Learning Planner 查看全部计划",
        "\n".join(lines)
    )


def evening_review_learning_plan():
    """晚上复盘今日学习计划。"""
    plan_data = load_learning_plan_data()
    today = get_today_text()

    today_plan = None

    for plan in plan_data["daily_learning_plans"]:
        if plan.get("date") == today:
            today_plan = plan
            break

    if today_plan is None:
        print("\n今天还没有 Learning Plan，无法复盘。")
        print("请先选择 2 生成今日学习计划。")
        return

    print("\n开始 Learning Plan 晚上复盘。")
    print(f"今日重点：{today_plan.get('today_focus', '')}")
    print(f"任务 1：{today_plan.get('task_1', '')}")
    print(f"任务 2：{today_plan.get('task_2', '')}")
    print(f"任务 3：{today_plan.get('task_3', '')}")

    status = input("\n完成情况（完成 / 部分完成 / 未完成）：").strip()
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

    today_plan["status"] = status
    today_plan["evening_review"] = review

    save_learning_plan_data(plan_data)

    content = format_learning_plan(today_plan)

    print("\nLearning Plan 晚上复盘已保存：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Learning Planner 晚上复盘",
        content
    )


def robot_answer_planner_question(planner):
    """回答学习规划相关问题。"""
    question = input("\n请输入问题，例如：今天为什么建议我学 ROS2？").strip()

    if not question:
        question = "今天为什么建议我学 ROS2？"

    question_lower = question.lower()

    today_focus = planner.decide_today_focus()

    if "为什么" in question and ("ros" in question_lower or "ros2" in question_lower):
        answer = (
            "因为你的 Skill Database 显示：Arduino、Python、OpenCV 已经有基础，"
            "但 ROS2 目前还没有开始。\n"
            "如果你未来要做真正的机器人系统，ROS2 是必须补上的能力。"
        )

    elif "今天" in question or "建议" in question or "学什么" in question:
        answer = (
            f"今天建议重点：{today_focus['focus']}。\n"
            f"原因：{today_focus['reason']}\n"
            f"预计时间：{today_focus['estimated_time']}。"
        )

    elif "历史" in question or "以前" in question:
        answer = (
            "根据 Project History，Eric 已经完成植物系统、Atlas 1.0 和 Atlas 2.0。"
            "这些项目说明 Eric 已经具备硬件、Python、OpenCV 和项目管理基础。"
            "所以现在不需要重复基础内容，而应该进入更系统的机器人学习。"
        )

    else:
        answer = (
            "Learning Planner 会根据 Profile、Skill Database 和 Project History 生成建议。\n"
            f"当前建议重点是：{today_focus['focus']}。\n"
            f"原因是：{today_focus['reason']}"
        )

    print("\n机器人回答：")
    print("-" * 70)
    print(answer)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Learning Planner 问题回答",
        f"Eric 的问题：{question}\n\n机器人回答：\n{answer}"
    )


def format_learning_plan(plan):
    strong_skills_text = "、".join(plan.get("strong_skills", [])) if plan.get("strong_skills") else "暂无"
    developing_skills_text = "、".join(plan.get("developing_skills", [])) if plan.get("developing_skills") else "暂无"
    weak_skills_text = "、".join(plan.get("weak_skills", [])) if plan.get("weak_skills") else "暂无"

    return (
        f"日期：{plan.get('date', '无日期')}\n"
        f"创建时间：{plan.get('created_time', '无时间')}\n"
        f"学生：{plan.get('student_name', 'Eric')}\n"
        f"当前项目：{plan.get('current_project', 'Atlas')}\n"
        f"当前版本：{plan.get('current_version', 'Atlas 3.0')}\n"
        f"目标：{plan.get('goal', '')}\n"
        f"今日重点：{plan.get('today_focus', '')}\n"
        f"原因：{plan.get('reason', '')}\n"
        f"任务 1：{plan.get('task_1', '')}\n"
        f"任务 2：{plan.get('task_2', '')}\n"
        f"任务 3：{plan.get('task_3', '')}\n"
        f"预计时间：{plan.get('estimated_time', '')}\n"
        f"强项技能：{strong_skills_text}\n"
        f"发展中技能：{developing_skills_text}\n"
        f"需要补强：{weak_skills_text}\n"
        f"学习风格：{plan.get('learning_style', '')}\n"
        f"状态：{plan.get('status', 'planned')}\n"
        f"晚上复盘：{plan.get('evening_review', '') if plan.get('evening_review') else '暂无'}"
    )


def test_log_write():
    """测试日志写入。"""
    content = (
        "这是 Atlas 3.0 Learning Planner 的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明第四阶段日志保存正常。"
    )

    write_to_project_log(
        "Atlas 3.0 Learning Planner 日志写入测试",
        content
    )


def show_intro(planner):
    print("\n==============================")
    print("Atlas 3.0")
    print("Stage 4: Learning Planner")
    print("==============================")
    print(f"学生：{planner.student_name}")
    print(f"目标：{planner.goal}")
    print(f"当前项目：{planner.current_project}")
    print(f"当前版本：{planner.current_version}")
    print(f"Profile 文件：{PROFILE_FILE}")
    print(f"Skills 文件：{SKILLS_FILE}")
    print(f"History 文件：{HISTORY_FILE}")
    print(f"Learning Plan 文件：{LEARNING_PLAN_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")
    print("当前目标：机器人主动生成今天的学习建议")
    print("==============================")


def main():
    planner = load_learning_planner()
    show_intro(planner)

    write_to_project_log(
        "Atlas 3.0 Learning Planner 程序启动",
        "Atlas 3.0 第四阶段 Learning Planner 程序已启动。"
    )

    # 启动时主动提醒一次
    print("\n机器人开机主动提醒：")
    print("-" * 70)
    print(planner.generate_morning_message())
    print("-" * 70)

    while True:
        print("\n请选择功能：")
        print("1. 显示开机主动提醒")
        print("2. 生成并保存今日 Learning Plan")
        print("3. 查看今天的 Learning Plan")
        print("4. 查看全部 Learning Plan")
        print("5. 解释 Learning Planner 判断逻辑")
        print("6. 晚上复盘今日 Learning Plan")
        print("7. 回答学习规划相关问题")
        print("8. 测试 project_log.txt 是否能写入")
        print("9. 退出")

        choice = input("请输入数字 1-9：").strip()

        if choice == "1":
            show_morning_message(planner)

        elif choice == "2":
            generate_and_save_today_plan(planner)

        elif choice == "3":
            show_today_plan()

        elif choice == "4":
            show_all_learning_plans()

        elif choice == "5":
            show_learning_logic(planner)

        elif choice == "6":
            evening_review_learning_plan()

        elif choice == "7":
            robot_answer_planner_question(planner)

        elif choice == "8":
            test_log_write()

        elif choice == "9":
            write_to_project_log(
                "Atlas 3.0 Learning Planner 程序退出",
                "Atlas 3.0 第四阶段 Learning Planner 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 9。")
            write_to_project_log(
                "Atlas 3.0 Learning Planner 无效输入",
                f"用户输入了无效菜单数字：{choice}"
            )


if __name__ == "__main__":
    main()