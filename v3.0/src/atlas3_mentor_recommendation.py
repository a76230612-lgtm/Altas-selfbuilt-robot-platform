import json
from datetime import datetime, date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

PROFILE_FILE = BASE_DIR / "profile.json"
SKILLS_FILE = BASE_DIR / "skills.json"
HISTORY_FILE = BASE_DIR / "history.json"
LEARNING_PLAN_FILE = BASE_DIR / "learning_plan.json"
EMOTION_FILE = BASE_DIR / "emotion_memory.json"
MENTOR_RECOMMENDATION_FILE = BASE_DIR / "mentor_recommendation.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


class MentorRecommendation:
    """Atlas 3.0 第六阶段：Mentor Recommendation 导师推荐系统"""

    def __init__(self, profile_data, skills_data, history_data, learning_plan_data, emotion_data, recommendation_data):
        self.profile_data = profile_data
        self.skills_data = skills_data
        self.history_data = history_data
        self.learning_plan_data = learning_plan_data
        self.emotion_data = emotion_data
        self.recommendation_data = recommendation_data

        self.student_name = profile_data.get("name", "Eric")
        self.age = profile_data.get("age", 13)
        self.goal = profile_data.get("goal", "AI Systems Engineer")
        self.current_project = profile_data.get("current_project", "Atlas")
        self.current_version = profile_data.get("current_version", "Atlas 3.0")
        self.learning_style = profile_data.get(
            "learning_style",
            "喜欢通过项目实战学习，不喜欢重复听很多理论。"
        )

        self.skills = skills_data.get("skills", {})
        self.project_history = history_data.get("project_history", [])
        self.daily_learning_plans = learning_plan_data.get("daily_learning_plans", [])
        self.emotion_records = emotion_data.get("emotion_records", [])
        self.recommendations = recommendation_data.get("recommendations", [])

    def get_skill_score(self, skill_name):
        skill = self.skills.get(skill_name)

        if skill is None:
            return None

        return skill.get("score", 0)

    def get_latest_learning_plan(self):
        if not self.daily_learning_plans:
            return None

        return self.daily_learning_plans[-1]

    def get_latest_emotion_record(self):
        if not self.emotion_records:
            return None

        return self.emotion_records[-1]

    def get_completed_project_names(self):
        names = []

        for project in self.project_history:
            if project.get("status") == "completed":
                names.append(project.get("project_name", "未命名项目"))

        return names

    def get_in_progress_project_names(self):
        names = []

        for project in self.project_history:
            if project.get("status") == "in_progress":
                names.append(project.get("project_name", "未命名项目"))

        return names

    def analyze_current_state(self):
        """综合分析 Eric 当前状态。"""
        arduino_score = self.get_skill_score("Arduino")
        python_score = self.get_skill_score("Python")
        opencv_score = self.get_skill_score("OpenCV")
        yolo_score = self.get_skill_score("YOLO")
        ros2_score = self.get_skill_score("ROS2")

        latest_learning_plan = self.get_latest_learning_plan()
        latest_emotion = self.get_latest_emotion_record()

        completed_projects = self.get_completed_project_names()
        in_progress_projects = self.get_in_progress_project_names()

        state = {
            "arduino_score": arduino_score,
            "python_score": python_score,
            "opencv_score": opencv_score,
            "yolo_score": yolo_score,
            "ros2_score": ros2_score,
            "latest_learning_plan": latest_learning_plan,
            "latest_emotion": latest_emotion,
            "completed_projects": completed_projects,
            "in_progress_projects": in_progress_projects
        }

        return state

    def decide_main_recommendation(self):
        """决定最重要的导师推荐。"""
        state = self.analyze_current_state()

        arduino_score = state["arduino_score"]
        python_score = state["python_score"]
        opencv_score = state["opencv_score"]
        yolo_score = state["yolo_score"]
        ros2_score = state["ros2_score"]
        latest_emotion = state["latest_emotion"]
        latest_learning_plan = state["latest_learning_plan"]

        # 情绪/调试节奏优先保护
        if latest_emotion is not None:
            debug_hours = latest_emotion.get("debug_hours", 0)
            feeling = latest_emotion.get("feeling", "")

            if debug_hours >= 4:
                return {
                    "main_focus": "Debug Rhythm Control",
                    "recommendation": "今天不要继续硬撑新功能。先休息 15 到 20 分钟，再回来只测试一个最小问题。",
                    "reason": f"Emotion Memory 显示 Eric 最近连续调试 {debug_hours} 小时，时间偏长。此时继续加功能容易制造更多 Bug。",
                    "action_1": "休息 15 到 20 分钟。",
                    "action_2": "回来后只打开一个文件，只测试一个功能。",
                    "action_3": "把问题写入 Bug 或 Project Log，不要同时改多个功能。",
                    "estimated_time": "30 分钟",
                    "priority": "high"
                }

            if "崩溃" in feeling or "不想做" in feeling:
                return {
                    "main_focus": "Reduce Task Size",
                    "recommendation": "今天不要扩大任务。只保留一个最小动作：查看昨天的 Learning Plan，并完成其中一个小任务。",
                    "reason": "Emotion Memory 显示 Eric 当前研发状态波动较大。此时应该缩小任务，而不是扩大项目范围。",
                    "action_1": "查看今天或最近一次 Learning Plan。",
                    "action_2": "只选择其中一个最小任务。",
                    "action_3": "完成后写入 Project Log。",
                    "estimated_time": "30 到 45 分钟",
                    "priority": "high"
                }

        # ROS2 是 Atlas 3.0 计划里的关键推荐方向
        if ros2_score is not None and ros2_score < 40:
            return {
                "main_focus": "ROS2",
                "recommendation": "下一步建议 Eric 开始学习 ROS2，而不是继续重复基础 Arduino。",
                "reason": (
                    "Skill Database 显示 Arduino、Python、OpenCV 已经有基础，但 ROS2 还没有开始。"
                    "如果 Eric 未来要做真正的机器人系统，ROS2 是必须补上的能力。"
                ),
                "action_1": "了解 ROS2 是什么，以及它为什么用于机器人系统。",
                "action_2": "整理一页 ROS2 笔记：Node、Topic、Message。",
                "action_3": "把 ROS2 作为 Atlas 3.0 后续长期学习重点。",
                "estimated_time": "2 小时",
                "priority": "high"
            }

        # YOLO 第二优先级
        if yolo_score is not None and yolo_score < 80:
            return {
                "main_focus": "YOLO",
                "recommendation": "下一步建议继续补强 YOLO，让机器人视觉识别能力更接近真实应用。",
                "reason": (
                    "OpenCV 已经有基础，但 YOLO 仍处于发展中。"
                    "如果机器人以后要识别物体、场景和人，YOLO 会比普通图像处理更重要。"
                ),
                "action_1": "复习 YOLO 的目标检测用途。",
                "action_2": "准备一个简单图片或摄像头测试素材。",
                "action_3": "记录 YOLO 和 OpenCV 的区别。",
                "estimated_time": "2 小时",
                "priority": "medium"
            }

        # Python 工程能力
        if python_score is not None and python_score < 90:
            return {
                "main_focus": "Python Engineering",
                "recommendation": "下一步建议提高 Python 工程化能力，把 Atlas 3.0 的代码整理成更清晰的模块。",
                "reason": (
                    "Atlas 3.0 已经有 Profile、Skill Database、Project History、Learning Planner、Emotion Memory。"
                    "如果继续发展，必须把代码结构整理清楚，否则会越来越难维护。"
                ),
                "action_1": "整理 Atlas 3.0 的所有文件清单。",
                "action_2": "画出 Profile、Skills、History、Learning Plan、Emotion Memory 的关系图。",
                "action_3": "准备后续合并版主程序。",
                "estimated_time": "2 小时",
                "priority": "medium"
            }

        # 默认：整合与展示
        return {
            "main_focus": "Atlas 3.0 Integration",
            "recommendation": "下一步建议把 Atlas 3.0 的六个阶段整合成一个完整主程序，并准备 Demo。",
            "reason": (
                "如果 Profile、Skill Database、Project History、Learning Planner、Emotion Memory 和 Mentor Recommendation 都已经能独立运行，"
                "下一步的重点不是继续加功能，而是整合、测试和展示。"
            ),
            "action_1": "检查六个阶段的 JSON 文件是否都存在。",
            "action_2": "检查 project_log.txt 是否有每个阶段的测试记录。",
            "action_3": "准备 Atlas 3.0 综合版主程序。",
            "estimated_time": "2 到 3 小时",
            "priority": "medium"
        }

    def generate_recommendation_text(self):
        """生成完整导师推荐文本。"""
        state = self.analyze_current_state()
        decision = self.decide_main_recommendation()

        completed_projects_text = "、".join(state["completed_projects"]) if state["completed_projects"] else "暂无"
        in_progress_projects_text = "、".join(state["in_progress_projects"]) if state["in_progress_projects"] else "暂无"

        latest_learning_plan = state["latest_learning_plan"]
        latest_emotion = state["latest_emotion"]

        lines = []

        lines.append(f"{self.student_name}，这是 Atlas 3.0 生成的导师推荐。")
        lines.append("")
        lines.append("一、机器人读取到的 Eric 画像")
        lines.append(f"年龄：{self.age}")
        lines.append(f"长期目标：{self.goal}")
        lines.append(f"当前项目：{self.current_project}")
        lines.append(f"当前版本：{self.current_version}")
        lines.append(f"学习风格：{self.learning_style}")
        lines.append("")

        lines.append("二、机器人读取到的技能状态")
        for skill_name, skill_info in self.skills.items():
            lines.append(
                f"- {skill_name}：{skill_info.get('score', 0)} 分，level：{skill_info.get('level', 'unknown')}"
            )
        lines.append("")

        lines.append("三、机器人读取到的项目历史")
        lines.append(f"已完成项目：{completed_projects_text}")
        lines.append(f"进行中项目：{in_progress_projects_text}")
        lines.append("")

        lines.append("四、机器人读取到的最新 Learning Plan")
        if latest_learning_plan is None:
            lines.append("暂时没有 Learning Plan。")
        else:
            lines.append(f"最近学习重点：{latest_learning_plan.get('today_focus', '未知')}")
            lines.append(f"计划状态：{latest_learning_plan.get('status', 'unknown')}")
            lines.append(f"预计时间：{latest_learning_plan.get('estimated_time', '未知')}")
        lines.append("")

        lines.append("五、机器人读取到的最新研发状态")
        if latest_emotion is None:
            lines.append("暂时没有 Emotion Memory 记录。")
        else:
            lines.append(f"最近状态：{latest_emotion.get('feeling', '')}")
            lines.append(f"连续调试时间：{latest_emotion.get('debug_hours', 0)} 小时")
            lines.append(f"主要问题：{latest_emotion.get('problem', '')}")
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
        lines.append(
            "这不是随机建议。它综合读取了 Eric Profile、Skill Database、Project History、Learning Planner 和 Emotion Memory。"
        )

        return "\n".join(lines), decision

    def generate_logic_explanation(self):
        """解释导师推荐逻辑。"""
        decision = self.decide_main_recommendation()
        state = self.analyze_current_state()

        lines = []

        lines.append("Atlas 3.0 Mentor Recommendation 判断逻辑：")
        lines.append("")
        lines.append("1. 先读取 Eric Profile")
        lines.append(f"   目标：{self.goal}")
        lines.append(f"   当前项目：{self.current_project}")
        lines.append("")
        lines.append("2. 再读取 Skill Database")
        lines.append(f"   Arduino：{state['arduino_score']} 分")
        lines.append(f"   Python：{state['python_score']} 分")
        lines.append(f"   OpenCV：{state['opencv_score']} 分")
        lines.append(f"   YOLO：{state['yolo_score']} 分")
        lines.append(f"   ROS2：{state['ros2_score']} 分")
        lines.append("")
        lines.append("3. 再读取 Project History")
        lines.append("   判断 Eric 不是零基础，而是已经完成植物系统、Atlas 1.0 和 Atlas 2.0。")
        lines.append("")
        lines.append("4. 再读取 Learning Planner")
        latest_plan = state["latest_learning_plan"]
        if latest_plan:
            lines.append(f"   最近学习重点：{latest_plan.get('today_focus', '未知')}")
            lines.append(f"   状态：{latest_plan.get('status', 'unknown')}")
        else:
            lines.append("   暂时没有 Learning Plan。")
        lines.append("")
        lines.append("5. 再读取 Emotion Memory")
        latest_emotion = state["latest_emotion"]
        if latest_emotion:
            lines.append(f"   最近研发状态：{latest_emotion.get('feeling', '')}")
            lines.append(f"   连续调试时间：{latest_emotion.get('debug_hours', 0)} 小时")
        else:
            lines.append("   暂时没有 Emotion Memory。")
        lines.append("")
        lines.append("6. 最后生成导师推荐")
        lines.append(f"   推荐重点：{decision['main_focus']}")
        lines.append(f"   推荐原因：{decision['reason']}")
        lines.append("")
        lines.append("结论：")
        lines.append(
            "Mentor Recommendation 是 Atlas 3.0 的最高层功能。它不是单独看某一个文件，"
            "而是综合 Eric 的画像、技能、项目历史、学习计划和研发状态，给出下一步判断。"
        )

        return "\n".join(lines)


