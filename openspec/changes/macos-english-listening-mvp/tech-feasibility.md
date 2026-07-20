---
change: "macos-english-listening-mvp"
created: "2026-07-20"
agent: "agent-3-development"
status: "poc-passed-toolchain-action-required"
---

## 1. 技术难点方案表

| 难点 | 成熟方案 | 最新技术调研 | 推荐方案 | POC 状态 | 遗留风险 |
|------|----------|--------------|----------|----------|----------|
| macOS 原生 UI | SwiftUI + AppKit hosting | Swift 6 主线程隔离更严格 | SwiftUI，UI 与会话状态保持单向绑定 | ✅ | 完整应用打包和 XCUITest 需要全量 Xcode |
| 系统英文 TTS | `AVSpeechSynthesizer` | delegate 可提供字符范围；buffer API 可无声验证 | 用适配器封装系统 API，以字符范围记录可恢复位置 | ✅ | 暂停后变速需停止当前 utterance 并从未读后缀重建 |
| PDF 文本提取 | PDFKit `PDFDocument` / `PDFPage.string` | 系统框架，无第三方依赖 | 按页提取文本并转为有序段落 | ✅ | 多栏、复杂排版的阅读顺序仅作 P2 兼容性探索 |
| DOCX 文本提取 | ZIP 解包 + WordprocessingML XML | ZIPFoundation 0.9.20 支持 SwiftPM 与现代 macOS | ZIPFoundation 解包，`XMLParser` 流式读取正文文本节点 | ✅ | 复杂对象、批注、页眉页脚需明确排除或专项测试 |
| 严格英文过滤 | UTF-8 单次扫描 | ASCII 规则比 Unicode 正则更确定且更省内存 | 后台执行字节级过滤并规范化空白 | ✅ | 18MB 在本机约 1.68 秒，禁止在主线程执行 |
| 5 秒文件修改检测 | `DispatchSourceFileSystemObject` | 可覆盖写入、扩展、属性、重命名、删除 | 监听文件描述符；rename/delete 后重新建立监听 | ✅ | 文件系统事件可能合并，业务层必须去重 |
| 播放状态一致性 | 单一状态机 + 串行事件处理 | Swift actor 可隔离并发状态 | `ReadingSession` 作为 actor/主状态控制器 | 设计待细化 | 需在 L2 契约中定义合法转换与幂等规则 |

## 2. 非功能性需求满足表

| 需求 | 目标 | 实现方案 | 验证方式 |
|------|------|----------|----------|
| 平台 | macOS 13+ | Swift Package 声明 `.macOS(.v13)`；原生 SwiftUI | POC 编译及 hosting view 布局通过 |
| 文件容量 | 支持 20MB 以内文件且 UI 不长期无响应 | 元数据先校验；解析和过滤在后台任务执行；UI 只接收结果 | 18.0MB 混合文本过滤耗时 1.681 秒 |
| 文件监控 | 修改后 5 秒内提示 | vnode DispatchSource，覆盖写入及原子替换 | 追加写入 0.210 秒；原子替换 0.212 秒 |
| TTS 可控性 | 进度可追踪，三档速度可区分 | delegate 字符范围 + utterance rate | 8 次范围回调；慢/快音频帧比例 1.75 |
| 隐私 | 文件不离开本机 | 仅系统框架和本地 Swift Package；无网络运行时依赖 | 依赖及数据流审查 |
| 安全 | 文档内容不执行 | DOCX 只读取 XML 文本节点；PDFKit 只读取页面字符串 | POC 仅产生纯字符串；L2 增加解析契约 |
| 可测试性 | 时间、TTS、监控可替换 | 依赖倒置，生产适配器实现协议 | L2 contract + Build 测试替身验证 |

## 3. 外部依赖评估表

| 依赖 | 版本 | 用途 | 许可证 | 替代方案 | POC 状态 |
|------|------|------|--------|----------|----------|
| SwiftUI / AppKit | macOS 13+ 系统框架 | 原生 UI 与应用生命周期 | Apple SDK | 无必要替代 | ✅ |
| AVFoundation | macOS 系统框架 | 英文 TTS 与进度回调 | Apple SDK | `NSSpeechSynthesizer`，能力较旧 | ✅ |
| PDFKit | macOS 系统框架 | 文本型 PDF 提取 | Apple SDK | 第三方 PDF 解析库 | ✅ |
| Foundation `XMLParser` | macOS 系统框架 | DOCX WordprocessingML 文本提取 | Apple SDK | 第三方 OOXML 库 | ✅ |
| ZIPFoundation | 0.9.20，revision `22787ff` | DOCX ZIP 容器解包 | MIT | 自研 ZIP 或系统进程，不推荐 | ✅ |
| 完整 Xcode | 未安装 | `.app` 工程、签名、XCTest/XCUITest、发布 | Apple 工具链 | 仅 SwiftPM 无法覆盖完整 UI E2E/发布流程 | ❌ 待安装 |

## 4. 高风险项详细分析

### 4.1 构建工具链完整性

- 问题描述：当前仅安装 Command Line Tools；`xcodebuild` 明确报错要求完整 Xcode。默认 `MacOSX26.5.sdk` 与 Swift 编译器补丁版本不匹配。
- 已验证绕行：指定本机 `MacOSX15.4.sdk` 后，SwiftUI 与全部 POC 可以编译运行。
- 推荐方案：在进入 Design L2 前安装与当前 macOS 匹配的完整 Xcode，切换 `xcode-select`，无 `SDKROOT` 覆盖重跑 POC，并增加最小 `.app` + XCTest/XCUITest 验证。
- 遗留风险：未安装 Xcode 时无法满足 MASE 的 macOS UI E2E 硬门禁，也无法可靠完成签名和发布。

