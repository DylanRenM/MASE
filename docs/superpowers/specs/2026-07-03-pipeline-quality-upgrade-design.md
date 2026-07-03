# 管道质量升级设计 — 从正则到LLM驱动的预处理与渲染

> 状态: 已确认 | 日期: 2026-07-03 | 基于: `2026-07-01-bazi-encyclopedia-design.md`

## 1. 背景与动机

当前管道在5个环节产生质量问题：

| # | 问题 | 根因 |
|---|------|------|
| 1 | 广告/垃圾内容未清除 | 两处广告正则互不统一，行级匹配无法处理行内广告，且模式库无法覆盖多变的广告文案 |
| 2 | 段落语义划分错误 | `_merge_broken_lines` 合并条件过保守，OCR/PDF产生的空格断裂切不干净 |
| 3 | 案例未归类整理 | 案例分离和专题归类两个环节都依赖粗粒度分类，未在终态输出中体现 |
| 4 | 语义段落拆分不合理 | 分块按字符数硬切，不尊重Markdown标题层级和内容结构 |
| 5 | HTML中Markdown渲染错误 | 手写`renderMd`正则只支持`#`/`##`/`###`，不支持`####`、嵌套列表等 |

**根本原因**：正则与规则在面对上百本不同来源、不同年代的电子书时，覆盖面天然不足，维护永无止境。唯一系统性解法是引入LLM驱动的文本规范化。

---

## 2. 管道架构变更

### 2.1 改前（当前）

```
FormatBridge → ContentCleaner → StructureParser → SemanticChunker → Vectorizer → Dedup → Builder → HTML
                 [正则清洗]                     [字符数硬切]                            [手写renderMd]
```

### 2.2 改后（目标）

```
FormatBridge → StructureParser → SemanticChunker(重构) → LLM Normalizer(新) → Vectorizer → Dedup → Builder(重构) → HTML(重构)
                                     [结构驱动分块]        [文本规范化+去广告标注]                    [案例分离+归类]   [marked.js]
```

### 2.3 关键变化

1. **砍掉 `ContentCleaner`** — 不在管道入口处用正则做广告清洗
2. **新增 `LLM Normalizer`** — 在分块后、向量化前，对每个块调用千问做文本规范化和垃圾标记
3. **重构 `SemanticChunker`** — 从字符数驱动改为结构驱动，尊重Markdown标题层级
4. **重构 `EncyclopediaBuilder`** — LLM Prompt加入案例分离/归类指令，自动跳过`[AD]`标记行
5. **重构 HTML 渲染** — 手写`renderMd`替换为`marked.js`，删除`clean_ads()`

---

## 3. LLM 文本规范化 + 去广告标注（新增模块）

### 3.1 位置

在管道中位于 `SemanticChunker` 之后、`ContentVectorizer` 之前。

### 3.2 职责

每个 `TextBlock` 发送给千问LLM，一次调用完成两件事：

1. **文本规范化**：修复断裂词（"结 婚"→"结婚"）、合并误断短行
2. **垃圾标记**：标注广告/水印/页眉页脚/页码残留，用`[AD]`前缀标记

### 3.3 Prompt 模板

```
你是一个文本预处理助手。请对以下八字命理文本块做两件事：

1. 【文本规范化】
   - 修复因OCR/PDF提取造成的断裂词（如"结 婚"→"结婚"、"分 析日 干"→"分析日干"）
   - 合并因强制换行被误断的短行
   - 保持原文内容不变，不做删改

2. 【垃圾标记】
   - 标记广告/水印行（如"加微信XXX"、"公众号XXX"、"好又全资源网"等）
   - 标记页眉页脚/页码残留（如孤立的数字"220"、"221"）
   - 用 [AD] 前缀标记每条垃圾行

输出格式：直接输出处理后的文本，垃圾行前加 [AD] 标记。

待处理文本：
{block_text}
```

### 3.4 输入/输出示例

输入：
```
年柱简社 日料时片
食 神 正印 元男正官
220 获取更多最新易学资料 加微信：804407916
其父亲上亿资产...
```

输出：
```
年柱 简社 日料 时片
食神 正印 元男 正官
[AD] 220 获取更多最新易学资料 加微信：804407916
其父亲上亿资产...
```

### 3.5 处理策略

- **批处理**：每批20个块，减少API调用次数
- **选择性调用**：只对疑似有问题的块触发（检测到空格断裂、短行、URL/微信关键词等特征），干净的块直接跳过
- **标记携带**：规范化后的文本（含`[AD]`标记）写回`TextBlock.text`，随管道流转

### 3.6 实现类

