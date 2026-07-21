# 模块契约

> MASE 2.0 Design 阶段 | Agent-3 (开发) 契约推导
> 定义 API 契约、模块契约、Gherkin 验收场景

---

## 1. API 契约

### 1.1 下载模板

```
GET /template/download
```

| 项目 | 规格 |
|------|------|
| **前置条件** | 无 |
| **成功响应** | `200`, Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, Content-Disposition: `attachment; filename="baseline_template.xlsx"` |
| **错误响应** | `500` — 模板文件缺失或生成失败 |

### 1.2 上传基线故事

```
POST /baseline/upload
Content-Type: multipart/form-data
Body: file (required, .xlsx or .xls)
```

| 项目 | 规格 |
|------|------|
| **前置条件** | 无 |
| **成功响应** | `200`, `{"status": "ok", "rows": [...], "points_distribution": {1: 3, 2: 2, ...}}` |
| **校验失败** | `400`, `{"status": "error", "errors": ["第3行故事点不在允许范围内", ...]}` |
| **格式错误** | `400`, `{"status": "error", "errors": ["请上传 .xlsx 或 .xls 文件"]}` |

### 1.3 确认入库

```
POST /baseline/confirm
Content-Type: application/json
Body: {"action": "replace" | "append"}
```

| 项目 | 规格 |
|------|------|
| **前置条件** | 已通过 `/baseline/upload` 校验，数据在 session 中 |
| **成功响应** | `200`, `{"status": "ok", "count": 12}` |
| **无前置数据** | `400`, `{"status": "error", "errors": ["请先上传文件"]}` |
| **不变量** | 操作后 `baseline_stories` 表和 FAISS 索引保持同步 |

### 1.4 故事点估算

```
POST /estimate
Content-Type: application/json
Body: {"title": "微信扫码登录", "description": "集成微信OAuth..."}
```

| 项目 | 规格 |
|------|------|
| **前置条件** | `baseline_stories` 至少 12 条（每个点数 ≥2） |
| **成功响应** | `200`, `{"estimate": 8, "confidence_min": 5, "confidence_max": 13, "reasoning": "...", "risk_notes": "...", "top_matches": [...], "degraded": false}` |
| **LLM 降级** | `200`, `{"estimate": 8, ..., "degraded": true, "note": "LLM 不可用，以下为数值估算结果"}` |
| **无基准数据** | `400`, `{"status": "error", "errors": ["请先上传基准故事集"]}` |
| **后置条件** | `estimate_history` 表新增 1 条记录 |

### 1.5 估算历史

```
GET /history
```

| 项目 | 规格 |
|------|------|
| **前置条件** | 无 |
| **成功响应** | `200`, `[{"id": 1, "title": "微信扫码登录", "estimate": 8, "created_at": "2026-07-21T10:00:00"}, ...]` |
| **空历史** | `200`, `[]` |

---

## 2. 模块级契约

### 2.1 core/fibonacci.py

```python
FIB_SCALES: list[int] = [1, 2, 3, 5, 8, 13]

def round_to_fibonacci(value: float) -> int:
    """
    前置条件: value >= 0
    后置条件: result ∈ {1, 2, 3, 5, 8, 13}
    不变量: |result - value| 在所有刻度中最小
    边界: value < 1 → 1; value > 13 → 13; value == 4.5 → 5
    """
```

### 2.2 core/validator.py

```python
class ValidationResult:
    valid: bool
    errors: list[str]

def validate_baseline(rows: list[dict]) -> ValidationResult:
    """
    前置条件: rows 为 list[dict]，每个 dict 含 id, title, description, points
    后置条件: valid=True ⇔ 所有规则通过
    不变量: errors 按行号升序排列
    """

def check_min_per_point(rows: list[dict]) -> dict[int, int]:
    """
    前置条件: rows 非空
    后置条件: result.keys() ⊆ {1, 2, 3, 5, 8, 13}
    后置条件: sum(result.values()) == len(rows)
    """
```

### 2.3 utils/excel_handler.py

