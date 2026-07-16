# 预处理层升级 + 全链路质量重构 设计文档

> 状态: 设计中 | 日期: 2026-07-02

## 1. 概述

### 1.1 背景

当前管线存在三类问题：

| 类别 | 问题 | 根因 |
|------|------|------|
| 格式覆盖 | 扫描版PDF无法解析、EPUB不支持、老DOC经常失败 | 缺少统一格式转换 + OCR |
| 内容质量 | 广告/水印混入(218处)、断句不合理(47.9%)、语义割裂 | 无预处理清洗 + 固定字数切分 |
| 分类/编排 | 病药派几乎空(1条)、综合兜底过大(2166条)、无LLM摘要 | 规则分类器关键词稀疏 + 编排走简单拼接 |

### 1.2 目标

1. 新增 **预处理层**：格式统一(MarkItDown) + 内容清洗(去广告/去水印/行合并) + 语义分块(按章节+自然段)
2. 重构 **分类层**：增强 RuleClassifier 关键词 + LLM兜底
3. 重构 **编排层**：单主标签去重 + LLM摘要生成
4. 完善 **API/UI**：分页 + 按需加载 + 二维矩阵导航(流派↔专题)
5. 支持**全量重建**：363本已入库书籍重新走新管线

---

## 2. 架构总览

```
                        预处理层 (新增) ───────────────────────┐
                     ┌──────────────────────────┐              │
  原始文件 ──→ ① FormatBridge   格式统一         │              │
  (docx/pdf/    (MarkItDown + PaddleOCR)          │              │
   doc/txt/     ──→ 输出: 干净 Markdown           │              │
   epub)        ──────────────────────────┘       │              │
                     ┌──────────────────────────┐              │
              ──→ ② ContentCleaner  内容清洗     │              │
                   (正则去广告/去水印/换行合并)    │              │
                   ──→ 输出: 净化的 Markdown      │              │
                     ──────────────────────────┘              │
                     ┌──────────────────────────┐              │
              ──→ ③ StructureParser 结构提取     │              │
                   (提取标题层级、章节边界)        │              │
                   ──→ 输出: [(section_title,     │              │
                          paragraphs)]           │              │
                     ──────────────────────────┘              │
                     ┌──────────────────────────┐              │
              ──→ ④ SemanticChunker  语义分块    │              │
                   (章节边界内 → 自然段 → 句号兜底)│              │
                   ──→ 输出: [TextBlock]         │              │
                     └──────────────────────────┘              │
                                                            │
  向量化+分类层 (增强) ────────────────────────────────────────┘
                     ┌──────────────────────────┐
  TextBlock ──→ ⑤ Vectorizer (Ollama embedding)  │
              ──→    (新增: 超时120s + 3次重试)   │
                     ───────────────────────────┘
                     ┌──────────────────────────┐
              ──→ ⑥ Classifier (增强)            │
                   (Rule: 扩展关键词 + 单主标签)   │
                   (LLM: 低置信度兜底)             │
                   ──→ 输出: [(vector, metadata)] │
                     └──────────────────────────┘

  去重+编排层 (重构) ──────────────────────────────────────────
                     ┌──────────────────────────┐
  Qdrant ──→ ⑦ Dedup (单主标签分组)              │
              ──→    (DBSCAN + LLM精判)          │
                     └──────────────────────────┘
                     ┌──────────────────────────┐
              ──→ ⑧ EncyclopediaBuilder (LLM摘要)│
                   (流派→专题 + 专题→流派 双索引)  │
                   ──→ 输出: encyclopedia.json   │
                     └──────────────────────────┘
```

---

## 3. 预处理层详细设计

### 3.1 FormatBridge — 格式统一

**文件**: `src/bazi/preprocessor.py` (新增)

```
输入: 文件路径, 后缀名
输出: Markdown 文本 (str) 或 None (无法处理)
```

**处理策略**（按优先级）:

| 文件类型 | 主策略 | 兜底策略 |
|----------|--------|----------|
| `.docx` | MarkItDown `WordConverter` | 现有 python-docx |
| `.doc` | MarkItDown + 现有二进制提取 | — |
| `.pdf` (有文本层) | MarkItDown `PdfMinerConverter` | 现有 pypdf |
| `.pdf` (扫描版) | PaddleOCR 逐页识别 | 标记为扫描版，吐OCR文本 |
| `.txt` | 现有 chardet 编码检测 | — |
| `.epub` | MarkItDown `EpubConverter` | — |

**MarkItDown 集成**:
```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert(file_path)
return result.text_content
```

**PaddleOCR 兜底**（仅扫描版PDF）:
- 用 pypdf 判断文本层是否为空 → 空的则走OCR
- PaddleOCR: `lang='ch'`, 逐页识别，合并为文本
- OCR结果不做行合并（留到 ContentCleaner 统一处理）

### 3.2 ContentCleaner — 内容清洗

**输入**: Markdown 文本
**输出**: 净化的 Markdown 文本

**清洗规则**（按顺序执行）:

1. **去水印/页眉页脚**:
   - 匹配模式: `好又全资源网.*加微信.*送.*电子书`
   - `AAKK\d+加微信进群聊`
   - `获取更多.*资料.*加微信.*`

