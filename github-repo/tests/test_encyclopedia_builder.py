"""EncyclopediaBuilder 百科全书编排器模块的单元测试

测试覆盖:
- build_entry: 百科条目构建（LLM 摘要 + 原文出处）
- build_encyclopedia: 完整百科构建（双索引结构）
- _format_source_blocks: 素材格式化
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# Helper: 构造 mock EncyclopediaBuilder，替换 classifier 为可控 mock
# ---------------------------------------------------------------------------

def _make_builder():
    """构造 EncyclopediaBuilder 实例，mock 掉 LLMClassifier 依赖。"""
    with patch("bazi.encyclopedia_builder.LLMClassifier", autospec=True):
        from bazi.encyclopedia_builder import EncyclopediaBuilder
        builder = EncyclopediaBuilder()
        # 替换 classifier 为 MagicMock
        builder._classifier = MagicMock()
        return builder


def _make_block(block_id, text, source_book="测试书", genre_tags=None, topic_tags=None):
    """构造一个知识块字典（模拟 knowledge_pool 中的 unique_block）。

    注意：仅当 genre_tags/topic_tags 为 None 时使用默认值，
    显式传入空列表 [] 会被保留（用于测试无标签场景）。
    """
    return {
        "block_id": block_id,
        "text": text,
        "source_book": source_book,
        "genre_tags": genre_tags if genre_tags is not None else ["格局派"],
        "topic_tags": topic_tags if topic_tags is not None else ["基础理论"],
    }


# ---------------------------------------------------------------------------
# TestBuildEntry
# ---------------------------------------------------------------------------

class TestBuildEntry:
    """测试 build_entry 百科条目构建"""

    def test_build_entry_with_llm_summary(self):
        """mock LLM 返回摘要，验证 content 包含"核心观点"和"原始素材" """
        builder = _make_builder()

        # mock LLM 返回摘要
        mock_summary = """## 核心观点
五行相生相克是八字命理的核心基础理论，各流派对此有不同阐述。

