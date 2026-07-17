# E2E 测试环境隔离与自动恢复设计方案

> 创建日期：2026-07-17
> 状态：Draft — 待评审
> 作者：Dylan Ren

## 1. 背景与问题

### 1.1 问题描述

E2E 测试在执行过程中可能通过 UI 操作修改系统设置、创建文件、变更配置项。当前体系仅在数据库层面做了隔离（`pilot_test.db` + `seed.py` 重建），但缺少对以下可变状态的隔离与恢复机制：

- **配置文件**（`.env`、`config.yaml`、`settings.json` 等）—— 测试可能修改配置项
- **文件系统**（上传目录、导出目录、日志文件等）—— 残留的测试文件污染环境
- **系统级持久化**（通过 UI 保存的全局设置）—— 可能写入非 DB 的持久化存储

### 1.2 根因分析

当前设计假设 E2E 测试为"只读操作"，但真实的 E2E 验收场景（如"修改系统设置 → 验证生效"、"上传文件 → 验证解析"）必然涉及写操作。"只读"假设导致设计和实践之间产生断层——测试需要写，但基础设施不支持安全地写后恢复。

### 1.3 当前已有的隔离机制

| 机制 | 实现方式 | 覆盖范围 |
|---|---|---|
| 数据库隔离 | `pilot_test.db` + `beforeAll` 重跑 `seed.py` | 仅 SQLite 数据 |
| 进程隔离 | `playwright.config.js` 中 `webServer` 自动拉起 | 仅进程，不隔离文件系统 |
| Worker 限制 | `workers: CI ? 1 : undefined` | 仅并行度控制 |

### 1.4 缺失的能力

- **没有 `afterAll` 状态恢复**：测试结束后不恢复任何状态
- **没有写入重定向**：文件/配置写入直接落到真实路径
- **没有环境验证**：无法检测测试是否造成了意外修改

## 2. 设计目标与非目标

### 2.1 目标

1. **100% 状态恢复**：任何 E2E 测试完成后，环境自动恢复到测试前状态
2. **无侵入性**：测试代码不需要显式编写清理逻辑，框架自动处理
3. **可验证性**：恢复后自动验证关键状态与前序一致，不一致时告警
4. **兼容现有体系**：不破坏已有的数据库隔离、seed.py、Page Object 等机制

### 2.2 非目标

- 不追求 Docker 容器级隔离（MASE 定位为轻量框架，不做强制基础设施依赖）
- 不替换现有 seed.py 机制（数据库隔离继续沿用当前方案）
- 不修改四 Agent 分工和六阶段流程

## 3. 方案：E2E Sandbox 三层防线

