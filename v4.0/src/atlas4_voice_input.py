import json
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
import speech_recognition as sr


BASE_DIR = Path(__file__).resolve().parent

VOICE_INPUT_LOG_FILE = BASE_DIR / "voice_input_log.txt"
PROJECT_LOG_FILE = BASE_DIR / "project_log.txt"
VOICE_INPUT_DATA_FILE = BASE_DIR / "voice_input_data.json"


def get_now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_to_voice_log(content):
    text = (
        "\n" + "=" * 70 + "\n"
        "Atlas 4.0 Voice Input Log\n"
        f"时间：{get_now_text()}\n"
        + "=" * 70 + "\n"
        + content + "\n"
        + "=" * 70 + "\n"
    )

    with open(VOICE_INPUT_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text)

    print("\n已写入 voice_input_log.txt")
    print(f"Voice Input Log 位置：{VOICE_INPUT_LOG_FILE}")


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


def create_default_voice_data():
    return {
        "student_name": "Eric",
        "voice_input_version": "Atlas 4.0 Voice Input v1",
        "voice_records": []
    }


def load_voice_data():
    if not VOICE_INPUT_DATA_FILE.exists():
        data = create_default_voice_data()
        save_voice_data(data)
        return data

    try:
        with open(VOICE_INPUT_DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        data = create_default_voice_data()

    if "student_name" not in data:
        data["student_name"] = "Eric"

    if "voice_input_version" not in data:
        data["voice_input_version"] = "Atlas 4.0 Voice Input v1"

    if "voice_records" not in data:
        data["voice_records"] = []

    save_voice_data(data)
    return data


def save_voice_data(data):
    with open(VOICE_INPUT_DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def save_voice_record(text, language, duration_seconds, status):
    data = load_voice_data()

    record = {
        "time": get_now_text(),
        "language": language,
        "duration_seconds": duration_seconds,
        "recognized_text": text,
        "status": status
    }

    data["voice_records"].append(record)
    save_voice_data(data)

    return record


def list_audio_devices():
    print("\n当前电脑音频设备：")
    print("-" * 70)

    try:
        devices = sd.query_devices()

        for index, device in enumerate(devices):
            name = device.get("name", "Unknown")
            max_input_channels = device.get("max_input_channels", 0)
            max_output_channels = device.get("max_output_channels", 0)

            print(
                f"{index}. {name} | "
                f"输入通道：{max_input_channels} | "
                f"输出通道：{max_output_channels}"
            )

        print("-" * 70)

        content = "已成功读取电脑音频设备列表。"
        write_to_voice_log(content)
        write_to_project_log(
            "Atlas 4.0 Voice Input 音频设备检测成功",
            content
        )

    except Exception as error:
        message = f"音频设备读取失败：{error}"
        print(message)

        write_to_voice_log(message)
        write_to_project_log(
            "Atlas 4.0 Voice Input 音频设备检测失败",
            message
        )


def record_audio_to_temp_wav(duration_seconds=5, sample_rate=16000):
    print("\n准备开始录音。")
    print(f"请 Eric 对着麦克风说话，录音时长：{duration_seconds} 秒。")
    print("开始录音...")

    try:
        audio_data = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()

    except Exception as error:
        raise RuntimeError(f"录音失败：{error}")

    print("录音结束。")

    audio_data = np.asarray(audio_data)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file_path = temp_file.name
    temp_file.close()

    write_wav(temp_file_path, sample_rate, audio_data)

    return temp_file_path


def recognize_speech_from_wav(wav_path, language):
    recognizer = sr.Recognizer()

    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)

    try:
        recognized_text = recognizer.recognize_google(audio, language=language)
        return recognized_text

    except sr.UnknownValueError:
        return ""

    except sr.RequestError as error:
        raise RuntimeError(
            f"语音识别服务连接失败：{error}\n"
            "可能原因：网络不可用，或 Google Speech Recognition 暂时无法访问。"
        )


def record_and_recognize_once():
    print("\n选择识别语言：")
    print("1. English")
    print("2. 中文")
    language_choice = input("请输入 1 或 2：").strip()

    if language_choice == "2":
        language = "zh-CN"
        language_name = "中文"
    else:
        language = "en-US"
        language_name = "English"

    duration_text = input("\n录音几秒？建议 5 秒，直接回车默认 5 秒：").strip()

    if duration_text.isdigit():
        duration_seconds = int(duration_text)
    else:
        duration_seconds = 5

    if duration_seconds < 2:
        duration_seconds = 2

    if duration_seconds > 15:
        duration_seconds = 15

    try:
        wav_path = record_audio_to_temp_wav(duration_seconds=duration_seconds)
        recognized_text = recognize_speech_from_wav(wav_path, language=language)

        if recognized_text:
            status = "recognized"
            content = (
                f"识别语言：{language_name}\n"
                f"录音时长：{duration_seconds} 秒\n"
                f"识别结果：{recognized_text}"
            )

            print("\nAtlas 听到的内容：")
            print("-" * 70)
            print(recognized_text)
            print("-" * 70)

        else:
            status = "not_recognized"
            content = (
                f"识别语言：{language_name}\n"
                f"录音时长：{duration_seconds} 秒\n"
                "识别结果：没有识别到清楚语音。\n"
                "建议：靠近麦克风，说话慢一点，环境安静一点。"
            )

            print("\n没有识别到清楚语音。")
            print("建议：靠近麦克风，说话慢一点，环境安静一点。")

        save_voice_record(
            text=recognized_text,
            language=language_name,
            duration_seconds=duration_seconds,
            status=status
        )

        write_to_voice_log(content)
        write_to_project_log(
            "Atlas 4.0 Voice Input 单次语音识别",
            content
        )

    except Exception as error:
        message = f"Voice Input 运行失败：{error}"

        print("\n" + message)

        save_voice_record(
            text="",
            language=language_name,
            duration_seconds=duration_seconds,
            status="error"
        )

        write_to_voice_log(message)
        write_to_project_log(
            "Atlas 4.0 Voice Input 运行失败",
            message
        )


def continuous_voice_test():
    print("\n连续语音识别测试。")
    print("每次录音 5 秒。")
    print("输入 q 可以退出连续测试。")

    while True:
        command = input("\n按回车开始一次录音，输入 q 退出：").strip().lower()

        if command == "q":
            print("已退出连续语音识别测试。")
            break

        record_and_recognize_once()


def show_recent_voice_records():
    data = load_voice_data()
    records = data.get("voice_records", [])

    if not records:
        message = "目前还没有语音识别记录。"
        print("\n" + message)
        write_to_voice_log(message)
        return

    recent_records = records[-5:]

    lines = []

    print("\n最近 5 条语音识别记录：")
    print("-" * 70)

    for record in recent_records:
        text = (
            f"时间：{record.get('time', '')}\n"
            f"语言：{record.get('language', '')}\n"
            f"录音时长：{record.get('duration_seconds', '')} 秒\n"
            f"状态：{record.get('status', '')}\n"
            f"识别结果：{record.get('recognized_text', '')}"
        )

        print(text)
        print("-" * 70)
        lines.append(text)

    write_to_voice_log("\n\n".join(lines))
    write_to_project_log(
        "Atlas 4.0 Voice Input 查看最近语音记录",
        "\n\n".join(lines)
    )


def test_log_write():
    content = (
        "这是 Atlas 4.0 Voice Input 第二阶段的日志写入测试。\n"
        "如果你能看到这段记录，说明 voice_input_log.txt 和 project_log.txt 都可以正常写入。"
    )

    write_to_voice_log(content)
    write_to_project_log(
        "Atlas 4.0 Voice Input 日志写入测试",
        content
    )


def show_intro():
    print("\n==============================")
    print("Atlas 4.0")
    print("Stage 2: Voice Input")
    print("==============================")
    print("目标：让 Atlas 录制 Eric 的声音，并转换成文字。")
    print("当前阶段只做 Voice Input，不做语音输出、不做记忆整合。")
    print(f"Voice Input Log 文件：{VOICE_INPUT_LOG_FILE}")
    print(f"Voice Input Data 文件：{VOICE_INPUT_DATA_FILE}")
    print(f"Project Log 文件：{PROJECT_LOG_FILE}")
    print("==============================")


def main():
    show_intro()

    write_to_project_log(
        "Atlas 4.0 Voice Input 程序启动",
        "Atlas 4.0 第二阶段 Voice Input 程序已启动。"
    )

    while True:
        print("\n请选择功能：")
        print("1. 查看电脑音频设备")
        print("2. 录音一次并转换成文字")
        print("3. 连续语音识别测试")
        print("4. 查看最近语音识别记录")
        print("5. 测试 voice_input_log.txt 和 project_log.txt 写入")
        print("6. 退出")

        choice = input("请输入数字 1-6：").strip()

        if choice == "1":
            list_audio_devices()

        elif choice == "2":
            record_and_recognize_once()

        elif choice == "3":
            continuous_voice_test()

        elif choice == "4":
            show_recent_voice_records()

        elif choice == "5":
            test_log_write()

        elif choice == "6":
            write_to_project_log(
                "Atlas 4.0 Voice Input 程序退出",
                "Atlas 4.0 第二阶段 Voice Input 程序已退出。"
            )
            print("\n程序已退出。")
            break

        else:
            print("输入无效，请输入 1 到 6。")


if __name__ == "__main__":
    main()