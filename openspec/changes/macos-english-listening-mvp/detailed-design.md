---
change: "macos-english-listening-mvp"
created: "2026-07-20"
agent: "agent-3-development"
---

## 管道/流程设计

### 文件加载管道

```text
FileImporter URL
  → FilePolicy(extension, regular-file, ≤20MB, readable)
  → SourceFingerprint(size, modificationDate, fileResourceIdentifier)
  → ParserFactory
      ├─ TXTParser
      ├─ DOCXParser
      └─ PDFParser
  → [RawParagraph]
  → EnglishTextFilter
  → [EnglishParagraph]
  → LoadedDocument (atomic publish)
  → ready
```

任何步骤失败都返回 typed error。用户选择新文件时，coordinator 先停止旧 TTS/monitor、清除旧 document/cursor/累计时间并进入 loading；新文档只在全部步骤成功后一次性发布，失败则进入 idle，不保留旧会话，也不发布半解析结果。

### 播放管道

```text
play event
  → verify source still exists/readable
  → reducer: ready → playing + startSpeech/startClock/startMonitor
  → SpeechEngine speaks current paragraph suffix
  → willSpeak(range) → cursor event → progress update
  → paragraphFinished
      ├─ not last → next paragraph
      └─ last → cursor reset → first paragraph (continuous loop)
```

### 暂停、继续与变速

1. pause：结算 active duration；先关闭 progress callback generation，再以 immediate boundary 请求 speech pause；状态变为 paused。暂停期间收到或恢复后才处理的旧 generation range 一律丢弃。
2. paused changeSpeed：只更新配置并标记 `requiresUtteranceRebuild`。
3. resume：
   - 速度未变且系统仍保留 utterance：打开新的 progress generation 后调用 `continueSpeaking()`；
   - 速度改变：退休旧 utterance identity 并产生 cancelled 终态，停止旧 utterance，从 cursor 未读后缀创建新 utterance；若系统 stop 失败，不启动新 request，并允许 fail-safe cleanup 再次 stop。
4. 绝不跳过未确认朗读完成的字符；必要时允许重复最近一个词。
5. `willSpeak` range 必须位于 request UTF-16 边界内且下界单调不减；安全恢复位置等于 `baseUTF16Offset + requestRange.lowerBound`，倒退 range 被丢弃。

### 停止与定时到期

stop 和 timerExpired 归一为同一 reducer effect 集：

1. 停止 TTS；
2. 停止 monitor 和 clock tick；
3. 清除 accumulated active duration；
4. cursor 归零；
5. 保留 document、speed 和 timer configuration；
6. 回到 ready。

“清除计时”指清除本轮累计时间，用户配置值保留，便于再次播放同样时长。

### 文件变化流程

1. monitor 收到任何 vnode event 后生成去重 token。
2. coordinator 仅在 playing 状态显示一次确认弹层，并暂停业务朗读及计时。
3. 用户选择 reload：停止旧会话，重新走加载管道，成功后从头 playing；失败则显示错误并进入 idle。
4. 用户选择 continue：关闭弹层，从内存旧内容和原 cursor 继续。
5. 原子替换/rename/delete 后生产 monitor 先取消旧 DispatchSource，由 cancel handler 关闭旧 descriptor，再以 50ms 间隔持续尝试重新打开原路径，直到成功或 stop；source generation 隔离取消后的迟到回调。

## 项目结构

```text
Package.swift
src/
├── morerduo/
│   ├── document_ingestion/
│   ├── english_content_filtering/
│   ├── speech_playback_control/
│   ├── active_reading_timer/
│   ├── reading_progress/
│   ├── source_file_monitoring/
│   ├── session_lifecycle/
│   └── shared/
└── morerduo_app/
tests/
├── unit/                  # 镜像 src/morerduo capability
├── integration/
├── contract/
├── e2e/
└── fixtures/
scripts/
├── build-morerduo-app.sh
└── verify-morerduo.sh
dist/                      # gitignored build output
```

SwiftPM targets：

- `MorerduoKit`：path `src/morerduo`；
- `MorerduoApp` executable：path `src/morerduo_app`；
- `MorerduoUnitTests` executable test runner：path `tests/unit`；
- `MorerduoIntegrationTests` executable test runner：path `tests/integration`；
- `MorerduoContractTests` executable test runner：path `tests/contract`；
- `MorerduoE2ERunner` executable：path `tests/e2e`。

## 数据模型

