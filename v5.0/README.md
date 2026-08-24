# Atlas 5.0 — Hardware Robot Engineering Edition

## 版本目标

把 4.0 的分散硬件反馈升级为具有二自由度头部、OLED、LED、摄像头、语音和 Safe Mode 行为状态机的桌面机器人原型。

## 主要功能

- Pan/Tilt 机械结构
- OLED/LED 状态反馈
- Python HAL
- 行为状态机
- ARM→ACTION→DISARM Safe Mode
- 中英文语音
- C950 外置摄像头
- 最终整合程序

## 真实资料状态

- 主要证据：用户提供的 `project_log.txt`。
- 源码：以保留下来的完整/累计主程序为准，来源在 `Source_Code/README.md` 中逐项说明。
- JSON：附件没有包含各版本当时的全部原始运行 JSON；`Data/evidence_summary.json` 是从日志重建的索引，不冒充原始数据库。
- TXT运行记录：`Data/project_log_excerpt.txt` 按版本保留原始日志行，未改写结果。
- 未提供的日期、角度、重量、循环次数或硬件回包均标为“未验证/待确认”。

## 文件说明

- `Development_Plan.docx`：该版本完整开发计划与验收标准。
- `Source_Code/`：Python 与可追溯的 Arduino/ESP32 源码。
- `Data/`：版本日志摘录、证据摘要 JSON、预期运行数据文件说明。
- `Engineering_Log.md`：Eric 的实际开发过程与学习记录。
- `Bug_Log.md`：问题、原因、解决方法和状态。
- `Test_Report.md`：仅根据真实日志填写的测试报告。
- `Version_Note.md`：相对上一版本的新增能力。

## 最简单运行方法

1. ESP32 需先烧录项目原来的 atlas5_body_firmware_oled_v1_success.ino；本归档未找到该原始文件。
2. 关闭 Arduino Serial Monitor。
3. 确认 Python 中 SERIAL_PORT=COM4、BAUD_RATE=115200；若设备端口变化只改端口。
4. 连接 C950 摄像头；舵机电源按原硬件方案独立供电并共地。
5. 安装依赖：python -m pip install pyserial opencv-python sounddevice scipy numpy SpeechRecognition pyttsx3。
6. 运行：python atlas5_final_voice_camera_robot.py。
7. 先通过 PING/LEDTEST/OLEDTEST，再按提示打开舵机电源。

## 安全与数据保护

- 运行前先复制整个版本文件夹作为备份。
- 不删除旧 JSON/TXT；程序迁移时先复制再运行。
- 串口监视器和 Python 不能同时占用同一个 COM 端口。
- 舵机不得长期由主控板 5V 引脚高负载供电；外接电源必须与主控板共地。
- 任何中位角都必须以实物方向为准，不能只假定 90° 就是正前方。

## 当前归档边界

本次按要求没有创建 `Process_Media/` 和 `Final_Demo/`。因此照片、视频、截图和最终 Demo 视频不在此包中。
