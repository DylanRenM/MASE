---
name: "code-review"
description: "多轮多代理并行代码评审，含 spec 合规检查与代码规约检查。v2"
---

# 多轮代码评审与 Bug 修复

基于"多代理并行审计 + 迭代修复 + 重审验证"策略，系统性发现并修复代码缺陷。

> 方法论验证数据：CMMI-EXAM 项目 6 轮评审，发现 156 个问题，收敛曲线 85→32→6→0，覆盖率 99%。

## 触发条件

用户说"评审代码"、"代码走查"、"review"、"找 bug"、"检查代码"等时调用本 Skill。

## 核心策略

### 三阶段流程

```
发现阶段 → 修复阶段 → 验证阶段
 (并行代理)  (按优先级)  (跑测试)
```

### 阶段一：发现（并行子代理审计）

将待审查文件按**模块分层**拆分为 4-5 组，每组启动一个 `general_purpose_task` 子代理并行审查。

**分组原则**：

| 组 | 覆盖范围 | 关注点 |
|----|---------|--------|
| 第 1 组 | 入口/路由/中间件 | 认证覆盖、路由注册、请求格式匹配、状态码规范 |
| 第 2 组 | 业务核心逻辑（service/manager） | 事务完整性、并发锁、边界条件、异常降级 |
| 第 3 组 | 外部集成（LLM/RAG/API调用） | 配置穿透、超时控制、错误脱敏、重试逻辑 |
| 第 4 组 | 前端 UI（组件/事件/渲染） | XSS 防护、事件生命周期、空值防护、状态一致性 |
| 第 5 组 | 数据存储/配置文件 | 密码哈希、连接池、原子写入、硬编码密钥 |
| 第 6 组 | spec 合规检查（specs/{capability}/spec.md） | 对照 spec 逐条核对实现是否满足要求，标注 covered/missing/deviated |
| 第 7 组 | 代码规约检查 | 命名规范、错误处理、日志规范、导入规范、函数复杂度 |

**每个子代理的审查清单**：

**通用**：
- Null/undefined 空值安全（`request.get_json()` 返回值判空）
- 错误处理完整性（`except Exception: pass` 静默吞异常）
- 死代码和未使用的 import
- 重复代码和过长函数 (>50行)

**Spec 合规（对照 specs/{capability}/spec.md）**：
- 读取 openspec/changes/ 下对应项目的 specs/ 目录
- 逐条核对每个 Requirement 和 Scenario 是否有对应实现
- 输出格式：`SPEC_GAP|[capability]|[requirement]|[scenario]|[status: covered/missing/deviated]|[detail]`

**代码规约（命名/错误处理/日志/导入/复杂度）**：
- 命名规范：文件名 snake_case/PascalCase、函数名动词开头、类名 PascalCase
- 错误处理：无裸 except: pass、异常类型具体化、错误信息含上下文
- 日志规范：级别正确（ERROR/WARN/INFO/DEBUG）、无敏感信息明文
- 导入规范：标准库→第三方→本地 顺序、无未使用 import、无循环依赖
- 函数复杂度：单函数不超过 50 行、圈复杂度不超过 10

输出格式：`CONVENTION|[filepath]|[line]|[rule]|[severity: high/medium/low]|[suggestion]`

**安全（独立维度，不可省略）**：
- 认证覆盖：每个受保护端点都有 `session.get('user_id')` 检查
- 授权正确：用户只能操作自己的资源（非 IDOR）
- XSS 防护：所有用户输入经 `escapeHtml` 后再拼接到 DOM
- 密码安全：使用 pbkdf2_hmac / bcrypt，非 SHA256 + 无盐
- API 密钥硬编码：检查源码和配置文件

**事务与并发**：
- 多语句写操作有显式 BEGIN/COMMIT/ROLLBACK
- 共享状态访问在锁内（Python: `threading.Lock`）
- 无 check-then-act 竞态（TOCTOU）
- `message_count += 1` 等非原子操作

**前后端协议**：
- 请求格式一致：前端 `Content-Type` ⇔ 后端解析方式
- 响应字段完整：后端返回 ⊇ 前端使用
- 路由匹配：前端 `fetch` 路径 ⊆ 后端路由（含 HTTP 方法匹配）
- 字段名一致：生产者字段名 == 消费者字段名

**前端特有**：
- 事件监听器是否在组件销毁时移除
- `innerHTML` / `insertAdjacentHTML` 是否经 `escapeHtml` 消毒
- `data-*` 属性中单引号是否转义
- `fetch` 调用是否有响应状态码检查

