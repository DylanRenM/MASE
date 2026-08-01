## Why

MASE v2 已经能用 Profile、`mase-state.yaml` 和分层门禁组织 AI 软件工程，但当前 `mase check/status` 主要检查文件存在性和任务数量，无法证明状态文件符合 Schema、声明的门禁与风险匹配、或“passed”证据确实来自一次可复现执行。磨耳朵实战已经暴露出整体检查通过但个别状态 YAML 损坏、复合技术栈不符合 Schema、多个 change 状态难以汇总等问题；在将 MASE 扩展到 Pilot 这类遗留项目之前，需要先补强治理可信度和 Brownfield 采用能力。

## What Changes

- 将项目检查从“目录存在”扩展为对 `.mase.yaml`、所有活动 change、`mase-state.yaml` Schema、Profile 必需产物、风险升级和门禁证据的一致性检查。
- 引入可执行门禁证据：记录命令、退出码、执行时间、Git commit/worktree、平台、日志或制品摘要，并验证证据与当前代码状态是否过期。
- 建立受控的 Brownfield 基线，允许遗留项目登记既有失败，但要求分类、负责人、到期策略和“不新增失败”门禁，禁止用基线掩盖当前变更回归。
- 增加多 change portfolio 状态、依赖/冲突展示和可操作的错误输出；零个或多个 change、损坏 YAML、未知 stack 不再抛出 Python traceback。
- 区分产品固有属性与本次 change 的影响面，基于 UI、鉴权、密钥、不可信输入、迁移等标准化风险触发器自动升级 Capability Profile 和必需门禁。
- 扩展技术栈模型，支持一个主 stack 加若干平台/工具链，而不是在单个枚举字符串中拼接复合栈。
- **BREAKING**：状态声明中的自由格式复合 `stack`、无结构的通过证据以及与 Profile 不匹配的 gate 将不再被视为有效；迁移工具必须提供非破坏预览和兼容转换。

## Capabilities

### New Capabilities

- `executable-gate-evidence`: 定义状态 Schema、风险驱动门禁、可复现证据、过期检测和结构化检查要求。
- `brownfield-adoption`: 定义遗留失败基线、回归增量门禁、债务治理和渐进收紧要求。
- `change-portfolio-status`: 定义多 change 汇总、依赖冲突、状态终态和友好诊断要求。

### Modified Capabilities

无。

## Impact

- CLI：`mase check`、`mase status`、`mase update`，并可能新增门禁记录/验证子命令。
- 核心模型：`mase_cli/state.py`、Profile 解析、风险分类和项目检查逻辑。
- Schema/模板：`.mase.yaml`、`schemas/mase-state.schema.json`、`templates/mase-state.yaml`、Profile 配置。
- 采用项目：磨耳朵等现有 v2 项目需要通过迁移工具规范化复合 stack 和证据；Pilot 可在此能力完成后使用 Brownfield 模式迁移。
- 测试与文档：增加损坏状态、证据过期、多 change、遗留失败基线及非破坏迁移回归测试。
