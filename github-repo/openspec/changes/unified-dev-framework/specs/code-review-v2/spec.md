## ADDED Requirements

### Requirement: Spec 合规检查
代码评审 SHALL 对照 `openspec/changes/{change-name}/specs/{capability}/spec.md` 逐条核对实现是否满足规格要求。

#### Scenario: 检查 spec 覆盖率
- **WHEN** 执行代码评审且 `openspec/changes/{change-name}/specs/` 目录存在
- **THEN** 系统读取每个 capability 的 spec.md，提取所有 ADDED Requirements 和 Scenario
- **AND** 系统逐条检查：Scenario 的 Given/When/Then 在实现中是否有对应行为

#### Scenario: 标注 spec 偏差
- **WHEN** 实现行为与 spec 描述不一致
- **THEN** 系统在审查报告中标注：`SPEC_GAP|[capability]|[requirement]|[scenario]|[status: deviated]|[偏差说明]`

#### Scenario: 标注 spec 缺失
- **WHEN** spec 中的 Scenario 在实现中无对应代码
- **THEN** 系统在审查报告中标注：`SPEC_GAP|[capability]|[requirement]|[scenario]|[status: missing]|[说明]`

#### Scenario: 标注 spec 实现
- **WHEN** spec 中的 Scenario 在实现中有对应代码且行为一致
- **THEN** 系统在审查报告中标注：`SPEC_GAP|[capability]|[requirement]|[scenario]|[status: covered]`

### Requirement: 代码规约检查 — 命名规范
代码评审 SHALL 检查文件名、变量名、函数名、类名是否符合项目约定的命名规范。

#### Scenario: 检查文件命名
- **WHEN** 审查 Python 项目
- **THEN** 系统检查 Python 文件是否使用 snake_case 命名（如 `book_parser.py`）
- **AND** 系统检查测试文件是否以 `test_` 前缀命名

#### Scenario: 检查变量和函数命名
- **WHEN** 审查代码
- **THEN** 系统检查变量名和函数名是否使用 snake_case（Python）或 camelCase（JS/TS）
- **AND** 系统检查类名是否使用 PascalCase

### Requirement: 代码规约检查 — 错误处理
代码评审 SHALL 检查异常处理是否规范：无裸 except、异常类型具体、错误信息包含上下文。

#### Scenario: 检查裸 except
- **WHEN** 审查 Python 代码
- **THEN** 系统 Grep `except\s*:` 模式，检查是否有不合理使用
- **AND** 系统标注 `CONVENTION|[filepath]|[line]|[裸except]|[severity: medium]|[建议指定异常类型]`

#### Scenario: 检查异常信息
- **WHEN** 审查异常处理代码
- **THEN** 系统检查异常信息是否包含足够上下文（如变量值、操作描述）

### Requirement: 代码规约检查 — 日志规范
代码评审 SHALL 检查日志级别使用是否正确、格式是否统一、是否输出敏感信息。

#### Scenario: 检查敏感信息泄露
- **WHEN** 审查日志输出代码
- **THEN** 系统检查日志中是否有密码、token、API key 等敏感信息明文输出

#### Scenario: 检查日志级别
- **WHEN** 审查日志语句
- **THEN** 系统检查 ERROR 级别是否用于可恢复异常、WARN 是否用于降级场景、INFO 是否用于关键业务流程节点

### Requirement: 代码规约检查 — 导入规范
代码评审 SHALL 检查 import 顺序（标准库 → 第三方 → 本地）、是否有未使用的 import、是否存在循环依赖。

#### Scenario: 检查 import 顺序
- **WHEN** 审查 Python 文件
- **THEN** 系统检查 import 排列顺序是否为：标准库 → 第三方库 → 本地模块，各组间有空行

#### Scenario: 检查未使用 import
- **WHEN** 审查代码
- **THEN** 系统 Grep import 语句，检查导入的模块/函数/类是否在代码中实际使用

### Requirement: 函数复杂度检查
代码评审 SHALL 检查函数长度是否超过 50 行、圈复杂度是否超过 10。

#### Scenario: 检查函数长度
- **WHEN** 审查代码
- **THEN** 系统检查是否有函数超过 50 行，如有则标注建议拆分

#### Scenario: 检查圈复杂度
- **WHEN** 代码逻辑存在多层嵌套 if/for/while
- **THEN** 系统估算圈复杂度，超过 10 时标注建议重构

## MODIFIED Requirements

### Requirement: 审查分组扩展
审查分组从现有 5 组扩展为 7 组，新增「第 6 组：spec 合规检查」和「第 7 组：代码规约检查」。

#### Scenario: 审查编排包含新分组
- **WHEN** 执行代码评审
- **THEN** 审查清单包含 7 组：
  1. 入口/路由/中间件
  2. 业务核心逻辑
  3. 外部集成
  4. 前端 UI
  5. 数据存储/配置文件
  6. spec 合规检查（新增）
  7. 代码规约检查（新增）

### Requirement: 多轮迭代角度扩展
多轮迭代的 R1 审查角度从「功能完整性」扩展为「功能完整性 + spec 合规性 + 代码规约」。

#### Scenario: R1 审查包含新维度
- **WHEN** 代码评审进入第 1 轮
- **THEN** R1 审查覆盖：功能完整性（对照 spec 逐条验证功能实现）、spec 合规性（实现与 spec 描述一致）、代码规约（命名/错误处理/日志/导入/复杂度）

### Requirement: 子代理审查 Prompt 更新
子代理审查的通用 Prompt 和安全审查 Prompt SHALL 包含新增的 spec 合规和代码规约检查项。

#### Scenario: 通用 Prompt 包含新维度
- **WHEN** 生成子代理审查 Prompt
- **THEN** Prompt 包含检查项：spec 合规（对照 spec.md 逐 Scenario 核对）、代码规约（命名/错误处理/日志/导入/复杂度）

### Requirement: 严重度定义扩展
严重度定义 SHALL 新增 spec 偏差和规约违规的分类。

#### Scenario: Spec 偏差严重度
- **WHEN** spec 中的 Scenario 在实现中缺失或偏差
- **THEN** 缺失标记为 severity: high，偏差标记为 severity: medium
