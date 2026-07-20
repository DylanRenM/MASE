# macOS MVP 需求—自动化追踪矩阵

> 基线：7 个 capability spec，共 36 条 ADDED Requirements。
>
> 门禁：API/模块契约 100%；Proposal P0 E2E 100%；Proposal P1 全通过。

| # | Capability / Requirement | 主要自动化证据 | 层级 |
|---|--------------------------|----------------|------|
| 1 | active-reading-timer / 定时配置范围 | `TimerConfigurationContractTests`、`timerConfigurationBoundaries` | Contract + E2E |
| 2 | active-reading-timer / 只累计实际朗读时间 | `ActiveTimeAccumulatorTests`、`activeReadingTimer` | Unit + E2E |
| 3 | active-reading-timer / 定时到期只触发一次 | `ActiveTimeAccumulatorContractTests`、`forwardsTimerExpiry`、`activeReadingTimer` | Contract + Integration + E2E |
| 4 | active-reading-timer / 单调时间 | `ContinuousReadingClock` production adapter、`realMinimumTimerSmoke` | Integration + E2E |
| 5 | document-ingestion / 支持的本地文档 | `DocumentLoaderTests`、`supportedDocumentsMainFlow` | Integration + E2E |
| 6 | document-ingestion / 文件策略校验 | `FilePolicyContractTests`、`invalidDocumentFailures` | Contract + E2E |
| 7 | document-ingestion / 扫描 PDF 与空内容处理 | `PDFParserTests`、`invalidDocumentFailures` | Unit + E2E |
| 8 | document-ingestion / 原子加载 | `DocumentLoaderTests`、`firstLaunchAndFileSelection` | Integration |
| 9 | english-content-filtering / 严格英文字符过滤 | `EnglishTextFilterContractTests`、`strictFilteringAndNoEnglish` | Contract + E2E |
| 10 | english-content-filtering / 保留段落边界 | `EnglishTextFilterContractTests.retainsParagraphOrder` | Contract |
| 11 | english-content-filtering / 无英文内容 | `EnglishTextFilterContractTests.rejectsNoEnglishContent`、`strictFilteringAndNoEnglish` | Contract + E2E |
| 12 | english-content-filtering / 内容作为纯数据 | `treatsScriptAsData`、`strictFilteringAndNoEnglish` | Contract + E2E |
| 13 | english-content-filtering / 大文件过滤不阻塞 UI | `EnglishFilterPipelineTests` 18MB performance/MainActor tests | Integration |
| 14 | reading-progress / 百分比与段落进度 | `ProgressCalculatorContractTests`、`playbackControlsAndLoop` | Contract + E2E |
| 15 | reading-progress / 暂停保持进度 | `ProgressCalculatorContractTests.pauseRetains...`、`playbackControlsAndLoop` | Contract + E2E |
| 16 | reading-progress / 停止与到期重置进度 | `ReadingSessionReducerTests`、`activeReadingTimer` | Unit + E2E |
| 17 | reading-progress / 循环边界进度 | `SpeechPlaybackReducerTests`、`playbackControlsAndLoop` | Unit + E2E |
| 18 | reading-progress / 进度计算确定性 | `ProgressCalculatorContractTests.producesDeterministic...` | Contract |
| 19 | session-lifecycle / 单一合法会话状态 | `ReadingSessionStateContractTests`、`modeEventMatrixPreservesContracts` | Contract + Unit |
| 20 | session-lifecycle / 选择新文件重置旧会话 | `selectingFileWhilePaused`、`lifecycleAndCompetitionBoundaries` | Unit + E2E |
| 21 | session-lifecycle / 应用重启不恢复会话 | `terminationReturnsToIdle`、`lifecycleAndCompetitionBoundaries`、release AX smoke | Unit + E2E |
| 22 | session-lifecycle / 快速控制保持一致 | `SessionCoordinatorTests.rapid...`、`lifecycleAndCompetitionBoundaries` | Integration + E2E |
| 23 | session-lifecycle / 错误可恢复 | `SessionCoordinatorTests.adapterFailure...`、`invalidDocumentFailures` | Integration + E2E |
| 24 | session-lifecycle / 本地隐私边界 | security scan、offline adapters、`strictFilteringAndNoEnglish` | Review + E2E |
| 25 | source-file-monitoring / 播放期间监控源文件 | `DispatchSourceFileMonitorTests`、`sourceModificationDecisions` | Integration + E2E |
| 26 | source-file-monitoring / 文件变化提示去重 | `sourceChangePromptIsDeduplicated` | Unit |
| 27 | source-file-monitoring / 重新加载新内容 | `reloadCompletion...`、`sourceModificationDecisions` | Integration + E2E |
| 28 | source-file-monitoring / 继续旧内容 | `continueOldContent...`、`sourceModificationDecisions` | Unit + E2E |
| 29 | source-file-monitoring / 播放前源文件可用性检查 | `deletingReadySource...`、`readySourceDeletion` | Integration + E2E |
| 30 | source-file-monitoring / 停止监控后无事件 | `stopRetiresOldCallbacks...`、`lateSourceTokenIsIgnored` | Integration + Unit |
| 31 | speech-playback-control / 使用系统默认英文语音播放 | `AVSpeechEngineTests.startConfigures...`、audible POC、`supportedDocumentsMainFlow` | Integration + POC + E2E |
| 32 | speech-playback-control / 持续循环播放 | `SpeechPlaybackReducerTests`、`playbackControlsAndLoop` | Unit + E2E |
| 33 | speech-playback-control / 暂停与继续位置 | `AVSpeechEngineTests.pause...`、`playbackControlsAndLoop` | Integration + E2E |
| 34 | speech-playback-control / 独立停止 | `ReadingSessionReducerTests`、`playbackControlsAndLoop` | Unit + E2E |
| 35 | speech-playback-control / 三档速度 | `SpeechRateConfiguration` tests、`playbackControlsAndLoop` | Integration + E2E |
| 36 | speech-playback-control / 单一活动 TTS | `SpeechSynthesizingContractTests`、rapid coordinator tests | Contract + Integration |

## 汇总

- Requirements：36/36 有自动化或系统适配器验证证据；
- API 级 DbC：DocumentLoading、EnglishFiltering、SpeechSynthesizing、SourceMonitoring、ReadingSessionReducing、ReadingSessionEffectExecuting 均有 contract tests；
- Proposal P0：7/7；Proposal P1：3/3；
- E2E sandbox：每个业务 spec 均 snapshot → restore → byte-level verify。
