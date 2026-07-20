## 1. 项目骨架与测试基础

- [x] 1.1 创建根级 SwiftPM manifest，配置 `MorerduoKit`、`MorerduoApp`、unit/integration/contract test 和 E2E runner targets（依赖：无，复杂度：M）
- [x] 1.2 创建 `src/morerduo` 七个 capability 目录、`src/morerduo_app` 和镜像 `tests/` 目录（依赖：1.1，复杂度：S）
- [x] 1.3 编写本地 app bundle、ad-hoc codesign 与统一 verify 脚本，并为脚本失败路径写测试（依赖：1.1，复杂度：M）
- [x] 1.4 先写 strict/relaxed `Contract` 工具测试，再实现 require/ensure/invariantCheck（依赖：1.1，契约：运行时策略，复杂度：M）
- [x] 1.5 先写 E2E 沙箱快照/恢复/一致性测试，再实现 `NativeSandbox`（依赖：1.1，复杂度：M）
- [x] 1.6 先写 AXIdentifier 查找与权限失败测试，再实现 `MorerduoPage` Accessibility driver（依赖：1.3，复杂度：M）
- [x] 1.7 运行骨架测试、格式检查和构建脚本，完成基础设施代码评审与本地 commit（依赖：1.2–1.6，复杂度：S）

## 2. document-ingestion capability

- [x] 2.1 复用检查：验证 Foundation resource values、PDFKit、ZIPFoundation 0.9.20 和 XMLParser API 满足 spec/contract（依赖：1.7，复杂度：S）
- [x] 2.2 先写 `FilePolicy` 合法格式、regular/readable、20MB 边界与错误契约测试（依赖：2.1，契约：FilePolicy，复杂度：M）
- [x] 2.3 实现 `FilePolicy`、`DocumentKind`、`SourceFingerprint` 和 typed `DocumentLoadError`（依赖：2.2，复杂度：M）
- [x] 2.4 先写 UTF-8 TXT 正常、空文件和不可读 fixture 行为测试，再实现 `TXTParser`（依赖：2.3，复杂度：M）
- [x] 2.5 先写 DOCX 正常、损坏、缺少 document.xml、50MB 解压上限和恶意 entry 测试，再实现目标式 `DOCXParser`（依赖：2.3，复杂度：L）
- [x] 2.6 先写文本 PDF、扫描 PDF、损坏 PDF 和多页顺序测试，再实现 `PDFParser`（依赖：2.3，复杂度：M）
- [x] 2.7 先写原子发布/中途失败回到 idle 与资源清理集成测试，再实现 `DocumentLoader` 分派与后台执行（依赖：2.4–2.6，契约：DocumentLoading，复杂度：M）
- [x] 2.8 运行单元、集成、契约测试；执行解析安全扫描和代码评审；本地 commit `feat(document-ingestion)`（依赖：2.7，复杂度：S）

## 3. english-content-filtering capability

- [x] 3.1 复用检查：对照 POC ASCII byte scan，确认不引入正则/第三方过滤库（依赖：2.8，复杂度：S）
- [x] 3.2 先写混合 Unicode、数字标点、连续空白、空段落、脚本文本和确定性契约测试（依赖：3.1，契约：EnglishFiltering，复杂度：M）
- [x] 3.3 实现 `RawParagraph`、`EnglishParagraph` 与 O(n) `EnglishTextFilter`（依赖：3.2，复杂度：M）
- [x] 3.4 先写 18–20MB 性能与 MainActor 非阻塞测试，再实现后台过滤编排（依赖：3.3，复杂度：M）
- [x] 3.5 运行单元、性能、契约测试；执行内容安全评审；本地 commit `feat(english-filtering)`（依赖：3.4，复杂度：S）

## 4. reading-progress capability

- [x] 4.1 复用检查：确认 prefix sums + UTF-16 cursor 与 AVSpeech range 兼容（依赖：3.5，复杂度：S）
- [x] 4.2 先写 idle、段内推进、段落切换、暂停、停止、循环和越界 cursor 契约测试（依赖：4.1，契约：ProgressCalculator，复杂度：M）
- [x] 4.3 实现 `ReadingCursor`、段落 prefix metadata、`ReadingProgress` 和 O(1) calculator（依赖：4.2，复杂度：M）
- [x] 4.4 运行单元/契约测试，完成纯函数代码评审，本地 commit `feat(reading-progress)`（依赖：4.3，复杂度：S）

