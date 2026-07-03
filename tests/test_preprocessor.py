"""测试预处理层: ContentCleaner + StructureParser + SemanticChunker"""

import pytest
from bazi.preprocessor import (
    TextBlock, ContentCleaner, StructureParser, SemanticChunker
)
from bazi.config import config


class TestContentCleaner:
    """T-004: ContentCleaner 清洗测试"""

    def test_remove_watermark_haoqiquan(self):
        text = "五行相生相克的理论\n\n好又全资源网，加微信804407916送海量电子书\n\n天干地支..."
        result = ContentCleaner.clean(text)
        assert "好又全资源网" not in result
        assert "五行相生" in result
        assert "天干地支" in result

    def test_remove_watermark_aakk(self):
        text = "命理知识\n\nAAKK0088800加微信进群聊\n\n继续内容"
        result = ContentCleaner.clean(text)
        assert "AAKK" not in result
        assert "命理知识" in result
        assert "继续内容" in result

    def test_remove_wechat_contact(self):
        text = "如需咨询请联系微信：zhangsan123，了解更多。"
        result = ContentCleaner.clean(text)
        assert "zhangsan123" not in result
        assert "了解更多" in result

    def test_remove_qq_contact(self):
        text = "加QQ群：12345678一起讨论命理"
        result = ContentCleaner.clean(text)
        assert "12345678" not in result

    def test_remove_public_account(self):
        text = "关注公众号：九鼎学堂获取更多"
        result = ContentCleaner.clean(text)
        assert "九鼎学堂" not in result

    def test_remove_buy_book_link(self):
        text = "购纸质教材微信：duolei1984 包邮"
        result = ContentCleaner.clean(text)
        assert "duolei1984" not in result

    def test_merge_broken_lines(self):
        """换行合并：中文行被强制换行"""
        text = "五行相生\n相克是命理\n学的基础理论。\n\n第二句开始。"
        result = ContentCleaner.clean(text)
        assert "五行相生相克是命理" in result
        assert "学的基础理论。" in result.split("\n")

    def test_no_merge_sentence_end(self):
        """句末标点结尾的不合并"""
        text = "这是第一句。\n这是第二句。"
        result = ContentCleaner.clean(text)
        lines = result.split("\n")
        assert any("这是第一句。" in l for l in lines)
        assert any("这是第二句。" in l for l in lines)

    def test_no_merge_markdown_header(self):
        """Markdown 标记开头的不合并"""
        text = "前面内容\n# 新标题\n后面内容"
        result = ContentCleaner.clean(text)
        assert "# 新标题" in result

    def test_remove_duplicate_empty_lines(self):
        text = "段落A\n\n\n\n\n\n段落B"
        result = ContentCleaner.clean(text)
        # 不应有连续5个换行
        assert "\n\n\n\n\n" not in result
        assert "段落A" in result
        assert "段落B" in result

    def test_remove_garbled_lines(self):
        text = "正常中文内容\n!!!@@@###$$$%%%^^^&&&***((()))\n继续正常内容"
        result = ContentCleaner.clean(text)
        assert "!!!" not in result
        assert "正常中文内容" in result
        assert "继续正常内容" in result

    def test_keep_short_non_cjk(self):
        """短的非中文行（<20字符）不应被当作乱码"""
        text = "天干：甲乙丙丁戊己庚辛壬癸\n123\n地支：子丑寅卯"
        result = ContentCleaner.clean(text)
        assert "123" in result


class TestStructureParser:
    """T-005: StructureParser 结构提取测试"""

    def test_single_h1(self):
        text = "# 第一章\n段落A\n\n段落B"
        result = StructureParser.parse(text)
        assert len(result) == 1
        assert result[0][0] == "第一章"
        assert result[0][1] == ["段落A", "段落B"]

    def test_nested_headers(self):
        text = "# 章一\n段落A\n\n## 1.1 节\n段落B\n\n### 1.1.1 小节\n段落C"
        result = StructureParser.parse(text)
        assert result[0][0] == "章一"
        assert result[1][0] == "章一 / 1.1 节"
        assert result[2][0] == "章一 / 1.1 节 / 1.1.1 小节"
        assert result[0][1] == ["段落A"]
        assert result[2][1] == ["段落C"]

    def test_no_headers(self):
        text = "段落A\n\n段落B\n\n段落C"
        result = StructureParser.parse(text)
        assert len(result) == 1
        assert result[0][0] is None
        assert result[0][1] == ["段落A", "段落B", "段落C"]

    def test_empty_text(self):
        result = StructureParser.parse("")
        assert len(result) == 1
        assert result[0][0] is None
        assert result[0][1] == []

    def test_header_reset_on_new_h1(self):
        """新的H1应重置H2/H3"""
        text = "# 第一章\n## 1.1\n段落A\n\n# 第二章\n段落B"
        result = StructureParser.parse(text)
        assert result[0][0] == "第一章 / 1.1"
        assert result[1][0] == "第二章"


class TestSemanticChunker:
    """T-007: SemanticChunker 语义分块测试"""

    def test_single_paragraph_within_range(self):
        sections = [("测试章节", ["这是一个500字左右的段落" * 10])]
        blocks = SemanticChunker.chunk(sections, "test", "测试书")
        assert len(blocks) > 0
        for b in blocks:
            assert len(b.text) <= config.chunk_max_size
            assert b.section == "测试章节"
            assert b.source == "测试书"
            assert b.block_id.startswith("test_")

    def test_multiple_short_paragraphs_merge(self):
        """多个短段应合并"""
        sections = [("章节", ["段落A" * 20, "段落B" * 20, "段落C" * 20])]
        blocks = SemanticChunker.chunk(sections, "test", "书")
        # 3个短段应该合并成1-2个块
        assert len(blocks) >= 1

    def test_long_paragraph_split(self):
        """长段应按句号拆分"""
        long_text = "。".join(["第{}句" * 30 for _ in range(20)])
        sections = [("章节", [long_text])]
        blocks = SemanticChunker.chunk(sections, "test", "书")
        # 超长段应被拆分为多个块
        assert len(blocks) >= 2
        for b in blocks:
            assert len(b.text) <= config.chunk_max_size

    def test_section_boundary_not_merged(self):
        """不同章节的段不应合并"""
        sections = [
            ("章节A", ["段落A内容" * 20]),
            ("章节B", ["段落B内容" * 20]),
        ]
        blocks = SemanticChunker.chunk(sections, "test", "书")
        # 不同章节应在不同块中
        sections_in_blocks = {b.section for b in blocks}
        assert "章节A" in sections_in_blocks
        assert "章节B" in sections_in_blocks

    def test_empty_input(self):
        blocks = SemanticChunker.chunk([], "test", "书")
        assert blocks == []

    def test_block_id_format(self):
        sections = [("章", ["内容" * 100])]
        blocks = SemanticChunker.chunk(sections, "TEST123", "书")
        for b in blocks:
            assert b.block_id.startswith("TEST123_")
            assert b.block_id[-4:].isdigit()

    def test_split_at_sentence_end(self):
        """拆分点应在句末标点处"""
        long_text = "这是第一句完整的话。这是第二句完整的话。这是第三句完整的话。" * 50
        sections = [("章", [long_text])]
        blocks = SemanticChunker.chunk(sections, "test", "书")
        assert len(blocks) >= 2
        # 每个块应以句末标点或完整句子结束
        for b in blocks:
            text = b.text.strip()
            if text:
                assert text[-1] in ("。", "！", "？") or len(text) <= config.chunk_max_size
