# Atlas 2.0 — Project Management Robot

## 版本目标

把 Atlas 从有记忆的导师原型升级为可以管理项目、每日任务、Bug 和周报的研发管理机器人。

## 主要功能

- Project Database
- Daily Task 创建/查看/复盘
- Bug Manager 新增/搜索/更新/统计
- Weekly Report 自动生成
- atlas2_data.json 统一数据库

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

1. 把 atlas2_main.py 与 Data/ 中需要沿用的数据放在同一目录。
2. 运行：python atlas2_main.py。
3. 首次运行会创建 atlas2_data.json。
4. 依次测试项目总览、Daily Task、Bug Manager、Weekly Report。
5. 退出后检查 project_log.txt 与 weekly_report.txt。

## 安全与数据保护

- 运行前先复制整个版本文件夹作为备份。
- 不删除旧 JSON/TXT；程序迁移时先复制再运行。
- 串口监视器和 Python 不能同时占用同一个 COM 端口。
- 舵机不得长期由主控板 5V 引脚高负载供电；外接电源必须与主控板共地。
- 任何中位角都必须以实物方向为准，不能只假定 90° 就是正前方。

## 当前归档边界

本次按要求没有创建 `Process_Media/` 和 `Final_Demo/`。因此照片、视频、截图和最终 Demo 视频不在此包中。