## 各家视角
各书观点基本一致。"""
        builder.classifier._call_llm.return_value = mock_summary

        blocks = [
            _make_block("b1", "五行相生：木生火，火生土，土生金，金生水，水生木。", source_book="子平真诠"),
            _make_block("b2", "五行相克：木克土，土克水，水克火，火克金，金克木。", source_book="滴天髓"),
        ]

        entry = builder.build_entry("格局派", "基础理论", blocks)

        assert entry["genre"] == "格局派"
        assert entry["topic"] == "基础理论"
        assert "核心观点" in entry["content"]
        assert "原始素材" in entry["content"]
        # 验证来源统计
        assert "共收录 2 段相关内容，来自 2 本书籍" in entry["content"]
        assert "子平真诠" in entry["content"]
        assert "滴天髓" in entry["content"]

    def test_build_entry_empty_blocks(self):
        """空 blocks 返回"暂无内容" """
        builder = _make_builder()

        entry = builder.build_entry("旺衰派", "财运", [])

        assert entry["content"] == "暂无内容"
        assert entry["sources"] == []
        assert entry["genre"] == "旺衰派"
        assert entry["topic"] == "财运"

    def test_build_entry_llm_error(self):
        """mock LLM 抛异常，返回带错误提示的内容"""
        builder = _make_builder()
        builder.classifier._call_llm.side_effect = ConnectionError("无法连接 LLM 服务")

        blocks = [
            _make_block("b1", "测试内容", source_book="测试书"),
        ]

        entry = builder.build_entry("盲派", "婚姻", blocks)

        # LLM 摘要部分应包含错误信息
        assert "LLM摘要生成失败" in entry["content"]
        assert "无法连接 LLM 服务" in entry["content"]
        # 原始素材部分仍然存在
        assert "原始素材" in entry["content"]
        assert "测试内容" in entry["content"]

    def test_build_entry_source_deduplication(self):
        """相同来源的块被合并统计"""
        builder = _make_builder()
        mock_summary = "## 核心观点\n测试摘要内容。"
        builder.classifier._call_llm.return_value = mock_summary

        blocks = [
            _make_block("b1", "第一段内容。", source_book="子平真诠"),
            _make_block("b2", "第二段内容。", source_book="子平真诠"),
            _make_block("b3", "第三段内容。", source_book="滴天髓"),
        ]

        entry = builder.build_entry("格局派", "事业", blocks)

        # 共 3 段，来自 2 本书籍
        assert "共收录 3 段相关内容，来自 2 本书籍" in entry["content"]
        # 子平真诠应有 2 段
        assert "《子平真诠》（2段）" in entry["content"]
        # 滴天髓应有 1 段
        assert "《滴天髓》（1段）" in entry["content"]

    def test_build_entry_see_also(self):
        """验证 see_also 包含其他流派链接"""
        builder = _make_builder()
        mock_summary = "## 核心观点\n测试。"
        builder.classifier._call_llm.return_value = mock_summary

        blocks = [_make_block("b1", "测试内容")]

        entry = builder.build_entry("旺衰派", "婚姻", blocks)

        assert "see_also" in entry
        assert isinstance(entry["see_also"], list)
        # 旺衰派不应该出现在自己的 see_also 中
        assert "旺衰派·婚姻" not in entry["see_also"]
        # 其他流派应该出现
        assert "格局派·婚姻" in entry["see_also"]


# ---------------------------------------------------------------------------
# TestBuildEncyclopedia
# ---------------------------------------------------------------------------

class TestBuildEncyclopedia:
    """测试 build_encyclopedia 完整百科构建"""

    def test_empty_knowledge_pool(self):
        """空 knowledge_pool 返回空字典"""
        builder = _make_builder()

        result = builder.build_encyclopedia({})

        assert result == {"by_genre": {}, "by_topic": {}}

    def test_single_entry_pool(self):
        """单个 genre x topic 的 knowledge_pool"""
        builder = _make_builder()
        mock_summary = "## 核心观点\n单一流派测试。"
        builder.classifier._call_llm.return_value = mock_summary

        pool = {
            "unique_blocks": [
                _make_block("b1", "单一内容块", source_book="测试书",
                            genre_tags=["盲派"], topic_tags=["婚姻"]),
            ],
        }

        result = builder.build_encyclopedia(pool)

        assert "by_genre" in result
        assert "by_topic" in result
        assert "盲派" in result["by_genre"]
        assert "婚姻" in result["by_genre"]["盲派"]
        assert result["by_genre"]["盲派"]["婚姻"]["genre"] == "盲派"
        assert result["by_genre"]["盲派"]["婚姻"]["topic"] == "婚姻"

    def test_double_index_structure(self):
        """验证返回的 {"by_genre": ..., "by_topic": ...} 双索引结构"""
        builder = _make_builder()
        mock_summary = "## 核心观点\n双索引测试。"
        builder.classifier._call_llm.return_value = mock_summary

        pool = {
            "unique_blocks": [
                _make_block("b1", "旺衰派婚姻内容", source_book="书A",
                            genre_tags=["旺衰派"], topic_tags=["婚姻"]),
                _make_block("b2", "格局派婚姻内容", source_book="书B",
                            genre_tags=["格局派"], topic_tags=["婚姻"]),
            ],
        }

        result = builder.build_encyclopedia(pool)

        # by_genre: 两流派
        assert "旺衰派" in result["by_genre"]
        assert "格局派" in result["by_genre"]
        assert "婚姻" in result["by_genre"]["旺衰派"]
        assert "婚姻" in result["by_genre"]["格局派"]

        # by_topic: 婚姻下有两个流派
        assert "婚姻" in result["by_topic"]
        assert "旺衰派" in result["by_topic"]["婚姻"]
        assert "格局派" in result["by_topic"]["婚姻"]
        # 引用应该指向同一个对象
        assert result["by_topic"]["婚姻"]["旺衰派"] is result["by_genre"]["旺衰派"]["婚姻"]

    def test_genre_topic_grouping(self):
        """验证块按 genre_tags[0] 和 topic_tags[0] 正确分组"""
        builder = _make_builder()
        mock_summary = "## 核心观点\n分组测试。"
        builder.classifier._call_llm.return_value = mock_summary

        pool = {
            "unique_blocks": [
                _make_block("b1", "内容A", source_book="书A",
                            genre_tags=["旺衰派"], topic_tags=["婚姻"]),
                _make_block("b2", "内容B", source_book="书B",
                            genre_tags=["旺衰派"], topic_tags=["财运"]),
                _make_block("b3", "内容C", source_book="书C",
                            genre_tags=["格局派"], topic_tags=["婚姻"]),
            ],
        }

        # mock LLM 返回三次（每个条目一次）
        builder.classifier._call_llm.side_effect = [
            "## 核心观点\n旺衰派·婚姻摘要。",
            "## 核心观点\n旺衰派·财运摘要。",
            "## 核心观点\n格局派·婚姻摘要。",
        ]

        result = builder.build_encyclopedia(pool)

        # 旺衰派应有 2 个 topic
        assert len(result["by_genre"]["旺衰派"]) == 2
        assert "婚姻" in result["by_genre"]["旺衰派"]
        assert "财运" in result["by_genre"]["旺衰派"]

        # 格局派应有 1 个 topic
        assert len(result["by_genre"]["格局派"]) == 1
        assert "婚姻" in result["by_genre"]["格局派"]

    def test_blocks_without_tags_default(self):
        """没有标签的块使用默认标签'综合'/'基础理论' """
        builder = _make_builder()
        mock_summary = "## 核心观点\n默认标签测试。"
        builder.classifier._call_llm.return_value = mock_summary

        pool = {
            "unique_blocks": [
                _make_block("b1", "无标签内容", source_book="未知书",
                            genre_tags=[], topic_tags=[]),
            ],
        }

        result = builder.build_encyclopedia(pool)

        # 默认流派：综合
        assert "综合" in result["by_genre"]
        assert "基础理论" in result["by_genre"]["综合"]

    def test_distinct_blocks_included(self):
        """distinct_blocks 也应被包含在百科中"""
        builder = _make_builder()
        mock_summary = "## 核心观点\ndistinct 测试。"
        builder.classifier._call_llm.return_value = mock_summary

        pool = {
            "unique_blocks": [],
            "distinct_blocks": [
                _make_block("b1", "distinct内容", source_book="书D",
                            genre_tags=["调候"], topic_tags=["健康"]),
            ],
        }

        result = builder.build_encyclopedia(pool)

        assert "调候" in result["by_genre"]
        assert "健康" in result["by_genre"]["调候"]


# ---------------------------------------------------------------------------
# TestFormatSourceBlocks
# ---------------------------------------------------------------------------

class TestFormatSourceBlocks:
    """测试 _format_source_blocks 素材格式化"""

    def test_truncation(self):
        """验证 _format_source_blocks 截断到 max_blocks=15"""
        builder = _make_builder()

        blocks = [
            _make_block(f"b{i}", f"素材内容第{i}段", source_book=f"书{i % 3 + 1}")
            for i in range(50)
        ]

        result = builder._format_source_blocks(blocks, max_blocks=15)

        # 应只包含 15 个素材块
        lines = [l for l in result.split("\n") if l.startswith("[素材")]
        assert len(lines) <= 15

    def test_block_text_truncation(self):
        """验证文本截断到 400 字"""
        builder = _make_builder()

        long_text = "测" * 800  # 800 字的测试文本
        blocks = [_make_block("b1", long_text, source_book="长文书")]

        result = builder._format_source_blocks(blocks, max_blocks=15)

        # 格式化后的文本每块最多 400 字
        assert "[素材1]" in result
        # 从结果中提取素材文本部分
        parts = result.split(": ")
        assert len(parts) >= 2
        displayed_text = parts[-1]
        assert len(displayed_text) <= 400

    def test_blocks_sorted_by_length(self):
        """验证素材块按文本长度降序排列"""
        builder = _make_builder()

        blocks = [
            _make_block("b1", "短", source_book="书A"),
            _make_block("b2", "中中中", source_book="书B"),
            _make_block("b3", "长长长长长", source_book="书C"),
        ]

        result = builder._format_source_blocks(blocks, max_blocks=15)

        lines = result.split("\n")
        # 最长的文本来自书C，应该出现在第一个素材块
        assert "书C" in lines[0]

    def test_empty_blocks(self):
        """空 blocks 返回空字符串"""
        builder = _make_builder()

        result = builder._format_source_blocks([], max_blocks=15)

        assert result == ""

    def test_unknown_source(self):
        """没有 source_book 字段时使用默认值'未知' """
        builder = _make_builder()

        block = {"block_id": "b1", "text": "无来源文本"}
        blocks = [block]

        result = builder._format_source_blocks(blocks, max_blocks=15)

        assert "《未知》" in result


# ---------------------------------------------------------------------------
# TestAdFiltering
# ---------------------------------------------------------------------------

class TestAdFiltering:
    """测试 [AD] 标记行在素材中被排除"""

    def test_ad_lines_excluded_from_source_blocks(self):
        """_format_source_blocks 应排除以 [AD] 开头的行"""
        builder = _make_builder()

        blocks = [
            _make_block("b1",
                        "日主喜印，因为没有这个印，那就是身弱。\n[AD] 加微信：804407916\n坐支辰土能晦火。",
                        source_book="测试书"),
        ]

        result = builder._format_source_blocks(blocks, max_blocks=15)

        assert "日主喜印" in result
        assert "[AD]" not in result
        assert "804407916" not in result

    def test_ad_text_not_in_entry_content(self):
        """带 [AD] 标记的原始文本不应出现在条目 content 中"""
        builder = _make_builder()
        builder.classifier._call_llm.return_value = "## 核心观点\n测试摘要"

        blocks = [
            _make_block("b1",
                        "正经内容。\n[AD] 好又全资源网 www.hao8451.com\n更多正经内容。",
                        source_book="测试书"),
        ]

        entry = builder.build_entry("旺衰派", "婚姻", blocks)

        assert "好又全资源网" not in entry["content"]
        assert "www.hao8451" not in entry["content"]

    def test_prompt_includes_ad_skip_instruction(self):
        """build_entry 的 Prompt 应包含跳过 [AD] 的指令"""
        builder = _make_builder()
        builder.classifier._call_llm.return_value = "test"

        blocks = [_make_block("b1", "测试内容", source_book="书")]
        # 不实际调用 LLM，只验证 Prompt 是否包含了关键指令
        # build_entry 内部调用 classifier._call_llm(prompt)
        entry = builder.build_entry("旺衰派", "婚姻", blocks)

        # 验证 classifier._call_llm 被调用时 prompt 中包含 [AD] 指令
        call_args = builder.classifier._call_llm.call_args
        if call_args:
            prompt = call_args[0][0]
            assert "[AD]" in prompt or "广告" in prompt or "跳过" in prompt


# ---------------------------------------------------------------------------
# TestCaseSeparation
# ---------------------------------------------------------------------------

class TestCaseSeparation:
    """测试案例分离与归类"""

    def test_case_blocks_filtered_in_build_case_database(self):
        """build_case_database 应保留 case_study 类型块"""
        builder = _make_builder()

        case_blocks = [
            {
                "block_id": "case1",
                "text": "命例：戊子 乙卯 丙辰 癸巳，2017年离婚",
                "source_book": "金镖门笔记",
                "topic_tags": ["婚姻"],
                "genre_tags": ["旺衰派"],
            },
        ]

        cases = builder.build_case_database(case_blocks)

        assert len(cases) == 1
        assert cases[0]["case_id"] == "case1"
        assert cases[0]["text"] == case_blocks[0]["text"]

    def test_case_database_preserves_tags(self):
        """命例数据库保留 topic_tags 和 genre_tags"""
        builder = _make_builder()

        case_blocks = [{
            "block_id": "case1",
            "text": "命例内容",
            "source_book": "测试书",
            "topic_tags": ["婚姻", "财运"],
            "genre_tags": ["格局派"],
        }]

        cases = builder.build_case_database(case_blocks)

        assert "婚姻" in cases[0]["topic_tags"]
        assert "财运" in cases[0]["topic_tags"]
        assert "格局派" in cases[0]["genre_tags"]

    def test_case_database_empty_input(self):
        """空输入返回空列表"""
        builder = _make_builder()
        cases = builder.build_case_database([])
        assert cases == []