def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_today_text():
    return date.today().strftime("%Y-%m-%d")


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


def create_default_profile():
    return {
        "name": "Eric",
        "age": 13,
        "goal": "AI Systems Engineer",
        "current_project": "Atlas",
        "current_version": "Atlas 3.0",
        "learning_style": "喜欢通过项目实战学习，不喜欢重复听很多理论。"
    }


def create_default_skills():
    return {
        "student_name": "Eric",
        "skill_database_version": "Atlas 3.0 Skill Database v1",
        "skills": {
            "Arduino": {
                "score": 95,
                "level": "strong",
                "note": "Eric can already use Arduino for hardware feedback."
            },
            "Python": {
                "score": 80,
                "level": "good",
                "note": "Eric can use Python for JSON, file reading and writing."
            },
            "OpenCV": {
                "score": 75,
                "level": "good",
                "note": "Eric can use OpenCV for camera detection."
            },
            "YOLO": {
                "score": 60,
                "level": "developing",
                "note": "Eric needs more YOLO practice."
            },
            "ROS2": {
                "score": 0,
                "level": "not_started",
                "note": "Eric has not started ROS2 yet."
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


def create_default_emotion_memory():
    return {
        "student_name": "Eric",
        "emotion_memory_version": "Atlas 3.0 Emotion Memory v1",
        "emotion_records": []
    }


def create_default_recommendation_data():
    return {
        "student_name": "Eric",
        "mentor_recommendation_version": "Atlas 3.0 Mentor Recommendation v1",
        "recommendations": []
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

    if not LEARNING_PLAN_FILE.exists():
        save_json(LEARNING_PLAN_FILE, data)

    if "daily_learning_plans" not in data:
        data["daily_learning_plans"] = []

    return data


def load_emotion_data():
    data = safe_load_json(EMOTION_FILE, create_default_emotion_memory())

    if not EMOTION_FILE.exists():
        save_json(EMOTION_FILE, data)

    if "emotion_records" not in data:
        data["emotion_records"] = []

    return data


def load_recommendation_data():
    data = safe_load_json(MENTOR_RECOMMENDATION_FILE, create_default_recommendation_data())

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "mentor_recommendation_version" not in data:
        data["mentor_recommendation_version"] = "Atlas 3.0 Mentor Recommendation v1"

    if "recommendations" not in data:
        data["recommendations"] = []

    save_json(MENTOR_RECOMMENDATION_FILE, data)
    return data


def save_recommendation_data(data):
    save_json(MENTOR_RECOMMENDATION_FILE, data)


def load_mentor():
    profile_data = load_profile_data()
    skills_data = load_skills_data()
    history_data = load_history_data()
    learning_plan_data = load_learning_plan_data()
    emotion_data = load_emotion_data()
    recommendation_data = load_recommendation_data()

    return MentorRecommendation(
        profile_data,
        skills_data,
        history_data,
        learning_plan_data,
        emotion_data,
        recommendation_data
    )


def generate_and_save_recommendation(mentor):
    recommendation_text, decision = mentor.generate_recommendation_text()

    data = load_recommendation_data()

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
        "full_text": recommendation_text
    }

    data["recommendations"].append(record)
    save_recommendation_data(data)

    mentor.recommendation_data = data
    mentor.recommendations = data["recommendations"]

    print("\nAtlas 3.0 导师推荐：")
    print("-" * 70)
    print(recommendation_text)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Mentor Recommendation 生成导师推荐",
        recommendation_text
    )


def show_latest_recommendation():
    data = load_recommendation_data()
    recommendations = data.get("recommendations", [])

    if not recommendations:
        message = "目前还没有导师推荐。请先选择 1 生成导师推荐。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 3.0 Mentor Recommendation 查看最新推荐",
            message
        )
        return

    latest = recommendations[-1]
    content = latest.get("full_text", "")

    print("\n最新导师推荐：")
    print("-" * 70)
    print(content)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Mentor Recommendation 查看最新推荐",
        content
    )


