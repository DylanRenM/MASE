## ADDED Requirements

### Requirement: 播放期间监控源文件
系统 MUST 在 playing 期间监控源文件的写入、扩展、属性、重命名和删除事件，并 SHALL 在变化发生后 5 秒内提示用户。

#### Scenario: [P1] 原地写入
- **WHEN** 外部程序在播放期间原地修改源文件
- **THEN** 系统在 5 秒内显示源文件变化提示

#### Scenario: [P1] 原子替换
- **WHEN** 外部程序通过临时文件原子替换源文件
- **THEN** 系统在 5 秒内显示源文件变化提示

### Requirement: 文件变化提示去重
同一待处理文件变化 MUST 最多显示一个确认提示，等待决定期间 MUST 暂停朗读和计时。

#### Scenario: [P1] 连续多次写入
- **WHEN** 一个保存操作产生多个文件系统事件
- **THEN** UI 只显示一个待处理提示
- **AND** 会话进入 awaitingReloadDecision

### Requirement: 重新加载新内容
用户选择重新加载时，系统 SHALL 停止旧 TTS，重新解析当前路径，并在成功后从新内容开头播放。

#### Scenario: [P1] 重新加载成功
- **WHEN** 用户在变化提示中选择重新加载且新文件有效
- **THEN** 新文档原子替换旧内存内容
- **AND** cursor 从头开始、会话恢复 playing

#### Scenario: [P1] 重新加载失败
- **WHEN** 用户选择重新加载但文件已损坏或删除
- **THEN** 系统显示对应读取错误
- **AND** 系统停止旧会话并进入 idle

### Requirement: 继续旧内容
用户选择继续时，系统 SHALL 使用内存中的旧内容和原 cursor 恢复播放，不得隐式混入新文件内容。

#### Scenario: [P1] 拒绝重新加载
- **WHEN** 用户在变化提示中选择继续旧内容
- **THEN** 系统从暂停 cursor 继续旧段落
- **AND** 有效朗读计时从恢复时继续累计

### Requirement: 播放前源文件可用性检查
文件处于 ready 后被移动、删除或变得不可读时，play MUST 失败并使会话回到 idle。

#### Scenario: [P1] 就绪后删除
- **WHEN** 用户选择文件进入 ready，随后外部删除该文件并点击播放
- **THEN** 系统提示文件已移动、删除或不可读
- **AND** 系统清除文档并回到 idle

### Requirement: 停止监控后无事件
会话停止、换文件或退出后，旧 monitor MUST 被取消，旧 token 的回调 MUST 被忽略。

#### Scenario: [P1] 换文件后的迟到事件
- **WHEN** 文件 A monitor 停止后产生迟到回调且文件 B 已就绪
- **THEN** 回调不得改变文件 B 的会话状态
