# MASE v2 项目结构规范

## 通用原则

1. 每类事实只有一个人工维护位置。
2. 产品、框架、测试、历史、培训和生成物物理分区。
3. 目录由 stack adapter 和 Profile 决定，不强迫 Swift 项目采用 Python 结构。
4. tests 在语义上镜像 capability，而不是机械复制每层目录。

## 最小通用项目

```text
project/
├── .mase.yaml                 # 项目元数据：version/profile/stack
├── project-rules.md           # 唯一项目规则源
├── AGENTS.md / CLAUDE.md ...  # generated IDE adapters
├── openspec/
│   └── changes/{name}/
│       ├── mase-state.yaml    # change 唯一状态；可绑定 framework_contract
│       │                      # 发布任务可内嵌可选 Release Overlay
│       ├── impact-analysis.yaml # 历史行为变更的调用链、分级、测试与回滚事实源
│       ├── impact-scope.md    # 由影响事实源生成
│       ├── test-scope.md      # 由影响事实源生成
│       ├── rollback.md        # 由影响事实源生成
│       ├── proposal.md
│       ├── design.md          # Profile/risk 需要时
│       ├── specs/{capability}/spec.md
│       └── tasks.md
├── src/ 或 Sources/           # stack adapter 决定
├── tests/ 或 Tests/
└── docs/
```

`openspec/master/` 是 archive/release 生成的只读快照，不是开发期双写目录。

三个 Markdown 视图不得独立维护；`mase impact render` 从 `impact-analysis.yaml` 重建并写入相同来源摘要。未修改历史行为的 change 仍需在 state 中完成影响分类或记录结构化豁免。

## Stack adapter

| Stack | 产品根 | 测试根 | 项目清单 |
|---|---|---|---|
| generic | 可选 | 可选 | 无强制语言清单 |
| python | `src/{package}/` | `tests/` | `pyproject.toml` |
| swift | `Sources/{Module}/` | `Tests/{Module}Tests/` | `Package.swift` |

新增 stack 时实现声明式必需路径和模板，不在 `check_project.py` 堆叠项目专属判断。

## MASE 框架仓库

```text
MASE/
├── framework-manifest.yaml    # 版本、发布与上下文边界
├── project-rules.md           # 规则源
├── profiles/                  # Lite/Standard/Strict
├── schemas/                   # 状态等机器契约
├── mase_cli/                  # CLI 运行时
├── agents/                    # 短路由器
├── skills/                    # SKILL.md + 按需 references
├── templates/                 # stack/Profile 感知模板
├── docs/                      # 现行规范
├── training/mase-framework/   # MASE 培训源、受保护模板与可编辑课件
├── scripts/                   # 框架构建、验证与边界审计
└── tests/                     # 只验证 MASE 框架
```

Release Overlay 的独立输入模板为 `templates/release-context.yaml`，契约为 `schemas/mase-release.schema.json`；合入 change 后仍由 `mase-state.yaml` 作为唯一状态源。`skills/release-software/` 保存平台中立流程、确定性计划脚本和一层 adapter references。项目专属的部署命令、CI/CD、Helm、Terraform、PowerShell 或商店自动化留在采用项目中，不复制进 MASE 核心。

MASE 框架与采用它开发的真实产品必须使用不同项目根和独立 Git 仓库。真实产品、产品数据、通用培训、研究演示、历史备份和构建缓存不得放入 `MASE/`。`scripts/audit_repository_boundary.py` 以显式 allowlist 检查顶层、现行 docs/training 和递归生成残留；manifest 的 `default_context_excludes` 只负责当前框架运行时的上下文预算，不再承担隐藏非框架内容的职责。

采用项目通过已安装 CLI 和版本化 Schema 使用 MASE；`mase-state.yaml` 可声明 `framework_contract` 固定 `name`、语义版本和 `installed-cli-and-versioned-schemas` 接口。框架验证使用临时采用项目，不访问任何命名产品仓库。

## 禁止模式

- 同时手工维护 project-rules、AGENTS、CLAUDE、CONVENTIONS、Copilot 五份规则。
- 在 CLI 源码内嵌大段项目模板。
- 把 Proposal、Specs 和 E2E 报告中的同一场景复制三遍。
- 把培训 HTML/PPT、历史设计或产品实例作为现行框架规范检索。
- 把采用 MASE 开发的真实产品源码、需求、OpenSpec 或构建缓存放进 MASE 框架仓库。
- 用 `.gitignore` 或 `default_context_excludes` 隐藏已经放入 MASE 的产品、备份或演示目录。
- 为 Lite 项目创建空的 architecture/detailed-design/contract 文档只为满足目录。
- 把 Windows、容器、HTTP、数据库或 LLM 假设写成所有发布都必须执行的通用清单。
- 把 release plan/checklist 的 pending 项目直接登记为 passed evidence。
