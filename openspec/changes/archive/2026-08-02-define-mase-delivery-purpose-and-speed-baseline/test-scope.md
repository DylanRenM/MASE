# 测试范围确认单

> Source digest: `sha256:04f000b26c71d200ebb15d0739c2066c64a7144b76249e789bab8d0a65c39490`

## 测试类型

- unit
- contract
- training_visual
- full_regression

## 测试选择

- tests/test_mase_delivery_purpose.py
- tests/test_mase_training_deck.py
- tests/test_mase_state_and_rules.py

## 受保护历史测试（基线 commit:69c7b1c）

- tests/test_mase_training_deck.py
- tests/test_mase_state_and_rules.py

## 数据来源

- structured MASE evidence indexes
- versioned 2.4 training source
- protected V1 deck

## 允许差异

- 核心表面增加统一宗旨与五个结果维度
- 课件增加低置信度 71% 示例和 unknown 边界

## 副作用隔离

只读 evidence 索引，课件重建不修改 V1，不写业务数据

## 副作用预算（verified）

- file_reads: MASE 规则、文档、evidence 索引、课件源和测试
- file_writes: 批准的 MASE 规则、文档、生成 adapter、2.4 课件和测试

### 禁止与超额副作用

- Pilot 文件、数据和测试
- 受保护 V1 课件
