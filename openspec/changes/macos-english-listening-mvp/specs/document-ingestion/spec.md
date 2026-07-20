## ADDED Requirements

### Requirement: 支持的本地文档
系统 SHALL 接受不超过 20MB 的常规 `.txt`、`.docx` 和可直接提取文本的 `.pdf` 文件，并 SHALL 拒绝 `.doc` 及其他格式。

#### Scenario: [P0] 加载有效 TXT
- **WHEN** 用户选择一个 20MB 以内且可读的 UTF-8 TXT
- **THEN** 系统解析文本并进入文件就绪状态
- **AND** 系统显示文件名且不自动播放

#### Scenario: [P0] 加载有效 DOCX
- **WHEN** 用户选择一个 20MB 以内且包含正文文本的有效 DOCX
- **THEN** 系统提取正文段落并进入文件就绪状态

#### Scenario: [P0] 加载文本型 PDF
- **WHEN** 用户选择一个 20MB 以内且页面包含可提取文本的 PDF
- **THEN** 系统按页面顺序提取文本并进入文件就绪状态

#### Scenario: [P1] 拒绝旧版 DOC
- **WHEN** 用户选择扩展名为 `.doc` 的文件
- **THEN** 系统显示不支持格式错误
- **AND** 系统不得记录该文件或进入播放状态

### Requirement: 文件策略校验
系统 MUST 在读取正文前校验文件是可读常规文件、扩展名受支持且大小不超过 20MB。

#### Scenario: [P1] 接受大小边界
- **WHEN** 用户选择大小恰好为 20MB 的有效受支持文件
- **THEN** 系统接受该文件并继续解析

#### Scenario: [P1] 拒绝超限文件
- **WHEN** 用户选择大小超过 20MB 的文件
- **THEN** 系统显示文件过大错误
- **AND** 系统不得读取文件正文

#### Scenario: [P1] 文件不可读或损坏
- **WHEN** 用户选择不存在、不可读或结构损坏的受支持文件
- **THEN** 系统返回类型明确的读取错误
- **AND** 系统保持可恢复的 idle 或原有 ready 状态

### Requirement: 扫描 PDF 与空内容处理
系统 SHALL 拒绝没有可直接提取文本的扫描 PDF，并 MUST NOT 执行 OCR。

#### Scenario: [P1] 扫描 PDF
- **WHEN** 用户选择所有页面均无可提取文本的 PDF
- **THEN** 系统提示不支持扫描件或 OCR
- **AND** 系统不得进入 ready 或 playing

#### Scenario: [P1] 空文件
- **WHEN** 用户选择零字节文件或解析结果没有文本
- **THEN** 系统提示文件为空或无可读内容

### Requirement: 原子加载
文档加载 MUST 原子成功或失败，系统 MUST NOT 向会话发布半解析文档。

#### Scenario: [P1] 解析中失败
- **WHEN** 文档解析在任意中间步骤失败
- **THEN** 新文档不得发布到当前会话
- **AND** 先前文档会话保持已清除，系统回到 idle
- **AND** 临时资源必须释放
