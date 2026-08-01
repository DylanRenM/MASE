# 测试范围确认单

> Source digest: `sha256:1cf08a1b084a958126d94b9cb6953a76892319b71677d8e5aaa9d93d87d53bca`

## 测试类型

- unit
- contract
- integration
- full_regression

## 测试选择

- tests/test_mase_gate_planning.py
- tests/test_mase_governance_models.py
- tests/test_release_governance.py

## 受保护历史测试（基线 commit:69c7b1c）

- tests/test_mase_gate_planning.py
- tests/test_mase_governance_models.py
- tests/test_release_governance.py

## 数据来源

- versioned repository fixtures

## 允许差异

- GatePlan 可按 development/merge/release/observe 目标延迟后续门禁

## 副作用隔离

临时目录测试且无业务数据写入

## 副作用预算（verified）

- file_reads: MASE 框架源码、Schema、配置和测试
- file_writes: 批准范围内的 MASE 框架文件

### 禁止与超额副作用

- Pilot 项目文件、数据与测试
