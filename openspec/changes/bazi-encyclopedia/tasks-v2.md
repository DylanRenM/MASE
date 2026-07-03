# 预处理层升级 + 全链路质量重构 — 实施计划

| 阶段 | 任务数 | 说明 |
|------|--------|------|
| Phase 0: Foundation | 3 | 骨架、配置、超时重试 |
| Phase 1: Preprocessor | 6 | FormatBridge + Cleaner + Parser + Chunker + Test + 依赖安装 |
| Phase 2: Classifier | 4 | 关键词扩展 + 单主标签 + LLM兜底 + Test |
| Phase 3: Pipeline Integration | 2 | 集成预处理层 + 更新分类流程 |
| Phase 4: Dedup + Encyclopedia | 4 | 单标签去重 + LLM摘要 + 双索引 + Test |
| Phase 5: API + UI | 6 | API分页 + 按需加载 + 导航切换 + 元信息 + 书籍分页 |
| Phase 6: Script Updates | 3 | batch_import + auto_rebuild + 废弃旧文件 |
| Phase 7: Testing | 4 | 集成测试 + 格式兼容 + 回归对比 + 全量套件 |
| Phase 8: Full Rebuild | 4 | 备份 → 清空 → 重导363本 → 重建百科 |

共 **36 个任务**，Phase 0-2 可并行推进。预计核心开发 2-4 天 + 全量重建 7-8 小时（夜间）。

关键风险：PaddleOCR 安装依赖（paddlepaddle-gpu）在 macOS 上可能有问题，如无法安装则 OCR 阶段先跳过，后续在 Linux 环境补上。
