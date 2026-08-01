## Why

即使门禁已按阶段和风险延迟，使用者仍看不到每个里程碑的预计耗时、缓存收益与冗余来源，无法判断为何等待或如何收窄范围。MASE 需要用历史证据形成成本计划，并把本轮框架优化作为 2.4.0 的一致版本能力交付。

## What Changes

- GatePlan 从历史 evidence 计算 gate 与里程碑的 p50/p90 预计耗时，区分开发、合并、发布和观察成本。
- 新增同候选冗余率、缓存命中率、失败定位时间、代码完成到可手测、候选冻结到发布认证等效率指标。
- 为 L1/L2/L3 设定默认时间预算；超限时只建议延迟发布门禁、收窄 selector、消除重复或复核风险，不跳过硬门禁。
- CLI 文本与 JSON 同时展示风险等级、分阶段预算、诊断和下一动作；无历史样本时明确标记未知。
- 将框架运行时、Schema、模板、规则、文档、分发清单和培训课件统一升级到 MASE `2.4.0`，培训新增能力融入原有相关章节。

## Capabilities

### New Capabilities

- `gate-cost-planning`: 基于历史证据的门禁耗时预测、预算诊断和阶段效率指标。

### Modified Capabilities

- `stage-aware-gate-planning`: GatePlan 输出各验证时点成本和预算状态。
- `current-mase-training-deck`: 可编辑 2.4 课件在相应章节讲解验证里程碑、Change Risk、Lite、DAG、缓存和成本指标。
- `framework-distribution-integrity`: 2.4.0 的运行时、Schema、模板、文档和课件版本一致且可分发。

## Impact

- 运行时/指标：`mase_cli/gates.py`、`mase_cli/state.py`、`mase_cli/main.py`、metrics 相关实现。
- 版本/分发：`pyproject.toml`、`package.json`、`framework-manifest.yaml`、模板和 wheel 检查。
- 培训：新增 2.4 结构化源和可编辑 PPTX，保留受保护 V1，不把新增内容堆放为脱节附录。
- 仅修改 MASE 仓库。