**Python 后端特有**：
- `import threading` 是否遗漏（导致 `NameError`）
- `litellm` 全局状态是否被多实例覆盖
- LRU 缓存是否在数据更新后失效（`cache_clear()`）
- 文件写入是否原子（`tmp + rename` / `fsync`）

**输出格式要求每个子代理使用**：
```
ISSUE|[filepath]|[line]|[title]|[severity: critical/high/medium/low]|[suggestion]
```

### 阶段二：修复（按严重度排序）

1. **Critical/High** 优先修复：认证漏洞、XSS、数据丢失、崩溃、密码安全
2. **Medium** 次之：竞态条件、事务缺失、事件泄漏、配置穿透
3. **Low** 最后：死代码、代码异味、重复常量、UI 细节偏差

每次修复后更新 TODO 列表追踪进度。

**重要规则**：
- 修复代码和回归测试必须在同一次修改中提交
- 跨界修改（前端+后端同时动）必须有端到端验证
- 不要为了"一致性"修改外部 API 的协议约定（如 litellm 的 `provider/model` 格式）

### 阶段三：验证

1. 运行全量测试：后端 `python3 -m pytest tests/ -q`，前端 `npm test -- --run`
2. 只有预先存在的失败（如需要运行中服务端的集成测试）可以接受
3. 新引入的测试失败必须立即修复
4. 修复 bug 后检查是否引入回归（运行涉及模块的全部测试）

### 多轮迭代

完成一轮后，用**不同角度**重新审查：

| 轮次 | 审查角度 | 目标覆盖率 |
|------|---------|-----------|
| R1 | 功能完整性 + spec 合规性 + 代码规约：对照 spec 逐条验证功能是否实现，同时检查实现与 spec 描述一致、代码符合规约 | ~40% |
| R2 | 接口协议：前后端字段名、路由、Content-Type 一致性 | ~60% |
| R3 | 细节对账：CSS/文案/时间格式/动画与 spec 精确一致 | ~75% |
| R4 | **安全纵深防御**：认证/XSS/密码/事务/并发全量扫描 | ~95% |
| R5 | 修复残留：复查上一轮 P0/P1 修复，扫描相邻模块回归 | ~98% |
| R6 | 最终验证：跨模块协议一致性（base64/JSON/路由） | ~99% |

**终止条件**：
1. P0 问题数为 0
2. 连续两轮发现新问题 < 5 个
3. 新问题中超过一半是上一轮修复引入的回归（边际收益为负）

> 数据参考：R4 是性价比最高的轮次（单轮发现占总量的 55%）。R5 后边际收益急剧下降。R6 后不应继续全量审查。

## 快速走查步骤（轻量模式）

当项目需要快速审查（1-2 轮）时，按以下 4 步执行：

### 第一步：结构扫描（5 分钟）
```
□ Grep 'marked\.parse(' → 检查是否都有 sanitize
□ Grep 'innerHTML\s*=\s*`' → 检查模板字面量中的变量是否已转义
□ Grep "hash_password\('[a-z0-9]+'\)" → 检查硬编码密码
□ Grep "secret_key\s*=\s*['\"]" → 检查硬编码密钥
□ Grep 'except\s*:' → 检查裸 except 是否合理
□ 检查所有路由是否都有认证保护
```

### 第二步：同类文件对比（10 分钟）
```
□ 如果同一个功能有两个实现文件（如 main.py 和 blueprints/）
  → 逐函数对比，修复差异
□ 如果同一个模式出现在 3+ 个文件中（如 parseMarkdown）
  → 确认是否已抽取到公共模块
□ 如果两个文件修复了相同的 Bug
  → 检查第三个文件是否有同样的问题
