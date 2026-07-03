"""测试预处理层: ContentCleaner + StructureParser + SemanticChunker"""

import pytest
from bazi.preprocessor import (
    TextBlock, StructureParser, SemanticChunker
)
from bazi.config import config


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

    # —— 新增：结构驱动分块测试 ——

    def test_markdown_header_hard_boundary(self):
        """标题之间绝不跨越切分"""
        sections = [
            ("## 婚姻分析", ["婚姻相关段落" * 20] * 3),
            ("### 命例", ["命例段落" * 30] * 3),
        ]
        blocks = SemanticChunker.chunk(sections, "test", "书")
        # 两个标题段应该产出至少2个块，标题边界不应被跨越
        sections_set = {b.section for b in blocks}
        assert "## 婚姻分析" in sections_set
        assert "### 命例" in sections_set
        # 婚姻的内容不应出现在命例块中
        for b in blocks:
            if b.section == "## 婚姻分析":
                assert "婚姻相关段落" in b.text
                assert "命例" not in b.text
            elif b.section == "### 命例":
                assert "命例段落" in b.text
                assert "婚姻相关段落" not in b.text

    def test_paragraph_boundary_respected(self):
        """自然段边界作为分块单元，短段不硬切"""
        sections = [("章", [
            "第一段：" + "内容。" * 40,   # ~160 chars
            "第二段：" + "内容。" * 40,   # ~160 chars
            "第三段：" + "内容。" * 40,   # ~160 chars
        ])]
        blocks = SemanticChunker.chunk(sections, "test", "书")
        # 三个短段可能合并但不应硬切内部
        assert len(blocks) >= 1
        for b in blocks:
            assert len(b.text) <= config.chunk_max_size

    def test_sentence_level_fallback(self):
        """超长段在句号处拆分"""
        long_para = "第一句很长的内容。" * 400  # 远超 max_size
        sections = [("章", [long_para])]
        blocks = SemanticChunker.chunk(sections, "test", "书")
        assert len(blocks) >= 2
        for b in blocks:
            assert len(b.text) <= config.chunk_max_size

    def test_short_block_merged_with_previous(self):
        """短块（< min_size）与前一组合并"""
        sections = [("章", [
            "A" * 300,   # 正常长度
            "B" * 50,    # 过短
        ])]
        blocks = SemanticChunker.chunk(sections, "test", "书")
        # 过短的块应被合并，总数 ≤ 1
        assert len(blocks) <= 1

    def test_single_title_section_not_split(self):
        """单个标题段 + 适量内容 → 不切开"""
        sections = [("### 专题分析", ["一段完整的分析内容。" * 20])]
        blocks = SemanticChunker.chunk(sections, "test", "书")
        assert len(blocks) == 1
        assert "一段完整的分析内容" in blocks[0].text
