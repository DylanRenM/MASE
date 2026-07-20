# 磨耳朵 Swift 编码规范

> 继承 `docs/coding-standards.md` 全部跨语言规则；本文仅增加 Swift/macOS 特定约束。

## 1. Swift 版本与构建

- Swift tools version 6.0；最低 macOS 13。
- 本机暂时显式使用 `/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk`。
- `Package.resolved` 必须提交；第三方版本不得使用 floating branch。
- 产品构建、测试和 app bundle 必须通过统一脚本，不接受“只在 IDE 中能运行”。

## 2. 命名与 API 设计

- 类型、protocol、enum：UpperCamelCase。
- 方法、属性、enum case：lowerCamelCase。
- 布尔值使用 `is/has/can/should` 前缀。
- 协议表达能力或角色：`DocumentLoading`、`SpeechSynthesizing`。
- 命令方法用动词，查询属性无副作用。
- 遵循 Swift API Design Guidelines；调用点应接近自然语言。

## 3. 类型与可选值

- 优先 struct/enum；只在 identity、actor 或系统 delegate 需要时使用 class。
- 领域状态必须 `Equatable`；跨并发边界类型必须 `Sendable`。
- 产品代码禁止 `!`、`as!`、`try!`；POC fixture 也优先 typed failure。
- 可选值只表达合法缺失，例如 timer limit nil = unlimited；不得用 nil 隐藏错误。
- 时间使用 `Duration` 和单调 clock，不以 Double 秒作为领域真值。

## 4. Swift Concurrency

- SwiftUI view model/coordinator 标记 `@MainActor`。
- 文件解析、过滤和归档解压不得在 MainActor 执行。
- 不使用无结构 `Task.detached`，除非明确说明 ownership、cancellation 和 Sendable 捕获。
- 每个 AsyncStream 必须定义 finish/cancel 生命周期，禁止 continuation 泄漏。
- actor 不得执行长时间同步 I/O；先复制必要值，再进入后台 operation。
- strict concurrency warning 视为错误处理。

## 5. 状态与副作用

- `ReadingSessionReducer` 必须保持纯函数。
- SwiftUI view 不得直接调用 AVFoundation、PDFKit、ZIPFoundation 或 DispatchSource。
- 系统 callback 必须先转换为带 session token 的领域事件。
- effect 必须可枚举、可比较并由 coordinator 串行执行。
- 重复播放、暂停、停止操作必须有明确幂等语义。

## 6. 错误处理

- 外部错误使用封闭 enum；UI 文案由单独 mapper 产生。
- 禁止空 `catch`、只打印不处理、把所有错误统一成 `unknown`。
- 错误必须携带安全上下文；日志不得包含完整文件路径或正文。
- `precondition/assert` 只保护 contract 中的程序员错误，不用于用户输入。
- adapter failure 后必须清理对应资源，禁止继续伪装 playing。

## 7. 文件和解析安全

- 先取 resource values 再读正文；拒绝非 regular file。
- 文件大小常量唯一：`DocumentLimits.maximumSourceBytes = 20 * 1024 * 1024`。
- DOCX 只读取 `word/document.xml`，uncompressed size 上限 50MB。
- XML 不解析外部实体；不执行宏、脚本或嵌入对象。
- 临时文件使用唯一目录和 `defer` 清理。
- PDFKit/ZIPFoundation 类型不得越过 document adapter 边界。

## 8. SwiftUI 与 Accessibility

- 每个用户可操作控件必须有稳定、唯一、语义化 `accessibilityIdentifier`。
- identifier 是 E2E 契约，修改必须同步 spec/page object。
- 不以颜色作为唯一状态提示；disabled 状态必须可被 Accessibility 读取。
- view body 只做声明式投影；复杂计算移到 view model/纯函数。
- 单个 view 超过 150 行或承担两个以上业务区域时拆分。
- 用户可见错误必须说明原因和恢复动作。

## 9. AVFoundation 适配

- `AVSpeechSynthesizer` 只能存在于 production speech adapter。
- delegate 需要强引用生命周期；所有 callback 携带当前 session token。
- NSRange 是 UTF-16 范围，禁止直接当 String.Index。
- speed 映射集中配置并有 POC/集成测试，不散落魔法 Float。
- stop 后迟到 delegate callback 必须丢弃。

## 10. 测试规范

- 单元/集成/契约使用 Swift Testing 可执行 runners；测试名描述行为结果。
- 每个 spec Scenario 至少映射一个测试 ID。
- 测试不得依赖真实等待分钟；注入 fake clock。
- 系统 TTS 自动化默认使用 silent buffer/fake；保留独立人工 audible POC。
- E2E 只通过 `MorerduoPage` 使用 AXIdentifier，禁止屏幕坐标和元素序号。
- 每个 E2E spec 必须 snapshot → `defer` restore → verify；恢复失败硬阻断。
- 测试 fixture 不得访问或修改用户真实文件。

## 11. DbC 运行时断言

- 公共 API 入口执行 `require`：外部输入失败返回 typed error。
- effect 完成执行 `ensure`：确认资源数、状态和 cursor 后置条件。
- reducer 前后执行 `invariantCheck`；Debug/Test 失败即 trap。
- Release invariant failure 执行 fail-safe cleanup 并记录不含敏感数据的 fault。
- 不得为了“通过生产”关闭文件大小、字符过滤、单 TTS、计时单调性等安全/业务不变量。

## 12. 文件组织

- 每个文件一个主要 public 类型；相关私有 helper 可同文件。
- 产品代码仅在 `src/morerduo` 和 `src/morerduo_app`。
- capability 子目录与 OpenSpec 名称一一对应，目录使用 snake_case。
- tests 镜像 capability；共享 fake 放 `tests/support`，不放产品 target。
- 单文件建议 ≤ 300 行；超过 400 行必须说明并拆分。
