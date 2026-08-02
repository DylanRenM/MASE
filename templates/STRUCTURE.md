# MASE v2 项目结构入口

项目结构由 `stack × Profile` 生成，不再复制固定 Python 全家桶。

```bash
mase init local-tool --stack generic --profile lite
mase init api --stack python --profile standard -p api_pkg -c auth catalog
mase init mac-app --stack swift --profile standard
```

通用最小结构：

```text
project/
├── .mase.yaml
├── project-rules.md
├── generated IDE adapters
├── openspec/changes/
├── docs/
├── <stack product root>
└── <stack test root>
```

详细约束见 `docs/project-structure-spec.md`。手工初始化时也必须遵守 `framework-manifest.yaml`、当前 Profile 和 stack adapter，禁止用本文件假设所有项目都有 models/routes/Playwright。