2. **去广告/联系方式**:
   - 微信号模式: `微信[号:]?\s*[a-zA-Z0-9_-]{5,}`
   - QQ号模式: `QQ[群号]?[：:]\s*\d{5,}`
   - 公众号模式: `公众号[：:]\s*\S+`
   - 购书链接: `购.*教材.*微信[：:]\s*\S+`

3. **换行合并**（原始资料语义连贯但被强制换行）:
   - 规则: 如果一行以中文字符结尾，下一行以中文字符开头，且两行合并后不超过80字 → 合并
   - 不合并的情况: 上一行以 `。！？…―` 结尾（自然段落结束）
   - 不合并的情况: 下一行以 `#` `-` `*` 开头（Markdown标记）

4. **去除重复空行**: 连续3个以上空行 → 压缩为2个

5. **去除乱码行**: 非中文字符占比 > 70% 且长度 > 20 的行

### 3.3 StructureParser — 结构提取

**输入**: 净化的 Markdown 文本
**输出**: `[(section_path, paragraphs)]`

- 解析 Markdown 标题: `#`, `##`, `###`
- 构建层级路径: 如 `"第一章 用神 / 1.1 取用法则"`
- 每个标题下的内容作为该章节的自然段列表
- 无标题文本 → `section_path = None`

### 3.4 SemanticChunker — 语义分块

**输入**: `(section_path, [paragraphs])`
**输出**: `[TextBlock]`

**TextBlock 结构**:
```python
@dataclass
class TextBlock:
    block_id: str         # {book_id}_{index:04d}
    text: str             # 块文本
    section: str | None   # 所属章节路径
    genre_tags: list[str] # 由Classifier填充
    topic_tags: list[str] # 由Classifier填充
    source: str           # 来源书名
```

**分块算法**:
1. **章节边界优先**: 不同章节不合并到同一块
2. **自然段优先**: 一个或多个完整自然段组成一块，目标200-800字
3. **长段拆分**: 单个自然段 > 800字 → 按句号（`。！？`）拆分，确保每块以完整句子结束
4. **短段合并**: 连续几个自然段累计 < 200字 → 与下一个自然段合并
5. **无重叠**: 不再使用固定重叠，改为保留章节上下文信息

---

## 4. 分类层增强

### 4.1 RuleClassifier 关键词扩展

**文件**: `src/bazi/content_vectorizer.py` — 修改 `RuleClassifier.genre_keywords` 和 `topic_keywords`

**扩展要点**:

| 流派 | 新增关键词 |
|------|-----------|
| 病药 | `病神`, `药神`, `取药`, `以为病`, `以为药`, `病重药轻`, `去病`, `格中若去病`, `有病`, `无病` |
| 调候 | `暖局`, `解冻`, `向阳`, `冬金`, `夏水`, `丙火调`, `壬水润`, `调候为急`, `寒木` |
| 阴阳 | `阴重`, `阳重`, `阴极`, `阳极`, `阴浊`, `阳浊`, `阴阳平衡`, `阴盛阳衰`, `阳盛阴衰` |
| 盲派 | `盲师`, `家传`, `铁断`, `一招`, `直读`, `象法`, `串宫`, `压运` |
| 格局派 | `立格`, `取格`, `成格`, `破格`, `格局成败`, `护卫`, `清纯`, `真假` |

**去重处理**: 移除 genre 和 topic 之间的重复关键词（如 `正官`, `七杀`, `文昌`, `寿元`），确保每个词只在一个维度打分。

### 4.2 单主标签策略

**当前**: `genre_tags[:3]` — 同块可能被分配给3个流派
**改为**: 每块只分配 **1个主流派** + **1个主专题**（得分最高者）

```
genre_tags = ["旺衰派"]          # 仅最高分
topic_tags = ["财运"]            # 仅最高分
secondary_genres = ["格局派"]   # 辅助信息，不参与分组
```

**LLM兜底**: 当 RuleClassifier 所有流派得分均为0时（即"综合"兜底），调用LLM做一次分类。

**跨标签内容处理**: 单主标签用于分组和去重，但 `secondary_genres` 和 `secondary_topics` 保留在块元数据中，用于在百科条目中生成"参见"交叉引用（如：一条标为旺衰派·婚姻的块，若secondary含财运，则在财运条目中出现"参见"链接）。

### 4.3 Ollama 超时+重试

```python
# content_vectorizer.py — Vectorizer
client = OpenAI(
    base_url=config.ollama_endpoint,
    api_key="ollama",
    timeout=120.0,  # 新增
    max_retries=3,   # 新增
)
```

---

## 5. 编排层重构

### 5.1 去重改进

- 使用 `单主标签` 分组，不再笛卡尔积
- DBSCAN: eps=0.12（改为更严格的余弦距离）
- LLM精判: 同组内2+块相似时才调用LLM判断是保留/合并/丢弃

### 5.2 LLM百科摘要

**文件**: `src/bazi/encyclopedia_builder.py` — 实际启用 `build_entry()` 方法

