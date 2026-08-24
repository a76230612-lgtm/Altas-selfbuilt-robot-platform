# Atlas 3.0 Source Code

## 来源原则

本目录只放入本次资料中能追溯的源码。`project_log.txt` 是运行证据，不等于源码；缺少的原始文件不会被猜测补写后冒充原件。

## 运行环境

- Python 3.10+（仅标准库）

## 建议运行顺序

1. 把 atlas3_main.py 放到可写目录。
2. 运行：python atlas3_main.py。
3. 首次运行检查 atlas3_data.json 是否生成。
4. 依次查看 Profile、Skills、History，并生成学习计划、情绪记录、导师推荐。
5. 退出后检查 project_log.txt。

## 版本特别说明

`atlas3_main.py` 是六阶段合并版，会创建/迁移 Profile、Skills、History、Learning Plan、Emotion 与 Recommendation 数据。
