# Atlas 6.0 Stage 8C Desktop Avoidance V2 — 操作手册

## 本轮目标

本轮不再验证厘米级距离控制，也不再调左右轮最终脉冲一致度。只完成四项正式验收：

1. ESP32、US-100和无线终端在电机断电时正常；
2. 左右编码器检查正常；
3. `drive`落地直行并在运行中用编码器微调PWM；
4. `avoid`能够在障碍、传感器异常和无线断线时安全停车。

完整固件：`Atlas_6_0_Stage_8C_Desktop_Avoidance_V2.ino`

本版距离状态（距离均从US-100正面量到障碍物）：

| 实测距离 | 状态 | `avoid`行为 | 普通`drive`行为 |
| ---: | --- | --- | --- |
| `≤8 cm` | `FORCE_STOP` | 立即停车/拒绝启动 | 立即停车/拒绝启动 |
| `>8–18 cm` | `CAUTION` | 停止前进，开始右转扫描；右侧不通再扫描左侧 | 停止 |
| `>18–<30 cm` | `WATCH` | 允许低速接近并持续测距 | 停止，不继续盲目前进 |
| `≥30 cm` | `CLEAR` | 允许低速前进 | 允许启动 |

为防止边界附近反复跳变，内部另有小范围迟滞：FORCE解除需`>10 cm`，CAUTION解除需`≥22 cm`，已经处于CLEAR时可保持到`28 cm`。

---

## 0. 开始前的固定规则

- 不运行`fd`、`fds`或旧`sync`测试；
- 不更改电机线、编码器线、PPR或21.4 cm轮周长；
- 上传代码时必须断开7.4 V电机电池；
- 台式电源与移动电池绝对不能同时接入L298N；
- 落地运动时使用已经通过测试的移动电池；
- 每个动作前单独输入一次`arm`；
- 看到ESP32启动横幅重新出现，就记录为“ESP32复位”并停止后续测试；
- 紧急情况直接输入`stop`，或断开电机电池插头。
- US-100只能看正前方，不能识别桌沿；落地运动优先在地面测试。若必须在桌面测试，桌沿必须有实体挡板，不能只依赖程序。

---

## 1. 上传完整固件

### 1.1 断电和摆放

1. 断开7.4 V电机电池；
2. 不使用台式电源；
3. 把小车架起，使左右轮离桌面至少2 cm；
4. 保持US-100、编码器和L298N控制线原样连接；
5. 用ESP32数据线连接电脑。

### 1.2 Arduino IDE操作

1. 打开`Atlas_6_0_Stage_8C_Desktop_Avoidance_V2.ino`；
2. 点击Arduino IDE顶部的开发板选择框；
3. 选择此前已经成功使用的`ESP32 Dev Module`；
4. 选择ESP32当前端口，通常为`COM4`；
5. 点击左上角“✓ 验证/编译”；
6. 等待底部显示编译成功；
7. 点击左上角“→ 上传”；
8. 等待显示上传成功；
9. 打开“串口监视器”；
10. 把波特率选择为`115200`；
11. 按一次ESP32的`EN/RESET`按钮；
12. 等待启动信息。

必须看到：

```text
ATLAS_6_0_STAGE_8C
build           : Desktop Avoidance V2
motors          : stopped
safety          : disarmed
distance FDS    : deferred / disabled
```

没有看到这段信息时，不连接电机电池。

---

## 2. 电机断电状态下验证US-100

7.4 V电机电池继续保持断开。

### 2.1 CLEAR

1. 把平整软纸箱放在US-100前方`35 cm`；
2. 在串口监视器输入：

```text
sensor
```

3. 按回车发送；
4. 确认显示`state : CLEAR`。

### 2.2 WATCH

1. 把纸箱移动到`24 cm`；
2. 等待约1秒；
3. 输入：

```text
sensor
```

4. 确认显示`state : WATCH`。

### 2.3 CAUTION

1. 把纸箱移动到`15 cm`；
2. 等待约1秒；
3. 输入：

