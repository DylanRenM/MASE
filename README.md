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
- CLI 支持 generic、python、swift，不再要求所有项目采用 Python 骨架。
- Lite 小循环只跑相关测试；Capability/最终边界再扩大验证。
- `openspec/master/` 只在归档时生成快照，不在开发中双写。
- 历史、培训、生成物和产品实例不进入默认 Agent 上下文。

## 命令

```text
mase init       初始化 Profile/stack 感知项目
mase doctor     环境预检
mase check      合规检查
mase status     状态/任务一致性
mase metrics    真实 Token 或 context proxy
mase update     非破坏迁移，支持 --dry-run
mase install    按 manifest 安装运行时
```

现行规范见 [docs/MASE-framework.md](docs/MASE-framework.md)，使用说明见 [docs/user-guide.md](docs/user-guide.md)。

## License

MIT © 2026 Measures Technology（麦哲思科技）
