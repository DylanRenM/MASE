# 磨耳朵 macOS MVP 契约定义

> 从 7 个 capability spec 的 Gherkin 场景推导。
>
> 适用层级：API 级 ☑　模块级 ☑　函数级 ☑
>
> Dev/测试：strict；本地 release：typed external errors + relaxed fail-safe recovery + structured internal diagnostics。

## 0. 公共类型约束

### `EnglishParagraph`

- `text` MUST 非空。
- `text.utf8` MUST 只包含 `A-Z`、`a-z`、单个 ASCII space。
- 不得以 space 开头或结尾，不得包含连续 space。
- `ordinal` MUST ≥ 0 且在同一文档内严格递增。

### `LoadedDocument`

- `paragraphs` MUST 非空。
- `url` MUST 为 file URL。
- `kind` MUST 与允许扩展名一致。
- `fingerprint.size` MUST 在 `0...20MB`。
- 发布后文档值不可变；重新加载创建新值而非就地修改。

### `ReadingCursor`

- 无文档时 MUST 为 `(0, 0)`。
- 有文档时 `paragraphIndex` MUST 在 paragraphs indices 内。
- `utf16Offset` MUST 在当前段落 `0...utf16Length`。

### `ReadingProgress`

- `fraction` MUST 在 `0...1` 且不可为 NaN/Infinity。
- `currentParagraph` 在无文档时为 0，有文档时在 `1...totalParagraphs`。
- `totalParagraphs` MUST ≥ 0。

## 一、API 级契约（硬性必做）

### API: `DocumentLoading.load(url:)`

- **前置条件**：
  - `url.isFileURL == true`；
  - 调用方不得假定 URL 已通过文件策略；该 API 自身必须验证外部输入。
- **成功后置条件**：
  - 返回 `ParsedDocument` 的段落顺序稳定；
  - 返回值不包含 UI、TTS 或网络对象；
  - 不保留打开的 file descriptor 或临时解压目录。
- **失败后置条件**：
  - 只抛出 `DocumentLoadError` 或包装后的 typed adapter error；
  - 不返回半结果；session 是否清除由调用前的 coordinator transition 决定；
  - 所有临时资源释放。
- **不变式**：
  - 不发起网络请求；
  - 不执行文档中的脚本、宏或嵌入对象。

### API: `EnglishFiltering.filter(_:)`

- **前置条件**：输入 ordinal 非负并按文档顺序排列。
- **成功后置条件**：
  - 返回数组非空；
  - 每个元素满足 `EnglishParagraph` 公共约束；
  - 输出顺序等于输入中非空过滤结果的相对顺序。
- **失败后置条件**：过滤结果全空时只返回 `noReadableEnglish`。
- **不变式**：确定性、无副作用、同输入同输出。

### API: `SpeechSynthesizing.start(_:)`

- **前置条件**：
  - request text 满足严格英文约束且非空；
  - base offset 与原段落边界一致；
  - speed 为 slow/normal/fast；
  - session token 与 request token 均属于当前 active generation；
  - 当前不存在另一个 active request，或调用方先执行 stop。
- **成功后置条件**：
  - 最终产生 finished/cancelled/failed 之一；
  - progress range 不越过 request UTF-16 范围；
  - `safeResumeUTF16Offset` 等于 `baseUTF16Offset + requestRange.lowerBound`，即当前 `willSpeak` 词范围的原段落下界；
  - 同一 request 只接受 `requestRange.lowerBound` 大于或等于上次安全下界的 progress，越界或倒退 range 必须丢弃。
- **失败后置条件**：返回 typed speech error，不伪造 playing。
- **不变式**：最多一个活动 utterance；stop 后不得发送新业务进度。

### API: `SpeechSynthesizing.pause/resume/stop`

