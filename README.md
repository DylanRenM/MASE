# MASE v2

MASE（Measures AI Software Engineering）是一套风险自适应 AI 软件工程框架：用可验收需求、风险 POC、API 契约、TDD 和 P0 E2E 保住质量底线，用 Lite / Standard / Strict Profile 控制过程重量和 Token 成本。

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
- 主 stack 只使用 generic、python、swift，Flutter、SwiftUI、Dart 等作为 toolchains 表达。
- GatePlan 由 Profile、标准风险、产品属性和 change 影响面推导，自动证据可验证新鲜度。
- Brownfield 可审核遗留失败基线；API/P0/凭据等硬门禁不可普通基线化。
- `mase status` 默认显示全部活动 change、依赖、影响路径冲突和基线债务。
- Lite 小循环只跑相关测试；Capability/最终边界再扩大验证。
- `openspec/master/` 只在归档时生成快照，不在开发中双写。
- 历史、培训、生成物和产品实例不进入默认 Agent 上下文。

## 命令

```text
mase init       初始化 Profile/stack 感知项目
mase doctor     环境预检
mase check      合规检查
mase status     多 change portfolio；--change 查看详情
mase gate       运行自动门禁或记录结构化人工证据
mase metrics    真实 Token 或 context proxy
mase context plan --change my-change --json
mase update     非破坏迁移，支持 --dry-run
mase install    按 manifest 安装运行时
```

自动门禁示例：

```bash
mase gate run api_contract --change my-change --input src --input tests -- python3 -m pytest -q tests
# 人工调试需要完整实时输出时再增加 --verbose
```

现行规范见 [docs/MASE-framework.md](docs/MASE-framework.md)，使用说明见 [docs/user-guide.md](docs/user-guide.md)。

## License

MIT © 2026 Measures Technology（麦哲思科技）