```

### 第三步：数据流追查（15 分钟）
```
□ 选取一个核心功能（如上传文件 → 处理 → 前端展示）
□ 全链路追踪数据：表单输入 → 后端处理 → 数据库 → API响应 → 前端渲染
□ 在每一步检查：转义、验证、字段名一致性
```

### 第四步：边界条件（10 分钟）
```
□ 并发场景：全局字典是否多线程安全
□ 异常路径：try 块中的资源是否在 finally 中释放
□ 空值处理：null/undefined/[] 是否能正常降级
```

### 走查优先级矩阵
| | XSS | 密码 | 认证 | 逻辑 |
|---|---|---|---|---|
| 发现难度 | 中 | 低 | 低 | 高 |
| 危害程度 | 高 | 高 | 高 | 中 |
| 修复成本 | 低 | 低 | 低 | 中 |
| **优先修复** | ✅ | ✅ | ✅ | → |

## 严重度定义

| 级别 | 定义 | 前端示例 | 后端示例 |
|------|------|---------|---------|
| **Critical** | 运行时一定崩溃或数据损坏 | `useRef` 未导入导致白屏 | `import threading` 遗漏导致 `NameError` |
| **High** | 安全漏洞、认证绕过、数据泄露 | `innerHTML` 未消毒、XSS 可执行 | API 端点无认证、明文返回密钥 |
| **Medium** | 逻辑错误、竞态条件、事务缺失 | 事件监听器泄漏（每次渲染翻倍） | 多语句写操作无 BEGIN/COMMIT |
| **Low** | 死代码、性能退化、代码异味 | 未使用的变量、重复的 `escapeHtml` | `except: pass` 开关、循环内 import |
| **spec-gap** | spec 场景在实现中缺失 | — | 功能未按 spec 实现 |
| **convention** | 违反代码规约 | 文件名/函数名不符合规范 | 裸 except、import 顺序错误 |

## 审查分组 Prompt 模板（按项目语言适配）

### 通用 Prompt（自动适配语言）

```
You are a code reviewer. Review the following files for bugs, code smells, 
security issues, and best practice violations.

Files to review (read them fully before judging):
1. <file1>
2. <file2>
...

Focus on (adapt to the detected language — Python or JavaScript/TypeScript):

Universal:
- Null/undefined/None safety
- Missing authentication checks on API endpoints
- Hardcoded secrets (API keys, passwords)
- Error swallowing (bare except: pass / empty catch)
- Race conditions (missing transactions, missing locks)
- XSS vulnerabilities (user input concatenated into DOM)
- Dead code and O(n²) complexity

If spec files exist (openspec/changes/{change-name}/specs/):
- Check each Requirement has corresponding implementation
- Check each Scenario's Given/When/Then is covered
- Report as SPEC_GAP|... format

Code conventions:
- Naming: snake_case for Python, camelCase for JS/TS
- Error handling: no bare except: pass, specific exception types
- Logging: correct level usage, no secrets in logs
- Imports: stdlib → third-party → local order, no unused imports
- Function complexity: under 50 lines, cyclomatic complexity < 10

If Python:
- Missing `with threading.Lock`
- Missing explicit BEGIN/COMMIT/ROLLBACK on multi-statement writes
- request.get_json() return value not null-checked
- except Exception: pass (not even a log)
- SHA256 without salt for password hashing
- litellm global state mutation between instances
- LRU cache not invalidated after data updates

If JavaScript/TypeScript:
- Event listener not removed on component unmount
- innerHTML without escapeHtml sanitization
- data-* attribute injection (unescaped quotes)
- fetch without response status check
- Missing AbortController for fetch cleanup
- Stale closure in useCallback/useMemo

Output format (ONLY for real issues):
ISSUE|[filepath]|[line]|[title]|[severity: critical/high/medium/low]|[suggestion]

If NO issues: ALL_CLEAN

Be strict. Report genuine bugs, logic errors, security issues. 
Do not report style nits.
```

### 安全审查专用 Prompt（第四轮）

```
You are a SECURITY auditor. Perform a deep security review of the following files.
Focus ONLY on security vulnerabilities. Do NOT report code quality or style issues.

Files to review:
1. <file1>
2. <file2>
...

Checklist:
- Authentication: Every protected endpoint has session/user check. No IDOR.
- Authorization: Users can only access their own resources.
- XSS: All user input sanitized before DOM insertion. escapeHtml/textContent used.
- Password: pbkdf2/bcrypt with salt. No SHA256 unsalted. No hardcoded defaults.
- Secrets: No API keys/credentials in source code or config files.
- Injection: SQL injection, command injection, path traversal.
- Transaction: Multi-statement writes have BEGIN/COMMIT/ROLLBACK.
- Race: Shared state access under lock. No TOCTOU.
- Config: LLM parameters pass through to downstream API. No silent drop.
- Input: request.get_json() null-checked. File size limits. String length limits.

Output format:
VULN|[filepath]|[line]|[title]|[severity: critical/high/medium/low]|[exploit scenario]|[fix]