def show_all_recommendations():
    data = load_recommendation_data()
    recommendations = data.get("recommendations", [])

    if not recommendations:
        message = "目前还没有任何导师推荐。"
        print("\n" + message)

        write_to_project_log(
            "Atlas 3.0 Mentor Recommendation 查看全部推荐",
            message
        )
        return

    print("\n全部导师推荐：")
    print("-" * 70)

    lines = []

    for index, item in enumerate(recommendations, start=1):
        text = (
            f"{index}. 日期：{item.get('date')} {item.get('time')} | "
            f"重点：{item.get('main_focus')} | "
            f"优先级：{item.get('priority')} | "
            f"预计时间：{item.get('estimated_time')}"
        )

        print(text)
        lines.append(text)

    write_to_project_log(
        "Atlas 3.0 Mentor Recommendation 查看全部推荐",
        "\n".join(lines)
    )


def show_recommendation_logic(mentor):
    explanation = mentor.generate_logic_explanation()

    print("\n导师推荐判断逻辑：")
    print("-" * 70)
    print(explanation)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Mentor Recommendation 判断逻辑",
        explanation
    )


def robot_answer_mentor_question(mentor):
    question = input("\n请输入问题，例如：我为什么现在要学 ROS2？").strip()

    if not question:
        question = "我为什么现在要学 ROS2？"

    question_lower = question.lower()
    decision = mentor.decide_main_recommendation()

    if "ros" in question_lower or "ros2" in question_lower:
        ros2_score = mentor.get_skill_score("ROS2")
        answer = (
            f"Eric，因为你的 ROS2 当前分数是 {ros2_score}。\n"
            "你的 Arduino、Python、OpenCV 已经有基础，说明你不再需要重复基础硬件。"
            "如果未来要做真正的机器人系统，ROS2 是必须补上的能力。"
        )

    elif "arduino" in question_lower:
        arduino_score = mentor.get_skill_score("Arduino")
        answer = (
            f"Eric，Arduino 当前分数是 {arduino_score}。\n"
            "它已经是你的强项，所以现在不建议继续重复基础 Arduino。"
            "更合理的下一步是进入 ROS2、YOLO 或系统整合。"
        )

    elif "今天" in question or "下一步" in question or "做什么" in question:
        answer = (
            f"今天建议重点：{decision['main_focus']}。\n"
            f"原因：{decision['reason']}\n"
            f"具体动作：\n"
            f"1. {decision['action_1']}\n"
            f"2. {decision['action_2']}\n"
            f"3. {decision['action_3']}"
        )

    elif "累" in question or "调试" in question or "debug" in question_lower:
        latest_emotion = mentor.get_latest_emotion_record()

        if latest_emotion:
            answer = (
                f"最近一次 Emotion Memory 显示：{latest_emotion.get('feeling', '')}。\n"
                f"连续调试时间：{latest_emotion.get('debug_hours', 0)} 小时。\n"
                "如果已经超过 3 到 4 小时，建议先休息，再回来做最小复现。"
            )
        else:
            answer = (
                "目前还没有 Emotion Memory 记录。建议先记录一次今天的调试状态，"
                "这样 Atlas 才能根据研发节奏给出提醒。"
            )

    else:
        answer = (
            "我会根据 Eric Profile、Skill Database、Project History、Learning Planner 和 Emotion Memory 来回答。\n"
            f"当前最重要推荐是：{decision['main_focus']}。\n"
            f"原因是：{decision['reason']}"
        )

    print("\n机器人回答：")
    print("-" * 70)
    print(answer)
    print("-" * 70)

    write_to_project_log(
        "Atlas 3.0 Mentor Recommendation 问题回答",
        f"Eric 的问题：{question}\n\n机器人回答：\n{answer}"
    )