每个 (流派, 专题) 组:
- 去重后的块 → LLM 摘要生成
- 输出结构:
  ```json
  {
    "title": "旺衰派 · 婚姻",
    "summary": "旺衰派认为婚姻主要看日支(夫妻宫)和官星/财星的旺衰...",
    "core_views": ["观点1", "观点2"],
    "school_differences": ["与格局派对比...", "与盲派对比..."],
    "classic_cases": [{"八字": "乾造 甲子...", "断语": "..."}],
    "sources": [{"book": "子平真诠", "blocks": 15}]
  }
  ```

### 5.3 双索引生成

```
encyclopedia.json:
{
  "by_genre": {            // 流派 → 专题 (现有)
    "旺衰派": { "婚姻": {...}, "健康": {...}, ... }
  },
  "by_topic": {            // 专题 → 流派 (新增)
    "婚姻": { "旺衰派": {...}, "格局派": {...}, ... },
    "健康": { "旺衰派": {...}, "盲派": {...}, ... }
  }
}
```

---

## 6. API & UI 变更

### 6.1 API 变更

| 端点 | 变更 |
|------|------|
| `GET /api/encyclopedia` | 新增参数 `?view=genre&genre=X&topic=Y` 按需返回单个条目 |
| `GET /api/encyclopedia?view=topic&topic=X` | 新增加载"专题→流派"视图 |
| `GET /api/books` | 新增 `?offset=0&limit=50` 分页 |
| `GET /api/cases` | 新增 `?topic=X&genre=Y&offset=0&limit=50` 分页+过滤 |

### 6.2 UI 变更

1. **导航切换按钮**: 左栏顶部 "按流派" / "按专题" 切换
2. **按需加载**: 点击具体条目时才请求 API（不再一次性加载1MB+）
3. **加载状态**: 请求中显示 loading
4. **条目元信息**: 显示来源书籍数、去重后块数、LLM生成摘要

---

## 7. 全量重建流程

### 7.1 迁移步骤

1. **备份现有数据**: 复制 `data/bazi.db` 和 `data/encyclopedia.json`
2. **清空重导**:
   - 删除所有 book 记录
   - 删除 Qdrant collection 的所有向量
3. **批量重新导入**: 363本文件逐个通过新管线
4. **百科重建**: 运行新编排层
5. **验证**: 对比重建前后的条目数、覆盖率

### 7.2 回滚方案

如有问题，恢复备份的 `data/bazi.db` + Qdrant collection。

---

## 8. 文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| **新增** | `src/bazi/preprocessor.py` | 预处理层(FormatBridge + ContentCleaner + StructureParser + SemanticChunker) |
| **修改** | `src/bazi/content_vectorizer.py` | 扩展 RuleClassifier 关键词 + 单主标签 + 超时重试 |
| **修改** | `src/bazi/pipeline.py` | 集成预处理层 + LLM兜底分类 |
| **修改** | `src/bazi/encyclopedia_builder.py` | 启用 LLM 摘要 + 双索引 |
| **修改** | `src/bazi/dedup_pipeline.py` | 单主标签分组 |
| **修改** | `src/bazi/app.py` | API分页 + 按需加载 + 双视图 |
| **修改** | `ui/index.html` | 导航切换 + 按需加载 + loading |
| **修改** | `main.py` | 集成预处理器初始化 |
| **废弃** | `src/bazi/book_parser.py` | 被 preprocessor.py 替代，保留以备回滚 |
| **删除** | `quick_rebuild.py` | 功能合并进 pipeline.py |
| **删除** | `recover_stuck.py` | 一次性脚本，不再需要 |
| **更新** | `batch_import.py` | 适配新管线 |
| **更新** | `auto_rebuild.py` | 适配新管线 |

---

## 9. 测试计划

| 测试 | 内容 |
|------|------|
| 单元测试 | ContentCleaner 各种广告/水印模式 |
| 单元测试 | SemanticChunker 自然段/章节边界切分 |
| 单元测试 | RuleClassifier 扩展关键词覆盖率 |
| 集成测试 | 扫描版PDF → OCR → 清洗 → 分块 → 分类 全链路 |
| 回归测试 | 与现有363本对比：条目数应增加(OCR恢复) + 广告数应为0 |

---

## 10. 性能估算

| 阶段 | 单本书耗时 | 363本估算 |
|------|-----------|-----------|
| MarkItDown 转换 | 1-5秒 | ~15分钟 |
| PaddleOCR (扫描PDF) | 30-60秒/页 | 仅~50本扫描书，每本按50页算：~25小时 |
| ContentCleaner + StructureParser | <1秒 | ~3分钟 |
| SemanticChunker | <1秒 | ~3分钟 |
| Ollama Embedding | 0.3秒/块 × ~200块/书 | ~6小时 |
| LLM分类兜底 | 仅综合兜底触发 | 少量 |
| Dedup + LLM摘要 | 每(流派,专题)组 ~30秒 | ~45分钟 |

**总计估算**: PaddleOCR 是瓶颈（扫描版PDF）。可通过以下优化:
- OCR结果缓存：同一文件不重复OCR
- 批量异步处理：在后台逐个处理，不影响已处理完成的非扫描书先入库
