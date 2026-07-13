---
name: webapp-testing
description: Toolkit for E2E testing & debugging of local web applications using Playwright. Supports writing E2E regression tests, executing full regression suites, verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.
license: Complete terms in LICENSE.txt
---

# Web Application Testing

To test local web applications, write native Python Playwright scripts.

**Helper Scripts Available**:
- `scripts/with_server.py` - Manages server lifecycle (supports multiple servers)

**Always run scripts with `--help` first** to see usage. DO NOT read the source until you try running the script first and find that a customized solution is abslutely necessary. These scripts can be very large and thus pollute your context window. They exist to be called directly as black-box scripts rather than ingested into your context window.

## Decision Tree: Choosing Your Approach

```
User task → MASE 阶段?
    ├─ Build（写 E2E 测试）→ 读 E2E Test Authoring 章节
    ├─ Verify（执行回归）→ 读 E2E Regression Execution 章节
    └─ 调试（原有场景）→ 进入原有 Decision Tree:
        Is it static HTML?
            ├─ Yes → Read HTML file directly to identify selectors
            │         ├─ Success → Write Playwright script using selectors
            │         └─ Fails/Incomplete → Treat as dynamic (below)
            │
            └─ No (dynamic webapp) → Is the server already running?
                ├─ No → Run: python scripts/with_server.py --help
                │        Then use the helper + write simplified Playwright script
                │
                └─ Yes → Reconnaissance-then-action:
                    1. Navigate and wait for networkidle
                    2. Take screenshot or inspect DOM
                    3. Identify selectors from rendered state
                    4. Execute actions with discovered selectors
```

## Example: Using with_server.py

To start a server, run `--help` first, then use the helper:

**Single server:**
```bash
python scripts/with_server.py --server "npm run dev" --port 5173 -- python your_automation.py
```

**Multiple servers (e.g., backend + frontend):**
```bash
python scripts/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python your_automation.py
```

To create an automation script, include only Playwright logic (servers are managed automatically):
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True) # Always launch chromium in headless mode
    page = browser.new_page()
    page.goto('http://localhost:5173') # Server already running and ready
    page.wait_for_load_state('networkidle') # CRITICAL: Wait for JS to execute
    # ... your automation logic
    browser.close()
```

## Reconnaissance-Then-Action Pattern

1. **Inspect rendered DOM**:
   ```python
   page.screenshot(path='/tmp/inspect.png', full_page=True)
   content = page.content()
   page.locator('button').all()
   ```

2. **Identify selectors** from inspection results

3. **Execute actions** using discovered selectors

## Common Pitfall

❌ **Don't** inspect the DOM before waiting for `networkidle` on dynamic apps
✅ **Do** wait for `page.wait_for_load_state('networkidle')` before inspection

## Best Practices

- **Use bundled scripts as black boxes** - To accomplish a task, consider whether one of the scripts available in `scripts/` can help. These scripts handle common, complex workflows reliably without cluttering the context window. Use `--help` to see usage, then invoke directly. 
- Use `sync_playwright()` for synchronous scripts
- Always close the browser when done
- Use descriptive selectors: `text=`, `role=`, CSS selectors, or IDs
- Add appropriate waits: `page.wait_for_selector()` or `page.wait_for_timeout()`

### E2E 专属最佳实践
- E2E 测试不修改 fixtures 数据（只读操作）
- 禁止 `sleep()`，用 `waitForResponse` 等待 API
- 每个 spec 文件 `beforeAll` 重新跑 `seed.py`
- `trace: 'on-first-retry'` 必须开启

## E2E Test Authoring

### 元素定位规范
<详见 `playwright-standards.md` 参考文件，5 级优先级：getByRole → getByLabel → getByPlaceholder → getByText → getByTestId>

### Page Object Model
每页一个 class，测试用例不裸写选择器。封装在 `e2e/helpers/pages.js`。

### fixtures 数据准备规范
`seed.py` 生成 `fixtures.json`，测试只读，不修改 fixtures 数据。

### 场景优先级标注
使用 Playwright tags 标注优先级，对应 proposal.md 中的 P0/P1/P2：

```javascript
test.describe('@P0 核心业务流程', () => {
  test('用户登录全流程', async ({ page }) => { ... });
});

test.describe('@P1 重要辅助功能', () => {
  test('知识库文档管理', async ({ page }) => { ... });
});
```

## E2E Regression Execution

### 执行命令
```bash
# 全量 E2E 回归
npx playwright test

# 仅执行 P0 核心场景（Verify 门禁）
npx playwright test --grep @P0

# 执行 P0 + P1
npx playwright test --grep "@P0|@P1"

# 输出 JSON 报告
npx playwright test --grep @P0 --reporter=json > e2e-report.json
```

### 报告查看
```bash
# HTML 报告
npx playwright show-report

# trace 回放（排查失败用例）
npx playwright show-trace <trace-path>
```

### 失败排查流程
1. 截图（screenshot）→ 查看页面状态
2. DOM（page.content()）→ 检查元素是否存在
3. trace（show-trace）→ 逐帧回放操作

## MASE Integration

### Build 阶段
- 每实现一个 P0 场景功能，同步编写对应 E2E 测试
- Capability 的所有 P0 场景 E2E 测试通过后，方可进入 Verify 阶段

### Verify 阶段
- 执行 `npx playwright test --grep @P0` 必须 100% 通过
- 生成 E2E 测试报告（含通过率、执行时间）
- 失败用例启动 bug-fixer 微循环修复

### Retro 阶段
- 从 `e2e-report.json` 提取覆盖率、执行时间等指标
- 写入复盘报告 `## 八、E2E 测试指标` 章节

## Reference Files

- **examples/** - Examples showing common patterns:
  - `element_discovery.py` - Discovering buttons, links, and inputs on a page
  - `static_html_automation.py` - Using file:// URLs for local HTML
  - `console_logging.py` - Capturing console logs during automation
- **playwright-standards.md** - Element locator priority rules and best practices