```
class LLMNormalizer:
    def normalize(self, blocks: list[TextBlock]) -> list[TextBlock]
    
    # 辅助方法
    def _needs_normalization(self, block: TextBlock) -> bool
    def _normalize_batch(self, blocks: list[TextBlock]) -> list[TextBlock]
```

---

## 4. 语义分块升级（重构）

### 4.1 变更内容

`SemanticChunker.chunk()` 从「字符数驱动」改为「结构驱动」。

### 4.2 分块策略（优先级从高到低）

1. **Markdown标题硬边界** — `#`/`##`/`###`/`####` 标题之间绝不跨越切分
2. **自然段落边界** — 标题段内以空行分隔的段落作为最小切分单元
3. **句号兜底** — 只在单段超过 `max_size`（500字）时，在句号处切开
4. **短块合并** — 不足 `min_size`（100字）的块与前一块合并

### 4.3 可视对比

```
改前: |──── 500字 ────|──── 500字 ────|  ← 可能切断标题/段落
改后: |## 婚姻分析...自然段...|### 命例...自然段...|  ← 标题边界不跨越
```

### 4.4 TextBlock结构不变

`TextBlock` 数据类字段无需修改，仅改 `chunk()` 方法实现。

---

## 5. 百科全书编排升级（重构）

### 5.1 LLM Prompt 增强

在现有的条目生成 Prompt 中新增以下指令：

```
4. 【经典命例】提取所有 case_study 类型的命例，按专题分类（婚姻/财运/事业/健康/六亲/学业/性格/用神/大运/流年）
   - 每个命例标注：八字干支、性别、结论摘要、来源书籍
   - 命例独立列出，不混入理论分析中
5. 【垃圾跳过】带有 [AD] 标记的行直接忽略，不要纳入任何分析
```

### 5.2 命例数据库独立产出

Builder 额外产出 `cases_by_topic.json`：

```json
{
  "婚姻": [
    {
      "八字": "戊子 乙卯 丙辰 癸巳",
      "性别": "男",
      "结论": "2017年离婚，此女一直在超市打工",
      "来源": "《金镖门老人参辛丑弟子班笔记》",
      "相关条目": ["旺衰派.婚姻", "格局派.婚姻"]
    }
  ]
}
```

### 5.3 广告不再泄漏

去广告标注在规范化阶段完成（`[AD]`前缀），Builder Prompt明确跳过，最终百科不再出现广告内容。

### 5.4 删除 generate_html.py 中的广告清洗

`generate_html.py` 中的 `clean_ads()` 函数及30+条正则全部删除。前端不再承担清洗职责。

---

## 6. HTML 渲染升级

### 6.1 Markdown渲染

手写`renderMd`替换为 [`marked.js`](https://github.com/markedjs/marked)：

```javascript
// 改前
function renderMd(md) { /* 手写正则，不支持####/嵌套列表 */ }

// 改后
function renderMd(md) {
    return marked.parse(md, { breaks: true, gfm: true });
}
```

引入方式：CDN加载或内联到HTML，保持单文件独立。

### 6.2 命例数据库UI

在现有Web界面新增独立命例子面板：
- 按专题筛选（dropdown）
- 命例卡片展示（八字干支、结论、来源、跳转至对应百科条目）
- 与百科条目双向互跳

---

## 7. 影响评估

### 7.1 处理时间

- LLM规范化：每块 ~1秒，仅对有问题的块（预估30%），20块/批 → 约 5,000块 × 1秒 ≈ 1.5小时
- 全管道总时间：原~6h → 重构后~7-8h

### 7.2 改动范围

| 文件 | 变更类型 |
|------|----------|
| `src/bazi/preprocessor.py` | 重构：删除 `ContentCleaner`，重构 `SemanticChunker` |
| `src/bazi/preprocessor.py` | 新增：`LLMNormalizer` 类 |
| `src/bazi/encyclopedia_builder.py` | 重构：Prompt模板升级，案例分离逻辑 |
| `src/bazi/generate_html.py` | 重构：删除 `clean_ads()`，集成 `marked.js` |
| `tests/test_preprocessor.py` | 重构：适配新分块逻辑，新增Normalizer测试 |
| `tests/test_encyclopedia_builder.py` | 新增：案例归类测试 |

### 7.3 不修改的部分

- `FormatBridge`（格式转换层）
- `ContentVectorizer`（向量化与分类）
- `DedupPipeline`（聚类去重）
- SQLite/Qdrant 数据模型

---

## 8. 自审清单

- [x] 无 TBD/TODO 占位符
- [x] 五节设计一脉相承：LLM规范化→结构分块→案例分离→marked.js渲染
- [x] 范围聚焦于质量升级，不扩大功能范围
- [x] 每个问题的解决方案对应明确的代码变更
- [x] 输入/输出示例验证可行性
- [x] 处理时间估算在可接受范围
