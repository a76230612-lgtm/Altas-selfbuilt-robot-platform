# Atlas 5.0 Source Code

## 来源原则

本目录只放入本次资料中能追溯的源码。`project_log.txt` 是运行证据，不等于源码；缺少的原始文件不会被猜测补写后冒充原件。

## 运行环境

- Python 3.10+
- pyserial
- opencv-python
- sounddevice
- scipy
- numpy
- SpeechRecognition
- pyttsx3
- ESP32 Arduino 库（最终固件原文件缺失）

## 建议运行顺序

1. ESP32 需先烧录项目原来的 atlas5_body_firmware_oled_v1_success.ino；本归档未找到该原始文件。
2. 关闭 Arduino Serial Monitor。
3. 确认 Python 中 SERIAL_PORT=COM4、BAUD_RATE=115200；若设备端口变化只改端口。
4. 连接 C950 摄像头；舵机电源按原硬件方案独立供电并共地。
5. 安装依赖：python -m pip install pyserial opencv-python sounddevice scipy numpy SpeechRecognition pyttsx3。
6. 运行：python atlas5_final_voice_camera_robot.py。
7. 先通过 PING/LEDTEST/OLEDTEST，再按提示打开舵机电源。

## 版本特别说明

`atlas5_final_voice_camera_robot.py` 是最终稳定 Python 程序；`atlas5_stage2_mechanical_test.ino` 从原聊天记录完整恢复。最终 ESP32 OLED 固件未提供，因此另有缺口说明；不要把 Stage2 Arduino 固件烧录到最终 ESP32 后直接运行 Final Python。
