## Why

现有 37 页课件适合作为框架概览，但不足以独立支撑影响链、门禁计划、测试分层、证据新鲜度和发布恢复的完整培训。需要在不复制维护两套内容的前提下扩展为 60 页以上的可编辑完整课程，并确保不会进入日常 Agent 上下文。

## What Changes

- 将 MASE 培训源扩展为 66 页，按“概念—机制—案例—演练”组织；新增机制页必须插入对应章节，不形成独立的后置附录。
- 新增学习目标、档位对比、GatePlan、上下文预算、影响链实战、契约差异、浏览器分层、候选冻结、发布恢复和贯穿案例。
- 改造 PPT 构建器以支持任意课程顺序、可变页数、可复用版式、新增可编辑页面、动态页码和完整/精简轨道。
- 保留 V1 课件字节不变，完整课件继续保持 16:9、Measures 标识、中文优先和可编辑文本。
- 更新自动验证，检查 66 页、章节覆盖、文本预算、页面边界、页码、必要主题和禁用旧说法。

## Capabilities

### New Capabilities

- `multi-track-training-generation`: 从单一结构化内容源生成 66 页完整培训版，并为未来精简轨道保留同源标签能力。

### Modified Capabilities

- `current-mase-training-deck`: 当前 MASE 课件从固定 37 页概览升级为 66 页完整课程，保留 V1 资产和当前框架语义。
- `framework-self-governance-and-training-consistency`: 课件生成和验证必须随当前运行时规则、效率约束和影响链治理同步。

## Impact

- 内容：`training/mase-framework/mase-training-v2.3.yaml` 与生成的可编辑 PPTX。
- 工具：`scripts/build_mase_training_deck.py`、`scripts/verify_mase_training_deck.py`、分析/渲染脚本。
- 测试：`tests/test_mase_training_deck.py` 及全量回归。
- 分发：`framework-manifest.yaml` 和 wheel 清单保持课件资源完整；`training/` 继续默认排除于 Agent 上下文。
- 依赖：内容以 `optimize-mase-execution-efficiency` 的最终流程语义为前置，不引入 Pilot 或任何采用项目内容。
