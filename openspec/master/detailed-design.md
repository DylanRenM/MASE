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

1. pause：结算 active duration；请求 speech pause；状态变为 paused。
2. paused changeSpeed：只更新配置并标记 `requiresUtteranceRebuild`。
3. resume：
   - 速度未变且系统仍保留 utterance：`continueSpeaking()`；
   - 速度改变：停止旧 utterance，从 cursor 未读后缀创建新 utterance。
4. 绝不跳过未确认朗读完成的字符；必要时允许重复最近一个词。

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
5. 原子替换/rename 后生产 monitor 重新打开路径并更新 descriptor。

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

错误枚举：`unsupportedFormat`、`notRegularFile`、`tooLarge`、`notReadable`、`corrupted`、`scannedPDF`、`unsupportedEncoding`、`noReadableEnglish`、`unsafeArchive`。

### `EnglishFiltering`

```swift
protocol EnglishFiltering: Sendable {
    func filter(_ paragraphs: [RawParagraph]) throws -> [EnglishParagraph]
}
```

### `SpeechSynthesizing`

```swift
protocol SpeechSynthesizing: Sendable {
    var events: AsyncStream<SpeechEvent> { get }
    func start(_ request: SpeechRequest) async throws
    func pause() async throws
    func resume() async throws
    func stop() async
}
```

`SpeechRequest` 包含 paragraph ID、未读后缀、原文 UTF-16 base offset 和 speed。

### `SourceMonitoring`

```swift
protocol SourceMonitoring: Sendable {
    var events: AsyncStream<SourceFileEvent> { get }
    func start(url: URL, fingerprint: SourceFingerprint) async throws
    func stop() async
}
```

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

非法事件不改变状态，并在 strict 构建中触发 invariant diagnostic；用户快速重复的合法事件必须幂等。

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
- Production relaxed：记录 fault、停止副作用并恢复到 idle/ready，禁止继续处于不一致 playing。

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
