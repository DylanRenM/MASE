## ADDED Requirements

### Requirement: 使用系统默认英文语音播放
系统 SHALL 使用 macOS 当前可用的默认英文系统语音朗读过滤后的英文内容，且 SHALL NOT 提供音色或发音人选择。

#### Scenario: [P0] 开始播放
- **WHEN** 有效文档处于 ready 且用户点击播放
- **THEN** 系统从第一段或合法恢复位置启动系统英文 TTS
- **AND** 会话进入 playing

#### Scenario: [P1] 无英文 voice
- **WHEN** 系统不存在可用英文 voice
- **THEN** 系统显示 TTS 不可用错误
- **AND** 会话不得进入 playing

### Requirement: 持续循环播放
系统 SHALL 在最后一个英文段落完成后自动回到第一段继续播放，且 SHALL NOT 提供循环次数设置。

#### Scenario: [P0] 文件末尾循环
- **WHEN** TTS 完成最后一个英文段落
- **THEN** cursor 重置到第一段开头
- **AND** 系统继续播放且保持 playing

### Requirement: 暂停与继续位置
系统 SHALL 在暂停时保留当前段落和已确认字符边界，并 SHALL 在继续时从该安全位置恢复，不得跳过未朗读内容。

#### Scenario: [P0] 暂停后原速继续
- **WHEN** 用户在 playing 点击暂停，随后不改变速度点击继续
- **THEN** 系统从已记录位置继续朗读
- **AND** 允许最多重复最近一个未确认完成的词，但不得跳词

### Requirement: 独立停止
系统 SHALL 在 playing 或 paused 提供停止操作；停止 MUST 终止 TTS、重置 cursor 到文件开头并保留文档为 ready。

#### Scenario: [P0] 播放时停止
- **WHEN** 用户在 playing 点击停止
- **THEN** 活动 TTS 立即终止
- **AND** cursor 归零、会话回到 ready

#### Scenario: [P0] 暂停时停止
- **WHEN** 用户在 paused 点击停止
- **THEN** 暂停位置被清除
- **AND** 再次播放从第一段开头开始

### Requirement: 三档速度
系统 SHALL 提供慢、正常、快三个互斥速度，默认正常；速度只可在 idle、ready 或 paused 修改，playing 时控件 MUST 禁用。

#### Scenario: [P0] 暂停后变速继续
- **WHEN** 用户暂停、选择新速度并继续
- **THEN** 系统从安全恢复位置用新速度朗读

#### Scenario: [P1] 播放中尝试变速
- **WHEN** 会话处于 playing
- **THEN** 三个速度控件均不可用
- **AND** 当前 utterance 速度不变

### Requirement: 单一活动 TTS
系统 MUST 保证同一时刻最多一个活动 TTS 会话，重复播放操作 MUST 幂等。

#### Scenario: [P0] 快速双击播放
- **WHEN** 用户在一秒内重复触发播放
- **THEN** 系统只创建一个活动 TTS 会话
