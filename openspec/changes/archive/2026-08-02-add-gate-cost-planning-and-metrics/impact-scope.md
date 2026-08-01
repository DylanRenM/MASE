# 影响范围说明书

> Source digest: `sha256:dc5be3c193f6d8f8dbde9e0c415bc27049de7a89afadc6f4148acaeb415db808`

- 影响等级：L3
- 决策：proceed
- 第一方调用方：4
- 系统边界：2

## 修改点

- mase_cli/gates.py::historical cost and efficiency metrics（external_contract）
- mase_cli/main.py::GatePlan cost output（external_contract）
- framework-manifest.yaml::MASE 2.4 distribution identity（configuration）
- training/mase-framework/mase-training-v2.4.yaml::integrated 2.4 training source（external_contract）

## 批准的文件与符号边界

- mase_cli/gates.py
- mase_cli/main.py
- pyproject.toml
- package.json
- package-lock.json
- framework-manifest.yaml
- project-rules.md
- README.md
- docs/MASE-framework.md
- docs/user-guide.md
- docs/glossary.md
- agents
- skills
- templates
- .mase/gates.yaml
- scripts/build_mase_training_deck.py
- scripts/verify_mase_training_deck.py
- scripts/analyze_pptx.py
- scripts/pptx_to_pdf.py
- scripts/run_framework_regression.py
- scripts/verify_wheel_manifest.py
- scripts/audit_repository_boundary.py
- training/mase-framework/mase-training-v2.4.yaml
- training/mase-framework/MASE框架培训讲义V2.4.pptx
- tests/test_mase_gate_planning.py
- tests/test_mase_training_deck.py
- tests/test_distribution_integrity.py
- tests/test_repository_boundary.py
- openspec/changes/add-gate-cost-planning-and-metrics

- mase_cli/gates.py:GateCostEstimate
- mase_cli/gates.py:plan_change
- mase_cli/main.py:gate plan output
- scripts/build_mase_training_deck.py:build

## 受保护不变量

- 时间预算不得跳过硬门禁
- 样本不足时不伪造 p50/p90
- V1 课件字节摘要不变
- 课件新内容融合到原有章节

## 受影响调用方

- L1 · mase_cli/main.py::gate plan output
- L2 · mase_cli/state.py::status metrics consumer
- L1 · scripts/verify_wheel_manifest.py::wheel resource validation
- L1 · scripts/build_mase_training_deck.py::structured source renderer

## 调用图差异（verified）

- 无

## 实现变更声明

### Spec 内变更

- GatePlan 历史成本与效率指标
- 超预算诊断不降低门禁
- MASE 2.4.0 一致版本与 66 页融合课件

### 附带/非 Spec 变更

- 无

## 隐性依赖通道

- serialization: discovered / controlled
- configuration_spi: discovered / controlled
- template: discovered / controlled
- generated_registration: discovered / controlled
- reflection: checked_empty / controlled
- async_callback: checked_empty / controlled

## 递归终止

- gate-cli: system_boundary（深度 1）
- installed-framework: system_boundary（深度 1）

## 诊断与剩余风险

- contract_or_semantic_change
- system_boundary_affected
- core_or_non_low_frequency
- implicit_dependency_or_uncertainty
- L3 独立综合评审仍需由非实现者确认
