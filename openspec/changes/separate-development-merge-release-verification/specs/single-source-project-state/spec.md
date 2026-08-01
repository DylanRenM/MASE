## ADDED Requirements

### Requirement: 过程阶段与验证里程碑分开报告
`mase status` SHALL 同时报告人工维护的 OpenSpec phase、证据派生的 verification milestone 和独立的 release outcome，并 SHALL 给出每个后续里程碑的未满足原因。

#### Scenario: Build 阶段已可手测
- **WHEN** phase 为 build 且 development gate 全部 fresh passed
- **THEN** 状态可报告 `dev_verified`，而不会因 phase 尚未进入 verify 抹去开发验证结果
