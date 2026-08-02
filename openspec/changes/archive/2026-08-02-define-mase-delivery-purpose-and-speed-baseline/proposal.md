## Why

MASE 2.4 已经将可手测、可合并、可发布和可观察拆成不同时点，但框架尚未用一个顶层宗旨统一“效率、正确性、健壮性、可靠性与可维护性”，也没有给出一套不夸大、可复算的提速估算方法。需要把设计宗旨与速度基线固化到框架、文档和培训课件中。

## What Changes

- 将 MASE 顶层设计宗旨定义为：让 Agentic Coding 高效交付正确、健壮、优化且易于维护的代码，确保正确满足需求、软件可靠运行，并持续消除坏味道。
- 将宗旨拆成可验证的五个结果维度：高效交付、需求正确、运行健壮、质量优化、整洁可维护。
- 新增可复算的速度收益模型，分别计算“代码完成到可手测”、“候选冻结到发布就绪”、同候选冗余执行率、缓存收益和返工率。
- 基于 MASE 当前 54 条结构化自验证记录给出低置信度示例基线：按 gate 观测中位数串行代理估算，旧式提前执行全部时点约 58 秒，2.4 达到 `dev_verified` 约 17 秒，可手测等待缩短约 71%。其中 5 个 gate 仅有 2 个样本，因此正式 p50/p90 仍为 `unknown`；该数值不冒充所有项目承诺。
- 更新核心规则、README、框架文档、用户指南、设计原则、术语表、Agent 指引和 2.4 培训课件，将宗旨放在原则与六步开发主线之前，将速度估算放入度量章节。

## Capabilities

### New Capabilities

- `delivery-purpose-and-speed-baseline`: 定义 MASE 设计宗旨、可验证结果维度、速度收益公式和实测/估算边界。

### Modified Capabilities

- `current-mase-training-deck`: 2.4 课件必须在前置章节呈现顶层宗旨，并在度量章节说明可校准的速度收益模型。
- `framework-self-governance-and-training-consistency`: 核心规则、现行文档、Agent 指引和培训课件必须对设计宗旨保持一致。

## Impact

- 规则/文档：`project-rules.md`、`README.md`、`docs/MASE-framework.md`、`docs/design-principles.md`、`docs/user-guide.md`、`docs/glossary.md`。
- Agent 指引：`agents/*/SKILL.md` 及由唯一规则源再生成的 IDE adapter。
- 培训：`training/mase-framework/mase-training-v2.4.yaml` 与可编辑 `MASE框架培训讲义V2.4.pptx`。
- 验证：文档宗旨一致性、估算公式、课件内容/版式和仓库边界测试。
- 不修改 MASE 版本号，仍为 `2.4.0`；不读取或修改 Pilot。
