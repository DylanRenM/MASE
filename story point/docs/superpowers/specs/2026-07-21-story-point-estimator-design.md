# 设计文档：AI故事点估算助手

> MASE 2.0 阶段：Design | 关联 Agent：A1 (计划统管)
> 目标项目：合并至 PILOT (COSMIC智能化度量工具)

## 1. 系统架构

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                   Flask Web Server (app.py)              │
│  ┌──────────┐ ┌─────────────┐ ┌──────────┐ ┌─────────┐ │
│  │ 路由注册  │ │ 模板渲染    │ │ 静态服务  │ │ API响应 │ │
│  │          │ │ (Jinja2)   │ │          │ │ (JSON)  │ │
│  └────┬─────┘ └──────┬──────┘ └──────────┘ └────┬────┘ │
└───────┼──────────────┼──────────────────────────┼───────┘
        │              │                          │
        ▼              ▼                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Services 层 (业务编排)                 │
│  ┌────────────────────┐ ┌──────────────────────────┐    │
│  │ baseline_service   │ │ estimate_service          │    │
│  │ 上传→校验→向量化→入库│ │ 输入→检索→加权→LLM裁决→报告│    │
│  └────────┬───────────┘ └───────────┬──────────────┘    │
└───────────┼─────────────────────────┼───────────────────┘
            │                         │
            ▼                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Core 层 (纯领域逻辑)                   │
│  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ estimator  │ │embedding │ │ reporter │ │validator │ │
│  │ 相似度计算 │ │API封装   │ │LLM报告   │ │Excel校验 │ │
│  │ TopK检索   │ │重试/降级 │ │Prompt构建│ │规则检查  │ │
│  │ 加权平均   │ │          │ │          │ │          │ │
│  └────────────┘ └──────────┘ └──────────┘ └──────────┘ │
│  ┌────────────┐ ┌──────────┐                            │
│  │excel_handler│ │fibonacci │                            │
│  │模板生成/解析│ │刻度舍入  │                            │
│  └────────────┘ └──────────┘                            │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│                    DB 层 (数据持久化)                     │
│  ┌──────────────────┐  ┌──────────────────────────────┐ │
│  │ SQLite            │  │ FAISS 向量索引               │ │
│  │ baseline_stories  │  │ data/faiss_baseline.index    │ │
│  │ estimate_history  │  │                              │ │
│  └──────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 1.2 职责边界

| 层 | 依赖 | 禁止依赖 |
|----|------|----------|
| Core | 无（纯 Python 标准库 + numpy） | Flask、SQLite、FAISS、文件系统 |
| Services | Core + DB | Flask（通过接口抽象） |
| DB | SQLite / FAISS | Core、Services、Flask |
| App (Flask) | Services | Core、DB（通过 Services 调用） |

### 1.3 对齐 PILOT 架构

| PILOT | StoryPoint |
|-------|------------|
| `cosmic_web.py` (Flask 入口) | `app.py` |
| `cosmic_metric_tool.py` (核心算法) | `core/estimator.py` + `core/reporter.py` |
| Jinja2 `templates/` | `templates/base.html` + `index.html` |
| `settings.json` (配置) | `config.py` (环境变量) |
| `cosmic.db` (SQLite) | `data/storypoint.db` |

## 2. 核心组件设计

### 2.1 估算器 (core/estimator.py)

```python
def compute_similarities(new_vector: np.ndarray, baseline_vectors: np.ndarray) -> np.ndarray:
    """计算新需求与所有基准故事的余弦相似度。"""
    ...

def get_top_k(similarities: np.ndarray, k: int = 3) -> list[tuple[int, float]]:
    """返回 TopK 的 (基准索引, 相似度) 列表，按相似度降序。"""
    ...

def weighted_average(top_indices: list[int], similarities: np.ndarray,
                     baseline_points: list[int]) -> float:
    """加权平均 = Σ(sim_i * points_i) / Σ(sim_i)。"""
    ...

def round_to_fibonacci(value: float) -> int:
    """四舍五入到最近斐波那契刻度 {1,2,3,5,8,13}。
       边界：4.5 → 5（向上取整避免低估）。"""
    ...
```

### 2.2 Embedding 封装 (core/embedding.py)

```python
class EmbeddingClient:
    def __init__(self, config: EmbeddingConfig):
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.model = config.model
        self.max_retries = 3

    def embed(self, text: str) -> np.ndarray:
        """生成单条文本的 Embedding 向量，含指数退避重试。"""
        ...

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """批量生成 Embedding 向量。"""
        ...
```

