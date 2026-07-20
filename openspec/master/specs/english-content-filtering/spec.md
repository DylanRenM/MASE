## ADDED Requirements

### Requirement: 严格英文字符过滤
系统 SHALL 只保留 ASCII 英文字母 `A-Z`、`a-z` 和必要的单词间空白；数字、标点、特殊字符及其他语言文字 MUST 被过滤。

#### Scenario: [P0] 混合字符输入
- **WHEN** 原文同时包含英文、数字、标点、中文和其他 Unicode 字符
- **THEN** 过滤结果只包含 ASCII 英文字母和单个空格

#### Scenario: [P0] 连续空白规范化
- **WHEN** 原文包含连续空格、制表符或换行
- **THEN** 单词间空白被规范化为单个空格
- **AND** 段落首尾不得保留空白

### Requirement: 保留段落边界
系统 SHALL 对每个原始段落独立过滤，并 SHALL 保留过滤后仍非空段落的顺序。

#### Scenario: [P0] 部分段落无英文
- **WHEN** 文档包含英文段落和过滤后为空的非英文段落
- **THEN** 空段落被移除
- **AND** 剩余英文段落顺序与原文一致

### Requirement: 无英文内容
过滤后没有任何非空英文段落时，系统 MUST 返回 `noReadableEnglish`，且 MUST NOT 启动 TTS。

#### Scenario: [P0] 全部为非英文
- **WHEN** 文档内容全部由数字、标点或其他语言字符组成
- **THEN** 系统提示未发现可朗读英文内容
- **AND** 系统保持非播放状态

### Requirement: 内容作为纯数据
过滤器 MUST 将所有输入视为数据，MUST NOT 解释或执行脚本、标记、宏或嵌入对象。

#### Scenario: [P0] 脚本文本
- **WHEN** TXT 或文档正文包含 `<script>alert("XSS")</script>`
- **THEN** 系统不得执行脚本
- **AND** 过滤结果只包含其中的英文字母与必要空白

### Requirement: 大文件过滤不阻塞 UI
对接近 20MB 上限的内容，过滤 MUST 在非主线程执行，并 MUST 以单次结果提交到会话。

#### Scenario: [P1] 大文本过滤
- **WHEN** 系统过滤接近 20MB 的混合文本
- **THEN** 主线程仍可处理 UI 事件
- **AND** 会话只收到完整成功结果或类型明确的失败
