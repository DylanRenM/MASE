# 项目目录结构规范

> 所有新项目必须遵循此结构，Classify 代码文件时严格遵守。

## 规范速查

```
project-root/
├── src/                          # ① 产品代码（唯一源码位置）
│   └── {package_name}/           #     Python 包名（snake_case）
│       ├── __init__.py
│       ├── {capability}/         #     按 specs/ 中的 capability 分模块
│       │   ├── __init__.py
│       │   ├── models/           #     数据模型（ORM/数据类）
│       │   │   ├── __init__.py
│       │   │   └── *.py
│       │   ├── services/         #     业务逻辑
│       │   │   ├── __init__.py
│       │   │   └── *.py
│       │   ├── routes/           #     API 路由（可选，有 HTTP 接口时）
│       │   │   ├── __init__.py
│       │   │   └── *.py
│       │   └── schemas/          #     请求/响应 Schema（可选）
│       │       ├── __init__.py
│       │       └── *.py
│       └── shared/               #     跨 capability 共享
│           ├── __init__.py
│           ├── config/           #     全局配置管理
│           │   ├── __init__.py
│           │   └── settings.py
│           ├── database/         #     数据库连接与 ORM 基类
│           │   ├── __init__.py
│           │   └── connection.py
│           └── utils/            #     通用工具函数
│               ├── __init__.py
│               └── *.py
│
├── tests/                        # ② 测试代码（镜像 src/ 结构）
│   ├── unit/                     #     单元测试
│   │   └── {capability}/
│   │       ├── __init__.py
│   │       ├── models/           #     镜像 src/{capability}/models/
│   │       │   ├── __init__.py
│   │       │   └── test_*.py
│   │       ├── services/         #     镜像 src/{capability}/services/
│   │       │   ├── __init__.py
│   │       │   └── test_*.py
│   │       └── routes/           #     镜像 src/{capability}/routes/
│   │           ├── __init__.py
│   │           └── test_*.py
│   ├── integration/              #     集成测试（跨 capability）
│   │   ├── __init__.py
│   │   └── test_*.py
│   ├── fixtures/                 #     测试数据文件（json/csv/txt）
│   │   └── {capability}/
│   │       ├── models/           #     镜像 src/{capability}/models/
│   │       └── services/         #     镜像 src/{capability}/services/
│   ├── conftest.py               #     pytest 共享 fixtures
│   └── __init__.py
│
├── docs/                         # ③ 文档（唯一文档位置）
│   ├── user-guide.md             #     用户使用手册
│   ├── lessons/                  #     经验教训（bug-fixer 原则7输出）
│   │   └── YYYY-MM-DD-{topic}.md
│   ├── cases/                    #     典型案例（可复用模式/反模式）
│   │   ├── bugs/                 #     BUG 案例
│   │   │   └── {case-name}.md
│   │   ├── patterns/             #     设计模式/代码模式
│   │   │   └── {pattern-name}.md
│   │   └── pitfalls/             #     踩坑记录
│   │       └── {pitfall-name}.md
│   └── superpowers/              #     设计文档归档
│       └── specs/
│           └── YYYY-MM-DD-{topic}-design.md
│
├── openspec/                     # ④ 规范文档（只读，由 Agent 产出）
│   └── changes/
│       └── {change-name}/
│           ├── .openspec.yaml
│           ├── proposal.md
│           ├── tech-feasibility.md
│           ├── architecture.md
│           ├── detailed-design.md
│           ├── tasks.md
│           └── specs/
│               └── {capability}/
│                   └── spec.md
│
├── scripts/                      # ⑤ 工具脚本（非产品代码）
│   ├── run.py                    #     项目入口脚本
│   └── migrate.py                #     数据迁移等一次性脚本
│
├── config/                       # ⑥ 配置文件（非代码）
│   ├── logging.yaml              #     日志配置
│   └── {env}.yaml                #     环境配置
│
├── pyproject.toml                # ⑦ 项目元信息
├── Makefile                      #     常用命令快捷入口
├── .env.example                  #     环境变量模板
├── .gitignore                    #     Git 忽略规则
└── README.md                     #     项目说明
```

## 设计原则

### 1. 唯一性 — 每类文件只有一个存放位置
- 产品代码 → `src/`
- 测试代码 → `tests/`
- 文档 → `docs/`
- 规范 → `openspec/`
- 脚本 → `scripts/`

绝对禁止：
- 将产品代码放在根目录
- 将测试和产品代码混放
- 将文档散落在各处

### 2. 镜像原则 — tests/ 目录结构镜像 src/

```
src/{pkg}/{capability}/models/foo.py       →  tests/unit/{capability}/models/test_foo.py
src/{pkg}/{capability}/services/bar.py     →  tests/unit/{capability}/services/test_bar.py
src/{pkg}/{capability}/routes/baz.py       →  tests/unit/{capability}/routes/test_baz.py
src/{pkg}/shared/config/settings.py        →  tests/unit/shared/config/test_settings.py
```

