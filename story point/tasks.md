# 开发任务清单

> MASE 2.0 Build 阶段 | Agent-3 (开发) 执行
> 基于设计文档 `docs/superpowers/specs/2026-07-21-story-point-estimator-design.md`

## 构建顺序

按依赖关系排序，每个 Capability 内的任务按 TDD 微循环执行（test → code → refactor）。

---

## C0: 项目脚手架与环境

**依赖**：无 | **预计文件**：8 个

- [ ] T0.1 创建 `.env.example` + `.gitignore`
- [ ] T0.2 创建 `config.py`（环境变量加载 + dataclass）
- [ ] T0.3 创建 `requirements.txt`（flask, openai, numpy, scikit-learn, openpyxl, python-dotenv, faiss-cpu, pytest, pytest-flask）
- [ ] T0.4 创建 `app.py` 最小 Flask 应用（`/` 返回空页面占位）
- [ ] T0.5 创建 `templates/base.html`（HTML5 骨架，引用 PILOT 风格）
- [ ] T0.6 验证：`python app.py` 可启动，浏览器访问 `localhost:5000` 能看到空白页面

---

## C1: Excel 模板下载与解析

**依赖**：C0 | **核心模块**：`utils/excel_handler.py`, `core/validator.py`

### TDD 微循环 1 — 斐波那契舍入

- [ ] T1.1 **RED**: `tests/unit/test_fibonacci.py` — 11 个测试用例
  ```
  4.5 → 5, 6.0 → 5, 6.5 → 8, 10.5 → 13,
  0.5 → 1, 0 → 1, 14 → 13,
  1.0 → 1, 2.0 → 2, 3.0 → 3, 5.0 → 5
  ```
- [ ] T1.2 **GREEN**: 实现 `utils/fibonacci.py` 的 `round_to_fibonacci()`
- [ ] T1.3 **REFACTOR**: 检查代码风格

### TDD 微循环 2 — Excel 校验器

- [ ] T1.4 **RED**: `tests/unit/test_validator.py` — 覆盖场景
  ```
  - 所有点数合法 → valid
  - 点数14 不在范围内 → 错误
  - 点数2 只有1条 → 错误
  - 点数13 缺0条 → 错误
  - 空标题 → 错误
  - 空描述 → 错误
  - 空数据 → 错误
  - 刚好12条覆盖全6个点数各2条 → valid
  ```
- [ ] T1.5 **GREEN**: 实现 `core/validator.py` 的 `validate_baseline()` + `check_min_per_point()`
- [ ] T1.6 **REFACTOR**: 提取错误消息模板常量

### TDD 微循环 3 — Excel 模板生成与解析

- [ ] T1.7 **RED**: `tests/unit/test_excel_handler.py` — 验证
  ```
  - generate_template → 文件存在，有4列表头
  - 故事点列有数据验证下拉框
  - parse_upload → 正确解析行数、列值
  - parse_upload → 空文件返回空列表
  ```
- [ ] T1.8 **GREEN**: 实现 `utils/excel_handler.py` 的 `generate_template()` + `parse_upload()`
- [ ] T1.9 **REFACTOR**: 提取列名常量

---

## C2: 基准故事管理与向量化

**依赖**：C1 | **核心模块**：`db/models.py`, `db/vector_store.py`, `core/embedding.py`, `services/baseline_service.py`

### TDD 微循环 4 — SQLite 数据模型

- [ ] T2.1 **RED**: `tests/integration/test_models.py` — 覆盖场景
  ```
  - 建表 → baseline_stories + estimate_history 存在
  - insert → 可查询
  - 全量替换 → 旧数据清除
  - 追加合并 → ID 冲突时跳过
  - 点数 CHECK 约束 → 14 被拒绝
  ```
- [ ] T2.2 **GREEN**: 实现 `db/models.py`（建表 + CRUD）
- [ ] T2.3 **REFACTOR**: 提取连接管理上下文管理器

### TDD 微循环 5 — FAISS 向量存储

- [ ] T2.4 **RED**: `tests/integration/test_vector_store.py`
  ```
  - 新建索引 → 可添加向量
  - 检索 → 返回最近邻
  - 保存 + 加载 → 向量一致
  - 空索引 → 检索报明确错误
  ```
- [ ] T2.5 **GREEN**: 实现 `db/vector_store.py`
- [ ] T2.6 **REFACTOR**: 封装索引重建逻辑

### TDD 微循环 6 — Embedding 客户端

- [ ] T2.7 **RED**: `tests/unit/test_embedding.py`（mock OpenAI API）
  ```
  - embed() → 返回预期维度向量
  - API 超时 → 重试3次后抛 EmbeddingAPIError
  - embed_batch() → 所有文本有对应向量
  ```
- [ ] T2.8 **GREEN**: 实现 `core/embedding.py` 的 `EmbeddingClient`
- [ ] T2.9 **REFACTOR**: 提取退避重试装饰器

