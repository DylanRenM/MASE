## Why

MASE 已能按风险调度测试并复用门禁证据，但 Token 路由仍主要依赖文字约定：归档和证据日志可能被误纳入上下文，长命令输出直接进入 Agent，上下文度量还需要人工传入平台用量。Pilot 实战表明，测试去重之后，历史产物、终端噪声和过度评审已成为主要的 Agent Token 放大器。

## What Changes

- 新增可执行的 context plan，按 Profile、任务场景、显式相关文件和框架排除规则生成有界上下文包，并报告纳入/排除原因。
- 扩充默认排除范围，覆盖真实的 OpenSpec 归档目录、MASE evidence、测试报告、日志、数据和生成物。
- 新增面向 Agent 的门禁摘要：完整脱敏日志继续落盘，模型默认只接收结果、耗时、有限失败摘要和日志路径。
- 自动记录平台提供的 input/output/cache Token；没有真实用量时仅记录文件数、字符数和工具输出字符数代理。
- 将 Standard 的深度安全评审改为风险触发；Strict 独立评审默认一轮，仅在有异议、候选变化或证据失效时追加。
- 更新项目初始化/升级提示，使缺少 `.mase/gates.yaml` 的采用项目无法误以为已经获得门禁去重与候选复用能力。

## Capabilities

### New Capabilities

- `enforced-context-routing`: 生成可审计、有预算且遵守排除规则的工作包上下文计划和用量记录。
- `concise-gate-evidence`: 将完整门禁日志与面向 Agent 的有限摘要分离，避免终端噪声进入模型上下文。
- `risk-scoped-review-routing`: 根据风险触发安全/独立评审，并定义无异议时的停止条件。

### Modified Capabilities

- `stage-aware-gate-planning`: 项目缺失 canonical gate definitions 时明确降级为不可复用的兼容模式。
- `evidence-freshness-and-reuse`: Gate Runner 默认向 Agent 返回有限摘要，完整增量输出改为显式 verbose 模式。

## Impact

- 影响 `mase_cli` 的 CLI、上下文度量、Gate Runner、Profile/风险规划和项目 update/check 诊断。
- 影响 `framework-manifest.yaml`、Profile、规则、模板、Schema 与相关测试。
- 不删除完整日志，不改变安全硬门禁的风险底线，不把字符数代理冒充真实 Token。