### 2.3 LLM 报告生成 (core/reporter.py)

```python
REPORT_PROMPT_TEMPLATE = """
你是故事点估算专家。基准刻度：1, 2, 3, 5, 8, 13。

新需求：
- 标题：{title}
- 描述：{description}

数值估算结果：{weighted_result} 点

最相似的 3 条基准故事：
{baseline_details}

请综合判断，严格按照以下 JSON 格式返回（不要包含其他文字）：
{{"estimate": <1|2|3|5|8|13>,
  "confidence_min": <integer>,
  "confidence_max": <integer>,
  "reasoning": "<中文估算依据>",
  "risk_notes": "<中文风险提示>"}}
"""

class ReportGenerator:
    def __init__(self, config: ChatConfig):
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.model = config.model

    def generate(self, title: str, description: str,
                 top_k_stories: list[dict], similarities: list[float],
                 weighted_avg: float) -> dict:
        """调用 Chat API 生成结构化估算报告。
           API 失败或返回非 JSON 时降级为纯数值报告。"""
        ...
```

### 2.4 Excel 校验器 (core/validator.py)

```python
class ValidationResult:
    valid: bool
    errors: list[str]  # 人类可读的错误描述

def validate_baseline(rows: list[dict]) -> ValidationResult:
    """
    校验规则（全部通过才为 valid）：
    1. 至少 1 行数据
    2. 故事点全部在 {1,2,3,5,8,13} 中
    3. 每个点数 (1,2,3,5,8,13) 至少 2 条
    4. 标题和描述均不为空
    """
    ...

def check_min_per_point(rows: list[dict]) -> dict[int, int]:
    """返回每个点数的计数，用于识别缺口。
       {1: 3, 2: 1, 3: 2, 5: 2, 8: 2, 13: 0}
       → 点数 2 只有 1 条，点数 13 只有 0 条"""
    ...
```

### 2.5 Excel 处理器 (utils/excel_handler.py)

```python
def generate_template(filepath: str):
    """生成基线故事模板 Excel，含表头和数据验证下拉框。"""
    ...

def parse_upload(filepath: str) -> list[dict]:
    """解析上传的 Excel 文件，返回行列表。
       [{id: "S1", title: "修改Logo", description: "...", points: 1}, ...]"""
    ...
```

## 3. 数据模型

### 3.1 SQLite 表结构

```sql
CREATE TABLE baseline_stories (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    points      INTEGER NOT NULL CHECK(points IN (1,2,3,5,8,13)),
    faiss_index INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE estimate_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT NOT NULL,
    description    TEXT NOT NULL,
    estimate       INTEGER NOT NULL,
    confidence_min INTEGER,
    confidence_max INTEGER,
    report_json    TEXT,
    degraded       INTEGER DEFAULT 0,   -- 1=LLM降级为纯数值
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 FAISS 索引

```
data/faiss_baseline.index     ← 二进制文件，启动时自动加载
```

FAISS 索引位置 `i` 对应 SQLite 中 `faiss_index = i` 的记录。上传时同步更新索引文件。

## 4. API / 路由设计

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| `GET` | `/` | - | HTML 页面 |
| `GET` | `/template/download` | - | Excel 文件流 |
| `POST` | `/baseline/upload` | `multipart/form-data` (file) | `{status, rows, points_distribution, errors}` |
| `POST` | `/baseline/confirm` | `{action: "replace" \| "append"}` | `{status, count}` |
| `POST` | `/estimate` | `{title, description}` | `{estimate, confidence, report, degraded}` |
| `GET` | `/history` | - | `[{id, title, estimate, created_at}, ...]` |

### 4.1 交互流程

```
GET / → 页面加载
  │
  ├── [下载模板] → GET /template/download → 浏览器下载 .xlsx
  │
  ├── [上传Excel] → POST /baseline/upload
  │     → 校验 → 返回预览 {rows, distribution, errors}
  │     → 用户确认 → 弹窗选择"替换"或"追加"
  │     → POST /baseline/confirm {action} → 入库 + 向量化
  │     → 返回 {status: "ok", count: 12}
  │
  ├── [输入需求 + 点估算] → POST /estimate {title, description}
  │     → 阶段一：检索 + 加权平均
  │     → 阶段二：LLM 裁决（或降级）
  │     → 返回结构化报告 JSON
  │
  └── [历史记录] → GET /history → 侧栏列表
