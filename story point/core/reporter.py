"""LLM 报告生成器。

构建 Prompt 调用 Chat API，生成结构化估算报告。
API 失败时降级为纯数值报告。
"""

import json
import re

from utils.fibonacci import round_to_fibonacci

REPORT_PROMPT_TEMPLATE = """你是故事点估算专家。基准刻度：1, 2, 3, 5, 8, 13。

新需求：
- 标题：{title}
- 描述：{description}
- 验收准则：{acceptance_criteria}

新需求复杂度特征：
{features_context}

数值估算结果：{weighted_result} 点

最相似的 {k} 条基准故事：
{baseline_details}

请综合判断，严格按照以下 JSON 格式返回（不要包含其他文字）：
{{"estimate": <1|2|3|5|8|13>,
  "confidence_min": <integer>,
  "confidence_max": <integer>,
  "reasoning": "<分 1./2./3. 列出判断依据，每条 1-2 句话>",
  "risk_notes": "<列出 2-3 条关键风险，每条 1 句话>"}}

reasoning 必须包含以下维度（用编号标注）：
1. 复杂度评估：基于特征（前端页面数、后端接口数、外部依赖等）评估开发复杂度是低/中/高
2. 基准对比：与最相似基准故事的差异分析，说明为何估高或估低
3. 参数权衡：如新旧点数边界时，解释为何向上/向下取整"""


class ReportGenerator:
    """LLM 报告生成器。

    Attributes:
        model: Chat 模型名称。
    """

    def __init__(self, base_url: str, api_key: str, model: str):
        self.model = model
        self._base_url = base_url
        self._api_key = api_key
        self._client = None  # 延迟初始化

    def _get_client(self):
        """获取 OpenAI 客户端实例（复用）。"""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        return self._client

    def generate(self, title: str, description: str,
                 top_k_stories: list[dict], similarities: list[float],
                 weighted_avg: float, new_features: dict = None,
                 acceptance_criteria: str = "") -> dict:
        """生成结构化估算报告。

        前置条件: title 和 description 非空,
                 len(top_k_stories) == len(similarities) >= 1。
        后置条件: 始终返回有效 dict，包含 estimate 字段。
        不变量: 不抛异常（降级为纯数值报告）。

        Args:
            title: 新需求标题。
            description: 新需求描述。
            top_k_stories: TopK 基准故事列表。
            similarities: 对应的相似度列表。
            weighted_avg: 加权平均点数。
            new_features: 新需求的复杂度特征字典（10个字段）。
            acceptance_criteria: 验收准则（可选，GWT格式）。

        Returns:
            {
                "estimate": int,
                "confidence_min": int | None,
                "confidence_max": int | None,
                "reasoning": str,
                "risk_notes": str,
                "top_matches": [...],
                "features": {...} | None,
                "degraded": bool
            }
        """
        top_matches = self._format_top_matches(top_k_stories, similarities)

        # 无参考基准时直接返回降级报告
        if not top_k_stories:
            return self._degraded_result(weighted_avg, top_matches, new_features)

        # 构建复杂度特征描述
        features_context = self._format_features_context(new_features)

        # 构建 prompt
        baseline_details = ""
        for i, (story, sim) in enumerate(zip(top_k_stories, similarities)):
            baseline_details += (
                f"{i + 1}. [{story['id']}] {story['title']} "
                f"({story['points']}点) - 相似度 {sim * 100:.0f}%\n"
            )

        prompt = REPORT_PROMPT_TEMPLATE.format(
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria.strip() if acceptance_criteria else "（无）",
            features_context=features_context,
            weighted_result=round_to_fibonacci(weighted_avg),
            k=len(top_k_stories),
            baseline_details=baseline_details.strip(),
        )

        # 调用 Chat API
        try:
            llm_result = self._call_chat_api(prompt)
        except Exception:
            return self._degraded_result(weighted_avg, top_matches, new_features)

        # 解析 JSON
        try:
            parsed = self._parse_json(llm_result)
            return {
                "estimate": parsed["estimate"],
                "confidence_min": parsed.get("confidence_min"),
                "confidence_max": parsed.get("confidence_max"),
                "reasoning": parsed.get("reasoning", ""),
                "risk_notes": parsed.get("risk_notes", ""),
                "top_matches": top_matches,
                "features": new_features,
                "degraded": False,
            }
        except Exception:
            return self._degraded_result(weighted_avg, top_matches, new_features)

    def _format_features_context(self, features: dict) -> str:
        """格式化复杂度特征为文本描述。"""
        if not features:
            return "（未提供复杂度特征）"

        field_labels = {
            "frontend_pages": "前端页面数",
            "backend_interfaces": "后端接口数",
            "db_change": "数据库变更",
            "external_dependency": "外部依赖",
            "async_processing": "异步处理",
            "transaction_required": "事务一致性",
            "business_branches": "业务分支数",
            "permission_control": "权限控制",
            "data_migration": "数据迁移",
            "cache_design": "缓存设计",
        }

        lines = []
        for field, label in field_labels.items():
            val = features.get(field, "-")
            lines.append(f"  - {label}: {val}")

        return "\n".join(lines)

    def _degraded_result(self, weighted_avg: float,
                         top_matches: list[dict],
                         features: dict = None) -> dict:
        """生成降级报告（纯数值）。"""
        estimate = round_to_fibonacci(weighted_avg)
        return {
            "estimate": estimate,
            "confidence_min": estimate,
            "confidence_max": estimate,
            "reasoning": "LLM 不可用，以下为基于加权平均的数值估算结果",
            "risk_notes": "由于 LLM 服务不可用，无法提供详细风险分析",
            "top_matches": top_matches,
            "features": features,
            "degraded": True,
        }

    def _call_chat_api(self, prompt: str) -> str:
        """调用 Chat API（兼容 OpenAI 接口）。

        Raises:
            Exception: 调用失败时抛出。
        """
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    def _parse_json(self, text: str) -> dict:
        """从 LLM 响应中解析 JSON。

        支持直接 JSON 和 markdown 代码块包裹的 JSON。

        Raises:
            ValueError: 解析失败时抛出。
        """
        text = text.strip()

        # 尝试提取 markdown 代码块中的 JSON
        code_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if code_match:
            text = code_match.group(1).strip()

        return json.loads(text)

    def _format_top_matches(self, stories: list[dict],
                            similarities: list[float]) -> list[dict]:
        """格式化 TopK 匹配结果。"""
        return [
            {
                "id": s["id"],
                "title": s["title"],
                "points": s["points"],
                "similarity": round(sim * 100),
            }
            for s, sim in zip(stories, similarities)
        ]
