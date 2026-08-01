# 测试范围确认单

> Source digest: `sha256:c9aa45f2b59d87ebe89e055f896797ecc17e73d7b4660c2bbdee76d0c2635bb8`

## 测试类型

- unit
- contract
- integration
- full_regression

## 测试选择

- tests/test_mase_profiles.py
- tests/test_mase_lite_workflow.py
- tests/test_mase_governance_models.py

## 受保护历史测试（基线 commit:69c7b1c）

- tests/test_mase_profiles.py
- tests/test_mase_governance_models.py

## 数据来源

- temporary-directory fixtures
- versioned profile fixtures

## 允许差异

- presentation 不再强制 P0
- 硬风险会自动提升
- L1/L2 不需形式化人工证据

## 副作用隔离

Lite 写入仅在 pytest 临时目录验证

## 副作用预算（verified）

- file_reads: MASE 框架源码、Profile、Schema和测试
- file_writes: 批准的框架文件及临时目录中的 Lite 工件

### 禁止与超额副作用

- Pilot 项目文件、数据与测试