```python
def generate_template(filepath: str) -> None:
    """
    前置条件: filepath 父目录存在且可写
    后置条件: 文件存在，含 "基准故事" sheet，A1:D1 为表头
    后置条件: D 列有数据验证下拉框 {1,2,3,5,8,13}
    """

def parse_upload(filepath: str) -> list[dict]:
    """
    前置条件: filepath 指向有效的 .xlsx/.xls 文件
    后置条件: 返回 list[dict]，每个 dict 含 id, title, description, points
    不变量: len(result) 等于数据行数（不含表头）
    """
```

### 2.4 core/estimator.py

```python
def compute_similarities(new_vector: np.ndarray, baseline_vectors: np.ndarray) -> np.ndarray:
    """
    前置条件: new_vector.shape == (D,), baseline_vectors.shape == (N, D)
    后置条件: result.shape == (N,), 0 <= result[i] <= 1
    不变量: 相同向量 → 1.0
    """

def get_top_k(similarities: np.ndarray, k: int = 3) -> list[tuple[int, float]]:
    """
    前置条件: len(similarities) >= k
    后置条件: len(result) == k, result 按相似度降序
    """

def weighted_average(indices: list[int], similarities: np.ndarray, points: list[int]) -> float:
    """
    前置条件: len(indices) >= 1, 所有 similarities > 0
    后置条件: min(points) <= result <= max(points)
    """
```

### 2.5 core/embedding.py

```python
class EmbeddingClient:
    def embed(self, text: str) -> np.ndarray:
        """
        前置条件: text 非空, API 配置有效
        后置条件: result.shape == (D,), D 为模型维度
        异常: EmbeddingAPIError — 3 次重试后仍失败
        """

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        前置条件: 所有 text 非空
        后置条件: result.shape == (N, D)
        不变量: result[i] 对应 texts[i]
        """
```

### 2.6 core/reporter.py

```python
class ReportGenerator:
    def generate(self, title: str, description: str,
                 top_k_stories: list[dict], similarities: list[float],
                 weighted_avg: float) -> dict:
        """
        前置条件: title 和 description 非空,
                 len(top_k_stories) == len(similarities) >= 1
        后置条件 (成功): result == {
            "estimate": int ∈ {1,2,3,5,8,13},
            "confidence_min": int,
            "confidence_max": int,
            "reasoning": str,
            "risk_notes": str,
            "degraded": False
        }
        后置条件 (降级): result == {
            "estimate": int,
            "degraded": True,
            "reasoning": "LLM 不可用，基于加权平均的数值估算结果"
        }
        不变量: estimate 始终有值（不抛异常）
        """
```

### 2.7 db/models.py

```python
class BaselineRepository:
    def insert_batch(self, stories: list[dict]) -> int:
        """前置条件: stories 非空; 后置条件: 返回插入行数"""

    def replace_all(self, stories: list[dict]) -> int:
        """前置条件: 无; 后置条件: 旧数据清除，返回插入行数"""

    def get_all(self) -> list[dict]:
        """后置条件: 按 faiss_index 升序返回"""

    def get_by_faiss_index(self, index: int) -> dict | None:
        """后置条件: 找到返回 dict，否则 None"""

    def count_by_point(self) -> dict[int, int]:
        """后置条件: result.keys() ⊆ {1,2,3,5,8,13}"""

class HistoryRepository:
    def add(self, title: str, description: str, estimate: int,
            confidence_min: int | None, confidence_max: int | None,
            report_json: str, degraded: bool) -> int:
        """后置条件: 返回新增记录 ID"""

    def get_recent(self, limit: int = 20) -> list[dict]:
        """后置条件: 按 created_at 降序，最多 limit 条"""
```

### 2.8 db/vector_store.py

```python
class VectorStore:
    def build_index(self, vectors: np.ndarray):
        """前置条件: vectors.shape == (N, D), N >= 1; 后置条件: 索引可检索"""

    def search(self, query: np.ndarray, k: int = 3) -> list[tuple[int, float]]:
        """前置条件: 索引已构建; 后置条件: len(result) == k"""

    def save(self, filepath: str):
        """前置条件: 索引已构建, 目录可写"""

    def load(self, filepath: str) -> bool:
        """后置条件: True⇔加载成功且索引可用; False⇔文件不存在或损坏"""
```

---

## 3. Gherkin 验收场景

### C1: Excel 模板下载与解析

