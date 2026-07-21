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

数值估算结果：{weighted_result} 点

最相似的 {k} 条基准故事：
{baseline_details}

请综合判断，严格按照以下 JSON 格式返回（不要包含其他文字）：
{{"estimate": <1|2|3|5|8|13>,
  "confidence_min": <integer>,
  "confidence_max": <integer>,
  "reasoning": "<中文估算依据>",
  "risk_notes": "<中文风险提示>"}}"""


class ReportGenerator:
    """LLM 报告生成器。

    Attributes:
        model: Chat 模型名称。
    """

    def __init__(self, base_url: str, api_key: str, model: str):
        self.model = model
        self._base_url = base_url
        self._api_key = api_key

    def generate(self, title: str, description: str,
                 top_k_stories: list[dict], similarities: list[float],
                 weighted_avg: float) -> dict:
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

        Returns:
            {
                "estimate": int,
                "confidence_min": int | None,
                "confidence_max": int | None,
                "reasoning": str,
                "risk_notes": str,
                "top_matches": [...],
                "degraded": bool
            }
        """
        top_matches = self._format_top_matches(top_k_stories, similarities)

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
            weighted_result=round_to_fibonacci(weighted_avg),
            k=len(top_k_stories),
            baseline_details=baseline_details.strip(),
        )

        # 调用 Chat API
        try:
            llm_result = self._call_chat_api(prompt)
        except Exception:
            # 降级：纯数值估算
            return self._degraded_result(weighted_avg, top_matches)

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
                "degraded": False,
            }
        except Exception:
            # 解析失败，降级
            return self._degraded_result(weighted_avg, top_matches)

    def _degraded_result(self, weighted_avg: float,
                         top_matches: list[dict]) -> dict:
        """生成降级报告（纯数值）。"""
        estimate = round_to_fibonacci(weighted_avg)
        return {
            "estimate": estimate,
            "confidence_min": estimate,
            "confidence_max": estimate,
            "reasoning": "LLM 不可用，以下为基于加权平均的数值估算结果",
            "risk_notes": "由于 LLM 服务不可用，无法提供详细风险分析",
            "top_matches": top_matches,
            "degraded": True,
        }

    def _call_chat_api(self, prompt: str) -> str:
        """调用 Chat API（兼容 OpenAI 接口）。

        Raises:
            Exception: 调用失败时抛出。
        """
        from openai import OpenAI

        client = OpenAI(base_url=self._base_url, api_key=self._api_key)
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
