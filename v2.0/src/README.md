# Atlas 2.0 Source Code

## 来源原则

本目录只放入本次资料中能追溯的源码。`project_log.txt` 是运行证据，不等于源码；缺少的原始文件不会被猜测补写后冒充原件。

## 运行环境

- Python 3.10+（仅标准库）

## 建议运行顺序

1. 把 atlas2_main.py 与 Data/ 中需要沿用的数据放在同一目录。
2. 运行：python atlas2_main.py。
3. 首次运行会创建 atlas2_data.json。
4. 依次测试项目总览、Daily Task、Bug Manager、Weekly Report。
5. 退出后检查 project_log.txt 与 weekly_report.txt。

## 版本特别说明

`atlas2_main.py` 是完整合并版，首次运行会在同目录创建或迁移 `atlas2_data.json`、`project_log.txt` 和 `weekly_report.txt`。
