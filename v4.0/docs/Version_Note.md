# Atlas 4.0 Version Note

## 版本定位

- 当前版本：Atlas 4.0 — Multimodal Proactive Mentor
- 相比基线：Atlas 3.0
- 版本目标：在 3.0 长期记忆之上整合视觉、语音输入、语音输出、主动导师与 Arduino 硬件反馈，形成完整多模态链路。

## 新增内容

- 新增视觉输入
- 新增真实语音输入
- 新增本地语音输出
- 整合3.0长期记忆
- 新增主动 Morning Brief
- 新增可验证串口硬件协议

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
