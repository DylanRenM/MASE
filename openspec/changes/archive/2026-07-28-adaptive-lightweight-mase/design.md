## Context

MASE 当前把四 Agent、六阶段和十步 TDD 循环应用到所有项目；规则同时复制到五个 IDE 文件，CLI 把 Python 目录结构和模板嵌入代码，change/master/验证报告维护多份状态。磨耳朵项目还证明了同一仓库同时容纳框架、Swift 产品、历史设计和培训生成物时，合规检查与上下文选择会失真。

本次改造必须保留现有用户文件和未提交改动，支持旧 v1.3 项目无损迁移，并且不改变磨耳朵产品行为。框架运行依赖保持轻量，仅使用 Python 标准库和已有 PyYAML。

## Goals / Non-Goals

**Goals:**

- 通过 Lite/Standard/Strict Profile 让门禁与风险匹配。
- 让状态、规则、版本和模板各自只有一个人工维护源。
- 让 CLI 能初始化和检查 generic、python、swift 项目。
- 让 Agent 默认读取任务所需最小上下文，并记录可量化 Token 指标。
- 让旧项目更新可预览、可备份、可回滚。

**Non-Goals:**

- 不重写 OpenSpec CLI 或模型平台的 Token 计费实现。
- 不修改磨耳朵 Swift 产品代码和自动化测试语义。
- 不在本次改造中重新制作培训 PPT/HTML 的视觉内容。
- 不强制删除历史资料；先隔离、标注和停止默认分发。

## Decisions

### D1：Profile 是策略集合，不是三条独立流水线

新增 `profiles/{lite,standard,strict}.yaml`，定义必需产物、门禁、测试节奏和评审强度。项目选择基础 Profile，单个 capability 可因文件解析、鉴权、并发、不可逆写入等风险提升一级，但不得降低 P0 E2E、API 契约或根因分析等已触发的硬门禁。

相比在 Agent 文档里复制三套流程，数据化 Profile 可由 CLI、Agent 和报告共同消费。

### D2：状态与证据分离，报告全部派生

每个 change 的 `mase-state.yaml` 是阶段、Profile、技术栈、风险和门禁证据的唯一状态源；`tasks.md` 保留工作项完成事实。`mase status` 联合读取二者并检测不一致，验证摘要和追踪矩阵从状态、Spec ID、测试标签和命令结果生成。

`openspec/master/` 不再在开发过程中通过模型做语义合并，只在 archive/release 生成只读快照。这样既保留系统全貌，也消除 change/master 双写。

### D3：CLI 使用声明式 manifest 和 stack adapter

新增 `framework-manifest.yaml` 统一版本、规则源、IDE 目标、模板、Profile 和不分发目录。CLI 不再内嵌模板。stack adapter 只描述目录与检查项：`generic` 为最低基线，`python` 和 `swift` 增加各自约束。

### D4：规则和 Skills 使用“短路由器 + references”

`project-rules.md` 保留不可违反的核心规则和路由表；IDE 文件由生成器加 source hash 产生。长 Skill 逐步拆成不超过约 100 行的分诊入口和按路径加载的 reference。任务可声明 `reads`，开发默认只加载当前 Spec、相关接口/测试和 diff。

### D5：测试按边界分级运行

实现微循环只运行相关单元/契约测试；Capability 完成运行其集成测试、评审和攻击面扫描；Build/Verify 门禁运行全量测试和 P0 E2E。Strict 或 capability 风险升级可以提高频率，但 Lite 不再每个 Scenario 全量 E2E。

### D6：迁移始终非破坏

`mase update` 先生成计划；修改前写 `.mase-backup/<timestamp>/`，只覆盖 manifest 标记为 generated 的文件。用户维护文件使用创建、追加或明确冲突，绝不静默覆盖。旧 master 与历史资料先标记 deprecated，不在无备份时删除。

### D7：仓库内容按用途隔离

框架运行时仅包含 CLI、profiles、schemas、templates、rules、agents 和 skills。历史设计进入 archive，培训进入 content/site，产品进入 examples。安装器只分发 manifest 明确列出的运行时内容，避免历史和产品文件进入 Agent 默认检索。

## Risks / Trade-offs

- [Profile 选择过轻导致漏检] → 风险触发器只能升级不能降级，P0/API 契约底线独立于 Profile。
- [迁移破坏用户自定义规则] → generated 文件携带 source hash；未知或已编辑文件产生冲突并备份。
- [一次移动大量历史文件造成链接失效] → 本次先用 manifest 排除和 deprecation 标注，物理迁移分批执行并提供链接检查。
- [状态仍与 OpenSpec tasks 不一致] → `mase status` 把不一致视为失败，阶段只能经 CLI 迁移函数改变。
- [Token 遥测不可获得平台精确值] → CLI 接受实际 input/output/cache 值，也提供上下文字符和文件数代理指标，并明确两者区别。

## Migration Plan

1. 新增 manifest、profiles、schemas 和行为测试，不改变旧命令。
2. 重构 init/check/status/doctor/metrics，旧参数保持兼容。
3. 由 manifest 生成 IDE 规则副本，验证哈希一致。
4. 更新 Agent、Skill、模板和现行文档，使其消费 Profile 与单一状态。
5. `mase update --dry-run` 显示 v1.3→v2 迁移；实际更新前创建备份。
6. 运行框架单测、CLI 集成测试、OpenSpec 校验和磨耳朵完整验证，确认产品无回归。

回滚时恢复 `.mase-backup/`，并可继续使用 v1.3 CLI；不删除旧 change/master 内容。

## Open Questions

- 精确 Token 值取决于模型平台是否提供 usage；本次先定义可注入的通用 JSONL 格式。
- 培训和历史资料最终是否拆分独立仓库，在完成 manifest 隔离后再决定。
