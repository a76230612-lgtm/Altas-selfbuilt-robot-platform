import json
from datetime import datetime
from pathlib import Path

import pyttsx3


BASE_DIR = Path(__file__).resolve().parent

VOICE_OUTPUT_LOG_FILE = BASE_DIR / "voice_output_log.txt"
VOICE_OUTPUT_DATA_FILE = BASE_DIR / "voice_output_data.json"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"


def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_to_voice_output_log(content):
    text = (
        "\n" + "=" * 70 + "\n"
        "Atlas 4.0 Voice Output Log\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(VOICE_OUTPUT_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 voice_output_log.txt")
    print(f"Voice Output Log 位置：{VOICE_OUTPUT_LOG_FILE}")


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
    print(f"Project Log 位置：{PROJECT_LOG_FILE}")


def create_default_voice_output_data():
    return {
        "student_name": "Eric",
        "voice_output_version": "Atlas 4.0 Voice Output v1",
        "voice_output_records": []
    }


def load_voice_output_data():
    if not VOICE_OUTPUT_DATA_FILE.exists():
        data = create_default_voice_output_data()
        save_voice_output_data(data)
        return data

    try:
        with open(VOICE_OUTPUT_DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        data = create_default_voice_output_data()

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "voice_output_version" not in data:
        data["voice_output_version"] = "Atlas 4.0 Voice Output v1"

    if "voice_output_records" not in data:
        data["voice_output_records"] = []

    save_voice_output_data(data)
    return data


def save_voice_output_data(data):
    with open(VOICE_OUTPUT_DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def save_voice_output_record(text, voice_name, rate, volume, status):
    data = load_voice_output_data()

    record = {
        "time": get_now_text(),
        "text": text,
        "voice_name": voice_name,
        "rate": rate,
        "volume": volume,
        "status": status
    }

    data["voice_output_records"].append(record)
    save_voice_output_data(data)

    return record


def create_tts_engine():
    try:
        engine = pyttsx3.init()
        return engine
    except Exception as error:
        raise RuntimeError(f"pyttsx3 初始化失败：{error}")


def list_voices():
    print("\n正在读取电脑可用语音列表...")

    try:
        engine = create_tts_engine()
        voices = engine.getProperty("voices")

        print("\n电脑可用语音：")
        print("-" * 70)

        if not voices:
            print("没有读取到语音。")
            return

        lines = []

        for index, voice in enumerate(voices):
            voice_name = getattr(voice, "name", "Unknown")
            voice_id = getattr(voice, "id", "Unknown")
            languages = getattr(voice, "languages", [])

            text = (
                f"{index}. 语音名称：{voice_name}\n"
                f"   语音 ID：{voice_id}\n"
                f"   languages：{languages}"
            )

            print(text)
            print("-" * 70)
            lines.append(text)

        content = "已成功读取电脑可用语音列表：\n\n" + "\n\n".join(lines)

        write_to_voice_output_log(content)
        write_to_project_log(
            "Atlas 4.0 Voice Output 查看语音列表",
            content
        )

    except Exception as error:
        message = f"读取语音列表失败：{error}"
        print("\n" + message)

        write_to_voice_output_log(message)
        write_to_project_log(
            "Atlas 4.0 Voice Output 读取语音列表失败",
            message
        )


def speak_text(text, rate=165, volume=1.0, voice_index=None):
    if not text:
        text = "Hello Eric. This is Atlas."

    try:
        engine = create_tts_engine()

        voices = engine.getProperty("voices")
        selected_voice_name = "default"

        if voice_index is not None and voices:
            if 0 <= voice_index < len(voices):
                selected_voice = voices[voice_index]
                engine.setProperty("voice", selected_voice.id)
                selected_voice_name = getattr(selected_voice, "name", "selected_voice")
            else:
                selected_voice_name = "default"

        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)

        print("\nAtlas 正在说：")
        print("-" * 70)
        print(text)
        print("-" * 70)

        engine.say(text)
        engine.runAndWait()

        content = (
            f"语音输出成功。\n"
            f"文本：{text}\n"
            f"语音：{selected_voice_name}\n"
            f"语速：{rate}\n"
            f"音量：{volume}"
        )

        save_voice_output_record(
            text=text,
            voice_name=selected_voice_name,
            rate=rate,
            volume=volume,
            status="spoken"
        )

        write_to_voice_output_log(content)
        write_to_project_log(
            "Atlas 4.0 Voice Output 语音输出成功",
            content
        )

    except Exception as error:
        message = f"语音输出失败：{error}"
        print("\n" + message)

        save_voice_output_record(
            text=text,
            voice_name="unknown",
            rate=rate,
            volume=volume,
            status="error"
        )

        write_to_voice_output_log(message)
        write_to_project_log(
            "Atlas 4.0 Voice Output 语音输出失败",
            message
        )


def test_basic_speech():
    text = "Hello Eric. I am Atlas. I can speak now."
    speak_text(text)


def test_chinese_speech():
    text = "你好 Eric，我是 Atlas。现在我已经可以说话了。"
    speak_text(text, rate=150)


def custom_speech():
    print("\n自定义语音输出。")
    text = input("请输入想让 Atlas 说的话：").strip()

    if not text:
        text = "Hello Eric. This is Atlas."

    rate_text = input("语速，建议 150 到 180，直接回车默认 165：").strip()

    if rate_text.isdigit():
        rate = int(rate_text)
    else:
        rate = 165

    if rate < 80:
        rate = 80

    if rate > 260:
        rate = 260

    volume_text = input("音量 0.0 到 1.0，直接回车默认 1.0：").strip()

    try:
        volume = float(volume_text) if volume_text else 1.0
    except Exception:
        volume = 1.0

    if volume < 0:
        volume = 0

    if volume > 1:
        volume = 1

    voice_index_text = input("语音编号，直接回车使用默认语音：").strip()

    if voice_index_text.isdigit():
        voice_index = int(voice_index_text)
    else:
        voice_index = None

    speak_text(
        text=text,
        rate=rate,
        volume=volume,
        voice_index=voice_index
    )


def atlas_greeting():
    text = (
        "Hello Eric. I am Atlas. "
        "I can see you, hear you, and now I can speak to you. "
        "Today, I will help you continue your AI mentor robot project."
    )

    speak_text(text, rate=160)


def atlas_task_reminder():
    text = (
        "Eric, here is your task reminder. "
        "Do not add too many new features at once. "
        "Test one function, record the result, and then continue."
    )

    speak_text(text, rate=160)


def atlas_debug_reminder():
    text = (
        "Eric, if you have been debugging for a long time, "
        "take a short break first. "
        "Then come back and test only one small problem."
    )

    speak_text(text, rate=155)


def show_recent_voice_output_records():
    data = load_voice_output_data()
    records = data.get("voice_output_records", [])

    if not records:
        message = "目前还没有 Voice Output 记录。"
        print("\n" + message)
        write_to_voice_output_log(message)
        return

    recent_records = records[-5:]
    lines = []

    print("\n最近 5 条 Voice Output 记录：")
    print("-" * 70)

    for record in recent_records:
        text = (
            f"时间：{record.get('time', '')}\n"
            f"文本：{record.get('text', '')}\n"
            f"语音：{record.get('voice_name', '')}\n"
            f"语速：{record.get('rate', '')}\n"
            f"音量：{record.get('volume', '')}\n"
            f"状态：{record.get('status', '')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    content = "\n\n".join(lines)

    write_to_voice_output_log(content)
    write_to_project_log(
        "Atlas 4.0 Voice Output 查看最近语音输出记录",
        content
    )


def test_log_write():
    content = (
        "这是 Atlas 4.0 Voice Output 第三阶段的日志写入测试。\n"
        "如果你能看到这段记录，说明 voice_output_log.txt 和 project_log.txt 都可以正常写入。"
    )

    write_to_voice_output_log(content)
    write_to_project_log(
        "Atlas 4.0 Voice Output 日志写入测试",
        content
    )


def show_intro():
    print("\n==============================")
    print("Atlas 4.0")
    print("Stage 3: Voice Output")
    print("==============================")
    print("目标：让 Atlas 把文字回复转换成语音。")
    print("当前阶段只做 Voice Output，不做语音输入整合、不做记忆整合。")
    print(f"Voice Output Log 文件：{VOICE_OUTPUT_LOG_FILE}")
    print(f"Voice Output Data 文件：{VOICE_OUTPUT_DATA_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")


def main():
    show_intro()

    write_to_project_log(
        "Atlas 4.0 Voice Output 程序启动",
        "Atlas 4.0 第三阶段 Voice Output 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 查看电脑可用语音列表")
        print("2. 测试英文语音输出")
        print("3. 测试中文语音输出")
        print("4. 自定义让 Atlas 说一句话")
        print("5. Atlas 问候语 Greeting")
        print("6. Atlas 任务提醒 Task Reminder")
        print("7. Atlas Debug 提醒")
        print("8. 查看最近 Voice Output 记录")
        print("9. 测试 voice_output_log.txt 和 project_log.txt 写入")
        print("10. 退出")

        choice = input("请输入数字 1-10：").strip()

        if choice == "1":
            list_voices()

        elif choice == "2":
            test_basic_speech()

        elif choice == "3":
            test_chinese_speech()

        elif choice == "4":
            custom_speech()

        elif choice == "5":
            atlas_greeting()

        elif choice == "6":
            atlas_task_reminder()

        elif choice == "7":
            atlas_debug_reminder()

        elif choice == "8":
            show_recent_voice_output_records()

        elif choice == "9":
            test_log_write()

        elif choice == "10":
            write_to_project_log(
                "Atlas 4.0 Voice Output 程序退出",
                "Atlas 4.0 第三阶段 Voice Output 程序已退出。"
            )

            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 10。")


if __name__ == "__main__":
    main()