## 5. active-reading-timer capability

- [x] 5.1 复用检查：验证 `ContinuousClock`/`Duration` API 与 POC 工具链兼容（依赖：4.4，复杂度：S）
- [x] 5.2 先写 nil、1、240、非法整数/小数的 timer configuration 契约测试（依赖：5.1，复杂度：S）
- [x] 5.3 实现 `TimerConfiguration` typed validation（依赖：5.2，复杂度：S）
- [x] 5.4 先写 fake clock 下 playing 累计、pause/prompt 冻结、resume、stop clear 和单次 expiry 测试（依赖：5.3，契约：active timer，复杂度：M）
- [x] 5.5 实现 `ActiveTimeAccumulator`、clock protocol 和 expiry token 去重（依赖：5.4，复杂度：M）
- [x] 5.6 运行单元/契约/竞态测试，完成计时评审，本地 commit `feat(active-reading-timer)`（依赖：5.5，复杂度：S）

## 6. session-lifecycle capability

- [x] 6.1 复用检查：确认 reducer/effect 模式不引入外部状态框架（依赖：5.6，复杂度：S）
- [x] 6.2 先写六种 mode、state constructors 和全部模块不变量测试（依赖：6.1，契约：session invariant，复杂度：M）
- [x] 6.3 实现 `ReadingSessionState`、event、effect、transition value types（依赖：6.2，复杂度：M）
- [x] 6.4 先写主流程、停止/到期同义、换文件、重启、非法事件和重复事件 reducer 测试（依赖：6.3，复杂度：L）
- [x] 6.5 实现纯 `ReadingSessionReducer` 与 strict/relaxed invariant handling（依赖：6.4，契约：ReadingSessionReducing，复杂度：L）
- [x] 6.6 先写 fake adapters 下 effect 顺序、失败恢复、迟到 token 和快速事件集成测试（依赖：6.5，复杂度：L）
- [x] 6.7 实现 `SessionCoordinator @MainActor` 的串行 effect 执行与 cancellation（依赖：6.6，复杂度：L）
- [x] 6.8 运行 reducer 穷举/集成/契约测试，完成并发评审，本地 commit `feat(session-lifecycle)`（依赖：6.7，复杂度：S）

## 7. speech-playback-control capability

- [x] 7.1 复用检查：验证 AVSpeechSynthesizer buffer、speaker、range、rate POC 与生产协议映射（依赖：6.8，复杂度：S）
- [x] 7.2 先写 `SpeechRequest` 英文字符、offset、speed 和单 active request 契约测试（依赖：7.1，复杂度：M）
- [x] 7.3 实现 speech public types、三档 rate 集中配置和 fake speech engine（依赖：7.2，复杂度：M）
- [x] 7.4 先写正常播放、range 映射、段落完成、最后段循环、stop 迟到回调，以及同 session 内重复/旧 utterance callback 测试（依赖：7.3，复杂度：L）
- [x] 7.5 实现 `AVSpeechEngine` delegate adapter，并以 session token + active utterance/request identity 双重隔离回调（依赖：7.4，复杂度：L）
- [x] 7.6 先写暂停原速继续、暂停变速后缀重建和不得跳词测试，再实现相应控制（依赖：7.5，复杂度：L）
- [x] 7.7 运行 silent 自动化和独立 audible 冒烟；完成系统适配器评审，本地 commit `feat(speech-control)`（依赖：7.6，复杂度：M）

## 8. source-file-monitoring capability

- [x] 8.1 复用检查：验证 DispatchSource write/atomic replacement POC 与生产事件集（依赖：7.7，复杂度：S）
- [x] 8.2 先写 start/stop、单 active source、5 秒约束、token 和 prompt 去重契约测试（依赖：8.1，复杂度：M）
- [x] 8.3 实现 `DispatchSourceFileMonitor` 的 descriptor 生命周期和事件映射（依赖：8.2，复杂度：L）
- [x] 8.4 先写 rename/delete rearm、迟到回调、ready 后删除播放失败集成测试，再实现协调逻辑（依赖：8.3，复杂度：L）
- [x] 8.5 先写 reload success/failure、continue old 与计时冻结 reducer/集成测试，再实现分支 effects（依赖：8.4，复杂度：M）
- [x] 8.6 运行真实沙箱文件修改测试，完成 descriptor/竞态安全评审，本地 commit `feat(source-monitoring)`（依赖：8.5，复杂度：S）

