# Atlas 1.0 Source Code

## 来源原则

本目录只放入本次资料中能追溯的源码。`project_log.txt` 是运行证据，不等于源码；缺少的原始文件不会被猜测补写后冒充原件。

## 运行环境

- Python 3.10+
- 可选：pyserial
- 可选：opencv-python

## 建议运行顺序

1. 在 Cursor 中打开 Source_Code/atlas_final_main_cumulative_1_to_3.py。
2. 确认同目录允许生成 JSON/TXT 文件。
3. 如只测试软件功能，可不连接 Arduino 与摄像头。
4. 运行：python atlas_final_main_cumulative_1_to_3.py。
5. 从菜单测试 Project Log、导师建议、情绪支持；硬件和摄像头按实际设备选择。

## 版本特别说明

独立的 `atlas_full_main.py` 未出现在附件中。本目录保存的累计主程序包含 1.0 的日志、导师建议、情绪支持、Arduino 与摄像头实现，同时也包含2.0和3.0功能；请通过菜单选择1.0相关功能。原始 Arduino 固件未提供。