```

## 5. 前端页面设计

### 5.1 布局（Jinja2 模板）

```
┌──────────────────────────────────────────────────────┐
│  📊 故事点估算助手                                    │
├──────────────────────────────┬───────────────────────┤
│  📤 基准故事管理              │  📋 估算历史           │
│  [📥 下载模板] [📤 上传Excel] │  ┌─────────────────┐ │
│  状态: ✓ 已加载 12 条        │  │ 微信登录 → 8    │ │
│                              │  │ 导出Excel → 5   │ │
├──────────────────────────────┤  └─────────────────┘ │
│  🚀 新需求估算                │                      │
│  标题: [________________]    │                      │
│  描述: [________________]    │                      │
│        [________________]    │                      │
│  [🔮 开始估算]               │                      │
│                              │                      │
│  ┌─ 估算报告 ───────────────┐│                      │
│  │  推荐点数: 8              ││                      │
│  │  置信区间: 5 ~ 13        ││                      │
│  │  🔍 参考基准              ││                      │
│  │  S4 第三方支付  8点  92% ││                      │
│  │  S5 积分排行   13点  78% ││                      │
│  │  S3 导出Excel   5点  45% ││                      │
│  │  📝 估算依据: ...        ││                      │
│  │  ⚠️ 风险提示: ...       ││                      │
│  └──────────────────────────┘│                      │
└──────────────────────────────┴───────────────────────┘
```

### 5.2 状态转换

- **空状态**：无基准故事时，估算区置灰，显示"请先上传基准故事集"
- **上传中**：显示解析进度 + 预览表格
- **向量化中**：显示进度"正在为 N 条基准故事生成向量..."
- **估算中**：三阶段进度（分析需求 → 检索基准 → 生成报告）
- **估算完成**：展示结构化报告卡片
- **错误状态**：内联红色提示，不刷新页面

## 6. 核心算法

### 6.1 两阶段估算

```
阶段一（数值计算）：
  新需求文本 → Embedding → 余弦相似度(Top3) → 加权平均 → 斐波那契舍入 → 粗估点数

阶段二（LLM 裁决）：
  Prompt(Top3详情 + 粗估点数) → Chat API → JSON解析 → 最终报告
  ↓ API 失败
  降级：纯数值报告（标注 ⚠️ LLM 不可用）
```

### 6.2 余弦相似度

```
similarity(A, B) = (A · B) / (||A|| × ||B||)
```

### 6.3 加权平均

```
weighted_avg = Σ(similarity_i × points_i) / Σ(similarity_i)
```

### 6.4 斐波那契舍入

```
FIB_SCALES = [1, 2, 3, 5, 8, 13]
round_to_fibonacci(4.5) = 5   (向上取整避免低估)
round_to_fibonacci(6.0) = 5
round_to_fibonacci(6.5) = 8
round_to_fibonacci(10.5) = 13
```

## 7. 错误处理

### 7.1 分层策略

| 层 | 错误类型 | 处理 |
|----|----------|------|
| 前端 | 格式错误、空输入 | 即时 JS 校验，内联提示 |
| API | 校验失败 | 400 + 结构化错误 {"errors": [...]} |
| Service | Embedding 不可用 | 阻断，提示用户检查配置 |
| Service | Chat API 不可用 | 降级为纯数值报告 |
| Service | Chat 返回非 JSON | 重试 1 次，仍失败则降级 |
| DB | FAISS 索引损坏 | 提示重新上传基准故事 |

### 7.2 Embedding 重试

```
第1次失败 → 等待 1s → 第2次 → 等待 2s → 第3次 → 阻断
```

## 8. 测试策略 (TDD)

### 8.1 三层防线

| 层级 | 工具 | 覆盖范围 |
|------|------|----------|
| 单元测试 | pytest | `core/` + `utils/` 所有纯函数 |
| 集成测试 | pytest + SQLite :memory: | `services/` + `db/` 编排流程 |
| E2E 测试 | Playwright | 完整 HTTP 交互流程 |

### 8.2 关键测试用例

**单元测试：**
- `round_to_fibonacci`: 边界值 (4.5→5, 6.0→5, 6.5→8, 0→1, 14→13)
- `compute_similarities`: 相同向量 → 1.0，正交向量 → 0.0
- `validate_baseline`: 每点数≥2、点数范围、空标题检测
- ReportGenerator 降级：mock Chat API 失败 → 返回纯数值报告

**集成测试：**
- 上传→校验→入库→FAISS→检索 全链路
- 全量替换 vs 追加合并
- Chat API 超时 → 降级报告标注 degraded=1

**E2E 测试：**
- 下载模板 → 上传有效文件 → 点数分布显示正确 → 估算成功
- 上传无效文件 → 看到校验错误信息
- 无基准故事时点击估算 → 看到提示

## 9. 配置管理

### 9.1 环境变量 (.env)

```
# Embedding 模型配置
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-xxx
EMBEDDING_MODEL=text-embedding-3-small