## 9. SwiftUI 应用集成

- [x] 9.1 复用检查：对照已确认交互原型和 SwiftUI POC，列出可直接复用布局/AXIdentifier 决策（依赖：8.6，复杂度：S）
- [x] 9.2 先写 `AppViewState` 映射测试，再实现主窗口 view model 投影（依赖：9.1，复杂度：M）
- [x] 9.3 先写 Accessibility identifier 契约测试，再实现文件区、进度区、播放/停止控制（依赖：9.2，复杂度：M）
- [x] 9.4 实现速度 segmented control、整数定时输入、disabled 状态和错误提示（依赖：9.3，复杂度：M）
- [x] 9.5 实现源文件修改确认弹层和 reload/continue 交互（依赖：9.4，复杂度：M）
- [x] 9.6 实现 macOS fileImporter、应用终止清理和首次启动 idle（依赖：9.5，复杂度：M）
- [x] 9.7 执行 frontend-design 评审：层级、状态可见性、键盘/VoiceOver、响应式最小窗口（依赖：9.6，复杂度：M）
- [x] 9.8 运行 UI 集成测试和手工功能走查，本地 commit `feat(morerduo-app)`（依赖：9.7，复杂度：S）

## 10. P0/P1 E2E 与环境隔离

- [x] 10.1 为每个 E2E spec 实现 beforeAll snapshot、afterAll restore + byte-level verify（依赖：9.8，复杂度：M）
- [x] 10.2 自动化 P0 TXT、DOCX、文本 PDF 选择与不自动播放主流程（依赖：10.1，复杂度：L）
- [x] 10.3 自动化 P0 循环、暂停/继续、暂停变速、独立停止和进度语义（依赖：10.2，复杂度：L）
- [x] 10.4 自动化 P0 严格过滤、无英文内容、脚本文本不执行（依赖：10.3，复杂度：M）
- [x] 10.5 自动化 P0 timer fake-clock 场景并保留真实最小计时冒烟（依赖：10.4，复杂度：M）
- [x] 10.6 自动化 P1 非法/损坏/超限/扫描 PDF 和文件删除场景（依赖：10.5，复杂度：L）
- [x] 10.7 自动化 P1 源文件原地修改、原子替换、reload/continue 分支（依赖：10.6，复杂度：L）
- [x] 10.8 自动化换文件、重启重置、快速控制和竞争边界场景（依赖：10.7，复杂度：L）
- [x] 10.9 运行全量 E2E，确认 P0 100%、P1 全通过、每个 sandbox 恢复一致（依赖：10.8，复杂度：M）

## 11. Build 完成门禁

- [x] 11.1 运行 unit + integration + contract + E2E + app bundle + codesign 全套验证（依赖：10.9，复杂度：M）
- [x] 11.2 执行 spec/contract/architecture 一致性代码评审并关闭全部发现项（依赖：11.1，复杂度：M）
- [x] 11.3 执行文件解析、归档、路径、日志隐私和无网络依赖安全扫描（依赖：11.2，复杂度：M）
- [x] 11.4 更新测试追踪矩阵，确认 36 requirements 和全部 P0/P1 场景均有自动化证据（依赖：11.3，复杂度：S）
- [x] 11.5 生成本地 `.app` 验收包和验证摘要，创建 Build 门禁本地 Conventional Commit（依赖：11.4，复杂度：S）

## Verification Checklist

- [x] 所有 7 个 capability 的 Gherkin scenarios 已覆盖
- [x] 所有 API 级 DbC 契约已翻译为 contract tests
- [x] P0 E2E 场景已分配且要求 100% 通过
- [x] 每个任务都具有明确依赖、完成证据和本地提交边界
- [x] 外部仓库、云端 CI、完整 Xcode 不属于 Build 前置依赖

## Planning Metadata

- 默认 Owner：Agent 3（A3）。
- 设计/UI/代码评审与安全扫描 Owner：Agent 4（A4）。
- 阶段门禁与豁免 Owner：Agent 1（A1）。
- 执行顺序：1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11；同一组内按任务编号和显式依赖顺序执行。
- 每个 capability 完成时创建本地 Conventional Commit；不向任何外部 remote 推送。