- **pause 前置条件**：当前存在 active utterance；重复 pause 必须幂等。
- **pause 后置条件**：使用 immediate boundary，并在调用系统 pause 前关闭当前 progress callback generation；暂停期间收到或旧 generation 延迟处理的 range 均不得推进业务 cursor，最近安全边界保持不变。
- **resume 前置条件**：处于 paused 且 request 仍有效；原速继续传 nil，变速继续传从安全 cursor 构造的新 request。
- **resume 后置条件**：原速打开新的 callback generation 后调用系统 continue；变速先退休旧 utterance identity、为旧 request 产生 cancelled 终态，再从新 request 后缀启动，不跳过未确认文本。
- **resume 失败后置条件**：系统 stop 失败时不得启动 replacement request，后续 fail-safe cleanup 必须仍可重试系统 stop。
- **stop 后置条件**：active count 为 0；后续迟到回调被 session token + request token + utterance identity + callback generation 丢弃；即使领域 request 已退休，cleanup 仍调用系统 stop。

### API: `SourceMonitoring.start(url:fingerprint:)`

- **前置条件**：URL 为当前文档本地路径，fingerprint 来源于同一路径。
- **成功后置条件**：write/extend/attrib/rename/delete 任一变化在 5 秒内进入 event stream。
- **失败后置条件**：返回 typed monitor error，会话不得假装监控成功。
- **不变式**：同一实例最多一个 active source；stop 后旧 token 回调无业务效果。

### API: `ReadingSessionReducing.reduce(state:event:)`

- **前置条件**：输入 state 满足全部 session 不变量。
- **成功后置条件**：
  - 返回新 state 仍满足全部不变量；
  - effects 顺序确定；
  - 相同 state/event 返回相同 transition。
- **不变式**：纯函数，不调用时钟、文件、TTS、日志或 UI。

### API: `ReadingSessionEffectExecuting.execute(_:)`

- **前置条件**：只由 `SessionCoordinator` 在其串行 effect domain 内调用；effect payload 满足对应 document、cursor、speed 与 token 契约。
- **成功后置条件**：
  - 返回 `nil` 表示当前 effect 已完成且没有同步领域结果；
  - 返回单个 `ReadingSessionEvent` 时，coordinator MUST 在同一 generation 内 reduce 该事件，并 MUST 丢弃原 batch 的剩余 effects；
  - cleanup effect 即使单项失败，后续 cleanup 仍 MUST best-effort 执行。
- **失败后置条件**：adapter failure 抛出 typed execution error或由 coordinator 按 effect 类型映射为 typed error；不得把失败伪装为成功状态。
- **不变式**：
  - `execute` 内 MUST NOT 同步回调并等待 `SessionCoordinator.send`；
  - superseding event 到达后，当前 cleanup 可完成，但旧 generation 后续非 cleanup effects MUST 被丢弃；
  - 被取消 effect 的返回事件或错误 MUST NOT 修改当前 generation；
  - effect execution 不得重叠。

## 二、模块级契约

### 模块: `document_ingestion`

- **前置条件**：所有 URL 均视为不可信外部输入。
- **后置条件**：只发布完整 `ParsedDocument` 或 typed failure。
- **不变式**：
  - 只接受 txt/docx/pdf；
  - 外层文件 ≤ 20MB；
  - DOCX 只读取 canonical `word/document.xml` 且 entry 解压大小 ≤ 50MB；
  - PDF 无可提取文本视为 scanned/unsupported；
  - 不访问网络。

### 模块: `english_content_filtering`

- **前置条件**：接受任意 Unicode 文本，包括恶意标记。
- **后置条件**：输出只含允许字符或返回 noReadableEnglish。
- **不变式**：O(n) 单次扫描，不使用可能产生灾难性回溯的正则。

### 模块: `speech_playback_control`

- **前置条件**：只接收过滤后 paragraph 和合法 cursor。
- **后置条件**：所有系统 delegate callback 转换为同时带 session token 与 request token 的领域事件。
- **不变式**：
  - active TTS ≤ 1；
  - playing 时速度不可变；
  - 已接受的 progress 安全下界单调不减，paused 时 progress generation 关闭；
  - 暂停变速后用未读后缀重建；
  - last paragraph finished 后只进入 first paragraph，不产生 completed 终态。