```text
sensor
```

4. 确认显示`state : CAUTION`。

### 2.4 FORCE_STOP

1. 电机电池保持断开；
2. 把纸箱移动到`6 cm`；
3. 等待约1秒；
4. 输入`sensor`；
5. 确认显示`state : FORCE_STOP`。

不要用`8 cm`、`18 cm`或`30 cm`本身做验收点，以免尺子误差和传感器小波动让状态落在边界另一侧。四项都正确才继续。

### 2.5 SENSOR_INVALID_STOP

1. 断开ESP32的USB供电；
2. 拔下US-100的Echo信号线（GPIO34），不要拔错VCC和GND；
3. 重新给ESP32接USB供电；
4. 等待启动完成；
5. 输入：

```text
sensor
```

6. 确认显示`SENSOR_INVALID_STOP`；
7. 再次断开ESP32供电；
8. 把Echo线重新接回GPIO34；
9. 恢复供电并确认传感器重新显示有效距离。

---

## 3. 切换到完全无线供电

1. 关闭串口监视器；
2. 拔掉ESP32与电脑之间的数据线；
3. 用已经验证通过的USB移动电源给ESP32供电；
4. 7.4 V电机电池仍暂时断开；
5. 等待手机或电脑看到Wi-Fi热点`ATLAS_6_0`；
6. 电脑连接该热点；
7. 密码输入`Atlas6Stage7`；
8. 在保存有`atlas_stage7c_tcp_terminal.py`的文件夹打开PowerShell；
9. 输入：

```powershell
py atlas_stage7c_tcp_terminal.py
```

10. 看到`ATLAS_6_0_STAGE_8C`后输入：

```text
status
```

必须确认：

- `safety : disarmed`；
- `motors : stopped`；
- 距离有效；
- TCP客户端已连接。

---

## 4. 轮子架空编码器检查

1. 保持小车架空，左右轮离地至少2 cm；
2. US-100前方保持大于35 cm；
3. 连接7.4 V电机移动电池；
4. 等待2秒；
5. 输入：

```text
arm
```

6. 看到`[Ready]`后输入：

```text
check left
```

7. 观察左轮必须向小车前进方向旋转；
8. 结果必须为`pulse check passed`；
9. 再输入：

```text
arm
```

10. 看到`[Ready]`后输入：

```text
check right
```

11. 观察右轮必须向小车前进方向旋转；
12. 结果必须为`pulse check passed`。

任一轮方向错误、active raw少于10或other raw大于3，都停止后续测试。

---

## 5. 两次落地直行验收

### 5.1 放到地面

1. 输入`stop`；
2. 断开7.4 V电机电池；
3. 把小车放到平整、坚硬、不打滑的地面；
4. 确保电源线和其他导线不拖地；
5. 前方和两侧清空；
6. US-100前方距离必须大于35 cm；
7. 重新连接7.4 V电机电池；
8. 输入`status`，确认`sensor state : CLEAR`。

### 5.2 第一次：150 ms低风险测试

依次输入：

```text
arm
```

```text
drive 80 150
```

要求：

- 两轮都起步；
- 小车向前；
- 自动停车；
- 最终为`disarmed`；
- ESP32没有重新出现启动横幅。

### 5.3 第二次：1000 ms正式验收

等待10秒，重新把小车放正，然后依次输入：

```text
arm
```

```text
drive 80 1000
```

要求：

- 开头使用PWM100起步；
- 约150 ms后切换到PWM80附近；
- 运行中可能显示`80/81`、`81/80`等小幅修正；
- 左右编码器都持续增加；
- 肉眼没有明显持续偏转；
- 1000 ms后自动停车；
- `result : passed`；
- ESP32没有复位。

不计算厘米数，也不要求左右最终脉冲相同。

---

## 6. 确认FDS已经停用

断开7.4 V电机电池后输入：

```text
fds 5
```

必须显示：

```text
reason code     : feature_deferred
reason          : exact-distance driving is not required for Atlas 6.0
```