If NO vulnerabilities: SECURE
```

## 高频 Bug 模式速查

### Python 后端高频模式（CMMI-EXAM 项目 6 轮 156 问题提炼）

1. **`session.get('user_id')` 遗漏** → 未认证访问 → 每个端点必须显式检查或用 `@require_login` 装饰器
2. **`request.get_json()` 返回 None 未判空** → `.get()` 调用崩溃 → 加 `if not data: return error`
3. **多语句写操作无事务包裹** → 部分写入不一致 → 加 `BEGIN`/`COMMIT`/`ROLLBACK`
4. **`threading.Lock` 覆盖范围不足** → 竞态条件 → 锁覆盖整个 critical section
5. **`SHA256` 无盐 + 无迭代** → 彩虹表可破 → 改用 `pbkdf2_hmac(iterations=600000)`
6. **`litellm.api_key` 模块级赋值** → 多实例互相覆盖 → 在 `completion()` 调用中传 `api_key=`
7. **`except Exception: pass`** → 错误静默消失 → 至少 `print()` 或 `logging.error()`
8. **前后端编解码不一致** → 前端发 base64，后端当原始字节 → 统一约定并以回归测试固化
9. **LRU 缓存不失效** → 索引更新后返回旧结果 → `index_all` 后调 `cache_clear()`
10. **`deepseek-chat` vs `deepseek/deepseek-chat`** → litellm 要求 `provider/model` 前缀 → 后端统一加前缀，不要各调各的
11. **文件写入非原子** → 写一半崩溃文件损坏 → `tmp + rename` 或写后 `fsync`
12. **动态路径端点遗漏认证** → `/api/users/{username}/freeze` 类型路径 → 参数化测试确保不漏
13. **`is_archived = FALSE`** → SQLite 中 FALSE 被当字符串 → 用 `0` 或 `'false'`
14. **管理员无法知晓默认密码** → 首次部署无法登录 → 首次创建 Admin 时打印到控制台
15. **旧格式密码兼容路径** → SHA256 无盐可被彩虹表破解 → 旧密码验证后自动升级到 pbkdf2

### 前端高频模式（React/TS/JS）

1. **`addEventListener` / `removeEventListener` options 不匹配** → 内存泄漏
2. **`useCallback` 空依赖数组引用外部变量** → 闭包陷阱
3. **`.then()` 链未 `return` Promise** → 调用方 `await` 失效
4. **`fetch` 无 `AbortController`** → 组件卸载后 setState
5. **`dangerouslySetInnerHTML` 未经消毒** → XSS
6. **`marked.setOptions()` 模块级副作用** → 全局状态污染
7. **`data-*` 属性中单引号未转义** → `data-sources='[...]'` 被 JSON 中的引号破坏
8. **事件监听器重复绑定** → 每次 `renderSessions` 添加新 listener → 仅对新增元素绑定
9. **附件 `content` 在发送前被清空** → 先捕获数据再清空引用
10. **`showToast` 未判空 container** → `null.appendChild()` 崩溃
11. **正则 `[→>]` 误匹配比较运算符** → 业务逻辑错误
12. **`JSON.parse("null")` 返回 `null` 未守卫** → TypeError 崩溃
13. **`useState` 初始化器无 try-catch** → localStorage 损坏时页面白屏
14. **`e.touches[0]` 无长度检查** → 触摸模拟崩溃

## 测试驱动审查（评审后必做）

完成评审和修复后，必须补充对应层级的自动化测试：

| 发现的 bug 类型 | 必须补充的测试层级 |
|----------------|-------------------|
| 认证绕过 | API 集成测试（参数化 401 断言） |
| 字段漂移/协议不匹配 | 契约测试（JSON Schema 校验） |
| XSS 注入 | XSS 防护测试（payload 集验证 escapeHtml） |
| 事务缺失 | 并发测试（多线程操作同一资源） |
| 空值崩溃 | 边界测试（None/空字符串/空数组） |
| 编码断裂 | 回归测试（前后端编解码往返验证） |
| 密码安全 | 单元测试（哈希算法 + 盐 + 迭代次数断言） |
| 事件泄漏 | 前端 E2E 测试（模拟交互后验证 DOM 状态） |

## 收敛参考数据

| 轮次 | 发现数 | 累计覆盖率 | 边际收益 |
|------|--------|-----------|---------|
| R1 | ~12 | ~40% | 高 — 功能缺失一次性暴露 |
| R2 | ~8 | ~60% | 高 — 协议断裂一次性暴露 |
| R3 | ~13 | ~75% | 中 — 细节偏差开始稀疏 |
| R4 | ~85 | ~95% | **最高** — 安全视角挖出全部历史债务 |
| R5 | ~32 | ~98% | 低 — 修复残留，不足R4的一半 |
| R6 | ~6 | ~99% | 极低 — 仅剩回归问题 |

> R4 不应跳过。R7 不应启动。
