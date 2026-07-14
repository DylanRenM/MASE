# Playwright E2E 自动化测试体系 - 设计文档

> 创建日期：2026-07-12
> 状态：Draft

## 1. 背景与目标

### 当前痛点

Pilot 项目（COSMIC/NESMA 智能度量平台）每次代码变更后，需要开发者手工点击所有页面验证功能未退化，耗时长且容易遗漏。项目现有约 50+ 个 pytest 单元测试，但完全没有浏览器端到端测试。

### 目标

1. **E2E 自动化回归**：核心业务流程可一键验证，减少手工回归投入
2. **TRAE 浏览器调试能力**：让 TRAE 通过 Playwright 直接操作浏览器定位 UI 问题，提升开发效率

### 非目标

- 不替代现有 pytest 单元测试
- 不追求 100% 覆盖率，先覆盖最高频的 6 个核心场景

## 2. 设计决策记录

| 决策 | 选项 | 理由 |
|:---|:---|:---|
| 测试组织方式 | 双轨制：Playwright 原生 runner（JS）+ Python `debug.py` | 回归用 Playwright 原生跑（完整 trace/screenshot/video），TRAE 调试用 Python 脚本（灵活内省） |
| 测试环境 | 独立测试数据库 `pilot_test.db` | 数据隔离，避免污染开发库 |
| 数据准备 | 与测试执行分离，`seed.py` 生成 `fixtures.json` | 借鉴 skills-hub 的 Fixture Runner 模式，并行安全 |
| 元素定位 | 优先语义定位器（getByRole/getByLabel），禁止 CSS class/id | 借鉴 playwright-expert 的最佳实践，UI 变动时更稳定 |
| 规模策略 | 增量覆盖，首期 6 个核心场景 | 快速见效后自然扩展 |

## 3. 目录结构

```
pilot/
├── tests/                          # 现有 pytest 单元测试（不动）
├── e2e/                            # 新增 E2E 测试根目录
│   ├── fixtures/
│   │   ├── seed.py                # 数据生成脚本
│   │   └── fixtures.json          # 生成后的数据清单（.gitignore）
│   ├── tests/
│   │   ├── auth.spec.js           # 登录/登出/权限
│   │   ├── cosmic-metric.spec.js  # COSMIC 度量全流程
│   │   ├── nesma-metric.spec.js   # NESMA 度量全流程
│   │   └── knowledge-hub.spec.js  # 知识库管理
│   ├── helpers/
│   │   └── pages.js               # Page Object Model
│   ├── debug.py                    # TRAE 调试入口
│   ├── playwright.config.js        # Playwright 配置
│   └── package.json                # Node 依赖
├── data/
│   ├── pilot_test.db               # 独立测试数据库（.gitignore）
│   └── test_fixtures/              # 测试上传用的示例文件
└── .trae/rules/
    └── playwright-standards.md     # 元素定位规范
```

## 4. 数据流与生命周期

### 执行流程

```
1. seed.py 执行
   ├── 创建/重置 pilot_test.db 和 kb_registry_test.db
   ├── 插入测试用户（admin / viewer，密码用 secrets.token_hex 随机生成）
   ├── 在 kb_registry_test.db 注册测试知识库，写入示例文档元数据
   └── 输出 fixtures.json

2. Flask 启动（playwright.config.js webServer）→ 连 pilot_test.db

3. Playwright 执行 .spec.js
   ├── 读取 fixtures.json
   ├── 浏览器操作（navigate、click、fill、assert）
   └── 只读操作，不修改 fixtures 数据

4. 测试结束 → 保留 pilot_test.db（方便失败后排查）
```

### fixtures.json 约定

```json
{
  "users": {
    "admin": { "username": "admin", "password": "<随机生成>", "role": "admin" },
    "viewer": { "username": "test_user", "password": "<随机生成>", "role": "user" }
  },
  "knowledge_bases": [
    { "id": "kb-001", "name": "测试知识库", "file_count": 3 }
  ],
  "test_files": {
    "requirement_doc": "data/test_fixtures/sample_requirement.docx"
  }
}
```

## 5. 元素定位策略

定位器优先级（从高到低），写入 `.trae/rules/playwright-standards.md`：

```
1. getByRole()    — 面向用户的语义定位（按钮、链接、标题等）
2. getByLabel()   — 表单标签定位
3. getByPlaceholder() — 输入框占位符
4. getByText()    — 可见文本匹配
5. getByTestId()  — data-testid 属性（仅当前 4 类无法定位时使用）
❌ 禁止：CSS class/id 选择器、XPath
```

