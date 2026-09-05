# Atlas 6.0 Stage 10/11接口预设计草案

## 1. 文档状态

- 状态：DRAFT
- 是否正式实施：否
- 是否连接ESP32：否
- 是否控制电机：否
- 是否完成Stage 10：否
- 是否完成Stage 11：否

本文件只用于提前学习和设计。最终串口格式、GPIO、端口和硬件参数必须等前序实体阶段完成后确认。

## 2. 计划中的系统链路

ROS2行为命令
→ atlas_safety
→ atlas_bridge
→ USB串口
→ ESP32
→ TB6612FNG
→ 左右电机

ESP32反馈
→ USB串口
→ atlas_bridge
→ ROS2 Topic
→ atlas_safety / atlas_odometry / atlas_behavior

## 3. 候选命令类型

以下全部是草案，不是最终协议：

- ARM
- DISARM
- STOP
- FORWARD
- BACKWARD
- LEFT
- RIGHT
- HEARTBEAT
- STATUS

## 4. 必须遵守的安全优先级

1. STOP拥有最高优先级。
2. DISARM必须立即禁止移动。
3. 未ARM时不得执行运动命令。
4. 非法命令不得触发运动。
5. 缺少字段不得触发运动。
6. 数值超出范围不得触发运动。
7. 串口断开必须停车。
8. 心跳超时必须停车。
9. ROS2程序退出必须停车。
10. Python异常必须停车。
11. ESP32复位后必须保持禁止移动。
12. 安全状态恢复后必须重新ARM。

## 5. 候选反馈类型

以下全部是草案：

- READY
- ARMED
- DISARMED
- STOPPED
- HEARTBEAT_OK
- ENCODER_DATA
- DISTANCE_DATA
- SENSOR_TIMEOUT
- SERIAL_ERROR
- INVALID_COMMAND

## 6. Stage 10未来验收项目

只有前序阶段完成后才能执行：

- ROS2能够发送STOP。
- ESP32能够接收STOP。
- ESP32能够返回编码器数据。
- ESP32能够返回距离数据。
- 串口断开后机器人立即停车。
- 错误数据不能触发运动。
- 心跳超时能够触发停车。

## 7. Stage 11未来验收项目

- 安全节点拥有最终否决权。
- 未ARM时拒绝移动。
- DISARM一定停车。
- 障碍物过近时拒绝前进。
- 距离数据无效时拒绝前进。
- 通信超时时停车。
- ROS2退出时停车。
- Python异常时停车。
- ESP32上电默认禁止移动。

## 8. 当前TBD项目

以下内容当前禁止猜测：

- ESP32准确串口设备名
- 最终串口波特率
- 电机GPIO
- 编码器GPIO
- US-100 GPIO
- 急停GPIO
- 最终串口消息格式
- 校验方式
- 心跳周期
- 超时时间
- PWM范围
- 实际停车距离

## 9. 当前结论

本文件只是Stage 10和Stage 11的设计预习。

在Stage 4至Stage 8没有按照计划书完成真实测试和验收以前，不得把本草案转换成实体运动控制程序，也不得宣布Stage 10或Stage 11开始或完成。
