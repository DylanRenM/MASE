## Why

MASE v1.3 在磨耳朵 macOS MVP 中证明了原型确认、风险 POC、契约和 P0 E2E 的质量价值，但固定六阶段、重复规则副本、多份状态与设计文档、Python 专属 CLI 和全量上下文读取造成了明显的流程与 Token 开销。现在需要把框架升级为按风险伸缩、机器生成证据、跨技术栈且具有单一事实来源的 MASE v2。

## What Changes

- 引入 Lite、Standard、Strict 三种过程 Profile，并允许高风险能力在轻量项目中局部升级。
- 将 `mase-state.yaml` 设为唯一状态源，门禁、追踪矩阵、验证摘要和 IDE 规则副本由工具生成。
- **BREAKING**：默认产物从固定的 proposal/architecture/detailed-design/contract/tasks 全家桶调整为风险驱动产物；日常 change 不再语义合并到 `openspec/master/`，只在归档时生成快照。
- **BREAKING**：`mase init` 和 `mase check` 不再假设 Python 项目，改为 Profile + stack adapter 驱动。
- 为 Agent/Skill 增加短路由器与按需 references，默认使用当前 capability、相关测试和 `git diff`，避免全量读取稳定文档。
- 将框架运行时、规范、历史资料、培训产物和产品实例划分为明确边界；生成物不再作为人工维护的规范源。
- 增加 `mase doctor`、`mase status`、`mase metrics` 及 JSON 输出，为环境预检、状态一致性和 Token 遥测提供自动证据。

## Capabilities

### New Capabilities

- `adaptive-process-profiles`: 根据风险和项目特征选择 Lite、Standard 或 Strict 门禁，并支持 capability 局部升级。
- `single-source-project-state`: 以唯一机器可读状态记录阶段、门禁和证据，派生报告及归档快照。
- `stack-aware-cli`: 初始化、检查、诊断和更新不同技术栈的 MASE 项目，不再绑定 Python 目录结构。
- `token-efficient-context-routing`: 通过短规则路由、任务读取清单、差异优先和遥测减少重复上下文。
- `framework-content-boundaries`: 区分框架运行时、规范、模板、历史、培训、生成物和产品实例，并建立一致的版本与发布边界。

### Modified Capabilities

<!-- 当前仓库没有 openspec/specs 基线；本变更以五个新 capability 建立 MASE v2 行为基线。 -->

## Impact

- 影响根级 AI IDE 规则、4 个 Agent、12 个 Skills、现行框架文档和初始化模板。
- 影响 `mase_cli` 的 init/check/update/contract，并新增 doctor/status/metrics 命令。
- 影响项目初始化结构和 `.mase.yaml` / `mase-state.yaml` 迁移方式；旧项目通过 `mase update --dry-run` 预览并保留备份。
- 不修改磨耳朵产品行为、Swift 产品代码或其验收包。
- 继续保留原型确认、高风险 POC、API 契约、根因分析和 P0 E2E 等质量底线。