```gherkin
Feature: Excel 模板下载与解析

  Scenario: 下载空白模板
    Given 用户访问首页
    When 用户点击"下载模板"按钮
    Then 浏览器开始下载 baseline_template.xlsx
    And 文件包含 "基准故事" sheet
    And A1:D1 分别是 ID、故事标题、故事描述、故事点
    And D 列有下拉数据验证 {1,2,3,5,8,13}

  Scenario: 解析有效的基线故事Excel
    Given 用户有一个包含 12 条故事的 Excel 文件
    And 每个点数 (1,2,3,5,8,13) 各 2 条
    When 用户上传该文件
    Then 系统返回 status=ok
    And 预览展示 12 行数据
    And 点数分布正确显示

  Scenario: 解析包含非法点数的Excel
    Given 用户有一个包含非法点数 14 的 Excel 文件
    When 用户上传该文件
    Then 系统返回 status=error
    And 错误信息包含"第X行故事点不在允许范围内"

  Scenario: 某点数不足两条
    Given 用户上传的 Excel 中点数 8 只有 1 条
    When 用户上传该文件
    Then 系统返回 status=error
    And 错误信息包含"点数8只有1条，至少需要2条"
```

### C2: 基准故事管理与向量化

```gherkin
Feature: 基准故事管理与向量化

  Scenario: 确认入库（全量替换）
    Given 系统中已有 12 条旧基准故事
    And 用户上传了新的 12 条基准故事通过校验
    When 用户选择"全量替换"并确认
    Then 旧数据全部清除
    And 新数据入库成功
    And FAISS 索引重建完成
    And 系统返回 count=12

  Scenario: 确认入库（追加合并）
    Given 系统中已有 6 条基准故事
    And 用户上传了新的 6 条基准故事通过校验
    When 用户选择"追加合并"并确认
    Then 旧数据保留
    And 新数据追加入库
    And FAISS 索引更新
    And 系统返回 count=12
```

### C3: 故事点估算引擎

```gherkin
Feature: 故事点估算引擎

  Scenario: 成功估算新需求
    Given 系统已加载 12 条基准故事
    When 用户输入标题"微信扫码登录"
    And 用户输入描述"集成微信OAuth2.0，实现扫码登录功能"
    And 点击"开始估算"
    Then 系统返回估算报告
    And 报告包含 推荐点数、置信区间、Top3参考基准、估算依据、风险提示
    And estimate_history 表中新增 1 条记录

  Scenario: 无基准故事时估算
    Given 系统中没有基准故事
    When 用户尝试估算
    Then 系统提示"请先上传基准故事集"
    And 估算区保持置灰状态

  Scenario: LLM不可用时降级
    Given 系统已加载基准故事
    And Chat API 不可用
    When 用户点击估算
    Then 系统返回纯数值估算报告
    And 报告中标注"⚠️ LLM 不可用"
    And degraded 字段为 true
```

### C4: Web 交互界面

```gherkin
Feature: Web 交互界面

  Scenario: 页面初始状态
    Given 用户首次访问首页
    When 页面加载完成
    Then 显示"故事点估算助手"标题
    And 显示"基准故事管理"区域
    And 显示"新需求估算"区域
    And 显示"估算历史"区域
    And 新需求估算区处于置灰状态

  Scenario: 上传后状态更新
    Given 用户成功上传并确认 12 条基准故事
    When 页面状态更新
    Then 状态显示"✓ 已加载 12 条"
    And 新需求估算区变为可交互状态

  Scenario: 估算历史记录
    Given 用户已完成 3 次估算
    When 用户查看"估算历史"区域
    Then 显示 3 条记录
    And 每条记录显示标题和估算点数
    And 按时间倒序排列
```

---

## 4. 不变式总结

| 不变式 | 检查层 |
|--------|--------|
| `baseline_stories` 行数 == FAISS 向量数 | DB + VectorStore |
| 所有 stories.points ∈ {1,2,3,5,8,13} | Validator (DB CHECK + 上传校验) |
| estimate_history 只增不删 | HistoryRepository (INSERT only) |
| `round_to_fibonacci(x)` ∈ {1,2,3,5,8,13} | fibonacci.py 后置条件 |
| 降级报告的 `degraded` 必为 true | reporter.py 后置条件 |
