# 测试范围确认单

> Source digest: `sha256:dc5be3c193f6d8f8dbde9e0c415bc27049de7a89afadc6f4148acaeb415db808`

## 测试类型

- unit
- contract
- integration
- node
- visual
- distribution
- full_regression

## 测试选择

- tests/test_mase_gate_planning.py
- tests/test_mase_training_deck.py
- tests/test_distribution_integrity.py
- tests/test_repository_boundary.py
- tests/sandbox/sandbox.test.js

## 受保护历史测试（基线 commit:69c7b1c）

- tests/test_mase_gate_planning.py
- tests/test_mase_training_deck.py
- tests/test_distribution_integrity.py
- tests/test_repository_boundary.py

## 数据来源

- structured evidence fixtures
- versioned 2.4 deck source
- protected V1 digest

## 允许差异

- GatePlan 增加分阶段预估与效率诊断
- 当前课件和分发版本升级为 2.4.0

## 副作用隔离

Node 依赖仅临时安装并自动清理，PPT 验证不修改 V1

## 副作用预算（verified）

- file_reads: MASE 源码、evidence 索引、版本元数据、培训源和测试
- file_writes: 批准的框架文件、2.4 可编辑课件与临时构建产物
- external_calls: npm registry during isolated regression dependency installation

### 禁止与超额副作用

- Pilot 项目文件、数据与测试
- 修改受保护 V1 课件
