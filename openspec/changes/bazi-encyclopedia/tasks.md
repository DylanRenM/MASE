## 1. 项目初始化

- [ ] 1.1 创建 Python 项目结构 (pyproject.toml / requirements.txt)，配置虚拟环境
- [ ] 1.2 添加核心依赖：qdrant-client, sentence-transformers, openai(兼容Ollama), pypdf, ebooklib, paddleocr, fastapi, uvicorn
- [ ] 1.3 初始化 SQLite 数据库，创建 books 和 pipeline_logs 表
- [ ] 1.4 创建 Qdrant collection: bazi_knowledge (768维, cosine距离)
- [ ] 1.5 编写项目 config 模块，支持本地模型路径、Qdrant路径、数据库路径等配置

## 2. 阶段1: 电子书解析与分块 (T-001 ~ T-006)

- [ ] 2.1 **TDD**: 编写 book-parser 的单元测试（txt/epub/pdf 各格式的解析和分块测试）
- [ ] 2.2 实现 TXT 解析器：编码检测（UTF-8/GBK），文本提取
- [ ] 2.3 实现 EPUB 解析器：解压 → XHTML 解析 → 章节树提取
- [ ] 2.4 实现 PDF 解析器：文字型 PDF 直接提取文本，保留页面边界
- [ ] 2.5 实现智能分块器：300-500字窗口，段落边界优先，50字重叠
- [ ] 2.6 实现书籍导入 API 端点：POST /api/books/import，接收文件，返回 book_id 和 block_count

## 3. 阶段2: 向量化与分类 (T-007 ~ T-012)

- [ ] 3.1 **TDD**: 编写 content-vectorizer 的单元测试（向量生成、标签分类）
- [ ] 3.2 实现 Embedding 服务：加载 bge-large-zh-v1.5，批量化块→向量
- [ ] 3.3 实现 Qdrant 写入服务：批量 upsert 向量及 payload
- [ ] 3.4 设计并实现 LLM 分类 Prompt（流派/专题/内容类型 一次输出）
- [ ] 3.5 实现 Ollama 本地千问调用模块（批量处理，进度报告）
- [ ] 3.6 实现分类结果回写：更新 Qdrant payload 中的 genre_tags, topic_tags, content_type

## 4. 阶段3: 聚类去重 (T-013 ~ T-018)

- [ ] 4.1 **TDD**: 编写 dedup-pipeline 的单元测试（DBSCAN聚类、去重判定结果处理）
- [ ] 4.2 实现分组查询：从 Qdrant 按 [流派×专题] 组合查询向量
- [ ] 4.3 实现 DBSCAN 聚类模块：组内聚类，cosine_similarity >= 0.85 归簇
- [ ] 4.4 实现候选对生成：从簇中提取需要 LLM 精判的候选对列表
- [ ] 4.5 实现 LLM 精判模块：调用千问，输出 duplicate/complementary/conflicting/distinct 分类
- [ ] 4.6 实现去重结果处理器：保留最优/标记融合/标注分歧/拆分独立条目

## 5. 阶段4: 百科全书编排 (T-019 ~ T-024)

- [ ] 5.1 **TDD**: 编写 encyclopedia-builder 的单元测试（条目结构、命例数据库）
- [ ] 5.2 实现知识池聚合：从去重结果中按 [流派×专题] 聚合保留块
- [ ] 5.3 实现条目生成模块：千问 LLM 按模板生成结构化条目（核心观点/各家论述/流派分歧/参见）
- [ ] 5.4 实现命例数据库构建器：提取 case_study 块，标注八字特征，按专题索引
- [ ] 5.5 实现百科全书 JSON 序列化：encyclopedia.json + cases.json
- [ ] 5.6 实现增量合并逻辑：新书去重后追加到现有百科全书

## 6. Web UI (T-025 ~ T-030)

- [ ] 6.1 **TDD**: 编写 UI 交互测试（书籍导入、目录浏览、条目渲染）
- [ ] 6.2 实现书籍管理面板：书籍列表、状态标识、操作按钮（导入/合并/删除）
- [ ] 6.3 实现百科浏览面板：左栏树状目录（流派→专题），右栏内容渲染
- [ ] 6.4 实现命例数据库面板：多维筛选（专题/流派/八字特征），与百科互跳
- [ ] 6.5 实现合并进度实时轮询：通过 API 获取 pipeline 进度，更新书籍状态
- [ ] 6.6 实现搜索结果过滤：目录树实时过滤 + 内容区关键词高亮

## 7. FastAPI 服务与管道调度 (T-031 ~ T-035)

- [ ] 7.1 实现管道编排器：串联 阶段1→2→3→4，阶段间状态管理
- [ ] 7.2 实现 API 端点：GET /api/books, POST /api/books/import, POST /api/books/{id}/merge, GET /api/books/{id}/progress
- [ ] 7.3 实现 API 端点：GET /api/encyclopedia, GET /api/cases?topic=&genre=&feature=
- [ ] 7.4 实现管道日志记录：每阶段开始/完成时写入 pipeline_logs
- [ ] 7.5 实现静态文件服务：托管 index.html 和 encyclopedia.json

## 8. 端到端测试与验证 (T-036 ~ T-038)

- [ ] 8.1 编写端到端测试：导入3本测试书 → 全管道处理 → 验证百科输出结构
- [ ] 8.2 性能测试：验证单本书各阶段处理时间在可接受范围内
- [ ] 8.3 增量合并测试：验证新书追加不影响已有百科内容
