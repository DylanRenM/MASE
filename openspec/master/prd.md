# MASE Master PRD

> 最近更新：2026-07-20
>
> 当前产品变更：`macos-english-listening-mvp`
>
> 权威需求基线：`docs/codes-projects/磨耳朵/需求规格书_2026-07-20-3.md`

## 产品愿景

“磨耳朵”为用户提供简单、离线、可控的英文材料反复听读能力。首个 MVP 面向 macOS 13+，优先验证本地文档解析、系统英文语音以及可靠的播放会话控制。

## 当前范围

- 导入 20MB 以内的 TXT、DOCX 和文本型 PDF；
- 仅保留英文字母与必要空白后交给系统 TTS；
- 支持持续循环、暂停、继续、独立停止和慢/正常/快三档速度；
- 支持留空不限时或 1–240 整数分钟的有效朗读时间定时；
- 展示百分比及当前英文段落/总段落数；
- 播放期间在 5 秒内发现源文件变化；
- 应用重启后不恢复上次会话。

## 已确认约束

- HTML 原型只用于交互走查，需求规格书是业务规则权威来源；
- 首版使用原生 SwiftUI 和 macOS 系统默认英文语音；
- 不支持旧版 DOC、扫描 PDF、OCR、音色选择和循环次数设置；
- 文档只在本地处理，不上传或执行其中的内容；
- Windows、iOS 和 Android 属于后续范围。

## Capabilities

| Capability | 状态 | 摘要 |
|------------|------|------|
| `document-ingestion` | Proposal 已确认 | 文件策略、TXT/DOCX/PDF 解析及错误反馈 |
| `english-content-filtering` | Proposal 已确认 | 严格 ASCII 英文字母与空白过滤 |
| `speech-playback-control` | Proposal 已确认 | 播放、循环、暂停、继续、停止、速度 |
| `active-reading-timer` | Proposal 已确认 | 有效朗读时间定时与不限时模式 |
| `reading-progress` | Proposal 已确认 | 百分比和段落进度 |
| `source-file-monitoring` | Proposal 已确认 | 5 秒内发现外部修改并分支处理 |
| `session-lifecycle` | Proposal 已确认 | 合法状态转换、竞争控制与会话重置 |

## 成功标准

1. P0 E2E 场景 100% 自动化通过。
2. API/模块级契约测试 100% 通过。
3. TXT、DOCX、文本型 PDF 正常路径全部可朗读。
4. 暂停位置、暂停计时冻结、停止重置、持续循环和定时到期符合需求。
5. 源文件修改在 5 秒内提示。
6. 文件内容不离开本机且不会作为代码执行。

## 变更记录

| 日期 | Change | 决策 |
|------|--------|------|
| 2026-07-20 | `macos-english-listening-mvp` | Proposal 与交互原型通过，进入 Design L1 |
