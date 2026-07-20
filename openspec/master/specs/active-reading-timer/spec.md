## ADDED Requirements

### Requirement: 定时配置范围
系统 SHALL 接受留空或 1 至 240 的整数分钟；留空表示不限时，其他值 MUST 被拒绝。

#### Scenario: [P0] 留空不限时
- **WHEN** 用户不设置时长并开始播放
- **THEN** 系统持续循环且不会因计时自动停止

#### Scenario: [P0] 接受最小值
- **WHEN** 用户设置 1 分钟
- **THEN** 系统接受配置并在播放开始时启动有效朗读时间累计

#### Scenario: [P0] 接受最大值
- **WHEN** 用户设置 240 分钟
- **THEN** 系统接受配置

#### Scenario: [P1] 拒绝非法值
- **WHEN** 用户输入 0、241、小数、负数或非数字
- **THEN** 系统显示 1 至 240 整数分钟的校验错误
- **AND** 非法值不得启动定时播放

### Requirement: 只累计实际朗读时间
计时器 MUST 只在会话确实处于 playing 时累计；paused、loading、awaitingReloadDecision 和 ready 均 MUST 冻结。

#### Scenario: [P0] 暂停冻结
- **WHEN** 定时朗读暂停 10 秒后继续
- **THEN** 这 10 秒不计入累计朗读时间

#### Scenario: [P1] 文件修改弹层冻结
- **WHEN** 播放因源文件修改提示而等待用户决定
- **THEN** 等待时间不计入累计朗读时间

### Requirement: 定时到期只触发一次
累计实际朗读时间达到 limit 时，系统 MUST 产生一次且仅一次到期事件，并 SHALL 执行与独立停止相同的重置语义。

#### Scenario: [P0] 到期自动停止
- **WHEN** 累计实际朗读时间首次达到配置 limit
- **THEN** 系统停止 TTS、清除本轮累计、cursor 归零并回到 ready
- **AND** 文档和定时配置保留

#### Scenario: [P1] 到期与段落完成竞争
- **WHEN** 定时到期和段落完成几乎同时发生
- **THEN** 系统只执行一次停止转换
- **AND** 不得启动下一轮 TTS

### Requirement: 单调时间
计时 MUST 基于单调 clock，而不是可被用户或网络调整的墙上时间。

#### Scenario: [P1] 系统时间变化
- **WHEN** 用户在播放期间调整日期或时钟
- **THEN** 有效朗读剩余时间不发生跳变
