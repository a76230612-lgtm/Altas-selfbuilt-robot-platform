# Atlas 2.0 Version Note

## 版本定位

- 当前版本：Atlas 2.0 — Project Management Robot
- 相比基线：Atlas 1.0
- 版本目标：把 Atlas 从有记忆的导师原型升级为可以管理项目、每日任务、Bug 和周报的研发管理机器人。

## 新增内容

- 新增项目数据库
- 新增每日任务与晚间复盘
- 新增结构化 Bug 管理
- 新增自动周报
- 统一四模块和旧数据迁移

## 保留的上一版能力

- 不删除旧版本的 JSON/TXT 历史数据。
- 保留 Project Log 作为跨版本证据链。
- 复用已经验证过的代码路径，新增功能通过统一主程序进入。
- 旧版本的故障记录保留，不因新版本成功而删除。

## 代码与数据变化

- 主程序：见 `Source_Code/README.md`。
- 运行数据：程序会在源码同目录创建 JSON/TXT；预期文件清单见 `Data/runtime_files_expected.txt`。
- 本归档的 `evidence_summary.json` 是证据索引，不是原始运行数据库。

## 已知限制

- `Test_Report.md` 中的 `PARTIAL` 和 `NOT VERIFIED` 项目仍需复测。
- 当前附件未包含的原始文件不会被推测为已存在。
- 媒体与最终 Demo 按本次要求未纳入。

## 升级/回退原则

1. 升级前复制整个旧版本目录。
2. 新代码首次运行时使用数据副本。
3. 若新功能失败，回到旧主程序和旧 JSON，不直接修改唯一备份。
4. 每次修复必须同时更新 Bug Log、Test Report 与 Version Note。
