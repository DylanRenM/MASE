## Why

现有 Lite/Standard/Strict 同时承担基础项目风险与本次变更风险，`ui_changed` 还会把纯展示改动直接提升为 P0 E2E，造成治理过重。MASE 需要独立的 Change Risk 与可升级的轻量 change 结构，让低风险改动快速到达开发验证，同时保留硬风险自动升级。

## What Changes

- 保留 Profile，新增 Change Risk L1–L4 及公共契约、核心计算、数据写入、认证、并发、跨系统、可逆性、稳定回归等维度。
- 将 UI 改动分类为 `presentation`、`interaction`、`journey`；纯展示使用 UI contract/视觉断言，关键交互和旅程才强制 P0。
- 为认证、授权、密钥、额度、迁移、不可逆写入、公共 API、核心算法、并发和持久状态机定义不可降级风险下限。
- 明确 Change Risk L1–L4 与历史代码影响等级 L1–L3 是两个独立概念。
- 新增单文件 `bugfix-lite` 工作流和 `mase fix start/promote`；风险升级时无损提升为完整 OpenSpec 结构。
- L1/L2 不生成形式化人工证据，L3 只要求一次独立综合审查，L4 按安全、恢复、发布风险保留独立决策。

## Capabilities

### New Capabilities

- `change-risk-governance`: 独立计算 Change Risk、硬触发下限与 UI 变更类别对应门禁。
- `lite-change-workflow`: 创建、校验并无损提升单文件低风险 change。

### Modified Capabilities

- `adaptive-process-profiles`: Profile 仅表达基础风险，最终门禁由 Profile、Change Risk、影响等级和硬触发共同决定。
- `risk-scoped-review-routing`: 人工评审按 Change Risk 路由，并区分自查与独立判断。
- `executable-profile-and-hard-gate-semantics`: UI 与其他硬触发采用细粒度、不可降级规则。

## Impact

- 运行时：`mase_cli/risk.py`、`mase_cli/state.py`、`mase_cli/main.py` 及新建 Lite workflow 模块。
- Schema/Profile/模板：状态 Schema、风险注册表、change 模板与升级生成逻辑。
- 文档/Agent/测试：风险分类、命令帮助、兼容迁移与人工评审规则。
- 不读取或修改 Pilot 项目。
