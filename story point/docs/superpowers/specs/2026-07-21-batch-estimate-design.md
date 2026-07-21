# 设计文档：批量故事点估算

> 关联项目：StoryPoint Estimator AI v2.0 | 2026-07-21

## 1. 需求

支持批量估算：下载模板 → 填入多条待估算故事 → 上传 → 返回估算结果Excel文件下载。

## 2. 数据流

```
下载模板(Excel: ID,标题,描述) → 用户填入 → 上传
  → 逐行: FeatureExtractor → FeatureEncoder → FAISS → weighted_avg
  → 生成结果Excel: ID,标题,描述,估算点数,置信下限,置信上限,估算依据,风险提示
  → 返回下载
```

## 3. API 设计

### GET /batch/template
下载批量估算模板 Excel。列：ID、标题、描述。

### POST /batch/estimate
上传填写好的 Excel，返回估算结果文件下载。

请求: multipart/form-data，file 字段
响应: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

处理逻辑:
1. 解析 Excel，提取每行的 ID、标题、描述
2. 逐行调用 `estimate_service.estimate(title, description)`
3. 将结果写入 Excel 并返回

## 4. 文件变更

| 文件 | 操作 |
|------|------|
| `utils/excel_handler.py` | 新增 `generate_batch_template()` + `generate_batch_result()` |
| `app.py` | 新增 `GET /batch/template` + `POST /batch/estimate` |
| `templates/index.html` | 新增批量估算区域（模板下载 + 上传按钮） |

## 5. 输出 Excel 格式

| 列 | 说明 |
|----|------|
| ID | 故事编号 |
| 标题 | 故事标题 |
| 描述 | 故事描述 |
| 估算点数 | Fibonacci 值 |
| 置信下限 | min |
| 置信上限 | max |
| 估算依据 | reasoning |
| 风险提示 | risk_notes |