电机不得运动。

---

## 7. 避障测试

### 7.1 CAUTION起步转向（本轮关键测试）

1. 先输入`stop`并断开7.4 V电机电池；
2. 把小车放在地面或有实体围挡的桌面中央；
3. 把软纸箱放在US-100前方`15 cm`；
4. 确保小车右侧至少有`30 cm`空地；
5. 左侧也不要放人、手、宠物或易碎物；
6. 重新连接7.4 V电机电池；
7. 等待1秒后输入`status`，必须确认`CAUTION`；
8. 依次输入：

```text
arm
```

```text
avoid 3000
```

预期：

- 不先向纸箱前进；
- 停顿约200 ms；
- 右转约300 ms；
- 停车并重新测距；
- 新方向达到`CLEAR`（首次进入需≥30 cm）时才向前；
- 3000 ms总时限到达后自动停车并解除ARM；
- 全程不碰纸箱、ESP32不复位。

### 7.2 WATCH接近后转向

1. 断开电机电池并重新把小车放正；
2. 把软纸箱放在US-100前方`24 cm`；
3. 确保小车右侧至少有`30 cm`空地；
4. 重新连接电机电池；
5. 输入`status`，确认`WATCH`；
6. 依次输入：

```text
arm
```

```text
avoid 3000
```

预期：

- 先以低速前进约几厘米；
- 距离进入CAUTION（约18 cm）后停车；
- 右转约300 ms；
- 停车并重新测距；
- 不得进入8 cm的FORCE_STOP范围；
- 3000 ms总时限到达后自动停车并解除ARM。

### 7.3 FORCE_STOP拒绝启动

1. 断开电机电池并把纸箱放到`6 cm`；
2. 重新连接电机电池；
3. 等待`status`显示`FORCE_STOP`；
4. 输入：

```text
arm
```

```text
avoid 3000
```

预期：

- 电机完全不启动；
- 命令被拒绝；
- 最终保持`disarmed`。

### 7.4 从CLEAR接近障碍

1. 断开电机电池并重新把小车放正；
2. 把软纸箱放在正前方`35 cm`；
3. 小车右侧保持至少`30 cm`空旷；
4. 重新连接电机电池并确认初始状态为`CLEAR`；
5. 输入：

```text
arm
```

```text
avoid 3000
```

预期：

- CLEAR时向前；
- 进入WATCH后继续受控接近；
- 接近18 cm时停车并开始扫描；
- 不碰撞纸箱；
- 执行一次右侧扫描；
- 整个动作最多3000 ms；
- 最终自动停车并解除ARM。

---

## 8. 无线断线停车回归测试

1. 前方保持CLEAR；
2. 输入：

```text
arm
```

```text
drive 80 1000
```

3. 小车刚开始运动后关闭PowerShell窗口，或按`Ctrl+C`结束无线终端；
4. 小车必须在约350 ms以内停止；
5. 重新运行无线终端；
6. 输入`status`；
7. 必须显示`disarmed`；
8. 不得自动恢复移动；
9. 不得出现ESP32启动横幅。

---

## 9. 最终通过标准

全部满足以下条件即可停止测试：

- US-100能区分CLEAR、WATCH、CAUTION、FORCE_STOP和无效数据；
- 左右`check`均通过且方向正确；
- `drive 80 150`通过；
- `drive 80 1000`通过且肉眼基本直行；
- `fds 5`被拒绝且电机不动；
- `avoid 3000`能停车、转向并在总时限后停止；
- FORCE_STOP时不会启动；
- 无线断线后约350 ms内停车；
- 全程ESP32没有复位；
- 全程无导线、插头或L298N异常发热、异味。

通过后记录：

```text
Stage 7 Core Mobility: PASSED
Exact-distance FDS: DEFERRED
Stage 8C Desktop Obstacle Avoidance V2: PASSED
```

然后停止轮子一致度测试，进入Atlas 6.0计划中的下一阶段。