| 类型 | 字段 | Swift 类型 | 说明 |
|------|------|------------|------|
| `DocumentKind` | value | enum `txt/docx/pdf` | 允许的文档种类 |
| `SourceFingerprint` | size, modifiedAt, resourceID | Int64, Date, Data? | 监控基线 |
| `RawParagraph` | text, ordinal | String, Int | 解析器原始输出 |
| `EnglishParagraph` | text, utf16Length, ordinal | String, Int, Int | 过滤后不可为空 |
| `LoadedDocument` | url, name, kind, fingerprint, paragraphs | value types | 只读会话文档 |
| `ReadingCursor` | paragraphIndex, utf16Offset | Int, Int | 恢复及进度位置 |
| `ReadingSpeed` | value | enum slow/normal/fast | 映射 rate 由适配器配置 |
| `TimerConfiguration` | limit | Duration? | nil 表示不限时 |
| `ActiveTimeState` | accumulated, segmentStartedAt | Duration, Instant? | 有效朗读时间真值 |
| `ReadingProgress` | fraction, current, total | Double, Int, Int | UI 只读投影 |
| `ReadingSessionState` | mode, document, cursor, speed, timer, prompt, error | struct | 唯一业务状态 |

### `SessionMode`

```swift
enum SessionMode: Equatable {
    case idle
    case loading
    case ready
    case playing
    case paused
    case awaitingReloadDecision
}
```

错误不是长期 mode；`UserFacingError` 与可恢复目标状态一起存储，dismiss 后回到 idle 或 ready。

## API 接口定义

### `DocumentLoading`

```swift
protocol DocumentLoading: Sendable {
    func load(url: URL) async throws -> ParsedDocument
}
```

错误枚举：`unsupportedFormat`、`notRegularFile`、`tooLarge`、`notReadable`、`emptyContent`、`corrupted`、`scannedPDF`、`unsupportedEncoding`、`noReadableEnglish`、`unsafeArchive`。

### `EnglishFiltering`

```swift
protocol EnglishFiltering: Sendable {
    func filter(_ paragraphs: [RawParagraph]) throws -> [EnglishParagraph]
}
```

### `SpeechSynthesizing`

```swift
@MainActor
protocol SpeechSynthesizing: Sendable {
    var events: AsyncStream<SpeechEvent> { get }
    func start(_ request: SpeechRequest) async throws
    func pause() async throws
    func resume(rebuildingWith request: SpeechRequest?) async throws
    func stop() async
}
```

`SpeechRequest` 包含 paragraph ID、未读后缀、原文 UTF-16 base offset、speed、session token 和 request token。`SpeechProgress.safeResumeUTF16Offset` 取当前 `willSpeak` range 映射回原段落后的 lower bound，而不是 range upper bound，以保证恢复最多重复当前未确认词且不跳词。delegate callback 必须同时匹配 active utterance identity、session token、request token 与 progress callback generation；同一 request 的已接受 range lower bound 必须单调不减。原速继续传 `nil` 并调用系统 `continueSpeaking()`，暂停变速则传新 request，先退休旧 identity、产生 cancelled 终态，再从安全 cursor 的未读后缀重建。系统 stop 失败时 replacement 不得启动，清理路径仍可重试 stop。

### `SourceMonitoring`

```swift
@MainActor
protocol SourceMonitoring: Sendable {
    var events: AsyncStream<SourceFileEvent> { get }
    func start(
        url: URL,
        fingerprint: SourceFingerprint,
        sessionToken: ReadingSessionToken
    ) async throws
    func stop() async
}
```

`SourceFileEvent` 携带非空 `SourceFileChange` option set 和启动时的 session token；公开策略常量 `SourceMonitorPolicy.maximumDetectionLatency` 固定为 5 秒。`DispatchSourceFileMonitor` 保持一个逻辑 monitoring request 和最多一个 active descriptor；每个 source 使用独立 generation，stop 先退休 generation 再 cancel，cancel handler 唯一负责 close。pause 停止 monitor；resume 先用无缓存 URL 重验 source，再恢复 speech/clock 并启动新 monitor，pause 前已排队的 source callback 显式忽略。业务 reducer 只在 matching playing session 接受首个 change 并进入 `awaitingReloadDecision`，后续重复 change 保持同一 prompt token；timer expiry 在 prompt 期间仍执行 stop 语义。reload/continue 均携带并匹配 `ReloadPromptToken`；reload 先停止旧 speech/monitor/clock，再以新 session token 对同一路径执行 `autoplay` 原子加载；continue 复用内存 document/cursor，只恢复 speech 与 clock，terminal 文件事件的 monitor rearm 由适配器自身完成。

### `ReadingSessionReducing`

