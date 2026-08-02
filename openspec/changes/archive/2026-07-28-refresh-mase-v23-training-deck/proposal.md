## Why

现有 MASE 培训讲义仍以 v1.x 的固定六阶段、统一重过程和过期命令为主线，与当前 v2.3 的风险自适应 Profile、Capability 局部升级、Gate Runner、候选冻结、上下文路由及属性测试能力明显不一致。继续使用会让学员形成错误流程认知，因此需要在保留旧版的前提下生成一份可验证、可维护的最新版 PPT。

## What Changes

- 新增 `MASE框架培训讲义V2.3.pptx`，直接沿用 V1 的 16:9 页面模板、37 页章节槽位和“理念 → Agent → 状态过程 → 工具 → 上手”教学骨架，不覆盖 V1 历史课件。
- 在 V1 骨架内更新内容：风险分诊与 Profile → Spec/契约 → 分级 TDD → Capability 门禁 → 候选冻结与 final → evidence/archive，而不是另起一套抽象概念目录。
- 增加 Lite/Standard/Strict、Capability 升级、硬门禁适用性、Gate Runner 新鲜度、Brownfield/Sandbox、上下文路由和风险驱动 PBT 内容。
- 更新四 Agent 的职责与停止条件，明确阶段是状态而非强制暂停点，Lite 可由单 Agent 连续完成。
- 删除或改写过期说法，包括“每 20 次对话提交”“所有项目都做完整设计”“GWT 是唯一事实源”“P0 E2E 永远触发”和旧初始化命令。
- 新增可复现的课件内容源、生成脚本和自动验证脚本，检查页数、版本、关键主题、禁用旧术语、页码、画布边界和生成一致性。
- 生成 PDF 预览并逐页渲染检查，但 PDF/临时预览作为验证制品，不替代可编辑 PPTX。
- 将英文术语改为中文主标题，并用日常场景、动作和结果解释 Profile、Capability、candidate、fresh/stale 等概念。

## Capabilities

### New Capabilities

- `current-mase-training-deck`: 提供与 MASE v2.3 现行规范一致、可生成和可验证的介绍/培训课件。

### Modified Capabilities

无。

## Impact

- 新增 `training/mase-framework/MASE框架培训讲义V2.3.pptx` 及其结构化内容源。
- 新增或更新 `scripts/` 下的课件构建与验证工具和相关测试。
- 新增 OpenSpec change 和 MASE 状态证据；不修改旧版 PPTX/PDF，不修改框架运行时 API、Profile 或产品代码。
