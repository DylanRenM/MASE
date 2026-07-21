"""特征提取器。

调用LLM API提取用户故事的复杂度特征（10个维度），用于替代原有的文本Embedding方案。
"""

import json
import re
import time

# ── 特征提取 Prompt 模板 ──────────────────────────────

FEATURE_EXTRACTION_PROMPT = """你是一个软件工程需求分析专家。请分析以下用户故事，提取其复杂度特征。

## 用户故事
标题：{story_title}
描述：{story_description}

## 验收准则
{acceptance_criteria}

## 输出格式
请严格按照以下JSON格式输出，不要添加任何额外文字：

{{
  "frontend_pages": 数字,          // 涉及前端页面数：0,1,2,3
  "backend_interfaces": 数字,      // 涉及后端接口数：0,1,2,3
  "db_change": "是/否",            // 是否涉及数据库变更（新增表/字段/索引）
  "external_dependency": "是/否",  // 是否涉及外部系统对接（第三方API、外部服务）
  "async_processing": "是/否",     // 是否涉及异步处理（消息队列、定时任务、回调通知）
  "transaction_required": "是/否", // 是否涉及事务一致性（强一致性、分布式事务）
  "business_branches": 数字,       // 业务规则分支数：1,2,3,4,5+
  "permission_control": "是/否",   // 是否涉及权限控制（RBAC、数据权限、按钮级权限）
  "data_migration": "是/否",       // 是否涉及数据迁移（历史数据清洗/导入/转换）
  "cache_design": "是/否"          // 是否涉及缓存设计（Redis、本地缓存、缓存策略）
}}

## 判断标准参考
- frontend_pages：涉及多少个独立页面/弹窗/表单？纯后端接口返回0
- backend_interfaces：需要新增或修改多少个API接口？
- db_change：是否要执行DDL语句（CREATE/ALTER TABLE）？
- external_dependency：是否调用外部API（微信、短信、支付、第三方系统）？
- async_processing：是否用到MQ、定时任务、Webhook回调？
- transaction_required：多个操作是否需要保证原子性（全部成功或全部失败）？
- business_branches：主流程中有多少个if-else/状态机分支？
- permission_control：是否需要区分不同角色看到不同数据或操作按钮？
- data_migration：是否需要写脚本迁移旧数据？
- cache_design：是否需要引入Redis缓存来提升性能？

请仅输出JSON，不要有其他内容。"""


class FeatureExtractionError(Exception):
    """特征提取失败异常。"""


class FeatureExtractor:
    """调用LLM提取用户故事的复杂度特征。

    Attributes:
        model: 使用的LLM模型名称。
    """

    def __init__(self, base_url: str, api_key: str, model: str, max_retries: int = 3):
        self.model = model
        self._max_retries = max_retries
        self._base_url = base_url
        self._api_key = api_key
        self._client = None  # 延迟初始化

    def _get_client(self):
        """获取 OpenAI 客户端实例（复用）。"""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        return self._client

    def extract(self, title: str, description: str, acceptance_criteria: str = "") -> dict:
        """提取单个用户故事的复杂度特征。

        前置条件: title 和 description 非空。
        后置条件: 返回包含10个特征字段的字典。

        Args:
            title: 故事标题。
            description: 故事描述。
            acceptance_criteria: 验收准则（可选，GWT格式）。

        Returns:
            {
                "frontend_pages": int,
                "backend_interfaces": int,
                "db_change": "是/否",
                "external_dependency": "是/否",
                "async_processing": "是/否",
                "transaction_required": "是/否",
                "business_branches": int,
                "permission_control": "是/否",
                "data_migration": "是/否",
                "cache_design": "是/否"
            }

        Raises:
            FeatureExtractionError: 重试 max_retries 次后仍失败。
        """
        last_error = None
        ac_text = acceptance_criteria.strip() if acceptance_criteria else "（无）"

        for attempt in range(self._max_retries):
            try:
                prompt = FEATURE_EXTRACTION_PROMPT.format(
                    story_title=title,
                    story_description=description,
                    acceptance_criteria=ac_text,
                )
                raw_response = self._call_api(prompt)
                features = self._parse_response(raw_response)
                self._validate_features(features)
                return features
            except (FeatureExtractionError, json.JSONDecodeError, ValueError) as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    time.sleep(wait)
            except Exception as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    time.sleep(2 ** attempt)

        raise FeatureExtractionError(
            f"特征提取失败（重试 {self._max_retries} 次）: {last_error}"
        )

    def extract_batch(self, stories: list[dict]) -> list[dict]:
        """批量提取故事特征（逐个调用LLM）。

        前置条件: 每个story包含 'title', 'description', 可选 'acceptance_criteria' 键。
        后置条件: 返回的features列表与输入stories一一对应。

        Args:
            stories: [{"id": ..., "title": ..., "description": ..., "acceptance_criteria": ..., "points": ...}, ...]

        Returns:
            [{"frontend_pages": ..., ...}, ...]，与stories一一对应。

        Raises:
            FeatureExtractionError: 任一故事提取失败时抛出。
        """
        return [self.extract(s["title"], s["description"], s.get("acceptance_criteria", "")) for s in stories]

    def _call_api(self, prompt: str) -> str:
        """调用LLM API获取原始响应。

        Raises:
            FeatureExtractionError: API调用失败时抛出。
        """
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # 低温度以获得稳定的结构化输出
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise FeatureExtractionError(f"API 调用失败: {e}")

    @staticmethod
    def _parse_response(text: str) -> dict:
        """从LLM响应中解析特征JSON。

        支持直接JSON和markdown代码块包裹的JSON。

        Raises:
            ValueError: 解析失败时抛出。
        """
        text = text.strip()

        # 尝试提取markdown代码块中的JSON
        code_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if code_match:
            text = code_match.group(1).strip()

        return json.loads(text)

    @staticmethod
    def _validate_features(features: dict):
        """校验特征字典的字段完整性和类型。

        Raises:
            ValueError: 校验失败时抛出。
        """
        required_fields = [
            "frontend_pages", "backend_interfaces", "db_change",
            "external_dependency", "async_processing", "transaction_required",
            "business_branches", "permission_control", "data_migration",
            "cache_design",
        ]

        for field in required_fields:
            if field not in features:
                raise ValueError(f"特征JSON缺少字段: {field}")

        # 校验数值字段
        features["frontend_pages"] = int(features["frontend_pages"])
        features["backend_interfaces"] = int(features["backend_interfaces"])
        features["business_branches"] = int(features["business_branches"])

        # 校验布尔字段
        bool_fields = [
            "db_change", "external_dependency", "async_processing",
            "transaction_required", "permission_control", "data_migration",
            "cache_design",
        ]
        for field in bool_fields:
            val = str(features[field]).strip()
            if val not in ("是", "否", "true", "false", "True", "False", "1", "0"):
                raise ValueError(f"字段 {field} 的值非法: {features[field]}")
