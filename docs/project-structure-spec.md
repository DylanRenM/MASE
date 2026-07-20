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
│       ├── mase-state.yaml    # change 唯一状态
│       ├── proposal.md
│       ├── design.md          # Profile/risk 需要时
│       ├── specs/{capability}/spec.md
│       └── tasks.md
├── src/ 或 Sources/           # stack adapter 决定
├── tests/ 或 Tests/
└── docs/
```

`openspec/master/` 是 archive/release 生成的只读快照，不是开发期双写目录。

## Stack adapter

| Stack | 产品根 | 测试根 | 项目清单 |
|---|---|---|---|
| generic | `src/` | `tests/` | 无强制语言清单 |
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
├── docs/archive/              # 非规范历史
├── training/                  # 非规范培训内容
├── examples/                  # 产品实例
└── tools/                     # 幻灯片等辅助工具
```

在完成物理迁移前，manifest 的 `default_context_excludes` 负责隔离历史、培训、产品代码和生成物。

## 禁止模式

- 同时手工维护 project-rules、AGENTS、CLAUDE、CONVENTIONS、Copilot 五份规则。
- 在 CLI 源码内嵌大段项目模板。
- 把 Proposal、Specs 和 E2E 报告中的同一场景复制三遍。
- 把培训 HTML/PPT、历史设计或产品实例作为现行框架规范检索。
- 为 Lite 项目创建空的 architecture/detailed-design/contract 文档只为满足目录。
