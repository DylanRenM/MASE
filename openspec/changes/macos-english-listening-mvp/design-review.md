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