```swift
protocol ReadingSessionReducing: Sendable {
    func reduce(
        state: ReadingSessionState,
        event: ReadingSessionEvent
    ) -> Transition
}

struct Transition: Equatable {
    let state: ReadingSessionState
    let effects: [ReadingSessionEffect]
}
```

### `ReadingSessionEffectExecuting`

```swift
protocol ReadingSessionEffectExecuting: Sendable {
    func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent?
}
```

会产生领域结果的 effect 必须把结果作为返回值交回 coordinator，在当前串行 batch 内继续 reduce；adapter 不得在 `execute` 内同步回调 `SessionCoordinator.send`。返回事件一旦被 reduce，其 transition 将取代原 batch 的剩余 effects。等待期间被取消的旧 effect 即使不配合取消并返回事件，coordinator 也必须在发布前丢弃该事件。cleanup effect 采用 best-effort 顺序执行，单项失败不得跳过后续 cleanup。

## 状态转换表

| 当前状态 | 事件 | 下一状态 | 主要 effect |
|----------|------|----------|-------------|
| idle | selectFile | loading | loadDocument |
| ready | selectFile | loading | stopOldResources, loadDocument |
| paused | selectFile | loading | stopSpeech, clearSession, loadDocument |
| ready | play | playing | verifySource, startSpeech, startClock, startMonitor |
| playing | play | playing | none（幂等） |
| playing | pause | paused | settleClock, pauseSpeech |
| paused | resume | playing | resume/rebuildSpeech, startClock |
| playing/paused | stop | ready | stopResources, resetCursorAndElapsed |
| playing | timerExpired | ready | 与 stop 相同 |
| playing | speechParagraphFinished | playing | nextParagraph 或 loopToStart |
| playing | sourceChanged | awaitingReloadDecision | settleClock, pauseSpeech |
| awaitingReloadDecision | reload | loading | stopResources, loadDocumentThenAutoplay |
| awaitingReloadDecision | continueOld | playing | resumeSpeech, startClock, rearmMonitor |
| any loaded | appTerminate | idle | stopResources, discardSession |

非法事件在 strict 构建中触发 invariant diagnostic；relaxed 构建发出不含文件路径或正文的结构化 fault、停止活动副作用并恢复 idle/ready。迟到 token 回调不属于非法事件，只做幂等忽略；用户快速重复的合法事件必须幂等。

## 关键算法/策略

### 严格英文过滤

- 输入：任意 Unicode 字符串数组。
- 输出：仅 `[A-Za-z]` 与单个 ASCII space 的非空段落。
- 复杂度：时间 O(n)，空间 O(m)，m ≤ n 的 UTF-8 byte count。
- 策略：逐 UTF-8 byte 扫描；保留 ASCII letter；ASCII whitespace 折叠为一个 space；其他 byte 丢弃；trim；空段落丢弃。
- 执行环境：detached/background task，禁止主线程处理大文件。

### 进度计算

- 预计算每段 UTF-16 长度和 prefix sums。
- `consumed = prefix[paragraphIndex] + clamped(utf16Offset)`。
- `fraction = total == 0 ? 0 : consumed / total`，强制在 `0...1`。
- 当前段落显示使用 1-based；未加载显示 `0 / 0`。
- 复杂度：构建 O(p)，每次更新 O(1)。

### 有效朗读时间

- playing enter：若无 startedAt，记录 `clock.now`。
- pause/stop/prompt enter：`accumulated += now - startedAt`，清空 startedAt。
- remaining：`max(limit - (accumulated + activeSegment), .zero)`。
- expiry event 使用 session token 去重，确保最多一次。

### DOCX 安全提取

- 拒绝非 regular file 和超 20MB 外层文件。
- 仅查找 canonical path `word/document.xml`。
- entry uncompressed size 上限 50MB；超限返回 `unsafeArchive`。
- XMLParser 禁止执行外部实体；只处理正文 `w:p`/`w:t`。
- 临时数据在函数作用域结束后释放，不持久化完整解压目录。

### 文件监控去重

- 每个 start 生成 UUID token。
- 回调携带 token；旧 token 事件丢弃。
- 首个事件设置 `pendingPrompt = true`，后续事件合并。
- rename/delete 后取消旧 source，用户选择后按 URL 决定重建。

## 错误处理与运行时契约

- 外部输入错误全部转为 typed recoverable error，不使用 `precondition` 崩溃。
- `precondition`/`assert` 仅保护程序员错误和 reducer 内部不变量。
- Dev/测试 strict：非法状态转换、越界 cursor、重复活动 TTS 立即失败。
- Production relaxed：非法 transition 或 cursor 违规使用当前 token 清理；真正的 state invariant 违规执行无 token emergency cleanup；两者均记录不含路径/正文的 fault 并恢复到 idle/ready，禁止继续处于不一致 playing。

