## ADDED Requirements

### Requirement: 百分比与段落进度
系统 SHALL 显示 `0...100%` 总体进度及“当前英文段落/英文总段落数”。

#### Scenario: [P0] 播放中推进
- **WHEN** TTS 报告当前段落字符范围推进
- **THEN** 百分比单调增加且保持在 0 至 100 之间
- **AND** 当前段落显示为 1-based 索引

#### Scenario: [P0] 未加载文档
- **WHEN** 会话处于 idle
- **THEN** 进度显示为 `0% · 0 / 0 段`

### Requirement: 暂停保持进度
paused 状态下进度 MUST 保持在最后确认的安全字符位置。

#### Scenario: [P0] 暂停期间
- **WHEN** 用户暂停并等待
- **THEN** 百分比和段落位置均不改变

### Requirement: 停止与到期重置进度
独立停止或定时到期后，进度 MUST 重置到文档开头，同时文档总段落数 MUST 保留。

#### Scenario: [P0] 停止重置
- **WHEN** 用户在非零进度点击停止
- **THEN** 百分比变为 0
- **AND** 当前段落变为第一段且总段落数不变

### Requirement: 循环边界进度
完成最后一段并开始下一轮时，进度 SHALL 从接近 100% 重置到第一段开头，不得显示越界值。

#### Scenario: [P0] 下一轮开始
- **WHEN** 最后一个段落完成且持续循环开始新一轮
- **THEN** 百分比重置为 0 附近
- **AND** 当前段落显示为 `1 / 总段落数`

### Requirement: 进度计算确定性
相同文档和 cursor MUST 产生相同进度结果，计算 MUST NOT 依赖 TTS voice 或 UI 刷新频率。

#### Scenario: [P1] 重复计算
- **WHEN** 使用同一段落长度元数据和 cursor 重复计算
- **THEN** 返回完全相同的 fraction、current 和 total
