"""阶段2: 全量向量化 + LLM 初步分类"""

import json
import os
import re
import time
from typing import Optional

import numpy as np

from .config import config
from .book_parser import Block


GENRE_TAGS = ["旺衰派", "格局派", "盲派", "神煞", "调候", "病药", "阴阳", "综合", "其他"]
TOPIC_TAGS = ["婚姻", "健康", "寿命", "六亲", "财运", "事业", "学业", "性格", "用神", "大运", "流年", "基础理论", "其他"]
CONTENT_TYPES = ["theory", "case_study", "mixed"]


class Vectorizer:
    """Embedding 向量化服务，支持 Ollama 和 SentenceTransformers 后端"""

    def __init__(self):
        self.backend = config.embedding_backend
        if self.backend == "ollama":
            self._init_ollama()
        else:
            self._init_sentence_transformers()

    def _init_ollama(self):
        """初始化 Ollama embedding"""
        from openai import OpenAI
        self._client = OpenAI(
            base_url=config.llm_base_url,
            api_key="ollama",
            timeout=config.classifier_timeout,
            max_retries=config.classifier_max_retries,
        )
        self._model = config.embedding_model
        self._dim = config.embedding_dim
        print(f"[Vectorizer] 使用 Ollama embedding: {self._model} ({self._dim}维)")

    def _init_sentence_transformers(self):
        """初始化 SentenceTransformers"""
        os.environ.setdefault("HF_ENDPOINT", config.hf_endpoint)
        from sentence_transformers import SentenceTransformer
        self._st_model = SentenceTransformer(config.embedding_model)
        self._dim = config.embedding_dim
        print(f"[Vectorizer] 使用 SentenceTransformer: {config.embedding_model} ({self._dim}维)")

    def encode(self, text: str) -> list[float]:
        """单文本向量化"""
        if self.backend == "ollama":
            resp = self._client.embeddings.create(
                model=self._model,
                input=text[:8000],
            )
            return resp.data[0].embedding
        else:
            vector = self._st_model.encode(text, normalize_embeddings=True)
            return vector.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        if self.backend == "ollama":
            vectors = []
            for i, text in enumerate(texts):
                vec = self.encode(text)
                vectors.append(vec)
                if (i + 1) % 50 == 0:
                    print(f"  向量化进度: {i+1}/{len(texts)}")
            return vectors
        else:
            vectors = self._st_model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
            return vectors.tolist()

    def vectorize_blocks(self, blocks: list[Block]) -> list[dict]:
        """将 Block 列表转为向量+payload，准备写入 Qdrant"""
        texts = [b.text for b in blocks]
        vectors = self.encode_batch(texts)

        results = []
        for block, vector in zip(blocks, vectors):
            results.append({
                "vector": vector,
                "payload": {
                    "book_id": block.book_id,
                    "source_book": block.source_book,
                    "chapter": block.chapter,
                    "block_id": block.block_id,
                    "block_text": block.text,
                    # 初步标签待分类填充
                    "genre_tags": [],
                    "topic_tags": [],
                    "content_type": "",
                }
            })
        return results

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """计算余弦相似度"""
        a = np.array(v1)
        b = np.array(v2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class LLMClassifier:
    """使用本地千问 LLM 做初步分类"""

    CLASSIFY_PROMPT = """你是一个八字命理专家。请对以下文本块进行分析，输出JSON格式的分类结果。

分类规则：
- genre_tags（流派标签，可多选）: [{genre_options}]
- topic_tags（专题标签，可多选）: [{topic_options}]
- content_type: "theory"（理论阐述）| "case_study"（命例分析）| "mixed"（混合）
- summary: 10字以内的内容概要

只输出JSON，不要其他任何文字：
{{"genre_tags": [...], "topic_tags": [...], "content_type": "...", "summary": "..."}}

文本块: {text}"""

    def __init__(self):
        self.base_url = config.llm_base_url
        self.model = config.llm_model
        self.temperature = config.llm_temperature

    def _call_llm(self, prompt: str) -> str:
        """调用 Ollama 兼容的 LLM API"""
        from openai import OpenAI

        client = OpenAI(
            base_url=self.base_url,
            api_key="ollama",
            timeout=config.classifier_timeout,
            max_retries=config.classifier_max_retries,
        )
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        return response.choices[0].message.content.strip()

    def _parse_classify_result(self, text: str) -> dict:
        """解析 LLM 返回的分类结果 JSON"""
        # 尝试提取 JSON
        json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                # 验证和补全字段
                result.setdefault("genre_tags", [])
                result.setdefault("topic_tags", [])
                result.setdefault("content_type", "mixed")
                result.setdefault("summary", "")
                return result
            except json.JSONDecodeError:
                pass

        # 返回空结果
        return {"genre_tags": [], "topic_tags": [], "content_type": "mixed", "summary": ""}

    def classify(self, text: str) -> dict:
        """对单个文本块分类"""
        prompt = self.CLASSIFY_PROMPT.format(
            genre_options=", ".join(GENRE_TAGS),
            topic_options=", ".join(TOPIC_TAGS),
            text=text[:2000],  # 截断防止超长
        )
        try:
            raw = self._call_llm(prompt)
            return self._parse_classify_result(raw)
        except Exception as e:
            return {"genre_tags": [], "topic_tags": [], "content_type": "mixed",
                    "summary": "", "error": str(e)}

    def classify_batch(self, texts: list[str]) -> list[dict]:
        """批量分类（逐个调用，带进度）"""
        results = []
        total = len(texts)
        for i, text in enumerate(texts):
            result = self.classify(text)
            results.append(result)
            if (i + 1) % 5 == 0 or i == 0:
                print(f"  [LLM分类] {i+1}/{total}", flush=True)
            if (i + 1) % 10 == 0:
                time.sleep(0.5)
        return results


class RuleClassifier:
    """基于关键词规则的快速分类器，作为 LLM 不可用时的回退方案

    单主标签策略: 每块只分配 1 个主流派 + 1 个主专题（得分最高者）
    次标签保存在 secondary_genres / secondary_topics 中
    """

    # genre 和 topic 之间去重后的关键词（每词仅在一个维度）
    # 去重词: 正官,七杀,文昌,寿元,正财,偏财 → 仅留在 topic 维度
    GENRE_KEYWORDS = {
        "旺衰派": ["旺衰", "身旺", "身弱", "日主旺", "日主弱", "得令", "失令", "得地", "失地",
                   "印旺", "比劫旺", "扶抑", "从格"],
        "格局派": ["格局", "立格", "取格", "成格", "破格", "格局成败", "护卫", "清纯", "真假",
                   "正官格", "七杀格", "正财格", "偏财格", "食神格", "伤官格", "印绶格",
                   "建禄", "月劫", "阳刃格", "从格论", "化格"],
        "盲派": ["盲派", "盲人", "盲师", "民间", "口诀", "铁口", "直断", "一针见血",
                 "家传", "铁断", "一招", "直读", "象法", "串宫", "压运"],
        "神煞": ["神煞", "天乙贵人", "桃花", "羊刃", "驿马", "将星", "华盖", "孤辰", "寡宿",
                 "文昌星", "天德", "月德", "魁罡", "金舆", "学堂", "词馆", "红鸾", "天喜"],
        "调候": ["调候", "寒暖", "燥湿", "金寒", "水冷", "火炎", "土燥",
                 "暖局", "解冻", "向阳", "冬金", "夏水", "丙火调", "壬水润", "调候为急", "寒木"],
        "病药": ["病药", "有病方为贵", "无伤不是奇", "病在", "药在",
                 "病神", "药神", "取药", "以为病", "以为药", "病重药轻", "去病",
                 "格中若去病", "有病", "无病", "病药理论"],
        "阴阳": ["阴阳", "阴盛", "阳盛", "纯阴", "纯阳", "坤造", "乾造",
                 "阴重", "阳重", "阴极", "阳极", "阴浊", "阳浊", "阴阳平衡",
                 "阴盛阳衰", "阳盛阴衰"],
    }

    TOPIC_KEYWORDS = {
        "婚姻": ["婚姻", "婚", "嫁", "夫", "妻", "配偶", "夫妻", "感情", "正官", "七杀",
                 "婚期", "合婚", "纳采", "嫁娶", "红娘", "媒妁"],
        "健康": ["健康", "疾病", "病", "伤", "疾", "残", "身体", "病症", "疾患"],
        "寿命": ["寿命", "寿", "夭折", "早亡", "长寿", "短命", "寿元", "生死",
                 "寿数", "寿限", "享年", "终年", "阳寿"],
        "六亲": ["六亲", "父母", "兄弟", "姐妹", "子女", "子息", "丈夫", "妻子",
                 "双亲", "兄长", "弟", "姊妹", "儿女", "子孙"],
        "财运": ["财运", "财", "富", "贫", "钱", "正财", "偏财", "求财", "经商",
                 "财帛", "发财", "破财", "进财", "钱财", "资产"],
        "事业": ["事业", "官", "职", "仕途", "功名", "科甲", "工作", "升迁",
                 "官运", "宦途", "职位", "升职", "权柄"],
        "学业": ["学业", "学", "考", "科甲", "功名", "读书", "学位", "考试",
                 "升学", "文昌", "科举", "书院", "求学"],
        "性格": ["性格", "性", "脾气", "品性", "为人", "性情", "品行", "德行",
                 "秉性", "心性"],
        "用神": ["用神", "喜用", "忌神", "喜神", "闲神", "仇神", "取用", "用神取",
                 "用神有力", "用神无力", "调候用神", "扶抑用神", "通关用神"],
        "大运": ["大运", "运程", "流年", "岁运", "行运", "起运", "排大运",
                 "运", "流年运", "岁", "交运"],
        "基础理论": ["天干", "地支", "五行", "十神", "生克", "合化", "刑冲", "合会",
                   "藏干", "纳音", "十二宫", "长生", "墓库"],
    }

    def __init__(self):
        pass

    def classify(self, text: str) -> dict:
        """基于关键词匹配的单主标签分类"""
        # 计算每个流派的得分
        genre_scores = {}
        for genre, keywords in self.GENRE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                genre_scores[genre] = score

        # 计算每个专题的得分
        topic_scores = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                topic_scores[topic] = score

        # 单主标签: 仅取最高分
        sorted_genres = sorted(genre_scores.items(), key=lambda x: -x[1])
        sorted_topics = sorted(topic_scores.items(), key=lambda x: -x[1])

        genre_tags = [sorted_genres[0][0]] if sorted_genres else []
        topic_tags = [sorted_topics[0][0]] if sorted_topics else []

        secondary_genres = [g for g, _ in sorted_genres[1:]] if len(sorted_genres) > 1 else []
        secondary_topics = [t for t, _ in sorted_topics[1:]] if len(sorted_topics) > 1 else []

        # 默认标签: 仅在完全无命中时使用
        if not genre_tags:
            genre_tags = []  # 触发 LLM 兜底
        if not topic_tags:
            topic_tags = ["基础理论"]

        # 判断内容类型
        has_case = any(kw in text for kw in
                       ["命例", "坤造", "乾造", "八字", "八字：", "年柱", "月柱", "日柱", "时柱"])
        has_theory = any(kw in text for kw in
                        ["是指", "代表", "称为", "谓之", "所谓", "原理", "原则", "规律"])

        if has_case and has_theory:
            content_type = "mixed"
        elif has_case:
            content_type = "case_study"
        else:
            content_type = "theory"

        return {
            "genre_tags": genre_tags,
            "topic_tags": topic_tags,
            "content_type": content_type,
            "summary": "",
            "secondary_genres": secondary_genres,
            "secondary_topics": secondary_topics,
        }

    def classify_batch(self, texts: list[str]) -> list[dict]:
        """批量分类"""
        results = []
        for text in texts:
            results.append(self.classify(text))
        return results

    def classify_with_fallback(self, text: str, llm_classifier: "LLMClassifier | None" = None) -> dict:
        """分类，无流派命中时触发 LLM 兜底"""
        result = self.classify(text)

        # 如果规则分类没有命中任何流派，使用 LLM 兜底
        if not result["genre_tags"] and config.llm_fallback_enabled and llm_classifier is not None:
            try:
                llm_result = llm_classifier.classify(text)
                if llm_result.get("genre_tags"):
                    result["genre_tags"] = llm_result["genre_tags"][:1]
                if llm_result.get("topic_tags") and not result["topic_tags"]:
                    result["topic_tags"] = llm_result["topic_tags"][:1]
            except Exception:
                pass

        # 最终兜底
        if not result["genre_tags"]:
            result["genre_tags"] = ["综合"]
        if not result["topic_tags"]:
            result["topic_tags"] = ["基础理论"]

        return result