# Chat 模型配置
CHAT_BASE_URL=https://api.deepseek.com/v1
CHAT_API_KEY=sk-xxx
CHAT_MODEL=deepseek-chat

# 应用配置
TOP_K=3
DATABASE_PATH=data/storypoint.db
FAISS_INDEX_PATH=data/faiss_baseline.index
```

### 9.2 配置加载 (config.py)

```python
from dataclasses import dataclass
import os

@dataclass
class EmbeddingConfig:
    base_url: str
    api_key: str
    model: str

@dataclass
class ChatConfig:
    base_url: str
    api_key: str
    model: str

@dataclass
class AppConfig:
    top_k: int = 3
    database_path: str = "data/storypoint.db"
    faiss_index_path: str = "data/faiss_baseline.index"

def load_config() -> tuple[EmbeddingConfig, ChatConfig, AppConfig]:
    ...
```

## 10. 文件结构

```
storypoint_estimator/
├── app.py                      # Flask 应用入口
├── config.py                   # 环境变量加载
├── core/
│   ├── __init__.py
│   ├── embedding.py            # Embedding API 封装
│   ├── estimator.py            # 相似度计算、TopK、加权平均
│   ├── reporter.py             # LLM 报告生成
│   └── validator.py            # Excel 校验规则
├── services/
│   ├── __init__.py
│   ├── baseline_service.py     # 基准故事上传流程
│   └── estimate_service.py     # 估算流程
├── db/
│   ├── __init__.py
│   ├── models.py               # SQLite 表定义与操作
│   └── vector_store.py         # FAISS 索引封装
├── utils/
│   ├── __init__.py
│   ├── excel_handler.py        # Excel 模板生成与解析
│   └── fibonacci.py            # 斐波那契刻度舍入
├── templates/
│   ├── base.html               # 页面骨架
│   └── index.html              # 主页面
├── static/
│   └── baseline_template.xlsx  # 可下载模板
├── data/
│   ├── .gitkeep
│   ├── storypoint.db           # 运行时 SQLite（自动生成）
│   └── faiss_baseline.index    # FAISS 索引（自动生成）
├── tests/
│   ├── unit/
│   │   ├── test_estimator.py
│   │   ├── test_fibonacci.py
│   │   ├── test_validator.py
│   │   └── test_reporter.py
│   ├── integration/
│   │   ├── test_baseline_service.py
│   │   └── test_estimate_service.py
│   └── e2e/
│       └── test_app_flow.spec.js
├── requirements.txt
├── .env.example
└── .gitignore
```

## 11. 决策记录

| 维度 | 决策 | 理由 |
|------|------|------|
| 算法 | Top3 加权 + LLM 裁决，Chat 失败降级 | 兼顾准确性和鲁棒性 |
| 基线门槛 | 每点数 ≥2 条，共 ≥12 条 | 确保 LLM 有足够参照物做类比推理 |
| LLM 供应商 | 灵活可配，Embedding / Chat 独立 | 支持国内多种 API 兼容接口 |
| 持久化 | SQLite + FAISS 索引文件 | 对齐 PILOT，重启自动恢复 |
| 重复上传 | 用户选择全量替换或追加合并 | 覆盖"纠正"和"增量"两种场景 |
| 技术架构 | Flask + Jinja2 | 对齐 PILOT 主架构，后续合并零成本 |
| 过程框架 | MASE 2.0 六阶段门禁 | 四 Agent 协作，PDCA 闭环 |
| 测试 | TDD 三层防线 | 单元→集成→E2E，对齐八大工程原则 |

## 12. 兼容性（与 PILOT 合并）

- 数据库文件独立 (`storypoint.db` vs `cosmic.db`)，不冲突
- 路由前缀可配置，嵌入 PILOT 时加 `/storypoint` 前缀
- 模板可复用 PILOT 的 `base.html` 骨架
- Core 层零依赖，可直接 `pip install` 到 PILOT 环境
- FAISS 依赖 (`faiss-cpu`) 在 PILOT `requirements.txt` 中新增

## 13. 未来扩展

- 支持自定义斐波那契刻度（如 20, 40, 100）
- 多轮对话式估算：用户反馈 → LLM 调整
- 团队协作：多人对同一需求独立估算 → 展示分歧
- 估算报告导出 PDF / Markdown
