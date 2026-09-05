# 06 — Atlas 6.0串口协议草案

## 状态

- 当前版本：Draft 0.1。
- Stage 2只建立协议表，不用于控制实体运动。
- 最终格式必须在读取Atlas 5.0原协议、确认ESP32型号和ROS2桥设计后锁定。
- 锁定后ESP32和ROS2两端必须同步修改，不允许单边变更。

## 基本约定草案

- 文本编码：UTF-8/ASCII兼容内容。
- 每条消息一行，以换行结束。
- 字段用英文逗号分隔。
- 命令与状态使用大写英文。
- 未知消息、字段数量错误或数值越界不得触发运动。

## ROS2到ESP32命令草案

| 消息 | 示例 | 预期作用 | Stage 2状态 |
|---|---|---|---|
| ARM | `CMD,ARM` | 允许进入待运动状态 | 未实现 |
| DISARM | `CMD,DISARM` | 禁止运动并停车 | 未实现 |
| STOP | `CMD,STOP` | 最高优先级停车 | 未实现 |
| FORWARD | `CMD,FORWARD,80` | 以受限PWM前进 | 未实现 |
| BACKWARD | `CMD,BACKWARD,80` | 以受限PWM后退 | 未实现 |
| LEFT | `CMD,LEFT,60` | 左转 | 未实现 |
| RIGHT | `CMD,RIGHT,60` | 右转 | 未实现 |
| HEARTBEAT | `CMD,HEARTBEAT` | 维持通信有效 | 未实现 |

## ESP32到ROS2数据草案

| 消息 | 示例 | 含义 | Stage 2状态 |
|---|---|---|---|
| READY | `STATUS,READY` | ESP32已启动且默认停车 | 占位固件仅打印说明，不实现正式协议 |
| ARMED | `STATUS,ARMED` | 已允许接收运动命令 | 未实现 |
| MOVING | `STATUS,MOVING` | 正在运动 | 未实现 |
| ENCODER | `DATA,ENCODER,1234,1228` | 左右编码器累计计数 | 未实现 |
| DISTANCE | `DATA,DISTANCE,38.5` | 距离厘米 | 未实现 |
| ERROR | `ERROR,SENSOR_TIMEOUT` | 传感器超时 | 未实现 |

## 必须后续确认

- 波特率。
- 最大行长度。
- PWM允许范围。
- 心跳与命令超时时间。
- 数值单位和小数位。
- 错误代码清单。
- 是否加入序号、时间戳或校验字段。