### TDD 微循环 7 — 上传服务

- [ ] T2.10 **RED**: `tests/integration/test_baseline_service.py`
  ```
  - 上传有效文件 → 入库 + FAISS 索引同步
  - 上传无效文件 → 返回校验错误，不入库
  - 全量替换 → 旧数据清除，新数据入库
  - 追加合并 → 旧数据保留，新数据追加
  ```
- [ ] T2.11 **GREEN**: 实现 `services/baseline_service.py`
- [ ] T2.12 **REFACTOR**: 提取流程步骤为独立方法

---

## C3: 故事点估算引擎

**依赖**：C2 | **核心模块**：`core/estimator.py`, `core/reporter.py`, `services/estimate_service.py`

### TDD 微循环 8 — 估算核心算法

- [ ] T3.1 **RED**: `tests/unit/test_estimator.py`
  ```
  - compute_similarities: 相同向量 → 1.0, 正交 → 0.0
  - get_top_k: k=3 → 返回3个最高相似度索引
  - weighted_average: 1.0×5 + 0.5×3 → 4.33
  ```
- [ ] T3.2 **GREEN**: 实现 `core/estimator.py`
- [ ] T3.3 **REFACTOR**: numpy 向量化优化

### TDD 微循环 9 — LLM 报告生成

- [ ] T3.4 **RED**: `tests/unit/test_reporter.py`（mock Chat API）
  ```
  - generate() → 返回有效 JSON {estimate, confidence_min, confidence_max, reasoning, risk_notes}
  - API 超时 → degraded=true, 返回数值报告
  - API 返回非 JSON → 重试1次 → 仍失败则降级
  ```
- [ ] T3.5 **GREEN**: 实现 `core/reporter.py` 的 `ReportGenerator`
- [ ] T3.6 **REFACTOR**: 提取 Prompt 模板为独立文件/常量

### TDD 微循环 10 — 估算服务编排

- [ ] T3.7 **RED**: `tests/integration/test_estimate_service.py`
  ```
  - 有基准故事 → 估算成功，返回完整报告
  - 无基准故事 → 返回明确错误
  - Chat API 降级 → 标注 degraded=1
  - 历史记录写入 → estimate_history 表有记录
  ```
- [ ] T3.8 **GREEN**: 实现 `services/estimate_service.py`
- [ ] T3.9 **REFACTOR**: 提取进度回调接口

---

## C4: Web 交互界面

**依赖**：C3 | **核心模块**：`app.py`, `templates/`

### TDD 微循环 11 — Flask 路由

- [ ] T4.1 **RED**: `tests/integration/test_app_routes.py`
  ```
  - GET / → 200, HTML 包含 story-point-estimator 关键字
  - GET /template/download → 200, Content-Type: application/vnd.openxmlformats
  - POST /baseline/upload → 有效文件返回 {status, rows, distribution}
  - POST /baseline/upload → 无效文件返回 {errors}
  - POST /baseline/confirm → {action: "replace"} → 成功
  - POST /estimate → 返回 {estimate, confidence, report, degraded}
  - GET /history → 返回 JSON 数组
  ```
- [ ] T4.2 **GREEN**: 实现 `app.py` 所有路由
- [ ] T4.3 **REFACTOR**: 提取蓝图或路由分组

### TDD 微循环 12 — 前端模板与交互

- [ ] T4.4 **RED**: `tests/e2e/test_app_flow.spec.js`（Playwright）
  ```
  - 场景1：打开页面 → 看到"故事点估算助手"标题
  - 场景2：点击下载模板 → 浏览器下载 .xlsx
  - 场景3：上传有效Excel → 看到预览表格 + 点数分布
  - 场景4：上传无效Excel → 看到错误提示
  - 场景5：无基准时点估算 → 看到"请先上传基准故事集"
  - 场景6：输入需求+点估算 → 看到估算报告卡片
  ```
- [ ] T4.5 **GREEN**: 实现 `templates/index.html` + 内联 JS
- [ ] T4.6 **REFACTOR**: 提取 CSS 到 `static/style.css`

---

## C5: 收尾与文档

- [ ] T5.1 E2E 全流程验证（P0 6个场景全部通过）
- [ ] T5.2 `mase-state.yaml` phase 更新为 `build`
- [ ] T5.3 Git commit（每20次对话或每Capability完成）

---

## 任务统计

| Capability | TDD 微循环 | 测试文件 | 源文件 |
|------------|-----------|----------|--------|
| C0 脚手架 | 1 | 0 | 5 |
| C1 Excel | 3 | 2 | 2 |
| C2 向量化 | 4 | 3 | 4 |
| C3 估算 | 3 | 2 | 3 |
| C4 界面 | 2 | 2 | 2 |
| C5 收尾 | 1 | 0 | 0 |
| **合计** | **14** | **9** | **16** |
