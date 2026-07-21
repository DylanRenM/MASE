# 设计文档：用户故事增加"验收准则"字段

> MASE 2.0 阶段：Design | 关联 Agent：A1 (计划统管)
> 日期：2026-07-21

## 1. 概述

### 1.1 背景

当前用户故事只有"标题"和"描述"两个文本字段。验收准则（GWT 格式：Given-When-Then）是用户故事的细化描述，提供了更多场景信息。将验收准则作为独立字段加入，可以让 LLM 在特征提取和估算裁决时获得更丰富的上下文，提升估算准确性。

### 1.2 目标

- 数据链路全程支持验收准则：Excel 输入 → 解析 → 存储 → LLM Prompt → 前端展示
- 验收准则参与估算全链路：特征提取、估算报告、基准质量分析
- 字段可选，不影响现有不填验收准则的流程

### 1.3 关键设计决策

| 决策 | 选择 |
|------|------|
| 参与范围 | 全链路（feature_extractor + reporter + quality analysis） |
| 必填性 | 可选字段，可为空 |
| 列顺序 | ID → 标题 → 描述 → 验收标准 → 故事点 |
| 前端展示 | 完整展示，不折叠 |
| 批量估算 | 支持 |
| 向量兼容 | 不迁移，存量基线需重新上传 |

## 2. 数据模型

### 2.1 新增字段

```python
# stories dict 新增字段
{
    "id": str,
    "title": str,
    "description": str,
    "acceptance_criteria": str,  # 新增，可为空字符串
    "points": int,
}
```

### 2.2 数据库变更

`baseline_stories` 表新增列：

```sql
ALTER TABLE baseline_stories ADD COLUMN acceptance_criteria TEXT NOT NULL DEFAULT '';
```

新部署时 `init_db()` 直接包含该列。

`estimate_history` 表**不修改**——历史记录已存完整 `report_json`。

## 3. LLM Prompt 变更

### 3.1 特征提取（feature_extractor.py）

`FEATURE_EXTRACTION_PROMPT` 增加验收准则部分：

```
用户故事：
{title}
{description}

验收准则：
{acceptance_criteria}

请提取以下10个复杂度维度的数据：
...
```

验收准则为空时显示"（无）"。

### 3.2 估算报告（reporter.py）

`REPORT_PROMPT_TEMPLATE` 增加验收准则行：

```
待估算故事：
标题：{title}
描述：{description}
验收准则：{acceptance_criteria}
```

### 3.3 质量分析（baseline_service.py）

`_build_stories_summary()` 每行追加验收准则：

```
- {r['id']}: {r['title']}（{r['description']}）验收准则：{r['acceptance_criteria']}
```

## 4. Excel 模板

### 4.1 列结构

| 列 | A | B | C | D | E |
|----|---|---|---|---|---|
| 内容 | ID | 故事标题 | 故事描述 | 验收标准 | 故事点 |

### 4.2 模板变更

- `BASELINE_HEADERS`: `["ID", "故事标题", "故事描述", "验收标准", "故事点"]`
- `BATCH_HEADERS`: 同上
- `BATCH_RESULT_HEADERS`: 同上
- `generate_template()`: 生成 5 列，E 列（故事点）保持数据校验下拉
- `generate_batch_template()`: 同上
- `generate_batch_result()`: 导出结果包含验收标准

### 4.3 解析变更

`parse_upload()` 和 `parse_batch_upload()` 列索引调整：

```python
stories.append({
    "id": row[0].strip(),
    "title": row[1].strip(),
    "description": row[2].strip(),
    "acceptance_criteria": row[3].strip() if len(row) > 3 else "",  # 新增
    "points": int(row[4]) if len(row) > 4 else 0,                   # 原 row[3]
})
```

## 5. 校验

不增加验收准则的必填校验（可选字段）。

## 6. 服务变更

### 6.1 EstimateService

`estimate(title, description, acceptance_criteria="")`：

- `acceptance_criteria` 传给 `report_generator.generate()`
- 历史记录写入 `report_json`

### 6.2 BaselineService

- `parse_and_validate()` 返回的 `rows` 包含 `acceptance_criteria`
- `confirm()` 入库时持久化 `acceptance_criteria`
- `_build_stories_summary()` 包含验收准则（质量分析用）

## 7. API 变更

### 7.1 `POST /estimate`

请求体新增字段：

```json
{
    "title": "...",
    "description": "...",
    "acceptance_criteria": "..."
}
```

### 7.2 `POST /baseline/upload`

响应 `rows` 每个元素含 `acceptance_criteria` 字段。

### 7.3 `GET /baseline/list`

响应每个 story 对象含 `acceptance_criteria` 字段。

### 7.4 `POST /batch/estimate`

上传解析的 rows 含 `acceptance_criteria`；估算结果导出 Excel 含"验收标准"列。

## 8. 前端展示

### 8.1 估算表单

描述输入框下方新增验收准则输入框：

```html
<textarea id="story-acceptance" placeholder="验收标准（可选，GWT格式）
Given ...
When ...
Then ..."></textarea>
```

`doEstimate()` 读取并提交 `acceptance_criteria`。

### 8.2 基准故事列表

列顺序：ID → 标题 → 描述 → 验收标准 → 点数

### 8.3 上传预览区

同上列顺序，完整展示验收准则。

## 9. 向量空间兼容性

验收准则参与特征提取后，10 维复杂度向量的值域发生变化。**存量基线需重新上传**。不提供迁移脚本——基线数据由用户手动管理，数量小，重新上传成本低。

## 10. 测试策略

| 测试类型 | 覆盖内容 |
|----------|----------|
| 单元测试（Excel handler） | 5 列模板生成和解析；验收准则列可空 |
| 单元测试（feature_extractor） | prompt 含验收准则 |
| 单元测试（reporter） | prompt 含验收准则 |
| 单元测试（quality_evaluator） | 不受影响（只处理向量） |
| 集成测试（models） | insert/get 含 acceptance_criteria |
| 集成测试（baseline_service） | 上传/确认含验收准则 |
| 集成测试（app routes） | 各 API 正确传递 acceptance_criteria |
| 手动验证 | 重新上传基准故事，确认估算功能正常 |

## 11. 不做什么

- 不自动生成验收准则
- 不迁移存量基线向量
- 不修改 estimate_history 表结构
- 不增加验收准则的必填校验
