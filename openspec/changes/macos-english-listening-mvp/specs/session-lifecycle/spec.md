## ADDED Requirements

### Requirement: 单一合法会话状态
系统 MUST 始终处于 idle、loading、ready、playing、paused 或 awaitingReloadDecision 之一，并 MUST NOT 同时表达互斥状态。

#### Scenario: [P0] 正常主流程
- **WHEN** 用户依次选择文件、播放、暂停、继续和停止
- **THEN** 状态依次合法转换为 loading、ready、playing、paused、playing、ready

### Requirement: 选择新文件重置旧会话
在 ready、playing 或 paused 选择新文件时，系统 MUST 停止旧副作用并清除旧 cursor 与累计时间；新文件成功后 SHALL 从头 ready。

#### Scenario: [P0] 暂停时换文件
- **WHEN** 文件 A 处于 paused 且用户选择有效文件 B
- **THEN** 文件 A 的 TTS、monitor、cursor 和累计时间被清除
- **AND** 文件 B 从第一段进入 ready 且不自动播放

### Requirement: 应用重启不恢复会话
MVP MUST NOT 持久化已选文件、播放位置、暂停状态或剩余时间；每次新启动 SHALL 从 idle 开始。

#### Scenario: [P1] 播放中强制关闭
- **WHEN** 应用在 playing 被终止并重新启动
- **THEN** 新会话为 idle 且没有已选文件或进度

#### Scenario: [P1] 暂停中关闭
- **WHEN** 应用在 paused 被关闭并重新启动
- **THEN** 暂停位置和计时均不恢复

### Requirement: 快速控制保持一致
所有用户事件 MUST 在单一串行域处理；快速重复或交替操作不得产生状态与系统副作用不一致。

#### Scenario: [P0] 快速交替暂停继续
- **WHEN** 用户在两秒内快速交替触发暂停和继续
- **THEN** 最终状态与最后一个合法事件一致
- **AND** 最多一个活动 TTS 和一个活动 monitor

### Requirement: 错误可恢复
外部输入和系统适配器错误 MUST 转为用户可理解的 typed error，并 MUST 停止可能不一致的副作用。

#### Scenario: [P1] 播放适配器失败
- **WHEN** TTS 在开始或恢复时返回错误
- **THEN** 系统停止 TTS、clock 和 monitor
- **AND** 系统回到包含文档的 ready 并显示错误

#### Scenario: [P1] 关闭错误提示
- **WHEN** 用户关闭一个可恢复错误提示
- **THEN** 系统回到该错误声明的 idle 或 ready 恢复状态

### Requirement: 本地隐私边界
系统 MUST NOT 将文件内容、文件路径或朗读文本发送到网络服务。

#### Scenario: [P0] 完整会话无网络依赖
- **WHEN** 用户在网络断开状态执行选择、播放、暂停、继续和停止
- **THEN** 所有核心功能仍可工作
- **AND** 文档数据仅存在于本地进程和临时测试沙箱
