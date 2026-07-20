---
change: "macos-english-listening-mvp"
created: "2026-07-20"
agent: "agent-3-development"
---

## 系统架构图

```text
┌─────────────────────────────────────────────────────────────┐
│ SwiftUI App (@MainActor)                                    │
│ MorerduoApp → MainWindow → SessionCoordinator view state     │
└──────────────────────────────┬──────────────────────────────┘
                               │ UserAction / ViewState
┌──────────────────────────────▼──────────────────────────────┐
│ SessionCoordinator (@MainActor)                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ReadingSessionReducer (pure)                         │  │
│  │ State + Event → State + [Effect]                    │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────┬──────────────┬───────────────┬──────────────┘
                │              │               │
       ┌────────▼──────┐ ┌─────▼────────┐ ┌────▼─────────────┐
       │DocumentLoading│ │SpeechSynthes.│ │ReadingClock      │
       │ protocol      │ │ protocol     │ │SourceMonitoring  │
       └────────┬──────┘ └─────┬────────┘ └────┬─────────────┘
                │              │               │
       ┌────────▼──────┐ ┌─────▼────────┐ ┌────▼─────────────┐
       │TXT/Foundation │ │AVFoundation  │ │ContinuousClock   │
       │PDF/PDFKit     │ │adapter       │ │DispatchSource    │
       │DOCX/ZIP+XML   │ │              │ │adapters          │
       └────────┬──────┘ └─────┬────────┘ └────┬─────────────┘
                └──────────────┴───────────────┘
                               │ typed Event
                               └──────────────► Coordinator
```

所有依赖方向指向领域协议。系统框架适配器不得反向依赖 SwiftUI。

## 技术栈决策表

| 决策点 | 候选方案 | 最终选择 | 理由 |
|--------|----------|----------|------|
| UI | SwiftUI、AppKit、Flutter | SwiftUI + 少量 AppKit | macOS MVP 原生、POC 已通过、最小依赖 |
| 构建 | SwiftPM、Xcode project、XcodeGen | SwiftPM + 本地 bundle 脚本 | 本地 Git、无完整 Xcode也可构建 |
| 状态 | ObservableObject 直接副作用、Reducer | 纯 Reducer + Coordinator | 状态转换可穷举、竞态可测试 |
| 并发 | GCD 混用、Swift Concurrency | `@MainActor` + async/await | 明确隔离 UI 与后台解析 |
| TTS | `NSSpeechSynthesizer`、AVSpeechSynthesizer | AVSpeechSynthesizer | 进度范围、速率和暂停能力已 POC |
| PDF | PDFKit、第三方库 | PDFKit | 系统框架、本地、无额外许可证 |
| DOCX | ZIPFoundation+XML、系统 unzip、完整 OOXML 库 | ZIPFoundation 0.9.20 + XMLParser | 轻量、MIT、目标 entry 提取 |
| 时间 | Timer 递减、ContinuousClock | 单调 clock + 累计 Duration | 暂停与调度延迟不造成漂移 |
| 文件监控 | 轮询、FSEvents、DispatchSource | DispatchSource vnode | 单文件低开销，修改检测 POC < 1 秒 |
| 单元测试 | XCTest、Swift Testing | Swift Testing 可执行 runners | 独立 Command Line Tools 可直接发现并执行；不依赖完整 Xcode 的 `.xctest` runner |
| UI E2E | XCUITest、坐标脚本、Accessibility | Accessibility + AXIdentifier | 本机验证通过，不依赖完整 Xcode |

## 组件/模块边界

### `document_ingestion`

- 职责：文件策略校验、类型分派、后台解析、段落原文输出。
- 输入：security-scoped/local file URL。
- 输出：`ParsedDocument` 或 `DocumentLoadError`。
- 依赖：Foundation、PDFKit、ZIPFoundation；不依赖 UI/TTS。

### `english_content_filtering`

- 职责：严格 ASCII 英文字母过滤、空白规范化、空段落剔除。
- 输入：解析后的原始段落。
- 输出：非空 `EnglishParagraph` 集合或 `noReadableEnglish`。
- 依赖：Swift 标准库；纯函数。

### `speech_playback_control`

