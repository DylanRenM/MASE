"""content-vectorizer 模块的单元测试"""

import pytest
from unittest.mock import patch, MagicMock
from bazi.content_vectorizer import Vectorizer
from bazi.book_parser import Block


@pytest.fixture
def sample_blocks():
    """生成测试用文本块"""
    return [
        Block(
            block_id="bk001_0001",
            text="正官是克我之神，代表约束和规范。在女命中，正官也代表丈夫。",
            source_book="子平真诠",
            chapter="论十神",
            book_id="bk001",
        ),
        Block(
            block_id="bk001_0002",
            text="七杀为克我之同性，具有攻击性和破坏力。七杀有力而制化则能成大器。",
            source_book="子平真诠",
            chapter="论十神",
            book_id="bk001",
        ),
        Block(
            block_id="bk002_0001",
            text="坤造：甲子年 丙寅月 庚辰日 丙戌时。此命官杀混杂，婚姻不顺。",
            source_book="滴天髓",
            chapter="女命章",
            book_id="bk002",
        ),
    ]


class TestVectorizer:
    """向量化服务测试"""

    def test_initialization(self):
        """测试向量化器初始化"""
        vectorizer = Vectorizer()
        assert vectorizer is not None
        assert vectorizer._model is not None
        assert vectorizer._dim == 768

    def test_encode_single_block(self, sample_blocks):
        """测试单块向量化"""
        vectorizer = Vectorizer()
        block = sample_blocks[0]
        vector = vectorizer.encode(block.text)
        assert len(vector) == 768
        assert isinstance(vector, list)

    def test_encode_batch(self, sample_blocks):
        """测试批量向量化"""
        vectorizer = Vectorizer()
        texts = [b.text for b in sample_blocks]
        vectors = vectorizer.encode_batch(texts)
        assert len(vectors) == len(texts)
        for v in vectors:
            assert len(v) == 768

    def test_vectorize_blocks(self, sample_blocks):
        """测试完整的块向量化流程（块→向量+元信息）"""
        vectorizer = Vectorizer()
        results = vectorizer.vectorize_blocks(sample_blocks)
        assert len(results) == len(sample_blocks)
        for i, result in enumerate(results):
            assert "vector" in result
            assert "payload" in result
            assert len(result["vector"]) == 768
            assert result["payload"]["block_id"] == sample_blocks[i].block_id
            assert result["payload"]["source_book"] == sample_blocks[i].source_book
            assert result["payload"]["block_text"] == sample_blocks[i].text

    def test_cosine_similarity(self, sample_blocks):
        """测试余弦相似度计算"""
        vectorizer = Vectorizer()
        # 两个八字理论文本应该相似
        v1 = vectorizer.encode(sample_blocks[0].text)  # 正官
        v2 = vectorizer.encode(sample_blocks[1].text)  # 七杀
        sim = vectorizer.cosine_similarity(v1, v2)
        assert 0 <= sim <= 1

        # 相同文本应该完全相似
        sim_self = vectorizer.cosine_similarity(v1, v1)
        assert sim_self > 0.99


class TestLLMClassifier:
    """LLM 分类器测试"""

    def test_classifier_initialization(self):
        """分类器初始化测试"""
        from bazi.content_vectorizer import LLMClassifier
        classifier = LLMClassifier()
        assert classifier is not None

    def test_classify_block(self, sample_blocks):
        """测试单块分类"""
        from bazi.content_vectorizer import LLMClassifier
        classifier = LLMClassifier()
        block = sample_blocks[0]
        result = classifier.classify(block.text)
        assert "genre_tags" in result
        assert "topic_tags" in result
        assert "content_type" in result
        assert isinstance(result["genre_tags"], list)
        assert isinstance(result["topic_tags"], list)
        assert result["content_type"] in ("theory", "case_study", "mixed")

    def test_classify_batch(self, sample_blocks):
        """测试批量分类"""
        from bazi.content_vectorizer import LLMClassifier
        classifier = LLMClassifier()
        texts = [b.text for b in sample_blocks]
        results = classifier.classify_batch(texts)
        assert len(results) == len(texts)
        for result in results:
            assert "genre_tags" in result
            assert "topic_tags" in result
            assert "content_type" in result
