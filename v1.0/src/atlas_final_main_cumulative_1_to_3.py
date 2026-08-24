import json
import time
from datetime import datetime, date, timedelta
from pathlib import Path

try:
    import serial
except ImportError:
    serial = None

try:
    import cv2
except ImportError:
    cv2 = None

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "atlas_final_data.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"
CAMERA_LOG_FILE = BASE_DIR / "camera_log.txt"
WEEKLY_REPORT_FILE = BASE_DIR / "weekly_report.txt"

# 自动迁移的旧数据文件
OLD_FILES = {
    "atlas_full": BASE_DIR / "atlas_full_data.json",      # 常见：Atlas 1.0 + 2.0 综合数据
    "atlas2": BASE_DIR / "atlas2_data.json",              # Atlas 2.0 数据
    "atlas3": BASE_DIR / "atlas3_data.json",              # Atlas 3.0 数据
    "integrated": BASE_DIR / "atlas_integrated_data.json",# 之前的 2.0 + 3.0 综合数据
    "memory": BASE_DIR / "memory.json",
    "profile": BASE_DIR / "profile.json",
    "skills": BASE_DIR / "skills.json",
    "history": BASE_DIR / "history.json",
    "learning_plan": BASE_DIR / "learning_plan.json",
    "emotion_memory": BASE_DIR / "emotion_memory.json",
    "recommendation": BASE_DIR / "mentor_recommendation.json",
    "projects": BASE_DIR / "projects.json",
    "tasks": BASE_DIR / "daily_tasks.json",
    "bugs": BASE_DIR / "bugs.json",
    "weekly_reports": BASE_DIR / "weekly_reports.json"
}

SERIAL_PORT = "COM3"
BAUD_RATE = 9600
arduino = None
CAMERA_INDEX = 0


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return date.today().strftime("%Y-%m-%d")


