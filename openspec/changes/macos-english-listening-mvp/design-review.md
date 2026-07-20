# Design L2 设计评审

> Change：`macos-english-listening-mvp`
>
> 日期：2026-07-20
>
> Reviewer：MASE Agent 4
>
> 结论：PASS（发现项已回改）

## 1. 评审范围

- `proposal.md` / 权威需求 v3；
- `tech-feasibility.md`；
- `design.md`、`architecture.md`、`detailed-design.md`；
- 7 个 capability specs；
- `contract.md`、`coding-standards.md`、`tasks.md`；
- 已确认交互原型 v2。

## 2. 发现与处理

### MAJOR-01：换文件失败语义不一致 — 已修复

- **Location**：`detailed-design.md` 文件加载管道、`document-ingestion/spec.md` 原子加载。
- **Problem**：初稿在新文件加载失败时保留旧文档，与“选择新文件即清除旧会话”不一致。
- **Fix**：选择新文件先停止/清除旧会话；新文件完整成功才发布，失败回到 idle；同步 contract 和 task。
- **Verification**：spec、detailed design、contract、task 四处语义一致。

### MAJOR-02：UI 状态与无障碍规范不足 — 已修复

- **Location**：`detailed-design.md`。
- **Problem**：初稿只有 E2E 定位策略，缺少窗口布局、各状态控件、焦点、键盘、VoiceOver 和 reduced-motion 规则。
- **Fix**：增加 SwiftUI 视觉与交互规范，明确已批准原型方向、最小窗口、状态矩阵、焦点顺序、快捷键、AXIdentifier、播报节流和性能边界。
- **Verification**：UI 规范覆盖 idle/loading/ready/playing/paused/prompt 全状态。

### MINOR-01：UI 层存在潜在重复状态投影 — 已修复

- **Location**：`architecture.md`。
- **Problem**：图中同时出现 AppViewModel 和 SessionCoordinator，可能形成双状态源。
- **Fix**：SessionCoordinator 直接暴露只读 view state；SwiftUI 不保留第二份业务状态。

### SUGGESTION-01：复杂排版兼容性 — 已接受为 P2

- **Location**：`tech-feasibility.md` / specs。
- **Problem**：多栏 PDF、DOCX 文本框/表格顺序可能与视觉顺序不同。
- **Decision**：维持系统/OOXML 原生顺序，列入 P2 探索，不扩大 MVP。

## 3. 架构质量

| 维度 | 结论 | 证据 |
|------|------|------|
| SRP / 高内聚 | PASS | 七个 capability 单一职责，UI/解析/TTS/时间/监控分离 |
| DIP / 受保护变化 | PASS | 四个系统能力以 protocol 隔离，fake 可注入 |
| 低耦合 | PASS | 系统 framework 只存在 adapter，不反向依赖 SwiftUI |
| KISS / YAGNI | PASS | 单进程、无数据库/网络/状态框架/工程生成器 |
| 状态一致性 | PASS | 纯 reducer + 单串行 coordinator + token 防迟到 callback |
| 安全 | PASS | 文件前置校验、DOCX 目标 entry/解压上限、无脚本/网络 |
| 可测试性 | PASS | pure core、fake clock/TTS/monitor、Accessibility page object |

## 4. 需求与契约一致性

- Proposal 的 7 个 capabilities 均有同名 spec。
- OpenSpec strict validation 通过，解析 36 条 ADDED requirements。
- 每条 requirement 至少一个四级 Scenario。
- API 级契约覆盖 DocumentLoading、EnglishFiltering、SpeechSynthesizing、SourceMonitoring、ReadingSessionReducing。
- 模块级不变量覆盖 7 个 capabilities。
- 高风险函数契约覆盖文件策略、DOCX、过滤、进度、时间和 reducer。
- tasks 明确引用 contract/TDD/E2E/评审/安全/commit。

## 5. 前端设计评审

| 维度 | 结论 | 说明 |
|------|------|------|
| 视觉方向 | PASS | 原生克制工作台，单一靛蓝强调，无 dashboard card 拼贴 |
| 信息层级 | PASS | 文件上下文 → 进度/主控制 → 速度/定时 |
| 状态可见性 | PASS | 六种业务状态的按钮、输入、modal 行为明确 |
| 键盘 | PASS | `⌘O`、Space、`⌘.` 与文本输入冲突规则明确 |
| Accessibility | PASS | label + AXIdentifier、焦点顺序、live announcement 节流 |
| reduced motion | PASS | 关闭非必要 motion，不影响状态反馈 |
| 性能 | PASS | UI 无文档解析；range callback UI 节流 ≤ 10Hz |

## 6. 门禁结论

无 BLOCKER、无未关闭 MAJOR。Design L2 资产可进入 master 合并检查；合并完成并经 Agent 1/用户确认后，才能把 `mase-state.yaml.phase` 更新为 `build`。

## 7. Build Capability 9 前端实现复核

日期：2026-07-20；范围：`src/morerduo/app_integration`、`src/morerduo_app` 和真实 ad-hoc signed `.app`。

| 维度 | 结论 | 实现证据 |
|------|------|----------|
| 层级与布局 | PASS | 单窗口文件→状态/进度/控制→设置层级；默认 760×640；系统将 500×400 请求钳制为 640×592（560 内容高度加标题栏） |
| 状态可见性 | PASS | `AppViewState` 单向投影六种 mode；停止始终占位；loading indicator、typed error alert、不可取消 reload sheet |
| 键盘与焦点 | PASS | `⌘O`、Space、`⌘.`；reload sheet 初始焦点在重新加载；主界面源码顺序即选择→播放→停止→速度→定时 |
| VoiceOver | PASS | 真实 AX 树可读取首屏 10 个稳定 identifier；idle 时文件/速度/定时 `AXEnabled=true`，播放/停止 `AXEnabled=false`；状态切换发送 announcement |
| 响应式与动效 | PASS | 内容最小 640×560、最大宽度 900；不使用非必要动画，系统 reduced-motion 下行为不变 |
| 性能 | PASS | 文档处理位于非 MainActor executor；业务 cursor 全量保留，UI 进度投影节流至最多 10Hz |
| 隐私与范围 | PASS | 不展示正文、不记录路径、不访问网络；无音色、循环次数、DOC/OCR 演示入口 |

实现复核发现并关闭 `AXEnabled` modifier 顺序问题：将 `.disabled` 放在 identifier/快捷键 modifier 之后，release `.app` 复测播放与停止均正确暴露 disabled。
