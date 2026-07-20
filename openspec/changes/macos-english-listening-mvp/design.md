## Context

“磨耳朵”是一个 macOS 13+ 本地英文文档循环听读应用。Proposal 和交互原型已经确认，Design L1 已验证 SwiftUI、系统 TTS、PDFKit、ZIPFoundation、严格英文过滤、文件监控、本地 `.app` 打包、ad-hoc 签名和 Accessibility 自动化。

项目采用仅本地 Git 的交付方式，不依赖外部代码仓库或云端 CI。当前 MASE 仓库同时承载框架代码，因此产品代码必须保持独立边界，且不得放入 `docs/`。

## Goals / Non-Goals

**Goals:**

- 建立可由 SwiftPM 构建的 macOS SwiftUI 应用结构；
- 用纯状态转换隔离播放业务规则与系统副作用；
- 对文档解析、过滤、TTS、时钟和文件监控定义可替换协议；
- 通过 Swift 单元/集成/契约测试和 Accessibility E2E 满足 MASE 门禁；
- 在 20MB 文件约束内保持 UI 响应；
- 保持本地数据、最小权限和安全文档解析。

**Non-Goals:**

- App Store 归档、Developer ID、公证或自动更新；
- XCUITest、外部 CI、远端代码托管；
- Windows、iOS、Android；
- OCR、旧版 DOC、音色选择、循环次数、会话恢复。

## Decisions

### D1：SwiftPM 作为唯一构建入口

产品使用根级 `Package.swift`，产品模块路径配置到 `src/morerduo/`，应用 target 位于 `src/morerduo_app/`，测试位于 `tests/`。本地脚本负责将 release executable 组装为 `.app`。

**替代方案：** Xcode project 提供成熟签名与 XCUITest，但本机空间不足且 MVP 不公开发布；XcodeGen/Tuist 会增加不必要依赖。

### D2：Reducer + Effect 架构

`ReadingSessionReducer` 是纯函数：输入当前状态与事件，输出新状态和 effect。`SessionCoordinator` 在 `@MainActor` 串行执行 effect，再把系统回调转换为事件。

**替代方案：** 直接在 SwiftUI `ObservableObject` 中调用 AVFoundation 较快，但难以验证快速重复操作、计时冻结和竞态不变量。

### D3：协议隔离系统框架

定义 `DocumentLoading`、`SpeechSynthesizing`、`ReadingClock`、`SourceMonitoring`。生产适配器使用 PDFKit、ZIPFoundation、AVFoundation、ContinuousClock 和 DispatchSource；测试注入 fake。

### D4：按段落组织 TTS 与进度

解析器输出非空英文段落。TTS 每次朗读一个段落，delegate 字符范围记录段内位置。速度不变时原生继续；暂停后变速时停止旧 utterance，并从未读后缀创建新 utterance。

### D5：只累计单调有效朗读时间

定时器保存累计 `Duration` 和当前播放片段开始 instant；暂停先结算再冻结。UI 刷新 tick 不是时间真值，避免后台调度延迟引起漂移。

### D6：Accessibility E2E 替代 XCUITest

所有交互控件提供稳定 `AXIdentifier`。本地 E2E runner 启动 ad-hoc signed app，通过 Accessibility 执行 P0 流程。每个 spec 建立文件沙箱快照，并在结束时恢复、校验。

### D7：目标式 DOCX 提取

生产实现只读取 ZIP 中的 `word/document.xml`，检查 entry 路径和解压大小，不展开宏、嵌入对象或其他 entry，降低 Zip Slip 与 zip bomb 风险。

## Risks / Trade-offs

- **Swift compiler 与默认 SDK 补丁不匹配** → 构建脚本显式设置现有 15.4 SDK，并在启动时故障快速暴露。
- **复杂 PDF 阅读顺序不稳定** → 按页使用 PDFKit 原生顺序，复杂多栏列为 P2，不承诺视觉顺序重建。
- **不同 voice 的字符回调粒度不同** → 只记录已回调安全边界，恢复允许回退到最近安全边界，不跳过文本。
- **Accessibility 权限可能未开启** → E2E 前置检查权限，缺失时给出明确设置指引并阻断，而非假通过。
- **ad-hoc 签名不适合公开分发** → MVP 明确限定本机使用；公开发布另开 change。
- **20MB 文档解析可能耗时** → 所有读取、解压、PDF 提取和过滤均离开主线程，结果以单次事务提交。

## Migration Plan

1. Design L2 完成 specs、contract 和 tasks。
2. Build 首任务创建 SwiftPM 产品骨架和本地 `.app` 脚本。
3. 按 capability 逐个 TDD 实现，不迁移现有 POC 到生产目录，只复用已验证方案。
4. P0 E2E 全部通过后进入 Verify。

回滚方式：每个 capability 独立本地 commit；回滚前按 R09 创建备份标签。产品不持久化数据，因此不存在数据迁移。

## Open Questions

无阻断性开放问题。复杂 TXT 编码、DOCX 表格顺序及多栏 PDF 作为 P2 探索项，不改变 MVP 契约。
