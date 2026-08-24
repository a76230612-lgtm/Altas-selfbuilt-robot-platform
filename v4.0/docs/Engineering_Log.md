# Atlas 4.0 Engineering Log

## 基本信息

- 项目：Atlas 4.0 — Multimodal Proactive Mentor
- 记录人：Eric
- 日志时间范围：2026-07-03 至 2026-07-04
- 主要依据：`project_log.txt` 与保留源码
- 归档说明：这是按原始记录整理的版本日志；未在原记录中出现的实测结果没有补造。

## 一、今日/阶段任务与完成情况

目标：在 3.0 长期记忆之上整合视觉、语音输入、语音输出、主动导师与 Arduino 硬件反馈，形成完整多模态链路。

- **Stage 1｜Vision**：用 OpenCV 打开摄像头并进行人脸存在检测。 输出 `vision/camera 日志`；完成判断：摄像头可打开并显示检测结果
- **Stage 2｜Voice Input**：录音、保存 WAV、SpeechRecognition 转文字并写入数据。 输出 `voice_input_data.json`；完成判断：能记录识别文本或明确失败原因
- **Stage 3｜Voice Output**：用 pyttsx3 输出英文语音并记录语音信息。 输出 `voice_output_data.json`；完成判断：文本能转语音
- **Stage 4｜Memory Integration**：读取 3.0 Profile、Skills、History、Plan、Emotion 和 Recommendation。 输出 `memory_integration_data.json`；完成判断：回答能说明使用的记忆来源
- **Stage 5｜Proactive Mentor**：总结昨天、决定今日重点、检查长期未推进任务并输出 Morning Brief。 输出 `proactive_mentor_data.json`；完成判断：能生成文字与语音 Morning Brief
- **Stage 6｜Hardware Feedback**：Python 通过 9600 串口发送 PING/STATUS/HAPPY/THINKING/WARNING/ERROR/NOD/OFF。 输出 `hardware_feedback_log.txt`；完成判断：COM4 握手成功并返回预期协议
- **Stage 7｜Full Integration**：在 atlas4_full_main.py 中合并六阶段并提供依赖状态总览。 输出 `atlas4_full_data.json`；完成判断：六模块依赖显示 OK，完整菜单可运行

## 二、使用工具、材料与软件

- Python 3.10+
- opencv-python
- sounddevice
- scipy
- SpeechRecognition
- pyttsx3
- pyserial

- 编辑与运行：Cursor / Windows 终端 / Python。
- 数据记录：JSON、TXT、Markdown。
- 硬件版本涉及 Arduino/ESP32、USB串口、摄像头、OLED、LED、舵机；准确型号以实物为准。

## 三、过程记录

1. Stage 1：Vision。用 OpenCV 打开摄像头并进行人脸存在检测。
2. Stage 2：Voice Input。录音、保存 WAV、SpeechRecognition 转文字并写入数据。
3. Stage 3：Voice Output。用 pyttsx3 输出英文语音并记录语音信息。
4. Stage 4：Memory Integration。读取 3.0 Profile、Skills、History、Plan、Emotion 和 Recommendation。
5. Stage 5：Proactive Mentor。总结昨天、决定今日重点、检查长期未推进任务并输出 Morning Brief。
6. Stage 6：Hardware Feedback。Python 通过 9600 串口发送 PING/STATUS/HAPPY/THINKING/WARNING/ERROR/NOD/OFF。
7. Stage 7：Full Integration。在 atlas4_full_main.py 中合并六阶段并提供依赖状态总览。

原始逐次运行记录保存在 `Data/project_log_excerpt.txt`，这里不重复粘贴全部终端输出。

## 四、遇到的问题与现象

- A4-B01：COM4/COM6 出现 FileNotFoundError，系统找不到端口。（状态：已解决）
- A4-B02：COM4/COM6 出现 PermissionError(13) 拒绝访问。（状态：已解决）
- A4-B03：单模块可运行但完整链路需要统一配置和数据来源。（状态：已解决）

## 五、分析原因与解决措施

### A4-B01

- 原因：配置端口与设备管理器当前端口不一致，或设备未连接。
- 措施：扫描串口并将配置改为实际 COM4。
- 验证：日志检测到 USB-SERIAL CH340 (COM4)。

### A4-B02

- 原因：Arduino 串口监视器、另一个 Python/Cursor 终端占用端口。
- 措施：关闭占用程序，拔插设备后重新连接。
- 验证：18:30:28 COM4 连接成功并完成 PING/PONG。

### A4-B03

- 原因：六阶段独立开发。
- 措施：建立 atlas4_full_main.py、atlas4_config.json 和 atlas4_full_data.json。
- 验证：状态总览显示四类依赖 OK，记忆来源为 atlas_unified_data.json。

## 六、实验/测试结果

| 编号 | 测试项 | 结果 | 原始证据 |
|---|---|---|---|
| T4-01 | 依赖检查 | PASS | 2026-07-04 状态总览：OpenCV、Voice Input、pyttsx3、pyserial 均 OK。 |
| T4-02 | Vision | PASS | 日志包含 Atlas 4.0 Vision 启动与阶段记录。 |
| T4-03 | Voice Input | PASS | 日志包含录音/识别阶段运行记录。 |
| T4-04 | Voice Output | PASS | Morning Brief 标记 spoken，语音文本被记录。 |
| T4-05 | Memory + Proactive Mentor | PASS | Morning Brief 引用 atlas_unified_data.json、昨天计划和情绪记录。 |
| T4-06 | Arduino 握手 | PASS | COM4，9600；PING 返回 PONG/OK:PING。 |
| T4-07 | 硬件协议 | PASS | STATUS/HAPPY/THINKING/WARNING/ERROR/NOD/OFF 均返回预期 OK。 |
| T4-08 | 长时间稳定性 | NOT VERIFIED | project_log.txt 未提供连续运行时长和循环次数。 |

## 七、遗留未解决问题

- 所有标为 `NOT VERIFIED` 或 `PARTIAL` 的测试仍需使用原硬件复测。
- 如果原始 JSON、Arduino/ESP32 固件或媒体证据后来找到，应放入对应目录并在 `Version_Note.md` 记录补档日期。
- 不应把本归档中的证据摘要 JSON 当成当时程序自动产生的原始数据库。

## 八、下一步计划

- 保留当前版本为只读历史基线。
- 运行前复制数据文件，避免新测试覆盖历史。
- 按 `Test_Report.md` 中未验证项目逐项补证。
- 学习总结：分阶段验证多模态依赖; 用配置文件管理串口与摄像头; 识别端口不存在与端口占用的差别; 建立语音—记忆—反馈的完整链路。
