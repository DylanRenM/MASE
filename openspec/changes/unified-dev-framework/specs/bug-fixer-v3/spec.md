## ADDED Requirements

### Requirement: 原则 8 — 测试反哺原则
修复完成后，系统 SHALL 复盘自动化测试为何未发现该 BUG，分析测试缺口，并补充对应测试用例以防止同类问题再次漏网。

#### Scenario: 复盘测试缺口
- **WHEN** 一个 BUG 被修复并通过回归验证
- **THEN** 系统分析：该 BUG 是否可被现有自动化测试捕获？如不能，原因是什么（缺场景/缺边界值/缺覆盖率）？
- **AND** 系统列出需要新增的测试用例

#### Scenario: 补充测试用例
- **WHEN** 测试缺口被识别
- **THEN** 系统将新场景补充到对应测试套件中，确保同类问题可被自动化测试捕获

#### Scenario: 不打补丁检查清单扩展
- **WHEN** 修复完成后，开发者检查不打补丁清单
- **THEN** 检查清单包含第 6 项：「自动化测试能否在 CI 中捕获同类问题？需要补充哪些用例？」

### Requirement: 运行时调试增强模式 — Debug Server 管理
当静态分析无法定位根因时，系统 SHALL 启动本地 Debug Server 用于收集运行时日志证据。

#### Scenario: 启动 Debug Server
- **WHEN** 分诊决策树判断需要运行时调试（多轮静态分析无效 / 偶发/并发/环境问题 / 用户主动要求）
- **THEN** 系统启动 Debug Server，输出启动命令和端口号
- **AND** 系统生成 `<sessionId>.env` 环境文件供插桩代码零配置读取

#### Scenario: Debug Server API
- **WHEN** Debug Server 运行中
- **THEN** 系统提供 POST /event 端点接收日志、GET /health 健康检查、GET /logs 查询日志、DELETE /logs 清除日志

### Requirement: 运行时调试增强模式 — 假设驱动插桩
系统 SHALL 基于 G3 假设-验证格式，为每个假设设计插桩点并植入代码，通过 Debug Server 上报运行时数据。

#### Scenario: 设计插桩点
- **WHEN** G3 输出了 2-3 个假设及验证方法
- **THEN** 系统为每个假设设计 1-3 个插桩点，使用 `#region debug-point <id>` 包裹
- **AND** 插桩代码通过 HTTP POST 上报日志到 Debug Server（NDJSON 格式，含 sessionId / runId / hypothesisId / timestamp / data）

#### Scenario: 插桩代码模板
- **WHEN** 需要在 Python 代码中插入调试日志
- **THEN** 系统使用 inline one-liner 网络上报，不引入新文件，不使用 `print()` / `console.log()`

### Requirement: 运行时调试增强模式 — 证据对比验证
修复完成后，系统 SHALL 通过 pre-fix 与 post-fix 日志对比，证明问题已解决且未引入新问题。

#### Scenario: pre-fix 与 post-fix 对比
- **WHEN** 最小修复实施完成
- **THEN** 系统清除旧日志，设置 `runId=post-fix`，引导用户复现
- **AND** 系统对比 pre-fix 和 post-fix 日志，确认异常指标消失、正常指标无退化

#### Scenario: 用户确认后清理
- **WHEN** 用户确认问题已解决
- **THEN** 系统移除所有插桩代码、删除 .dbg/ 文件、停止 Debug Server、归档 debug-<sessionId>.md

### Requirement: 增强模式触发条件
分诊决策树 SHALL 在以下条件触发运行时调试增强模式：用户主动要求、多轮静态分析仍无法定位根因、问题属于偶发/并发（路径 E）/环境（路径 F）/性能（路径 D）类型。

#### Scenario: 用户主动触发
- **WHEN** 用户说「帮我调试一下」或类似表述
- **THEN** 系统进入运行时调试增强模式

#### Scenario: 静态分析失效触发
- **WHEN** 路径 A 或 B 经过 2 轮分析仍无法确认根因
- **THEN** 系统自动建议启用运行时调试增强模式

#### Scenario: 特定路径默认启用
- **WHEN** 分诊决策树匹配到路径 D（性能）、E（并发）、F（环境）
- **THEN** 运行时调试增强模式默认启用

## MODIFIED Requirements

### Requirement: 分诊决策树扩展
分诊决策树 SHALL 在原有 7 类错误分类基础上，新增「启用运行时调试」判断分支。

#### Scenario: 决策树包含调试分支
- **WHEN** Agent 4 执行 bug-fixer Skill
- **THEN** 分诊决策树包含判断：「是否已尝试静态分析但未定位？或属于路径 D/E/F？」→ 是 → 启用运行时调试增强模式