## SwiftUI 视觉与交互规范

### 视觉方向

- 延续已批准原型的“克制 macOS 原生工作台”：纸张白/石墨灰为主，单一靛蓝表示主要动作和播放状态。
- 使用系统 SF/PingFang 字体是有意的原生选择；通过字号、字重、留白和分隔线建立层级，不引入装饰性字体或营销 hero。
- 一个主窗口、一个主动作，不使用 dashboard card 拼贴或多重强调色。

### 布局

- 默认窗口 760×640，最小窗口 640×560；内容区域最大宽度 900。
- 顶部：产品名和文件上下文；中央：状态、百分比、段落进度和主播放控制；底部：速度与定时设置。
- 停止按钮始终占位，非 playing/paused 时 disabled，避免状态切换导致布局跳动。
- 错误使用 sheet/alert；源文件变化使用 modal confirmation，且必须阻止重复弹层。

### 已批准原型与 POC 复用决策

| 区域 | 生产复用 | 决策 |
|------|----------|------|
| 窗口 | 原型单窗口三段式工作台 | 顶部文件上下文、中央状态/进度/控制、底部速度/定时；默认 760×640，最小 640×560 |
| 文件 | 原型文件名、格式提示与选择入口 | 只保留真实 `fileImporter`；移除“载入示例”演示按钮 |
| 播放 | POC 主播放/暂停按钮与独立停止按钮 | 保留 `playPauseButton`、`stopButton`；停止始终占位，非 playing/paused 时禁用 |
| 设置 | 原型三档 segmented control 与分钟输入 | 不提供音色、循环次数；定时仅接受留空或 1...240 整数分钟 |
| 提示 | 原型源文件修改 modal | 决定事件必须携带当前 `ReloadPromptToken`；移除“模拟修改/模拟到期”演示工具 |
| 内容 | 原型脚注与隐私说明 | 不展示整篇正文或当前段落全文，避免大文档 UI 开销与无障碍噪声 |

稳定 Accessibility identifiers：

- `appTitle`、`filePickerButton`、`fileNameLabel`、`sessionStatus`；
- `readingProgress`、`readingProgressLabel`；
- `playPauseButton`、`stopButton`；
- `speedPicker`、`timerMinutesField`、`timerValidationMessage`；
- `errorMessage`、`reloadSourceDialog`、`continueOldContentButton`、`reloadSourceButton`。

所有 identifier 由单一常量定义提供，SwiftUI 与 E2E page object 共享同一字符串契约；原型 HTML id 仅作设计参考，不直接成为生产 API。

### 状态可见性

- idle：显示支持格式/20MB，播放与停止 disabled。
- loading：显示进度指示，文件选择和播放 disabled。
- ready：显示文件名、`0% · 1 / N 段`，播放 enabled。
- playing：主按钮显示暂停，速度和定时输入 disabled，停止 enabled。
- paused：主按钮显示继续，速度 enabled，定时输入保持 disabled，停止 enabled。
- awaitingReloadDecision：主窗口控件不可操作，modal 具有初始焦点。

### 键盘与无障碍

- 文件选择 `⌘O`；播放/暂停 Space；停止 `⌘.`；所有快捷键不得抢占文本输入。
- 焦点顺序：选择文件 → 播放/继续 → 停止 → 速度 → 定时。
- 所有可操作元素必须同时设置 accessibility label 和稳定 identifier。
- 状态变化通过 accessibility live announcement 提示，但进度高频回调最多每秒播报一次。
- 颜色对比满足 WCAG AA；状态不得只依赖颜色。
- `accessibilityReduceMotion` 开启时禁用非必要 entrance/进度动画，只保留即时状态切换。

### 前端性能

- view body 不解析文件或计算大文本；只渲染不可变 view state。
- TTS 高频 range callback 节流到 UI ≤ 10Hz；业务 cursor 仍保留全部安全边界。
- 段落全文不在 UI 展开，避免大文档产生巨型 Text view。

## 本地构建与验证

```text
scripts/verify-morerduo.sh
  1. swift build 后依次执行 unit + integration + contract Swift Testing runners
  2. swift build -c release
  3. 组装 dist/磨耳朵.app
  4. plutil + codesign strict verify
  5. E2E sandbox snapshot
  6. Accessibility P0 specs
  7. sandbox restore + byte-level verify
```

任何一步失败均返回非零状态并阻断后续门禁。
