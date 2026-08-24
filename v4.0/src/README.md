# Atlas 4.0 Source Code

## 来源原则

本目录只放入本次资料中能追溯的源码。`project_log.txt` 是运行证据，不等于源码；缺少的原始文件不会被猜测补写后冒充原件。

## 运行环境

- Python 3.10+
- opencv-python
- sounddevice
- scipy
- SpeechRecognition
- pyttsx3
- pyserial

## 建议运行顺序

1. 关闭 Arduino IDE 串口监视器。
2. 在 atlas4_config.json 中确认 serial_port=COM4、baud_rate=9600、camera_index=0。
3. 安装依赖：python -m pip install pyserial opencv-python sounddevice scipy SpeechRecognition pyttsx3。
4. 运行：python atlas4_full_main.py。
5. 先查看依赖状态，再逐项测试 Vision、Voice、Memory、Proactive Mentor 和 Hardware。

## 版本特别说明

`atlas4_full_main.py` 是六阶段整合主程序。原始 Arduino `.ino` 未随资料提供；`atlas4_body_firmware_reconstructed_from_log.ino` 是按照已验证的串口回包与引脚状态重建的参考固件，文件头明确标注了身份，不能当作历史原件。