不镜像 = 出问题。文件多了之后找不到对应关系。

### 3. Capability 对齐 — src/ 的一级分组与 specs/ 一一对应
```
specs/book-parser/spec.md     →  src/{pkg}/book_parser/
specs/content-vectorizer/     →  src/{pkg}/content_vectorizer/
...
```

`shared/` 例外：跨 capability 共享的代码放这里。

### 4. 根目录整洁 — 根目录只放项目级别文件
允许在根目录的：
- `pyproject.toml`、`Makefile`、`.env.example`、`.gitignore`、`README.md`
- 目录（`src/`、`tests/`、`docs/`、`openspec/`、`scripts/`、`config/`）

禁止在根目录的：
- Python 源文件（应该放 `src/` 或 `scripts/`）
- 测试文件（应该放 `tests/`）
- 数据文件（应该放 `data/`）
- Python `__pycache__` 目录

## 文件命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| Python 包名 | snake_case | `book_parser/` |
| Python 模块 | snake_case | `content_vectorizer.py` |
| Python 类 | PascalCase | `class BookParser` |
| 函数/方法 | snake_case, 动词开头 | `def parse_epub()` |
| 测试文件 | `test_{被测模块}.py` | `test_book_parser.py` |
| 测试函数 | `test_{场景}.py` | `def test_parse_empty_chapter()` |
| JSON/YAML 配置 | kebab-case | `logging.yaml` |

## 禁止模式

### 禁止：根目录散落 Python 文件
```diff
- project-root/main.py
- project-root/batch_import.py
- project-root/recover_stuck.py
+ project-root/scripts/run.py
+ project-root/scripts/batch_import.py
+ project-root/scripts/recover_stuck.py
```

### 禁止：测试与产品代码混放
```diff
- src/bazi/test_parser.py       # 测试代码不应在 src/
+ tests/unit/book_parser/test_parser.py
```

### 禁止：测试无组织结构
```diff
- tests/test_book_parser.py
- tests/test_content_vectorizer.py
+ tests/unit/book_parser/test_book_parser.py
+ tests/unit/content_vectorizer/test_content_vectorizer.py
```

## 创建新项目流程

1. 复制 `openspec/changes/_template/` → `openspec/changes/{name}/`
2. 确认 `specs/{capability}/` 目录结构（决定 src/ 的模块分组）
3. 按本规范创建目录骨架：
   ```bash
   # 产品代码
   mkdir -p src/{pkg}/{capability1,capability2}/models
   mkdir -p src/{pkg}/{capability1,capability2}/services
   mkdir -p src/{pkg}/{capability1,capability2}/routes
   mkdir -p src/{pkg}/{capability1,capability2}/schemas
   mkdir -p src/{pkg}/shared/{config,database,utils}
   
   # 测试代码
   mkdir -p tests/unit/{capability1,capability2}/{models,services,routes}
   mkdir -p tests/unit/shared/{config,database,utils}
   mkdir -p tests/integration
   mkdir -p tests/fixtures/{capability1,capability2}/{models,services}
   
   # 其他
    mkdir -p scripts config
    mkdir -p docs/lessons
    mkdir -p docs/cases/{bugs,patterns,pitfalls}
    touch .env.example .gitignore Makefile README.md
    ```

## 文档清单

| 路径 | 内容 | 谁维护 |
|------|------|--------|
| `README.md` | 项目简介 + 快速开始 | 手动 |
| `docs/user-guide.md` | 完整使用手册 | Agent 1 (Release 阶段) |
| `docs/lessons/` | 经验教训记录 | Agent 4 (bug-fixer 原则7输出) |
| `docs/cases/bugs/` | BUG 经典案例 | Agent 4 (Verify 阶段) |
| `docs/cases/patterns/` | 可复用设计模式 | Agent 3 (Build 阶段) |
| `docs/cases/pitfalls/` | 踩坑记录 | 任何 Agent |
| `docs/superpowers/specs/` | 设计文档归档 | brainstorming Skill |
| `openspec/changes/` | 当前变更规范 | Agent 2 + Agent 3 |

## 与麦哲思AI软件开发统一流程的关系

| 框架阶段 | 创建的目录 |
|----------|-----------|
| 创建新项目 | `src/`, `tests/`, `scripts/`, `config/`, 根目录配置文件 |
| 阶段 2 (Design L2) | `openspec/changes/{name}/` 完整结构 |
| 阶段 3 (Build) | `src/{pkg}/{capability}/` + `tests/unit/{capability}/` |
| 阶段 5 (Release) | `docs/user-guide.md` + `README.md` 更新 |