- 职责：系统 TTS 适配、段落队列、字符范围、暂停/继续/停止/速度。
- 输入：`SpeechCommand`。
- 输出：`SpeechEvent` async stream。
- 依赖：AVFoundation，仅存在于生产适配器。

### `active_reading_timer`

- 职责：验证 1–240 分钟设置，累计实际播放 Duration，产生到期事件。
- 输入：timer command 与 clock instant。
- 输出：剩余时间视图值和一次性 expiry event。
- 依赖：`ReadingClock` 协议。

### `reading_progress`

- 职责：从段落索引、段内范围计算百分比和显示值。
- 输入：`ReadingCursor` + 段落长度元数据。
- 输出：`ReadingProgress`。
- 依赖：无；纯函数。

### `source_file_monitoring`

- 职责：播放期间监控 write/rename/delete，去重并通知 source changed。
- 输入：source URL、原始 fingerprint。
- 输出：`SourceFileEvent` async stream。
- 依赖：Dispatch、Foundation。

### `session_lifecycle`

- 职责：合法状态转换、effect 编排、重复操作幂等、换文件/重启重置。
- 输入：`ReadingSessionEvent`。
- 输出：`ReadingSessionState` + effects。
- 依赖：上述协议，不依赖具体适配器。

### `morerduo_app`

- 职责：应用生命周期、SwiftUI view、文件 importer、错误与修改确认弹层。
- 输入：用户事件和 `SessionCoordinator` 暴露的只读 view state。
- 输出：无业务返回值。
- 依赖：`MorerduoKit` 公共接口。

## 接口协议

本产品没有网络 API。API 级契约指 Swift 模块公共协议。

### `DocumentLoading`

- 协议：Swift async function。
- 签名：`load(url: URL) async throws -> ParsedDocument`。
- 语义：原子成功或 typed failure，不暴露半解析文档。

### `SpeechSynthesizing`

- 协议：Swift command + `AsyncStream<SpeechEvent>`。
- 命令：prepare、play、pause、resume、stop、changeSpeed。
- 语义：同一时刻最多一个活动 utterance。

### `ReadingClock`

- 协议：单调 instant 查询与异步 sleep。
- 语义：不受系统墙上时间调整影响。

### `SourceMonitoring`

- 协议：start/stop + `AsyncStream<SourceFileEvent>`。
- 语义：停止后不得继续发送业务事件。

## 部署拓扑

```text
Local Git working tree
  └─ swift build -c release
      └─ scripts/build-app.sh
          ├─ 磨耳朵.app/Contents/MacOS/morerduo
          ├─ Info.plist
          └─ ad-hoc codesign
              └─ 当前用户 Mac（macOS 13+）
```

不部署服务器、不创建数据库、不上传文档。应用只访问用户通过文件选择器授权的本地 URL。

## E2E 测试策略

### Page Object 结构

```text
tests/e2e/
├── pages/MorerduoPage.swift
├── specs/DocumentPlaybackSpec.swift
├── specs/SessionControlsSpec.swift
├── specs/TimerSpec.swift
├── specs/SourceChangeSpec.swift
└── support/NativeSandbox.swift
```

`MorerduoPage` 封装 AXUIElement 查询和用户动作；spec 不直接使用坐标或元素索引。

### fixtures 数据准备方案

- `tests/fixtures/` 按 capability 保存 TXT/DOCX/PDF。
- 每个 spec 启动时由 `NativeSandbox` 复制 fixture 到唯一临时目录并记录快照。
- spec 结束时 `defer` 关闭 app、恢复文件/配置并做字节级一致性校验。
- 环境恢复失败立即阻断后续 spec。

### 元素定位策略

1. `AXIdentifier`（稳定契约，例如 `playPauseButton`）；
2. Accessibility role + label；
3. 用户可见文本仅用于状态断言；
4. 禁止坐标和“第 N 个元素”定位。

### 测试环境配置

- base app：`dist/磨耳朵.app` 的 ad-hoc signed debug/test 构建。
- 启动方式：`NSWorkspace.openApplication` 或 `open -n`。
- 权限前置：Accessibility 已授权给 test runner；缺失即 fail-fast。
- 时间：注入 accelerated test clock；保留一个真实最小计时冒烟场景。
- 执行：本地 Swift Testing executable runners → bundle build → E2E runner。