### 模块: `active_reading_timer`

- **前置条件**：limit 为 nil 或 1...240 整数分钟转换的正 Duration。
- **后置条件**：remaining 不为负；expiry 每个 session token 最多一次。
- **不变式**：
  - 只有 playing 累计；
  - 使用单调时间；
  - pause/prompt/stop 先结算 active segment 再清空 startedAt。

### 模块: `reading_progress`

- **前置条件**：paragraph lengths 非空时全部 > 0，cursor 合法。
- **后置条件**：输出满足 ReadingProgress 公共约束。
- **不变式**：同一轮朗读中进度除循环边界/stop 外不回退。

### 模块: `source_file_monitoring`

- **前置条件**：start/stop 由 coordinator 串行调用。
- **后置条件**：资源关闭；rename/delete 后不泄露 descriptor。
- **不变式**：pending prompt 最多一个；旧 token 不影响新文档。

### 模块: `session_lifecycle`

- **前置条件**：所有外部 callback 携带当前 session token。
- **后置条件**：transition effect 成功或失败最终都收敛到合法状态。
- **不变式**：
  - mode 六选一；
  - playing ⇒ document != nil、active speech = 1、clock active；
  - paused/awaitingReloadDecision ⇒ clock inactive；
  - idle ⇒ document nil、cursor zero、无 active resources；
  - ready ⇒ document != nil、cursor 合法、无 active speech/monitor；
  - stop/timerExpired 语义相同；
  - app launch 初始状态恒为 idle。

## 三、函数级契约（高风险路径）

### 函数: `FilePolicy.validate(url:resourceValues:)`

- **前置条件**：resourceValues 对应 url。
- **后置条件**：成功时 extension 合法、regular/readable、size ≤ 20MB。
- **违反后果**：可能读取不可信设备节点或造成资源耗尽。

### 函数: `DOCXParser.extractDocumentXML(archive:)`

- **前置条件**：archive 可打开且外层文件已过策略校验。
- **后置条件**：只返回 canonical entry 的数据，大小 ≤ 50MB。
- **违反后果**：Zip Slip、zip bomb、内存耗尽。

### 函数: `filterEnglishASCII(_:)`

- **前置条件**：任意 String。
- **后置条件**：输出满足 `^[A-Za-z]+(?: [A-Za-z]+)*$` 或为空。
- **违反后果**：需求违规、TTS 朗读非英文内容。

### 函数: `ProgressCalculator.progress(lengths:cursor:)`

- **前置条件**：cursor 在 lengths 定义的文档范围内。
- **后置条件**：fraction 有限且在 0...1；输入不修改。
- **违反后果**：UI 越界、暂停恢复错误。

### 函数: `ActiveTimeAccumulator.settle(now:)`

- **前置条件**：now 不早于 segmentStartedAt。
- **后置条件**：active segment 至多结算一次，startedAt 变 nil。
- **违反后果**：重复计时或负剩余时间。

### 函数: `ReadingSessionReducer.reduce(state:event:)`

- **前置条件**：state invariant valid。
- **后置条件**：transition state invariant valid；effects 无重复启动资源。
- **违反后果**：并行 TTS、计时漂移、迟到回调污染新会话。

## 四、运行时契约策略

### Dev / 测试 strict

- `precondition`：仅用于调用者/程序员错误和内部边界。
- `assert`：每次 reducer 前后验证 session invariant。
- contract test：每个公共协议前置/后置/不变式至少一个正向与一个反向用例。
- 非法 transition 立即失败测试，不允许静默忽略未声明事件。

### 本地 release relaxed

- 外部文件、TTS、权限和 monitor 错误全部转 typed error，不崩溃。
- 内部 invariant 违规必须记录不含路径或正文的结构化 fault、执行无 token emergency cleanup 并恢复 idle/ready。
- 不得用 relaxed 模式跳过输入校验、安全上限或隐私约束。
