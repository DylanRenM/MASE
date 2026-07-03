# 项目目录结构

> 创建新项目时，按此结构初始化。详见 `docs/superpowers/specs/2026-07-03-project-structure-spec.md`

## 初始化命令

```bash
# 产品代码 — 每个 capability 按职责分子目录
mkdir -p src/{pkg}/{capability1,capability2}/models
mkdir -p src/{pkg}/{capability1,capability2}/services
mkdir -p src/{pkg}/{capability1,capability2}/routes
mkdir -p src/{pkg}/{capability1,capability2}/schemas
mkdir -p src/{pkg}/shared/{config,database,utils}

# 测试代码 — 镜像 src/
mkdir -p tests/unit/{capability1,capability2}/{models,services,routes}
mkdir -p tests/unit/shared/{config,database,utils}
mkdir -p tests/integration
mkdir -p tests/fixtures/{capability1,capability2}/{models,services}

# 其他目录
mkdir -p scripts config
mkdir -p docs/lessons
mkdir -p docs/cases/{bugs,patterns,pitfalls}

# 根目录文件
touch .env.example .gitignore Makefile README.md
touch tests/conftest.py tests/__init__.py
```

## 最终结构

```
project-root/
├── src/{package_name}/
│   ├── __init__.py
│   ├── {capability}/          # 每个 capability 一个模块
│   │   ├── __init__.py
│   │   ├── models/            # 数据模型（ORM/数据类）
│   │   ├── services/          # 业务逻辑
│   │   ├── routes/            # API 路由（可选）
│   │   └── schemas/           # 请求/响应 Schema（可选）
│   └── shared/                # 跨 capability 共享
│       ├── config/            # 全局配置
│       ├── database/          # 数据库连接
│       └── utils/             # 通用工具
├── tests/
│   ├── unit/{capability}/
│   │   ├── models/            # 镜像 src/{capability}/models/
│   │   ├── services/          # 镜像 src/{capability}/services/
│   │   └── routes/            # 镜像 src/{capability}/routes/
│   ├── integration/
│   ├── fixtures/{capability}/
│   └── conftest.py
├── docs/
│   ├── user-guide.md
│   ├── lessons/                # 经验教训（bug-fixer 原则7输出）
│   │   └── YYYY-MM-DD-{topic}.md
│   ├── cases/                  # 典型案例
│   │   ├── bugs/               # BUG 案例
│   │   ├── patterns/           # 设计模式
│   │   └── pitfalls/           # 踩坑记录
│   └── superpowers/specs/
├── openspec/changes/{name}/
│   └── specs/{capability}/
├── scripts/
├── config/
├── pyproject.toml
├── Makefile
├── .env.example
├── .gitignore
└── README.md
```

## 分类说明

| 子目录 | 放什么 | 不放什么 |
|--------|--------|---------|
| `models/` | ORM 模型、数据类、类型定义 | 业务逻辑、API 处理 |
| `services/` | 核心逻辑、算法、业务规则 | 路由注册、HTTP 处理 |
| `routes/` | API 端点定义、参数校验 | 业务逻辑（调 services） |
| `schemas/` | Pydantic 模型、请求/响应体 | ORM 模型（用 models） |
| `shared/config/` | 全局设置、环境变量读取 | 业务特定配置 |
| `shared/database/` | 连接管理、Session 工厂 | 数据模型（用 models） |
| `shared/utils/` | 日志、异常处理、工具函数 | 业务相关的工具 |
