# Capability 10 Native E2E 报告

> Change：`macos-english-listening-mvp`
>
> 日期：2026-07-20
>
> 结论：P0 100%，P1 全通过，sandbox 恢复一致

## 执行口径

- 原生业务 E2E 使用真实 `DocumentLoader`、过滤、reducer、effect executor、AppViewState 和真实 `DispatchSourceFileMonitor`；系统 TTS 与分钟级时间分别注入 silent fake 和可控单调 clock。
- release smoke 直接启动 ad-hoc signed `dist/磨耳朵.app`，通过真实 Accessibility tree 校验首次 idle、稳定 AXIdentifier 与 enabled 状态。
- 每个业务 spec 在 fixture 创建后 snapshot，场景结束或抛错后均 restore，并重新 snapshot 做 byte-level equality；fixture 根目录只允许位于系统临时目录。
- 真实单调时钟保留 1 分钟最小配置启动冒烟；到期、暂停冻结和单次 expiry 使用 fake clock 确定性推进。

## Proposal E2E 追踪

| Proposal 场景 | 自动化证据 | 结果 |
|---------------|------------|------|
| E2E-P0-001 TXT 主流程 | `supportedDocumentsMainFlow` | PASS |
| E2E-P0-002 DOCX 主流程 | `supportedDocumentsMainFlow` | PASS |
| E2E-P0-003 文本 PDF 主流程 | `supportedDocumentsMainFlow` | PASS |
| E2E-P0-004 暂停、变速与继续 | `playbackControlsAndLoop` | PASS |
| E2E-P0-005 独立停止 | `playbackControlsAndLoop` | PASS |
| E2E-P0-006 有效朗读时间定时 | `activeReadingTimer`、`realMinimumTimerSmoke` | PASS |
| E2E-P0-007 严格英文过滤 | `strictFilteringAndNoEnglish` | PASS |
| E2E-P1-001 非法及不可读文件 | `invalidDocumentFailures`、`readySourceDeletion` | PASS |
| E2E-P1-002 源文件修改 | `sourceModificationDecisions` | PASS |
| E2E-P1-003 换文件与重启重置 | `lifecycleAndCompetitionBoundaries` | PASS |
| E2E-P2-001 边界与竞争探索 | `lifecycleAndCompetitionBoundaries` | PASS |

## 最新结果

- E2E 总计：20/20；
- Proposal P0：7/7，100%；
- Proposal P1：3/3，100%；
- release Accessibility smoke：1/1；
- sandbox snapshot/restore/verify 基础设施：5/5；
- 未修改用户文件、用户配置或外部仓库。