def test_log_write():
    content = (
        "这是 Atlas 3.0 Mentor Recommendation 的日志写入测试。\n"
        "如果你能在 project_log.txt 里看到这段话，说明第六阶段日志保存正常。"
    )

    write_to_project_log(
        "Atlas 3.0 Mentor Recommendation 日志写入测试",
        content
    )


def show_intro(mentor):
    print("\n==============================")
    print("Atlas 3.0")
    print("Stage 6: Mentor Recommendation")
    print("==============================")
    print(f"学生：{mentor.student_name}")
    print(f"目标：{mentor.goal}")
    print(f"当前项目：{mentor.current_project}")
    print(f"当前版本：{mentor.current_version}")
    print(f"Profile 文件：{PROFILE_FILE}")
    print(f"Skills 文件：{SKILLS_FILE}")
    print(f"History 文件：{HISTORY_FILE}")
    print(f"Learning Plan 文件：{LEARNING_PLAN_FILE}")
    print(f"Emotion Memory 文件：{EMOTION_FILE}")
    print(f"Mentor Recommendation 文件：{MENTOR_RECOMMENDATION_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")
    print("当前目标：综合读取 Eric 的成长画像，自动生成导师推荐")
    print("==============================")


def main():
    mentor = load_mentor()
    show_intro(mentor)

    write_to_project_log(
        "Atlas 3.0 Mentor Recommendation 程序启动",
        "Atlas 3.0 第六阶段 Mentor Recommendation 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 生成并保存导师推荐")
        print("2. 查看最新导师推荐")
        print("3. 查看全部导师推荐")
        print("4. 解释导师推荐判断逻辑")
        print("5. 回答导师推荐相关问题")
        print("6. 测试 project_log.txt 是否能写入")
        print("7. 退出")

        choice = input("请输入数字 1-7：").strip()

        if choice == "1":
            generate_and_save_recommendation(mentor)

        elif choice == "2":
            show_latest_recommendation()

        elif choice == "3":
            show_all_recommendations()

        elif choice == "4":
            show_recommendation_logic(mentor)

        elif choice == "5":
            robot_answer_mentor_question(mentor)

        elif choice == "6":
            test_log_write()

        elif choice == "7":
            write_to_project_log(
                "Atlas 3.0 Mentor Recommendation 程序退出",
                "Atlas 3.0 第六阶段 Mentor Recommendation 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 7。")
            write_to_project_log(
                "Atlas 3.0 Mentor Recommendation 无效输入",
                f"用户输入了无效菜单数字：{choice}"
            )


if __name__ == "__main__":
    main()