```
┌─────────────────────────────────────────────────────┐
│               E2E Sandbox 三层防线                      │
├─────────────────────────────────────────────────────┤
│                                                       │
│  第一层：状态快照与恢复 (Snapshot & Restore)              │
│  ┌─────────────────────────────────────────────┐    │
│  │ beforeAll: 捕获快照                           │    │
│  │   ├── 文件系统：指定目录的文件树 + 内容哈希       │    │
│  │   ├── 配置文件：指定配置项的值                  │    │
│  │   └── 环境变量：关键变量的快照                   │    │
│  │                                             │    │
│  │ afterAll: 恢复快照 + 状态验证                  │    │
│  │   ├── 文件系统：删除多余文件，恢复被修改文件      │    │
│  │   ├── 配置文件：回写原始值                      │    │
│  │   ├── 环境变量：恢复原始值                      │    │
│  │   └── 验证：断言恢复后状态 == 快照              │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  第二层：写入重定向 (Write Redirection)                  │
│  ┌─────────────────────────────────────────────┐    │
│  │ 数据库：已有 pilot_test.db 隔离（不变）         │    │
│  │ 文件上传：重定向到 e2e/sandbox/uploads/         │    │
│  │ 文件导出：重定向到 e2e/sandbox/exports/         │    │
│  │ 配置文件：应用 E2E_SANDBOX_MODE 环境变量         │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  第三层：环境健康检查 (Environment Health Check)         │
│  ┌─────────────────────────────────────────────┐    │
│  │ afterAll 中自动执行：                          │    │
│  │   ├── 关键文件完整性检查                       │    │
│  │   ├── 端口占用检查                             │    │
│  │   └── 异常时 Block 后续测试 + 输出清理指南       │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### 3.1 第一层：状态快照与恢复

#### 3.1.1 快照清单配置

在每个项目的 `e2e/` 目录下新增 `sandbox.config.json`，声明需要快照管理的资源：

```json
{
  "snapshot": {
    "directories": [
      "data/uploads/",
      "data/exports/",
      "data/logs/"
    ],
    "files": [
      ".env",
      "config.yaml",
      "data/settings.json"
    ],
    "env_vars": [
      "APP_ENV",
      "DEBUG",
      "DATABASE_URL"
    ]
  },
  "validation": {
    "strict": true
  }
}
```

#### 3.1.2 快照机制

**文件系统快照**——记录每个文件的相对路径 + SHA-256 哈希 + 修改时间：

```json
{
  "data/uploads/": null,
  "data/exports/report.xlsx": "sha256:abc123...",
  ".env": "sha256:def456..."
}
```

**配置文件快照**——对结构化配置做深度序列化：

```json
{
  ".env": {
    "APP_ENV": "development",
    "DEBUG": "true",
    "DATABASE_URL": "sqlite:///data/pilot.db"
  }
}
```

#### 3.1.3 恢复逻辑（关键）

恢复采用 **"增删改" 三向对齐** 策略：

```
恢复 = {
  1. 新增文件删除：快照中不存在的文件 → 删除
  2. 删除文件恢复：快照中存在但当前不存在的文件 → 报错（异常状态，不能自动恢复）
  3. 修改文件回滚：内容哈希不一致 → 用快照备份覆盖
}
```

对配置文件采用**值级恢复**而非文件级恢复——即只恢复修改过的键，不整体覆盖文件（避免丢失测试期间其他进程的正常写入）。

#### 3.1.4 状态验证

恢复完成后，重新计算快照并与原始快照对比，必须完全一致。不一致时：
- 输出 `diff` 报告
- 输出清理命令供开发者手动处理
- 设置 `process.exitCode = 1` 阻止后续测试

### 3.2 第二层：写入重定向

#### 3.2.1 数据库（已有，不变）

沿用 `pilot_test.db` + `seed.py` 机制。

#### 3.2.2 文件系统重定向

在应用启动时设置以下环境变量，让应用将读写操作定向到 sandbox 目录：

```bash
E2E_SANDBOX_MODE=true
E2E_UPLOAD_DIR=e2e/sandbox/uploads/
E2E_EXPORT_DIR=e2e/sandbox/exports/
E2E_LOG_DIR=e2e/sandbox/logs/
```

应用代码通过读取这些环境变量来决定路径：

```python
# cosmic_web.py 中的路径配置
UPLOAD_DIR = os.environ.get('E2E_UPLOAD_DIR', 'data/uploads/')
EXPORT_DIR = os.environ.get('E2E_EXPORT_DIR', 'data/exports/')
```

#### 3.2.3 应用改造点

应用需要支持通过环境变量切换存储路径（类似已有 `--test` 参数的数据库路径切换）。改造量约 5-10 行，与现有 `--test` 模式改造同级别。

### 3.3 第三层：环境健康检查

在 `afterAll` 中自动执行以下检查：

| 检查项 | 方法 | 失败处置 |
|---|---|---|
| 关键文件未丢失 | 快照对比 | Block 后续测试 |
| 端口未被额外占用 | `lsof -i :<port>` | Block 后续测试 |
| 测试数据库独立完整 | `pilot_test.db` 存在且可读 | 仅告警 |
| sandbox 目录可清理 | 检查权限 | 仅告警 |

### 3.4 实现载体：`e2e/helpers/sandbox.js`

不侵入 Playwright 测试代码本身。测试用例在 `beforeAll` / `afterAll` 中调用 sandbox helper：

```javascript
// e2e/helpers/sandbox.js
import { snapshot, restore, verify } from './sandbox.js';

test.beforeAll(async () => {
  await snapshot();  // 捕获环境快照
  // ... 原有的 seed.py 调用 ...
});

