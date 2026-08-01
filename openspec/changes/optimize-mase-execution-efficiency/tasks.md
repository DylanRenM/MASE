## 1. 上下文范围

- [x] 1.1 为上下文计划增加工作包/Capability 范围、结构化 reads 解析和 CLI 参数
  reads: mase_cli/context.py, mase_cli/main.py, tests/test_mase_context.py
- [x] 1.2 阻止宽泛目录、二进制和隐藏缓存自动展开，并加入可审计预算阻断/覆盖
  reads: mase_cli/context.py, framework-manifest.yaml, tests/test_mase_context.py
- [x] 1.3 增加上下文范围、预算、兼容模式和真实 change 回归测试
  reads: tests/test_mase_context.py, openspec/changes/add-impact-chain-analysis/mase-state.yaml

## 2. 紧凑 Evidence

- [x] 2.1 定义 evidence sidecar 与活动摘要 Schema，保持旧内嵌记录兼容
  reads: schemas/mase-state.schema.json, schemas/mase-evidence.schema.json, mase_cli/state.py
- [x] 2.2 实现原子 sidecar 写入、摘要加载和按需详情读取
  reads: mase_cli/evidence.py, mase_cli/state.py, mase_cli/main.py
- [x] 2.3 更新状态、新鲜度、retention、迁移和失败回滚测试
  reads: tests/test_mase_gate_evidence.py, tests/test_mase_gate_planning.py

## 3. GatePlan 与测试去重

- [x] 3.1 增加 selector 包含率、重复节点和跨 gate 重叠诊断
  reads: mase_cli/gates.py, schemas/mase-gates.schema.json, tests/test_mase_gate_planning.py
- [x] 3.2 默认只计划 required gate，支持 `--all` 并修正 manual 前序命令
  reads: mase_cli/gates.py, mase_cli/main.py, tests/test_mase_gate_planning.py
- [x] 3.3 为 MASE 自身登记 Capability 测试清单并收窄差异、冒烟和回滚 selector
  reads: .mase/gates.yaml, .mase/tests.yaml, mase_cli/test_selection.py
- [x] 3.4 清理 Profile 重复声明并显式处理公共契约适用性，不降低现有硬门禁
  reads: mase_cli/risk.py, profiles/strict.yaml, schemas/mase-state.schema.json, tests/test_mase_profiles.py

## 4. 规则、迁移与验证

- [x] 4.1 更新 project-rules、Agent、用户指南、Schema 和模板
  reads: project-rules.md, agents, docs/MASE-framework.md, docs/user-guide.md, templates/mase-state.yaml
- [x] 4.2 验证 update dry-run、旧项目兼容、wheel 分发和仓库边界
  reads: tests/test_mase_update.py, tests/test_distribution_integrity.py, scripts/audit_repository_boundary.py
- [x] 4.3 运行定向测试和完整框架回归，记录执行量与上下文缩减结果
  reads: scripts/run_framework_regression.py, .mase/gates.yaml, .mase/tests.yaml
