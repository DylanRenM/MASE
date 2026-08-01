# 测试范围确认单

> Source digest: `sha256:edb05581908202fe5757e5e8f2462c2479474dad98b8c40c915443513eea823c`

## 测试类型

- unit
- contract_differential
- integration
- full_chain_smoke
- rollback_verification

## 测试选择

- tests/test_mase_impact_analysis.py
- tests/test_mase_gate_planning.py
- tests/test_mase_governance_models.py
- tests/test_mase_cli_operations.py
- tests/test_mase_cli_stacks.py
- tests/test_mase_update.py
- tests/test_distribution_integrity.py
- tests/test_mase_training_deck.py

## 受保护历史测试（基线 commit:69c7b1c）

- tests/test_mase_impact_analysis.py
- tests/test_mase_training_deck.py

## 数据来源

- existing deterministic MASE framework tests
- temporary adopting-project fixtures

## 允许差异

- new mase impact CLI commands are available
- new changes begin with undecided impact classification
- analysis-stage gates precede later stages when impact analysis applies

## 副作用隔离

temporary project roots; no production or Pilot files are read or written

## 副作用预算（unverified）

- file_reads: MASE 框架源码、Schema、规则、测试和培训模板
- file_writes: 批准路径中的框架文档、Schema、测试、培训源和 V2.3 PPT

### 禁止与超额副作用

- Pilot 产品源码、测试、数据库和运行数据
