# 测试范围确认单

> Source digest: `sha256:80062e81f4403ea3940d676ea7bfbfce26cb7c568dd657738f6ce60c26bc999f`

## 测试类型

- unit
- contract
- integration
- full_regression

## 测试选择

- tests/test_mase_gate_planning.py
- tests/test_mase_gate_evidence.py

## 受保护历史测试（基线 commit:69c7b1c）

- tests/test_mase_gate_planning.py
- tests/test_mase_gate_evidence.py

## 数据来源

- temporary gate registries
- versioned evidence fixtures

## 允许差异

- 非法环路在执行前失败
- 完整等价时才可 subsume 或 cache hit

## 副作用隔离

evidence 写入仅在 pytest 临时目录验证

## 副作用预算（verified）

- file_reads: MASE 源码、gate 配置、Schema和测试
- file_writes: 批准的框架文件与测试临时 evidence

### 禁止与超额副作用

- Pilot 项目文件、数据与测试