### 4.2 TTS 暂停位置与暂停后变速

- 问题描述：`continueSpeaking()` 可以恢复同一 utterance，但不能改变已经创建的 utterance rate。
- 成熟方案：通过 `willSpeakRangeOfSpeechString` 记录已读字符范围；速度不变时继续，速度改变时停止并从未读后缀创建新 utterance。
- POC 结果：系统英文 voice 可生成音频；正常速度获得 80,316 帧和 8 次字符范围回调；慢/快帧数比例 1.75。
- 推荐方案：业务层保存段落索引与最后完成的安全字符边界，TTS 适配器负责后缀重建。
- 遗留风险：不同系统 voice 的回调粒度可能不同，Build 阶段需用至少两种本机英文 voice 做探索测试。

### 4.3 DOCX 解包与正文提取

- 问题描述：Apple 系统框架没有适合本需求的高级 DOCX API。
- 成熟方案：DOCX 是 ZIP 容器，正文位于 `word/document.xml`；ZIPFoundation 提供 Swift 原生解包。
- POC 结果：ZIPFoundation 0.9.20 成功解包最小 DOCX，`XMLParser` 成功读取 `w:t` 文本。
- 推荐方案：锁定 0.9.20；只读取正文文本节点并明确拒绝损坏/加密容器。
- 遗留风险：表格和文本框的阅读顺序需要 fixture 测试；宏和嵌入对象不解析、不执行。

### 4.4 PDF 文本顺序与扫描件识别

- 问题描述：`PDFPage.string` 能提取文本型 PDF，但复杂布局的顺序取决于 PDF 内部结构。
- POC 结果：生成的文本 PDF 可被 PDFKit 正确提取。
- 推荐方案：按页提取；页面无文本时作为扫描件/无可读文本处理；复杂布局列为 P2。
- 遗留风险：不能保证所有多栏 PDF 符合视觉阅读顺序，但不影响 MVP 的明确范围。

### 4.5 文件变化检测生命周期

- 问题描述：编辑器可能原地写入，也可能用临时文件原子替换源文件。
- POC 结果：原地追加 0.210 秒、原子替换 0.212 秒触发，均远低于 5 秒目标。
- 推荐方案：监听 `.write/.extend/.attrib/.rename/.delete`；对 rename/delete 关闭旧描述符并按路径重新建立监听；提示事件去重。
- 遗留风险：网络盘及特殊文件系统不在 MVP 保证范围内。

## 5. 可复用构件清单

| 构件 | 来源 | 用途 | 复用方式 |
|------|------|------|----------|
| `NSHostingView` / SwiftUI | AppKit / SwiftUI | 原生界面 | 直接使用 SwiftUI App，必要处桥接 AppKit |
| `AVSpeechSynthesizer` | AVFoundation | TTS、暂停/继续、进度回调 | 封装为 `SpeechEngine` 适配器 |
| `PDFDocument` | PDFKit | PDF 按页文本提取 | 封装为 `PDFDocumentParser` |
| `FileManager.unzipItem` | ZIPFoundation 0.9.20 | DOCX 解包 | 封装为 `DOCXDocumentParser` |
| `XMLParser` | Foundation | 流式读取 DOCX 文本节点 | 私有 delegate，不暴露 XML 细节 |
| `DispatchSourceFileSystemObject` | Dispatch | 本地文件变化监听 | 封装为可替换的 `SourceFileMonitor` |
| `ContinuousClock` | Swift 标准库 | 单调时间与可测试计时抽象 | 生产 clock 适配器；测试注入虚拟 clock |

## 6. POC 验证记录

| 验证项 | 脚本路径 | 结果 | 备注 |
|--------|----------|------|------|
| SwiftUI 原生布局 | `poc/Sources/MorerduoPOC/main.swift` | ✅ | hosting view 成功布局 |
| 英文 TTS / 进度 / 速度 | 同上 | ✅ | Samantha voice；80,316 帧；8 个范围；速率比 1.75 |
| PDFKit 文本提取 | 同上 | ✅ | 提取 40 个字符 |
| ZIPFoundation DOCX | 同上 | ✅ | 0.9.20，最小 DOCX 解包及 XML 提取成功 |
| 18MB 级英文过滤 | 同上 | ✅ | 1.681 秒；输出字符集满足约束 |
| 文件原地修改 | 同上 | ✅ | 0.210 秒检测 |
| 文件原子替换 | 同上 | ✅ | 0.212 秒检测 |
| 完整 Xcode / XCUITest | `xcodebuild -version` | ❌ | 当前只安装 Command Line Tools |

### 重跑命令

当前环境：

```bash
cd openspec/changes/macos-english-listening-mvp/poc
SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk swift run morerduo-poc
```

安装并选择匹配的完整 Xcode 后：

```bash
cd openspec/changes/macos-english-listening-mvp/poc
swift run morerduo-poc
```

## 7. Design L1 结论

核心产品方案技术可行，系统框架与唯一第三方运行依赖 ZIPFoundation 均已真实跑通。当前唯一阻断项是本机构建工具链不完整：缺少完整 Xcode，无法验证 `.app` 打包和 XCUITest。安装并选择匹配的 Xcode 后，重跑 POC 与最小 UI 测试即可关闭 Design L1 门禁。