## 6. Page Object 封装

每个页面一个 class，集中在 `e2e/helpers/pages.js`：

- `LoginPage`：登录表单操作、错误提示断言
- `CosmicMetricPage`：文档上传、方法选择、结果表格读取、Excel 导出
- `NesmaMetricPage`：同上 + NESMA 特有字段验证
- `KnowledgeHubPage`：文档上传、解析状态、对话交互

测试用例通过 Page Object 间接操作，不直接写选择器。

## 7. TRAE 调试工具（debug.py）

### 能力接口

```bash
python e2e/debug.py --action navigate --url "<path>"
python e2e/debug.py --action screenshot --selector "<css>"
python e2e/debug.py --action dom --selector "<css>"
python e2e/debug.py --action console
python e2e/debug.py --action trace
```

### 设计原则

- 复用 `pages.js` 的 Page Object，不裸写选择器
- 默认有头模式（`--headed`），TRAE 调试时用户可见
- 输出结构化 JSON，TRAE 可直接解析
- 不进 CI，纯粹开发调试工具

## 8. 错误处理与稳定性

| 场景 | 策略 |
|:---|:---|
| 元素未找到 | 默认等 10s（Playwright auto-wait），超时后截图 + 保存 DOM |
| Flask 未启动 | `webServer` 配置自动拉起 |
| 测试数据污染 | 每个 spec 文件 `beforeAll` 重新跑 `seed.py` |
| 登录态失效 | 全局 `beforeEach` 检查，失效自动重登 |
| 异步渲染 | 用 `waitForResponse` 等待 API 返回，禁止 `sleep()` |
| CI 失败排查 | `trace: 'on-first-retry'`，可用 `npx playwright show-trace` 回放 |

## 9. Playwright 配置概要

```js
// e2e/playwright.config.js
module.exports = {
  webServer: {
    command: 'python cosmic_web.py --test',
    port: 5000,
    timeout: 30 * 1000,
    reuseExistingServer: !process.env.CI,
  },
  testDir: './tests',
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://localhost:5000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
};
```

## 10. 首期测试用例清单

| # | 所属文件 | 测试用例 | 验证点 | 优先级 |
|:---|:---|:---|:---|:---:|
| 1 | auth.spec.js | 登录成功 | 表单提交 → 跳转首页 → 显示用户名 | P0 |
| 2 | auth.spec.js | 登录失败 - 错误密码 | 显示错误提示，不跳转 | P1 |
| 3 | cosmic-metric.spec.js | COSMIC 度量全流程 | 上传文档 → 选方法 → 执行 → 表格有结果 → 导出 Excel | P0 |
| 4 | nesma-metric.spec.js | NESMA 度量全流程 | 同 COSMIC 但验证 NESMA 特有字段 | P0 |
| 5 | knowledge-hub.spec.js | 知识库文档上传 | 上传 → 解析状态变化 → 可检索 | P1 |
| 6 | knowledge-hub.spec.js | 知识库对话 | 发送消息 → 收到 AI 回复 | P1 |

P0 = 每次提交必须跑，P1 = 每日 / PR 时跑。

## 11. 前置依赖：cosmic_web.py 测试模式

为实现测试数据库隔离，`cosmic_web.py` 需增加 `--test` 命令行参数：

- 不带 `--test`：连接 `data/pilot.db`（现有行为，不改）
- 带 `--test`：连接 `data/pilot_test.db`，调用前确保 `seed.py` 已执行

实现方式：在 `cosmic_web.py` 的数据库连接初始化处读取 `sys.argv`，选择对应的数据库路径。这是对主程序的最小侵入性改动（约 3-5 行代码）。

## 12. 测试数据文件清单

`data/test_fixtures/` 目录需准备以下文件（作为测试资产随 git 提交）：

| 文件 | 用途 | 格式 |
|:---|:---|:---|
| `sample_requirement.docx` | COSMIC/NESMA 度量测试 | 包含一个简单需求描述的 .docx |
| `sample_spec.pdf` | 知识库文档上传测试 | 可解析的 PDF 文件 |

## 13. 演进路径

1. **v1（本期）**：6 个核心场景 + debug.py + fixtures 体系
2. **v2**：扩展到管理后台（用户管理、配置管理）
3. **v3**：引入契约文件（evidence.json），供下游消费 + CI 集成
