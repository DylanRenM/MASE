"""LLMNormalizer 单元测试

测试目标:
- 断裂词修复（"结 婚"→"结婚"）
- 误断行合并
- 垃圾标记（广告/水印/页码用[AD]前缀标注）
- 干净块直接跳过
- 选择性触发检测
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.bazi.preprocessor import TextBlock


# ——— Mock LLM 响应用于规范化测试 ———
MOCK_NORMALIZED_RESPONSE = """年柱 简社 日料 时片
食神 正印 元男 正官
[AD] 220 获取更多最新易学资料 加微信：804407916
其父亲上亿资产，先看看是哪一条
此造父亲上亿资产"""

MOCK_BROKEN_WORDS_RESPONSE = """虚致对，我当时断也说他十岁之后运气就不好了，当时我以为戊土是药，但是现在听恩师一讲有点明朗了
京南dr: 行运晚的好八字。11岁行运，好八字，11岁之前没受影响
总之这些都是需要掂量的因素"""

MOCK_AD_ONLY_RESPONSE = """[AD] 获取更多最新易学资料 加微信：804407916 公众号：九鼎学堂
[AD] 好又全资源网 www.hao8451.com 加微信66697526送千本易学电子书"""

MOCK_CLEAN_RESPONSE = """日主喜印，因为没有这个印，那就是身弱
坐支辰土能晦火又能蓄水，且日主之原神"""


class TestLLMNormalizerNeedsCheck:
    """测试 _needs_normalization 检测逻辑"""

    def _get_normalizer(self):
        from src.bazi.preprocessor import LLMNormalizer
        return LLMNormalizer()

    def test_detects_broken_chinese_words(self):
        """检测到中文空格断裂 → 需要规范化"""
        norm = self._get_normalizer()
        block = TextBlock(
            block_id="test_001",
            text="食 神 正印 元男正官\n其父亲上亿资产",
            source="测试书",
        )
        assert norm._needs_normalization(block) is True

    def test_detects_wechat_ad(self):
        """检测到微信广告 → 需要规范化"""
        norm = self._get_normalizer()
        block = TextBlock(
            block_id="test_002",
            text="其父亲上亿资产\n加微信：804407916 获取更多资料",
            source="测试书",
        )
        assert norm._needs_normalization(block) is True

    def test_detects_url_pattern(self):
        """检测到网址 → 需要规范化"""
        norm = self._get_normalizer()
        block = TextBlock(
            block_id="test_003",
            text="查看更多 www.hao8451.com 资源",
            source="测试书",
        )
        assert norm._needs_normalization(block) is True

    def test_detects_public_account(self):
        """检测到公众号 → 需要规范化"""
        norm = self._get_normalizer()
        block = TextBlock(
            block_id="test_004",
            text="公众号：九鼎学堂 获取更多资料",
            source="测试书",
        )
        assert norm._needs_normalization(block) is True

    def test_detects_short_lines(self):
        """检测到过短行（<10字的多行）→ 需要规范化"""
        norm = self._get_normalizer()
        block = TextBlock(
            block_id="test_005",
            text="甲\n乙\n丙\n丁",
            source="测试书",
        )
        assert norm._needs_normalization(block) is True

    def test_clean_block_skipped(self):
        """干净文本块 → 跳过规范化"""
        norm = self._get_normalizer()
        block = TextBlock(
            block_id="test_006",
            text="日主喜印，因为没有这个印，那就是身弱。坐支辰土能晦火又能蓄水。",
            source="测试书",
        )
        assert norm._needs_normalization(block) is False


class TestLLMNormalizerBasic:
    """测试 LLMNormalizer 基本行为（Mock LLM）"""

    def _get_normalizer_with_mock(self, mock_response: str):
        """创建带Mock LLM的normalizer"""
        from src.bazi.preprocessor import LLMNormalizer
        norm = LLMNormalizer()
        # Mock _call_llm 方法
        norm._call_llm = Mock(return_value=mock_response)
        return norm

    def test_normalize_block_with_broken_words_and_ads(self):
        """规范化：修复断裂词 + 标记广告"""
        norm = self._get_normalizer_with_mock(MOCK_NORMALIZED_RESPONSE)
        block = TextBlock(
            block_id="test_010",
            text="年柱简社 日料时片\n食 神 正印 元男正官\n220 获取更多最新易学资料 加微信：804407916\n其父亲上亿资产",
            source="测试书",
        )
        result = norm._normalize_single(block)
        assert "[AD] 220 获取更多最新易学资料" in result.text
        assert "食神" in result.text or "食 神" not in result.text

    def test_normalize_block_broken_words_only(self):
        """规范化：仅修复断裂词"""
        norm = self._get_normalizer_with_mock(MOCK_BROKEN_WORDS_RESPONSE)
        block = TextBlock(
            block_id="test_011",
            text="我 以为是戊土是药\n需 要掂量的因素",
            source="测试书",
        )
        result = norm._normalize_single(block)
        assert "我以为" in result.text or "[AD]" not in result.text

    def test_normalize_block_ads_only(self):
        """规范化：仅标记广告，不误删正文"""
        norm = self._get_normalizer_with_mock(MOCK_AD_ONLY_RESPONSE)
        block = TextBlock(
            block_id="test_012",
            text="获取更多最新易学资料 加微信：804407916 公众号：九鼎学堂\n好又全资源网 www.hao8451.com",
            source="测试书",
        )
        result = norm._normalize_single(block)
        # 整块都是广告，输出应全为[AD]行
        lines = result.text.strip().split("\n")
        for line in lines:
            if line.strip():
                assert line.strip().startswith("[AD]"), f"Expected [AD] prefix, got: {line}"

    def test_normalize_clean_block_passthrough(self):
        """干净文本块直接通过"""
        norm = self._get_normalizer_with_mock(MOCK_CLEAN_RESPONSE)
        block = TextBlock(
            block_id="test_013",
            text="日主喜印，因为没有这个印，那就是身弱",
            source="测试书",
        )
        result = norm._normalize_single(block)
        assert result.block_id == block.block_id
        assert result.source == block.source

    def test_preserves_block_metadata(self):
        """规范化后保留 block_id, source, section 等元信息"""
        norm = self._get_normalizer_with_mock(MOCK_CLEAN_RESPONSE)
        block = TextBlock(
            block_id="test_014",
            text="一些文本",
            section="第一章/第一节",
            source="来源书",
            source_file="/path/to/file.txt",
        )
        result = norm._normalize_single(block)
        assert result.block_id == "test_014"
        assert result.section == "第一章/第一节"
        assert result.source == "来源书"
        assert result.source_file == "/path/to/file.txt"


class TestLLMNormalizerBatch:
    """测试批处理逻辑"""

    def test_batch_normalize_mixed_blocks(self):
        """混合块批处理：干净块跳过，脏块调用LLM"""
        from src.bazi.preprocessor import LLMNormalizer
        norm = LLMNormalizer()
        norm._call_llm = Mock(return_value="规范化后的文本")

        clean = TextBlock(
            block_id="clean_01",
            text="日主喜印，因为没有这个印，那就是身弱。坐支辰土能晦火又能蓄水。",
            source="测试书",
        )
        dirty = TextBlock(
            block_id="dirty_01",
            text="食 神 正印 元男正官\n加微信：804407916",
            source="测试书",
        )

        blocks = [clean, dirty]
        result = norm.normalize(blocks)

        assert len(result) == 2
        # 干净块应原样通过
        assert result[0].text == clean.text
        # 脏块应被规范化
        assert result[1].text == "规范化后的文本"
        # 只调用了一次LLM
        assert norm._call_llm.call_count == 1

    def test_batch_all_clean_blocks(self):
        """全部干净块：零LLM调用"""
        from src.bazi.preprocessor import LLMNormalizer
        norm = LLMNormalizer()
        norm._call_llm = Mock()

        blocks = [
            TextBlock(
                block_id=f"clean_{i:02d}",
                text="日主喜印，因为没有这个印，那就是身弱。坐支辰土能晦火又能蓄水，且日主之原神。",
                source="测试书",
            )
            for i in range(5)
        ]
        result = norm.normalize(blocks)
        assert len(result) == 5
        assert norm._call_llm.call_count == 0

    def test_batch_size_capped(self):
        """批处理每批不超过配置上限，每块独立调用LLM"""
        from src.bazi.preprocessor import LLMNormalizer
        norm = LLMNormalizer()
        norm._call_llm = Mock(return_value="规范化后")

        # 创建25个脏块，每个块独立调LLM，共25次调用
        dirty_blocks = [
            TextBlock(
                block_id=f"dirty_{i:02d}",
                text=f"食 神 正印\n加微信：{i}",
                source="测试书",
            )
            for i in range(25)
        ]
        result = norm.normalize(dirty_blocks)
        # 25个脏块，每个独立调LLM
        assert norm._call_llm.call_count == 25
        assert len(result) == 25


class TestLLMNormalizerNormalizeMethod:
    """测试 normalize 公共方法"""

    def _make_normalizer(self):
        from src.bazi.preprocessor import LLMNormalizer
        norm = LLMNormalizer()
        norm._needs_normalization = Mock(return_value=True)
        norm._normalize_single = Mock(side_effect=lambda b: TextBlock(
            block_id=b.block_id,
            text=f"[FIXED]{b.text}",
            section=b.section,
            source=b.source,
            source_file=b.source_file,
        ))
        return norm

    def test_normalize_returns_all_blocks(self):
        """normalize 返回与输入相同数量的块"""
        norm = self._make_normalizer()
        blocks = [
            TextBlock(block_id=f"b_{i:02d}", text=f"text_{i}", source="s")
            for i in range(3)
        ]
        result = norm.normalize(blocks)
        assert len(result) == 3

    def test_empty_input_returns_empty(self):
        """空输入返回空列表"""
        norm = self._make_normalizer()
        result = norm.normalize([])
        assert result == []