test.afterAll(async () => {
  await restore();   // 恢复环境
  await verify();    // 验证恢复结果
});
```

测试用例无需修改任何业务逻辑。

## 4. 目录结构变更

```
pilot/
├── e2e/
│   ├── sandbox/                  # 新增：sandbox 运行时目录 (.gitignore)
│   │   ├── uploads/              # 测试期间的上传文件
│   │   ├── exports/              # 测试期间的导出文件
│   │   ├── logs/                 # 测试期间的日志
│   │   └── snapshots/            # 自动快照存储
│   ├── helpers/
│   │   ├── pages.js              # 已有：Page Object
│   │   └── sandbox.js            # 新增：Sandbox helper
│   ├── sandbox.config.json       # 新增：快照清单配置
│   ├── fixtures/                 # 已有（不变）
│   ├── tests/                    # 已有（不变）
│   ├── debug.py                  # 已有（不变）
│   └── playwright.config.js      # 修改：注入环境变量
```

## 5. 与现有机制的集成

### 5.1 与 seed.py 的关系

`seed.py` 仍然负责数据库初始化。sandbox 机制在数据库层面之外增加了文件/配置/环境变量三个维度的保护。二者协作而非替代：

```
beforeAll:
  1. sandbox.snapshot()   ← 新增：快照文件/配置/环境
  2. seed.py              ← 已有：重建测试数据库
  → 执行测试用例
afterAll:
  3. sandbox.restore()    ← 新增：恢复文件/配置/环境
  4. sandbox.verify()     ← 新增：验证恢复一致性
```

### 5.2 与 playwright.config.js 的集成

`playwright.config.js` 中的 webServer 命令增加环境变量注入：

```js
webServer: {
  command: 'E2E_SANDBOX_MODE=true E2E_UPLOAD_DIR=e2e/sandbox/uploads/ python cosmic_web.py --test',
  port: 5000,
  // ...
}
```

### 5.3 与 webapp-testing Skill 的集成

`SKILL.md` 的 "E2E 专属最佳实践" 条目新增：

- `beforeAll` 调用 `sandbox.snapshot()` 捕获环境状态
- `afterAll` 调用 `sandbox.restore()` 恢复环境
- 每个 spec 文件的 `afterAll` 中调用 `sandbox.verify()` 验证环境一致性

## 6. 对受控文件的影响

| 文件 | 操作 | 说明 |
|---|---|---|
| `e2e/helpers/sandbox.js` | **新增** | Sandbox 核心逻辑 |
| `e2e/sandbox.config.json` | **新增** | 快照清单配置 |
| `e2e/playwright.config.js` | 修改 | 注入 sandbox 环境变量 |
| `skills/webapp-testing/SKILL.md` | 修改 | 新增 sandbox 最佳实践条目 |
| `docs/superpowers/specs/2026-07-14-e2e-playwright-reinforcement-design.md` | 修改 | 补充环境隔离章节 |
| 应用代码（`cosmic_web.py` 等） | 修改 | 支持 sandbox 环境变量路径切换 |

## 7. 决策记录

| 决策项 | 选择 | 理由 |
|---|---|---|
| 隔离策略 | 快照恢复为主 + 写入重定向为辅 | 快照恢复是兜底机制，写入重定向减少恢复压力 |
| 恢复粒度 | 值级恢复（配置）/ 文件级恢复（文件系统） | 配置文件可能被并发修改，文件级覆盖会丢失数据 |
| 写入重定向方式 | 环境变量注入 | 最小侵入，与现有 `--test` 模式一致 |
| 恢复验证 | 强制 + block | 不通过则阻止后续测试，避免污染扩散 |
| Sandbox 目录 | `e2e/sandbox/` 并加入 .gitignore | 运行时产物，不应提交 |

## 8. 实施计划

### Phase 1: Sandbox Helper 实现
- `e2e/helpers/sandbox.js` — snapshot / restore / verify 核心函数
- `e2e/sandbox.config.json` — 快照清单模板
- 单元测试验证 sandbox 逻辑正确

### Phase 2: 应用改造
- 应用代码支持 `E2E_UPLOAD_DIR` / `E2E_EXPORT_DIR` 等环境变量
- `playwright.config.js` webServer 命令注入环境变量

### Phase 3: 规范更新
- `SKILL.md` 补充 sandbox 最佳实践
- 设计文档补充环境隔离章节

### Phase 4: 试点验证
- 在 pilot 项目中集成 sandbox
- 执行全量 E2E 回归，验证环境恢复正确
- 手动破坏环境验证检测机制有效

## 9. 成功标准

- [ ] 任何 E2E 测试执行后，`e2e/sandbox.config.json` 中声明的所有状态与测试前完全一致
- [ ] 恢复验证失败时，后续测试被 Block
- [ ] 现有 E2E 测试代码无需修改即可享受保护
- [ ] 写入重定向使测试期间的文件变更不触及生产目录
