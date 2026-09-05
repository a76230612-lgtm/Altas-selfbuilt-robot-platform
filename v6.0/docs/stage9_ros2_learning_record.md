# Atlas 6.0 Stage 9 ROS2纯软件预学习记录

## 1. 基本信息

- 项目：Atlas 6.0 Modular Mobile Robot
- 记录人：Eric
- 日期：请填写实际日期
- 当前项目主线：Stage 4准备阶段
- 本次任务性质：Stage 9 ROS2纯软件预学习
- 是否连接ESP32：否
- 是否连接电机驱动：否
- 是否控制实体机器人：否
- ROS2版本：ROS2 Jazzy
- Ubuntu版本：Ubuntu 24.04
- 工作区：/mnt/d/桌面/Atlas/Atlas_6.0/ros2_ws
- Package：atlas_ros2_basics

## 2. 节点和Topic

### 发布节点

- 节点：command_node
- 功能：发布字符串状态命令

### 订阅节点

- 节点：display_node
- 功能：接收并显示字符串状态命令

### Topic

- Topic名称：/atlas_demo_command
- Message类型：std_msgs/msg/String

## 3. 发布内容

command_node按照程序设定发布以下字符串：

1. IDLE
2. ARMED
3. MOVING
4. STOPPED
5. DISARMED

## 4. Stage 9知识验收回答

### 问题1：哪个节点负责发送？

command_node负责发送消息。

### 问题2：哪个节点负责接收？

display_node负责接收并显示消息。

### 问题3：Topic叫什么？

Topic叫作：

/atlas_demo_command

### 问题4：Message是什么类型？

Message类型是：

std_msgs/msg/String

### 问题5：关闭其中一个节点后会发生什么？

关闭command_node以后，display_node仍然可以继续运行，但不会收到新的消息。

关闭display_node以后，command_node仍然继续发布消息，但没有display_node显示消息。

重新启动关闭的节点以后，只要ROS2环境和工作区已经正确source，通信应当恢复。

## 5. 实际测试记录

### command_node运行结果

请粘贴真实输出或概括真实现象：

待填写。

### display_node运行结果

请粘贴真实输出或概括真实现象：

待填写。

### ros2 topic echo结果

请粘贴真实输出或概括真实现象：

待填写。

## 6. 当前结论

本次已经完成Atlas 6.0 Stage 9的ROS2纯软件预学习练习。

这不代表Atlas 6.0项目主线已经正式完成Stage 9。项目主线仍需按照Stage 4、Stage 5、Stage 6、Stage 7、Stage 8的顺序完成实体测试和验收。

本次没有连接ESP32、电机驱动、电机或电池，没有进行任何实体运动测试。
