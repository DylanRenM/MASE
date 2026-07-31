# MASE v2

MASE（Measures AI Software Engineering）是一套风险自适应 AI 软件工程框架：用可验收需求、影响链分析、风险 POC、API 契约、TDD 和 P0 E2E 保住质量底线，用 Lite / Standard / Strict Profile 控制过程重量和 Token 成本。

## 快速开始

```bash
python3 -m pip install .
mase install --source .
mase doctor --stack swift
mase init my-project --stack swift --profile lite
cd my-project
mase check
```

旧 Python 参数保持兼容：

```bash
mase init api -p api_pkg -c auth catalog
```

## 核心变化

- `project-rules.md` 是唯一规则源，IDE 文件自动生成。
- `mase-state.yaml` 是 change 唯一状态源，报告自动派生。
- 采用项目可用 `framework_contract` 绑定已安装 CLI 与版本化 Schema；MASE 与产品仓库保持独立。
- 主 stack 只使用 generic、python、swift，Flutter、SwiftUI、Dart 等作为 toolchains 表达。
- GatePlan 由 Profile、标准风险、产品属性和 change 影响面推导，自动证据可验证新鲜度。
- 历史行为变更在设计前扫描显性调用方和隐性依赖，实现后按实际差异复扫；L1/L2/L3 只增加验证强度，不成为第四种 Profile。
- Brownfield 可审核遗留失败基线；API/P0/凭据等硬门禁不可普通基线化。
- `mase status` 默认显示全部活动 change、依赖、影响路径冲突和基线债务。
- Lite 小循环只跑相关测试；Capability/最终边界再扩大验证。
- `openspec/master/` 只在归档时生成快照，不在开发中双写。
- 产品实例、通用培训、研究演示、历史备份和生成物不进入 MASE 仓库；MASE 培训材料与运行时物理分区。

## 命令

```text
mase init       初始化 Profile/stack 感知项目
mase doctor     环境预检
mase check      合规检查
mase status     多 change portfolio；--change 查看详情
mase gate       运行自动门禁或记录结构化人工证据
mase impact     分类、校验、复扫并生成影响范围/测试范围/回滚视图
mase metrics    真实 Token 或 context proxy
mase context plan --change my-change --json
mase update     非破坏迁移，支持 --dry-run
mase install    按 manifest 安装运行时
python3 scripts/audit_repository_boundary.py  检查仓库只包含 MASE 框架内容
```

自动门禁示例：

```bash
mase gate run api_contract --change my-change --input src --input tests -- python3 -m pytest -q tests
# 人工调试需要完整实时输出时再增加 --verbose
```

现行规范见 [docs/MASE-framework.md](docs/MASE-framework.md)，使用说明见 [docs/user-guide.md](docs/user-guide.md)。

## 仓库边界

MASE 是过程框架，不是产品 monorepo。采用 MASE 的应用必须位于独立同级目录并维护自己的状态、数据、测试和 Git 生命周期。根目录采用显式 allowlist；非现行文档、非 MASE 培训、演示站点、备份、产品数据库和构建缓存都会被边界审计拒绝。默认 `pytest` 只收集 `tests/` 中的框架测试。

## License

MIT © 2026 Measures Technology（麦哲思科技）
