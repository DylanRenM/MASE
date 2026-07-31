# 测试范围确认单

> Source digest: `sha256:2ab76a85604cdfb789a1012cd38e10ce083fd373a793dbe1bf16e447e1b2a321`

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

## 数据来源

- existing deterministic MASE framework tests
- temporary adopting-project fixtures

## 允许差异

- new mase impact CLI commands are available
- new changes begin with undecided impact classification
- analysis-stage gates precede later stages when impact analysis applies

## 副作用隔离

temporary project roots; no production or Pilot files are read or written