def yesterday():
    return (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")


def week_range():
    d = date.today()
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end


def read_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def log(title, content):
    text = "\n" + "=" * 70 + f"\n{title}\n时间：{now()}\n" + "=" * 70 + f"\n{content}\n" + "=" * 70 + "\n"
    PROJECT_LOG_FILE.open("a", encoding="utf-8").write(text)
    print("\n已写入 project_log.txt")
    print(f"日志文件位置：{PROJECT_LOG_FILE}")


def camera_log(title, content):
    text = "\n" + "=" * 70 + f"\n{title}\n时间：{now()}\n" + "=" * 70 + f"\n{content}\n" + "=" * 70 + "\n"
    CAMERA_LOG_FILE.open("a", encoding="utf-8").write(text)
    PROJECT_LOG_FILE.open("a", encoding="utf-8").write(text)
    print("\n已写入 camera_log.txt 和 project_log.txt")


def weekly_log(content):
    text = "\n" + "=" * 70 + f"\nAtlas Weekly Report\n生成时间：{now()}\n" + "=" * 70 + f"\n{content}\n" + "=" * 70 + "\n"
    WEEKLY_REPORT_FILE.open("a", encoding="utf-8").write(text)
    print("\n已写入 weekly_report.txt")


def next_id(items):
    ids = [x.get("id") for x in items if isinstance(x, dict) and isinstance(x.get("id"), int)]
    return max(ids) + 1 if ids else 1


def comma_list(text):
    return [x.strip() for x in text.split(",") if x.strip()]


def default_data():
    return {
        "student_name": "Eric",
        "atlas_version": "Atlas Final 1.0 + 2.0 + 3.0",
        "database_version": "Atlas Final Unified Database v1",

        # Atlas 1.0
        "progress_records": [],
        "project_logs": [],
        "mentor_advice_records": [],
        "emotion_support_records": [],
        "chat_records": [],
        "hardware_test_records": [],
        "camera_presence_records": [],

        # Atlas 2.0
        "projects": [
            {"id": 1, "name": "智能植物养护系统", "status": "完成", "progress": 100, "category": "AI + Hardware + Plant Care", "description": "Eric 已完成的科创项目。", "next_step": "整理项目证据。"},
            {"id": 2, "name": "Atlas 1.0", "status": "完成", "progress": 100, "category": "AI Mentor Robot", "description": "长期记忆、Project Log、导师建议、情绪支持、Arduino/OLED、摄像头检测。", "next_step": "已整合进最终版。"},
            {"id": 3, "name": "Atlas 2.0", "status": "完成", "progress": 100, "category": "Project Management Robot", "description": "项目数据库、每日任务、Bug、周报。", "next_step": "已整合进最终版。"},
            {"id": 4, "name": "Atlas 3.0", "status": "完成", "progress": 100, "category": "Digital Twin Mentor Robot", "description": "成长画像、技能数据库、项目历史、学习规划、研发情绪记忆、导师推荐。", "next_step": "录制最终 Demo。"}
        ],
        "daily_tasks": [],
        "bugs": [],
        "weekly_reports": [],

        # Atlas 3.0
        "profile": {
            "name": "Eric",
            "age": 13,
            "goal": "AI Systems Engineer",
            "current_project": "Atlas",
            "current_version": "Atlas Final",
            "interests": ["AI", "Robot", "Python", "Basketball"],
            "strengths": ["Arduino", "Python", "OpenCV", "Project Iteration", "Hardware Prototyping"],
            "weaknesses": ["ROS2", "Advanced Robot System Design", "Long-term Engineering Documentation"],
            "learning_style": "喜欢通过项目实战学习，不喜欢重复听很多理论。",
            "mentor_note": "Eric is building Atlas as a long-term AI research mentor robot."
        },
        "skills": {
            "Arduino": {"score": 95, "level": "strong", "note": "Eric can use Arduino for hardware feedback."},
            "Python": {"score": 80, "level": "good", "note": "Eric can use Python for JSON, file management, and OpenCV."},
            "OpenCV": {"score": 75, "level": "good", "note": "Eric can use OpenCV for camera detection."},
            "YOLO": {"score": 60, "level": "developing", "note": "Eric needs more object detection practice."},
            "ROS2": {"score": 0, "level": "not_started", "note": "ROS2 is important for future robot systems."}
        },
        "next_learning_focus": "ROS2",
        "project_history": [
            {"id": 1, "project_name": "智能植物养护系统", "version": "1.0 - 1.1", "status": "completed", "project_type": "AI + Hardware + Plant Care", "main_goal": "Build a smart plant care system.", "skills_learned": ["Arduino", "Sensors", "Serial Communication", "Hardware Wiring", "Project Iteration"], "key_problems": ["Hardware stability", "Sensor reading"], "transfer_to_atlas": "这些能力帮助 Atlas 控制硬件反馈。", "evidence": "Project logs, demo videos, prototype"},
            {"id": 2, "project_name": "Atlas 1.0 / AI Research Mentor Robot", "version": "1.0", "status": "completed", "project_type": "AI Mentor Robot", "main_goal": "Build a basic AI research mentor robot.", "skills_learned": ["Python", "JSON", "OpenCV", "Arduino Communication", "Project Log", "Debugging"], "key_problems": ["Camera false detection", "File path issue"], "transfer_to_atlas": "1.0 建立记忆、日志、硬件和视觉基础。", "evidence": "atlas_full_main.py, memory records"},
            {"id": 3, "project_name": "Atlas 2.0", "version": "2.0", "status": "completed", "project_type": "Project Management Robot", "main_goal": "Manage projects, daily tasks, bugs, and weekly reports.", "skills_learned": ["Project Database", "Daily Task", "Bug Manager", "Weekly Report"], "key_problems": ["Too many files", "Need integration"], "transfer_to_atlas": "2.0 建立研发管理能力。", "evidence": "atlas2_data.json"},
            {"id": 4, "project_name": "Atlas 3.0", "version": "3.0", "status": "completed", "project_type": "Digital Twin Mentor Robot", "main_goal": "Build Eric Digital Twin.", "skills_learned": ["Profile", "Skill Database", "Project History", "Learning Planner", "Emotion Memory", "Mentor Recommendation"], "key_problems": ["Need final integration"], "transfer_to_atlas": "3.0 建立个性化导师能力。", "evidence": "atlas3_data.json"}
        ],
        "daily_learning_plans": [],
        "emotion_records": [],
        "recommendations": []
    }


def ensure(data):
    d = default_data()
    for k, v in d.items():
        if k not in data:
            data[k] = v
    list_keys = ["progress_records", "project_logs", "mentor_advice_records", "emotion_support_records", "chat_records", "hardware_test_records", "camera_presence_records", "projects", "daily_tasks", "bugs", "weekly_reports", "project_history", "daily_learning_plans", "emotion_records", "recommendations"]
    for k in list_keys:
        if not isinstance(data.get(k), list):
            data[k] = d[k]
    if not isinstance(data.get("profile"), dict):
        data["profile"] = d["profile"]
    if not isinstance(data.get("skills"), dict):
        data["skills"] = d["skills"]
    if not data["projects"]:
        data["projects"] = d["projects"]
    if not data["project_history"]:
        data["project_history"] = d["project_history"]
    return data


def merge_list(base, extra):
    result = list(base)
    signatures = {json.dumps(x, ensure_ascii=False, sort_keys=True) for x in result if isinstance(x, dict)}
    for item in extra:
        if not isinstance(item, dict):
            continue
        sig = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if sig not in signatures:
            result.append(item)
            signatures.add(sig)
    return result


def migrate_data():
    if DATA_FILE.exists():
        data = ensure(read_json(DATA_FILE, default_data()))
        write_json(DATA_FILE, data)
        return data

    data = default_data()

    # 大型综合文件迁移
    for key in ["atlas_full", "atlas2", "atlas3", "integrated"]:
        old = read_json(OLD_FILES[key], {})
        if not old:
            continue
        for list_key in ["progress_records", "project_logs", "mentor_advice_records", "emotion_support_records", "chat_records", "hardware_test_records", "camera_presence_records", "projects", "daily_tasks", "bugs", "weekly_reports", "project_history", "daily_learning_plans", "emotion_records", "recommendations"]:
            if isinstance(old.get(list_key), list):
                data[list_key] = merge_list(data.get(list_key, []), old[list_key])
        if isinstance(old.get("profile"), dict):
            data["profile"].update(old["profile"])
        if isinstance(old.get("skills"), dict):
            data["skills"].update(old["skills"])
        if old.get("next_learning_focus"):
            data["next_learning_focus"] = old["next_learning_focus"]

    # 分散文件迁移
    memory = read_json(OLD_FILES["memory"], {})
    for list_key in ["progress_records", "project_logs", "mentor_advice_records", "emotion_support_records", "chat_records", "hardware_test_records", "camera_presence_records"]:
        if isinstance(memory.get(list_key), list):
            data[list_key] = merge_list(data[list_key], memory[list_key])

    profile = read_json(OLD_FILES["profile"], {})
    if isinstance(profile, dict) and profile:
        data["profile"].update(profile)

    skills = read_json(OLD_FILES["skills"], {})
    if isinstance(skills.get("skills"), dict):
        data["skills"].update(skills["skills"])
    if skills.get("next_learning_focus"):
        data["next_learning_focus"] = skills["next_learning_focus"]

    history = read_json(OLD_FILES["history"], {})
    if isinstance(history.get("project_history"), list):
        data["project_history"] = merge_list(data["project_history"], history["project_history"])

    lp = read_json(OLD_FILES["learning_plan"], {})
    if isinstance(lp.get("daily_learning_plans"), list):
        data["daily_learning_plans"] = merge_list(data["daily_learning_plans"], lp["daily_learning_plans"])

    em = read_json(OLD_FILES["emotion_memory"], {})
    if isinstance(em.get("emotion_records"), list):
        data["emotion_records"] = merge_list(data["emotion_records"], em["emotion_records"])

    rec = read_json(OLD_FILES["recommendation"], {})
    if isinstance(rec.get("recommendations"), list):
        data["recommendations"] = merge_list(data["recommendations"], rec["recommendations"])

    for file_key, list_key, inner_key in [
        ("projects", "projects", "projects"),
        ("tasks", "daily_tasks", "daily_tasks"),
        ("bugs", "bugs", "bugs"),
        ("weekly_reports", "weekly_reports", "weekly_reports")
    ]:
        obj = read_json(OLD_FILES[file_key], {})
        if isinstance(obj.get(inner_key), list):
            data[list_key] = merge_list(data[list_key], obj[inner_key])

    data = ensure(data)
    write_json(DATA_FILE, data)
    log("Atlas Final 总数据库初始化", "已创建 atlas_final_data.json，并尝试迁移 Atlas 1.0、2.0、3.0 的旧数据。")
    return data


def save(data):
    write_json(DATA_FILE, data)


# ===================== Atlas 1.0 =====================

def connect_arduino():
    global arduino
    if serial is None:
        log("Arduino 连接记录", "没有安装 pyserial，硬件反馈暂时不可用。安装命令：python -m pip install pyserial")
        return None
    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        log("Arduino 连接记录", f"Arduino 已连接：{SERIAL_PORT}")
        return arduino
    except Exception as e:
        log("Arduino 连接记录", f"暂时没有连接到 Arduino，软件功能仍可使用。原因：{e}")
        return None


def send_arduino(cmd):
    if arduino is None:
        return
    try:
        arduino.write((cmd + "\n").encode("utf-8"))
        time.sleep(0.2)
    except Exception as e:
        log("Arduino 指令发送失败", str(e))


def save_chat(data, user_input, reply):
    data["chat_records"].append({"date": today(), "time": datetime.now().strftime("%H:%M:%S"), "user_input": user_input, "robot_reply": reply})
    save(data)
    log("Atlas 1.0 Chat Record", f"Eric 输入：\n{user_input}\n\n机器人回答：\n{reply}")


def progress_advice(text):
    lower = text.lower()
    if "atlas 3.0" in lower or "profile" in lower or "skill" in lower:
        return "下一步检查 Profile、Skills、History、Learning Planner、Emotion Memory 和 Mentor Recommendation 是否能联动。"
    if "atlas 2.0" in lower or "bug" in lower or "weekly" in lower:
        return "下一步检查 Project Database、Daily Task、Bug Manager 和 Weekly Report 是否能保存和查询。"
    if "失败" in text or "报错" in text or "卡住" in text:
        return "先记录失败现象、触发条件、尝试过的方法和下一步排查方向。"
    if "完成" in text:
        return "建议保存截图、录屏，并写入 Project Log，作为版本证据。"
    return "建议把今天的进展拆成：完成了什么、遇到什么问题、明天做什么。"


def add_progress(data):
    text = input("\n今天的进展：").strip()
    if not text:
        print("没有输入，不保存。")
        return
    data["progress_records"].append({"date": today(), "time": datetime.now().strftime("%H:%M:%S"), "content": text})
    send_arduino("WARNING" if any(x in text for x in ["问题", "失败", "报错", "卡住"]) else "HAPPY")
    reply = f"已保存到长期记忆。\n机器人记住了：{text}\n\n导师建议：\n{progress_advice(text)}"
    save(data)
    save_chat(data, text, reply)
    print("\n" + reply)


def add_project_log(data):
    print("\n开始填写 Project Log。")
    goal = input("今天目标：").strip() or "未填写"
    done = input("今天完成：").strip() or "未填写"
    problem = input("遇到的问题：").strip() or "暂时没有明显问题"
    solution = input("怎么解决：").strip() or "暂时没有解决方案"
    next_step = input("下一步：").strip() or "继续推进当前项目"
    advice = "建议保存截图、运行结果和日志。"
    if problem not in ["无", "暂时没有明显问题"]:
        advice += " 问题不要删除，要保留为真实 debug 证据。"
    record = {"date": today(), "time": datetime.now().strftime("%H:%M:%S"), "today_goal": goal, "today_finished": done, "problem": problem, "solution": solution, "next_step": next_step, "mentor_advice": advice}
    data["project_logs"].append(record)
    data["progress_records"].append({"date": today(), "time": record["time"], "content": done})
    save(data)
    content = f"目标：{goal}\n完成：{done}\n问题：{problem}\n解决：{solution}\n下一步：{next_step}\n导师建议：{advice}"
    print("\n" + content)
    log("Atlas 1.0 Project Log", content)


def ask_basic_mentor(data):
    q = input("\nEric 的问题：").strip() or "我下一步该做什么？"
    recent_progress = data["progress_records"][-1]["content"] if data["progress_records"] else "暂无"
    recent_task = data["daily_tasks"][-1].get("today_plan", "暂无") if data["daily_tasks"] else "暂无"
    recent_bug = data["bugs"][-1].get("bug_title", "暂无") if data["bugs"] else "暂无"
    reply = f"我先读取历史：\n最近进展：{recent_progress}\n最近任务：{recent_task}\n最近 Bug：{recent_bug}\n\n导师建议："
    if "下一步" in q or "怎么" in q:
        reply += "先运行一键 Demo 总览，确认 1.0、2.0、3.0 都能被一个主程序调用。"
    elif "报错" in q or "bug" in q.lower() or "卡住" in q:
        reply += "先记录 Bug，再做最小复现，不要同时改多个功能。"
    else:
        reply += "按 1.0 记忆与感知、2.0 项目管理、3.0 个性化导师三层结构推进。"
    data["mentor_advice_records"].append({"date": today(), "time": datetime.now().strftime("%H:%M:%S"), "question": q, "advice": reply})
    save(data)
    print("\n" + reply)
    log("Atlas 1.0 导师建议", reply)


def basic_emotion_support(data):
    feeling = input("\nEric 当前研发状态：").strip() or "有点卡住"
    reply = "我不是心理医生，我只是研发导师。"
    if "失败" in feeling or "报错" in feeling:
        reply += "\n失败和报错是研发过程的一部分。先记录触发条件和尝试过的方法。"
    elif "卡住" in feeling or "不知道" in feeling:
        reply += "\n卡住通常是任务太大。下一步只做一个最小测试。"
    elif "累" in feeling or "烦" in feeling or "崩溃" in feeling:
        reply += "\n先暂停，再回来继续。不要用情绪判断项目价值。"
    else:
        reply += "\n继续把当前问题写入 Project Log。"
    data["emotion_support_records"].append({"date": today(), "time": datetime.now().strftime("%H:%M:%S"), "feeling": feeling, "support": reply})
    save(data)
    print("\n" + reply)
    log("Atlas 1.0 研发情绪支持", reply)


def remember_yesterday(data):
    y = yesterday()
    parts = [f"昨天日期：{y}"]
    for key, title, field in [("progress_records", "进展", "content"), ("daily_tasks", "任务", "today_plan"), ("bugs", "Bug", "bug_title")]:
        rows = [r for r in data[key] if r.get("date") == y]
        if rows:
            parts.append(f"\n{title}：")
            for r in rows:
                parts.append("- " + str(r.get(field, "")))
    if len(parts) == 1:
        parts.append("昨天没有找到记录。")
    reply = "\n".join(parts)
    print("\n" + reply)
    log("Atlas 1.0 回忆昨天记录", reply)


def test_hardware(data):
    tests = [("HAPPY", "开心"), ("WARNING", "提醒"), ("ERROR", "错误"), ("THINKING", "思考"), ("NOD", "点头"), ("OFF", "关闭")]
    lines = []
    for cmd, desc in tests:
        print(f"测试 {cmd}：{desc}")
        send_arduino(cmd)
        lines.append(f"{cmd}：{desc}")
        time.sleep(0.5)
    data["hardware_test_records"].append({"date": today(), "time": datetime.now().strftime("%H:%M:%S"), "content": lines})
    save(data)
    log("Atlas 1.0 硬件反馈测试", "\n".join(lines))


def camera_check(data):
    if cv2 is None:
        msg = "没有安装 opencv-python。安装命令：python -m pip install opencv-python numpy"
        print(msg)
        log("摄像头错误", msg)
        return
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        msg = "摄像头打开失败。请检查是否被其他软件占用。"
        print(msg)
        camera_log("摄像头测试失败", msg)
        return
    face_model = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(face_model)
    if face_cascade.empty():
        msg = "OpenCV 人脸模型加载失败。"
        print(msg)
        camera.release()
        camera_log("摄像头测试失败", msg)
        return
    print("摄像头检测开始。按 q 退出。")
    start = time.time()
    frames = 0
    face_frames = 0
    while True:
        ok, frame = camera.read()
        if not ok:
            break
        frames += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(45, 45))
        if len(faces) > 0:
            face_frames += 1
            status = "PERSON PRESENT"
            color = (0, 255, 0)
            send_arduino("HAPPY")
        else:
            status = "NO PERSON"
            color = (0, 0, 255)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.putText(frame, "Press q to quit", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("Atlas Final Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        if time.time() - start > 40:
            break
    camera.release()
    cv2.destroyAllWindows()
    ratio = face_frames / frames if frames else 0
    result = f"总帧数：{frames}\n检测到人脸帧数：{face_frames}\n人脸比例：{ratio:.2%}\n最终判断：{'检测到 Eric 在画面中' if ratio > 0 else '未检测到 Eric'}"
    data["camera_presence_records"].append({"date": today(), "time": datetime.now().strftime("%H:%M:%S"), "result": result})
    save(data)
    print("\n" + result)
    camera_log("Atlas 1.0 摄像头检测", result)


# ===================== Atlas 2.0 =====================

def project_summary(data):
    lines = [f"Eric 现在一共有 {len(data['projects'])} 个项目。"]
    completed = [p for p in data["projects"] if p.get("status") in ["完成", "completed"]]
    lines.append(f"已完成项目：{len(completed)} 个。")
    lines.append("项目列表：")
    for p in data["projects"]:
        lines.append(f"- {p.get('name', p.get('project_name', '未命名'))} | 状态：{p.get('status')} | 完成度：{p.get('progress', 0)}%")
    return "\n".join(lines)


def show_projects(data):
    content = project_summary(data)
    print("\nProject Database：")
    print("-" * 70)
    print(content)
    print("-" * 70)
    log("Atlas 2.0 Project Database", content)


def show_project_options(data):
    print("\n当前项目：")
    for p in data["projects"]:
        print(f"{p.get('id', '?')}. {p.get('name', p.get('project_name', '未命名'))} | {p.get('status')} | {p.get('progress', 0)}%")


def today_task(data):
    for t in data["daily_tasks"]:
        if t.get("date") == today():
            return t
    return None


def task_text(t):
    return f"日期：{t.get('date')}\n项目：{t.get('project_name')}\n计划：{t.get('today_plan')}\n预计：{t.get('estimated_hours')}小时\n优先级：{t.get('priority')}\n状态：{t.get('status')}\n实际完成：{t.get('finished_result', '')}\n问题：{t.get('problem', '')}\n下一步：{t.get('next_step', '')}\n导师评价：{t.get('mentor_comment', '')}"


def create_task(data):
    old = today_task(data)
    if old:
        print("\n今天已有任务：")
        print(task_text(old))
        if input("是否覆盖？输入 y：").strip().lower() != "y":
            return
        data["daily_tasks"].remove(old)
    show_project_options(data)
    project = input("\n今天任务属于哪个项目？").strip() or "Atlas Final"
    plan = input("今天准备完成什么？").strip() or "测试 Atlas Final"
    h = input("预计几个小时？").strip()
    priority = input("优先级（高/中/低）：").strip() or "高"
    reason = input("为什么做？").strip() or "这是最终综合版测试。"
    task = {"date": today(), "created_time": datetime.now().strftime("%H:%M:%S"), "project_name": project, "today_plan": plan, "estimated_hours": int(h) if h.isdigit() else 1, "priority": priority, "reason": reason, "status": "未完成", "evening_review_done": False, "finished_result": "", "problem": "", "next_step": "", "mentor_comment": ""}
    data["daily_tasks"].append(task)
    save(data)
    content = task_text(task)
    print("\n" + content)
    log("Atlas 2.0 创建 Daily Task", content)


def show_task(data):
    t = today_task(data)
    content = task_text(t) if t else "今天还没有 Daily Task。"
    print("\n" + content)
    log("Atlas 2.0 查看 Daily Task", content)


def review_task(data):
    t = today_task(data)
    if not t:
        print("今天还没有 Daily Task。")
        return
    status = input("完成情况（完成/部分完成/未完成）：").strip()
    done = input("今天实际完成了什么？").strip() or "未填写"
    problem = input("遇到什么问题？").strip() or "无"
    next_step = input("明天下一步？").strip() or "继续完成任务"
    if status not in ["完成", "部分完成", "未完成"]:
        status = "部分完成"
    t.update({"status": status, "evening_review_done": True, "finished_result": done, "problem": problem, "next_step": next_step, "mentor_comment": "研发管理的重点是形成闭环。"})
    save(data)
    content = task_text(t)
    print("\n" + content)
    log("Atlas 2.0 Daily Task 复盘", content)


def bug_text(b):
    return f"Bug ID：{b.get('id')}\n日期：{b.get('date')}\n项目：{b.get('project_name')}\n标题：{b.get('bug_title')}\n现象：{b.get('bug_description')}\n触发条件：{b.get('trigger_condition')}\n尝试：{b.get('attempted_solution')}\n严重程度：{b.get('severity')}\n状态：{b.get('status')}\n解决方法：{b.get('solution', '')}\n下一步：{b.get('next_step')}\n导师建议：{b.get('mentor_comment')}"


def add_bug(data):
    project = input("Bug 属于哪个项目？").strip() or "Atlas Final"
    title = input("Bug 标题：").strip()
    if not title:
        print("Bug 标题不能为空。")
        return
    desc = input("Bug 现象：").strip() or "未填写"
    trigger = input("什么时候出现？").strip() or "未填写"
    attempted = input("尝试过什么？").strip() or "无"
    severity = input("严重程度（高/中/低）：").strip()
    if severity not in ["高", "中", "低"]:
        severity = "中"
    next_step = input("下一步？").strip() or "继续最小复现"
    mentor = "先做最小复现，不要同时改多个功能。"
    bug = {"id": next_id(data["bugs"]), "date": today(), "created_time": datetime.now().strftime("%H:%M:%S"), "project_name": project, "bug_title": title, "bug_description": desc, "trigger_condition": trigger, "attempted_solution": attempted, "severity": severity, "status": "未解决", "solution": "", "fixed_time": "", "next_step": next_step, "mentor_comment": mentor}
    data["bugs"].append(bug)
    save(data)
    content = bug_text(bug)
    print("\n" + content)
    log("Atlas 2.0 新增 Bug", content)


def show_bugs(data):
    keyword = input("直接回车查看全部 Bug；输入关键词搜索：").strip()
    matched = []
    for b in data["bugs"]:
        s = json.dumps(b, ensure_ascii=False)
        if not keyword or keyword.lower() in s.lower():
            matched.append(b)
    if not matched:
        content = "没有找到 Bug。"
    else:
        content = "\n\n".join(bug_text(b) for b in matched)
    print("\n" + content)
    log("Atlas 2.0 查询 Bug", content)


def update_bug(data):
    bug_id = input("要更新的 Bug ID：").strip()
    if not bug_id.isdigit():
        print("请输入数字 ID。")
        return
    bug = next((b for b in data["bugs"] if b.get("id") == int(bug_id)), None)
    if not bug:
        print("没有找到这个 Bug。")
        return
    print(bug_text(bug))
    status = input("新状态（未解决/排查中/已解决）：").strip()
    solution = input("解决方法或排查结果：").strip()
    next_step = input("下一步：").strip()
    if status in ["未解决", "排查中", "已解决"]:
        bug["status"] = status
    if solution:
        bug["solution"] = solution
    if next_step:
        bug["next_step"] = next_step
    if bug.get("status") == "已解决":
        bug["fixed_time"] = now()
    save(data)
    content = bug_text(bug)
    print("\n" + content)
    log("Atlas 2.0 更新 Bug", content)


def weekly_report(data):
    start, end = week_range()
    tasks = [t for t in data["daily_tasks"] if start <= datetime.strptime(t.get("date", today()), "%Y-%m-%d").date() <= end]
    bugs = [b for b in data["bugs"] if start <= datetime.strptime(b.get("date", today()), "%Y-%m-%d").date() <= end]
    lines = ["Atlas Final Weekly Report", f"周报周期：{start} 至 {end}", "", "一、项目总览", project_summary(data), "", "二、Daily Task", f"本周任务数：{len(tasks)}", *[f"- {t.get('date')} | {t.get('project_name')} | {t.get('today_plan')} | {t.get('status')}" for t in tasks], "", "三、Bug", f"本周 Bug 数：{len(bugs)}", *[f"- {b.get('bug_title')} | {b.get('status')} | {b.get('severity')}" for b in bugs], "", "四、Atlas 3.0 补充", f"Learning Plan：{len(data['daily_learning_plans'])} 条", f"Emotion Memory：{len(data['emotion_records'])} 条", f"Mentor Recommendation：{len(data['recommendations'])} 条"]
    content = "\n".join(lines)
    data["weekly_reports"].append({"week_start": str(start), "week_end": str(end), "created_date": today(), "created_time": datetime.now().strftime("%H:%M:%S"), "content": content})
    save(data)
    weekly_log(content)
    log("Atlas Final Weekly Report", content)
    print("\n" + content)


def show_weekly(data):
    content = data["weekly_reports"][-1]["content"] if data["weekly_reports"] else "目前还没有 Weekly Report。"
    print("\n" + content)
    log("查看最新 Weekly Report", content)


# ===================== Atlas 3.0 =====================

def profile_text(data):
    p = data["profile"]
    return f"{p.get('name', 'Eric')}，我已经读取你的成长画像。\n年龄：{p.get('age')}\n目标：{p.get('goal')}\n当前项目：{p.get('current_project')}\n当前版本：{p.get('current_version')}\n兴趣：{'、'.join(p.get('interests', []))}\n强项：{'、'.join(p.get('strengths', []))}\n需要补强：{'、'.join(p.get('weaknesses', []))}\n学习风格：{p.get('learning_style')}"


def show_profile(data):
    content = profile_text(data)
    print("\n" + content)
    log("Atlas 3.0 查看 Eric Profile", content)


def profile_intro(data):
    p = data["profile"]
    content = f"{p.get('name', 'Eric')}，目前你正在开发 {p.get('current_project')}，当前版本是 {p.get('current_version')}。你的目标是成为 {p.get('goal')}。"
    print("\n" + content)
    log("Atlas 3.0 Profile 身份回答", content)


def update_profile(data):
    p = data["profile"]
    for key, label in [("name", "名字"), ("age", "年龄"), ("goal", "目标"), ("current_project", "当前项目"), ("current_version", "当前版本"), ("learning_style", "学习风格")]:
        value = input(f"{label}（当前：{p.get(key)}）：").strip()
        if value:
            p[key] = int(value) if key == "age" and value.isdigit() else value
    save(data)
    content = profile_text(data)
    print("\n" + content)
    log("Atlas 3.0 更新 Profile", content)


def level(score):
    if score >= 90: return "strong"
    if score >= 75: return "good"
    if score >= 40: return "developing"
    if score > 0: return "beginner"
    return "not_started"


def skill_score(data, name):
    item = data["skills"].get(name)
    return item.get("score", 0) if item else None


def strong_skills(data):
    return [k for k, v in data["skills"].items() if v.get("score", 0) >= 80]


def developing_skills(data):
    return [k for k, v in data["skills"].items() if 40 <= v.get("score", 0) < 80]


def weak_skills(data):
    return [k for k, v in data["skills"].items() if v.get("score", 0) < 40]


def show_skills(data):
    lines = ["Eric 的 Skill Database："]
    for k, v in data["skills"].items():
        lines.append(f"- {k}：{v.get('score')} 分，level：{v.get('level')}，说明：{v.get('note')}")
    lines.append(f"强项：{'、'.join(strong_skills(data))}")
    lines.append(f"发展中：{'、'.join(developing_skills(data))}")
    lines.append(f"需要补强：{'、'.join(weak_skills(data))}")
    content = "\n".join(lines)
    print("\n" + content)
    log("Atlas 3.0 查看 Skill Database", content)


def skill_advice(data):
    ros2 = skill_score(data, "ROS2")
    yolo = skill_score(data, "YOLO")
    if ros2 is not None and ros2 < 40:
        content = "Arduino、Python、OpenCV 已经有基础，但 ROS2 还没开始。下一步建议学习 ROS2，而不是继续重复基础 Arduino。"
    elif yolo is not None and yolo < 80:
        content = "下一步建议继续补强 YOLO，让机器人视觉识别能力更强。"
    else:
        content = "基础技能较好，可以准备 Atlas Final Demo。"
    print("\n" + content)
    log("Atlas 3.0 技能建议", content)


def update_skill(data):
    name = input("技能名称：").strip()
    if not name:
        return
    if name not in data["skills"]:
        data["skills"][name] = {"score": 0, "level": "not_started", "note": "New skill"}
    score_text = input(f"新分数（当前：{data['skills'][name].get('score')}）：").strip()
    note = input(f"说明（当前：{data['skills'][name].get('note')}）：").strip()
    if score_text.isdigit():
        score = max(0, min(100, int(score_text)))
        data["skills"][name]["score"] = score
        data["skills"][name]["level"] = level(score)
    if note:
        data["skills"][name]["note"] = note
    save(data)
    content = f"{name}：{data['skills'][name]}"
    print("\n" + content)
    log("Atlas 3.0 更新技能", content)


def history_text(data):
    lines = [f"Eric 的 Project History，共 {len(data['project_history'])} 个项目："]
    for p in data["project_history"]:
        lines.append(f"- {p.get('project_name')} ({p.get('version')}) | {p.get('status')} | 学到：{'、'.join(p.get('skills_learned', []))}")
    return "\n".join(lines)


def show_history(data):
    content = history_text(data)
    print("\n" + content)
    log("Atlas 3.0 查看 Project History", content)


def history_transfer(data):
    content = "Eric 的项目不是孤立的：植物系统训练硬件和串口通信，Atlas 1.0 训练记忆、日志、硬件反馈和摄像头，Atlas 2.0 训练项目管理，Atlas 3.0 把这些经验整合成 Eric Digital Twin。"
    print("\n" + content)
    log("Atlas 3.0 项目迁移建议", content)


def search_history(data):
    kw = input("搜索关键词：").strip()
    result = [p for p in data["project_history"] if kw.lower() in p.get("project_name", "").lower()]
    content = "\n\n".join(json.dumps(p, ensure_ascii=False, indent=2) for p in result) if result else "没有找到。"
    print("\n" + content)
    log("Atlas 3.0 搜索历史项目", content)


def decide_focus(data):
    ros2 = skill_score(data, "ROS2")
    yolo = skill_score(data, "YOLO")
    if ros2 is not None and ros2 < 40:
        return {"focus": "ROS2", "reason": "Arduino、Python、OpenCV 已经有基础，但 ROS2 还没开始。", "task_1": "了解 ROS2 是什么。", "task_2": "整理 Node、Topic、Message 三个概念。", "task_3": "把 ROS2 加入长期学习计划。", "estimated_time": "2 小时"}
    if yolo is not None and yolo < 80:
        return {"focus": "YOLO", "reason": "OpenCV 已有基础，但 YOLO 还在发展中。", "task_1": "复习 YOLO 用途。", "task_2": "准备测试素材。", "task_3": "记录 YOLO 和 OpenCV 区别。", "estimated_time": "2 小时"}
    return {"focus": "Atlas Final Demo", "reason": "1.0、2.0、3.0 已整合，下一步应展示证据。", "task_1": "测试一键 Demo。", "task_2": "录制 Demo。", "task_3": "写 Version Note。", "estimated_time": "2 小时"}


def morning_message(data):
    p = data["profile"]
    f = decide_focus(data)
    return f"{p.get('name', 'Eric')}，早上好。\n我已经读取 1.0 长期记忆、2.0 项目管理和 3.0 成长画像。\n今天建议重点：{f['focus']}。\n原因：{f['reason']}\n预计时间：{f['estimated_time']}。"


def show_morning(data):
    content = morning_message(data)
    print("\n" + content)
    log("Atlas 3.0 开机主动提醒", content)


def generate_plan(data):
    p = data["profile"]
    f = decide_focus(data)
    plan = {"date": today(), "created_time": datetime.now().strftime("%H:%M:%S"), "student_name": p.get("name", "Eric"), "current_project": p.get("current_project", "Atlas"), "current_version": p.get("current_version", "Atlas Final"), "goal": p.get("goal"), "today_focus": f["focus"], "reason": f["reason"], "task_1": f["task_1"], "task_2": f["task_2"], "task_3": f["task_3"], "estimated_time": f["estimated_time"], "strong_skills": strong_skills(data), "developing_skills": developing_skills(data), "weak_skills": weak_skills(data), "learning_style": p.get("learning_style"), "status": "planned", "evening_review": ""}
    data["daily_learning_plans"] = [x for x in data["daily_learning_plans"] if x.get("date") != today()]
    data["daily_learning_plans"].append(plan)
    save(data)
    content = json.dumps(plan, ensure_ascii=False, indent=2)
    print("\n" + content)
    log("Atlas 3.0 生成 Learning Plan", content)


def show_today_plan(data):
    plan = next((p for p in data["daily_learning_plans"] if p.get("date") == today()), None)
    content = json.dumps(plan, ensure_ascii=False, indent=2) if plan else "今天还没有 Learning Plan。"
    print("\n" + content)
    log("Atlas 3.0 查看 Learning Plan", content)


def learning_logic(data):
    f = decide_focus(data)
    content = f"判断逻辑：\n1. 读取 1.0 长期记忆和 Project Log。\n2. 读取 2.0 项目、任务、Bug、周报。\n3. 读取 3.0 Profile、Skills、History。\n4. 当前建议：{f['focus']}。\n原因：{f['reason']}"
    print("\n" + content)
    log("Atlas 3.0 Learning Planner 判断逻辑", content)


def review_plan(data):
    plan = next((p for p in data["daily_learning_plans"] if p.get("date") == today()), None)
    if not plan:
        print("今天还没有 Learning Plan。")
        return
    status = input("完成情况（完成/部分完成/未完成）：").strip() or "部分完成"
    done = input("实际完成：").strip() or "未填写"
    problem = input("问题：").strip() or "无"
    next_step = input("明天下一步：").strip() or "继续当前计划"
    plan["status"] = status
    plan["evening_review"] = f"完成情况：{status}\n实际完成：{done}\n问题：{problem}\n明天下一步：{next_step}"
    save(data)
    content = json.dumps(plan, ensure_ascii=False, indent=2)
    print("\n" + content)
    log("Atlas 3.0 Learning Plan 复盘", content)


def add_emotion(data):
    feeling = input("今天研发状态：").strip() or "有点卡住"
    h = input("连续调试几个小时？").strip()
    hours = int(h) if h.isdigit() else 1
    problem = input("卡在哪个问题？").strip() or "未填写"
    attempted = input("尝试过什么？").strip() or "未填写"
    next_step = input("下一步？").strip() or "先缩小问题，再做最小测试。"
    record = {"date": today(), "time": datetime.now().strftime("%H:%M:%S"), "feeling": feeling, "debug_hours": hours, "problem": problem, "attempted": attempted, "next_step": next_step}
    data["emotion_records"].append(record)
    save(data)
    advice = emotion_advice(record)
    content = json.dumps(record, ensure_ascii=False, indent=2) + "\n\n机器人提醒：\n" + advice
    print("\n" + content)
    log("Atlas 3.0 新增 Emotion Memory", content)


def emotion_advice(record):
    hours = record.get("debug_hours", 0)
    feeling = record.get("feeling", "")
    if hours >= 4:
        return f"你已经连续调试 {hours} 小时，建议先休息 15 到 20 分钟，再回来只测试一个最小问题。"
    if "卡住" in feeling or "失败" in feeling or "报错" in feeling:
        return "先记录问题，不要同时改多个功能。"
    return "当前节奏可控，继续记录 Project Log。"


def show_emotions(data):
    records = data["emotion_records"][-5:]
    content = "\n\n".join(json.dumps(r, ensure_ascii=False, indent=2) for r in records) if records else "暂无 Emotion Memory。"
    print("\n" + content)
    log("Atlas 3.0 查看 Emotion Memory", content)


def emotion_summary(data):
    records = data["emotion_records"]
    long_count = len([r for r in records if r.get("debug_hours", 0) >= 3])
    stuck = len([r for r in records if "卡住" in r.get("feeling", "")])
    content = f"研发状态记录：{len(records)} 条。\n连续调试 3 小时以上：{long_count} 次。\n卡住记录：{stuck} 次。\n说明：这不是心理诊断，只是研发节奏记录。"
    print("\n" + content)
    log("Atlas 3.0 Emotion Memory 总结", content)


def emotion_reminder(data):
    content = emotion_advice(data["emotion_records"][-1]) if data["emotion_records"] else "暂无研发状态记录。"
    print("\n" + content)
    log("Atlas 3.0 Emotion Memory 提醒", content)


def decide_recommendation(data):
    if data["emotion_records"] and data["emotion_records"][-1].get("debug_hours", 0) >= 4:
        return {"focus": "Debug Rhythm Control", "recommendation": "先休息 15 到 20 分钟，再回来只测试一个最小问题。", "reason": "最近连续调试时间过长。", "actions": ["休息", "只开一个文件", "只测一个功能"], "time": "30 分钟", "priority": "high"}
    f = decide_focus(data)
    return {"focus": f["focus"], "recommendation": f"下一步建议做 {f['focus']}。", "reason": f["reason"], "actions": [f["task_1"], f["task_2"], f["task_3"]], "time": f["estimated_time"], "priority": "high" if f["focus"] == "ROS2" else "medium"}


def mentor_recommendation(data):
    p = data["profile"]
    r = decide_recommendation(data)
    content = f"{p.get('name', 'Eric')}，这是 Atlas Final 导师推荐。\n\n读取到的目标：{p.get('goal')}\n推荐重点：{r['focus']}\n推荐内容：{r['recommendation']}\n推荐原因：{r['reason']}\n优先级：{r['priority']}\n具体动作：\n1. {r['actions'][0]}\n2. {r['actions'][1]}\n3. {r['actions'][2]}\n预计时间：{r['time']}\n\n这不是随机建议，它综合读取了 1.0、2.0、3.0 数据。"
    data["recommendations"].append({"date": today(), "time": datetime.now().strftime("%H:%M:%S"), "main_focus": r["focus"], "priority": r["priority"], "recommendation": r["recommendation"], "reason": r["reason"], "actions": r["actions"], "estimated_time": r["time"], "full_text": content})
    save(data)
    print("\n" + content)
    log("Atlas 3.0 生成 Mentor Recommendation", content)


def show_recommendation(data):
    content = data["recommendations"][-1].get("full_text") if data["recommendations"] else "暂无导师推荐。"
    print("\n" + content)
    log("查看最新导师推荐", content)


def recommendation_logic(data):
    r = decide_recommendation(data)
    content = f"推荐逻辑：\n1. 读取 1.0 长期记忆、Project Log、摄像头/硬件记录。\n2. 读取 2.0 项目、任务、Bug、周报。\n3. 读取 3.0 Profile、Skills、History、Learning Plan、Emotion Memory。\n4. 当前推荐：{r['focus']}。\n原因：{r['reason']}"
    print("\n" + content)
    log("导师推荐判断逻辑", content)


# ===================== Demo / overview =====================

def database_overview(data):
    content = f"""总数据库文件：{DATA_FILE}
版本：{data.get('atlas_version')}

Atlas 1.0 数据：
- progress_records：{len(data['progress_records'])} 条
- project_logs：{len(data['project_logs'])} 条
- mentor_advice_records：{len(data['mentor_advice_records'])} 条
- emotion_support_records：{len(data['emotion_support_records'])} 条
- chat_records：{len(data['chat_records'])} 条
- hardware_test_records：{len(data['hardware_test_records'])} 条
- camera_presence_records：{len(data['camera_presence_records'])} 条

Atlas 2.0 数据：
- projects：{len(data['projects'])} 个
- daily_tasks：{len(data['daily_tasks'])} 条
- bugs：{len(data['bugs'])} 条
- weekly_reports：{len(data['weekly_reports'])} 条

Atlas 3.0 数据：
- profile：已整合
- skills：{len(data['skills'])} 项
- project_history：{len(data['project_history'])} 个
- daily_learning_plans：{len(data['daily_learning_plans'])} 条
- emotion_records：{len(data['emotion_records'])} 条
- recommendations：{len(data['recommendations'])} 条
"""
    print("\n" + content)
    log("Atlas Final 总数据库概览", content)


def one_click_demo(data):
    p = data["profile"]
    f = decide_focus(data)
    r = decide_recommendation(data)
    content = f"""Atlas Final 1.0 + 2.0 + 3.0 Demo Overview

一、Atlas 1.0：基础研发导师能力
- 长期记忆：{len(data['progress_records'])} 条
- Project Log：{len(data['project_logs'])} 条
- 导师建议：{len(data['mentor_advice_records'])} 条
- 研发支持：{len(data['emotion_support_records'])} 条
- 硬件反馈：{len(data['hardware_test_records'])} 条
- 摄像头检测：{len(data['camera_presence_records'])} 条

二、Atlas 2.0：项目管理能力
{project_summary(data)}
- Daily Task：{len(data['daily_tasks'])} 条
- Bug：{len(data['bugs'])} 条
- Weekly Report：{len(data['weekly_reports'])} 条

三、Atlas 3.0：Eric Digital Twin
- 姓名：{p.get('name')}
- 目标：{p.get('goal')}
- 当前版本：{p.get('current_version')}
- 强项技能：{'、'.join(strong_skills(data))}
- 需要补强：{'、'.join(weak_skills(data))}
- Project History：{len(data['project_history'])} 个项目
- Learning Plan：{len(data['daily_learning_plans'])} 条
- Emotion Memory：{len(data['emotion_records'])} 条
- Mentor Recommendation：{len(data['recommendations'])} 条

四、今日主动建议
- 今日重点：{f['focus']}
- 原因：{f['reason']}

五、导师推荐
- 推荐重点：{r['focus']}
- 推荐内容：{r['recommendation']}

机器人总结：Atlas Final 已经整合 1.0 的记忆与感知、2.0 的项目管理、3.0 的 Eric Digital Twin 和导师推荐。
"""
    print("\n" + "=" * 70)
    print(content)
    print("=" * 70)
    log("Atlas Final 一键 Demo 总览", content)


def test_log():
    log("Atlas Final 日志写入测试", "这是 Atlas 1.0 + 2.0 + 3.0 最终整合版的日志写入测试。")


def intro(data):
    p = data["profile"]
    print("\n==============================")
    print("Atlas Final Main Program")
    print("Atlas 1.0 + 2.0 + 3.0 最终整合版")
    print("==============================")
    print(f"学生：{p.get('name', 'Eric')}")
    print(f"目标：{p.get('goal')}")
    print(f"当前项目：{p.get('current_project')}")
    print(f"当前版本：{p.get('current_version')}")
    print(f"总数据库：{DATA_FILE}")
    print(f"Project Log：{PROJECT_LOG_FILE}")
    print(f"Camera Log：{CAMERA_LOG_FILE}")
    print(f"Weekly Report：{WEEKLY_REPORT_FILE}")
    print("==============================")
    print("功能：1.0 记忆/硬件/摄像头 + 2.0 项目管理 + 3.0 Digital Twin/Mentor")
    print("==============================")


def main():
    global arduino
    data = migrate_data()
    arduino = connect_arduino()
    intro(data)
    log("Atlas Final 主程序启动", "atlas_final_main.py 已启动。")
    print("\n机器人开机主动提醒：")
    print("-" * 70)
    print(morning_message(data))
    print("-" * 70)

    while True:
        print("""
请选择功能：
1. 一键 Demo 总览
2. 查看总数据库概览

=== Atlas 1.0 基础研发导师 ===
3. 记录一句话长期记忆
4. 生成 Project Log
5. 根据历史记录生成导师建议
6. 研发失败时的情绪支持
7. 回忆昨天做了什么
8. 测试 Arduino / OLED / 舵机反馈
9. 摄像头检测 Eric 是否在画面里

=== Atlas 2.0 项目管理 ===
10. Project Database：查看项目总览
11. Daily Task：创建或更新今天任务
12. Daily Task：查看今天任务
13. Daily Task：晚上复盘
14. Bug Manager：新增 Bug
15. Bug Manager：查看全部 Bug / 搜索 Bug
16. Bug Manager：更新 Bug 状态
17. Weekly Report：生成本周周报
18. Weekly Report：查看最新周报

=== Atlas 3.0 Eric Digital Twin ===
19. Profile：查看 Eric 成长画像
20. Profile：机器人身份回答
21. Profile：更新 Eric Profile
22. Skill Database：查看技能数据库
23. Skill Database：下一步学习建议
24. Skill Database：更新技能分数
25. Project History：查看项目历史
26. Project History：项目迁移建议
27. Project History：搜索历史项目
28. Learning Planner：开机主动提醒
29. Learning Planner：生成今日 Learning Plan
30. Learning Planner：查看今日 Learning Plan
31. Learning Planner：解释判断逻辑
32. Learning Planner：晚上复盘
33. Emotion Memory：新增研发状态记录
34. Emotion Memory：查看最近研发状态
35. Emotion Memory：查看研发状态总结
36. Emotion Memory：机器人提醒
37. Mentor Recommendation：生成导师推荐
38. Mentor Recommendation：查看最新推荐
39. Mentor Recommendation：解释推荐逻辑

40. 测试 project_log.txt 是否能写入
41. 退出
""")
        c = input("请输入数字 1-41：").strip()
        if c == "1": one_click_demo(data)
        elif c == "2": database_overview(data)
        elif c == "3": add_progress(data)
        elif c == "4": add_project_log(data)
        elif c == "5": ask_basic_mentor(data)
        elif c == "6": basic_emotion_support(data)
        elif c == "7": remember_yesterday(data)
        elif c == "8": test_hardware(data)
        elif c == "9": camera_check(data)
        elif c == "10": show_projects(data)
        elif c == "11": create_task(data)
        elif c == "12": show_task(data)
        elif c == "13": review_task(data)
        elif c == "14": add_bug(data)
        elif c == "15": show_bugs(data)
        elif c == "16": update_bug(data)
        elif c == "17": weekly_report(data)
        elif c == "18": show_weekly(data)
        elif c == "19": show_profile(data)
        elif c == "20": profile_intro(data)
        elif c == "21": update_profile(data)
        elif c == "22": show_skills(data)
        elif c == "23": skill_advice(data)
        elif c == "24": update_skill(data)
        elif c == "25": show_history(data)
        elif c == "26": history_transfer(data)
        elif c == "27": search_history(data)
        elif c == "28": show_morning(data)
        elif c == "29": generate_plan(data)
        elif c == "30": show_today_plan(data)
        elif c == "31": learning_logic(data)
        elif c == "32": review_plan(data)
        elif c == "33": add_emotion(data)
        elif c == "34": show_emotions(data)
        elif c == "35": emotion_summary(data)
        elif c == "36": emotion_reminder(data)
        elif c == "37": mentor_recommendation(data)
        elif c == "38": show_recommendation(data)
        elif c == "39": recommendation_logic(data)
        elif c == "40": test_log()
        elif c == "41":
            send_arduino("OFF")
            log("Atlas Final 主程序退出", "atlas_final_main.py 已退出。")
            print("程序已退出。")
            break
        else:
            print("输入无效，请输入 1 到 41。")
            log("Atlas Final 无效输入", f"用户输入了无效菜单数字：{c}")

    if arduino is not None:
        arduino.close()


if __name__ == "__main__":
    main()
