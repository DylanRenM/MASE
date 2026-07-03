"""预处理层: 格式统一 + 内容清洗 + 结构提取 + 语义分块

上游输入: 原始文件路径 (docx/pdf/doc/txt/epub)
下游输出: TextBlock 列表，供 Pipeline 进入向量化和分类阶段

架构:
    FormatBridge    → Markdown 文本
    ContentCleaner  → 净化的 Markdown
    StructureParser → [(section_path, paragraphs)]
    SemanticChunker → [TextBlock]
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import config


@dataclass
class TextBlock:
    """语义分块产出单元"""
    block_id: str                          # {book_id}_{index:04d}
    text: str                              # 块文本
    section: Optional[str] = None          # 所属章节路径
    genre_tags: list = field(default_factory=list)     # 主流派标签（单个）
    topic_tags: list = field(default_factory=list)     # 主专题标签（单个）
    source: str = ""                       # 来源书名
    secondary_genres: list = field(default_factory=list)  # 次流派
    secondary_topics: list = field(default_factory=list)  # 次专题
    source_file: str = ""                  # 来源文件路径


class FormatBridge:
    """格式统一层: 将各类文档转换为干净的 Markdown 文本

    支持: docx, doc, pdf (含扫描版OCR兜底), txt, epub
    """

    def __init__(self):
        self._md_converter = None
        self._ocr = None

    def _get_md(self):
        if self._md_converter is None:
            try:
                from markitdown import MarkItDown
                self._md_converter = MarkItDown()
            except ImportError:
                self._md_converter = False
        return self._md_converter if self._md_converter is not False else None

    def _get_ocr(self):
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(lang=config.ocr_lang, show_log=False)
            except Exception:
                self._ocr = False
        return self._ocr if self._ocr is not False else None

    def convert(self, file_path: str, suffix: str) -> Optional[str]:
        """将文件转换为 Markdown 文本。返回 None 表示无法处理"""
        path = Path(file_path)
        if not path.exists():
            return None

        suffix = suffix.lower().lstrip(".")

        if suffix == "txt":
            return self._convert_txt(path)
        elif suffix == "docx":
            return self._convert_docx(path)
        elif suffix == "doc":
            return self._convert_doc(path)
        elif suffix == "pdf":
            return self._convert_pdf(path)
        elif suffix == "epub":
            return self._convert_epub(path)
        else:
            return None

    def _convert_txt(self, path: Path) -> str:
        try:
            import chardet
            raw = path.read_bytes()
            detected = chardet.detect(raw)
            encoding = detected.get("encoding", "utf-8") or "utf-8"
            return raw.decode(encoding, errors="replace")
        except Exception:
            return path.read_text(encoding="utf-8", errors="replace")

    def _convert_docx(self, path: Path) -> Optional[str]:
        md = self._get_md()
        if md is not None:
            try:
                result = md.convert(str(path))
                if result and result.text_content:
                    return result.text_content
            except Exception:
                pass
        # 兜底: python-docx
        try:
            from docx import Document
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception:
            return None

    def _convert_doc(self, path: Path) -> Optional[str]:
        md = self._get_md()
        if md is not None:
            try:
                result = md.convert(str(path))
                if result and result.text_content:
                    return result.text_content
            except Exception:
                pass
        # 兜底: 先试 docx 兼容
        try:
            from docx import Document
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception:
            pass
        return None

    def _convert_pdf(self, path: Path) -> Optional[str]:
        # 尝试提取文本层
        md = self._get_md()
        text_content = None
        if md is not None:
            try:
                result = md.convert(str(path))
                if result and result.text_content:
                    text_content = result.text_content
            except Exception:
                pass

        # 用 pypdf 验证文本层是否为空
        import pypdf
        try:
            reader = pypdf.PdfReader(str(path))
            native_text = "\n".join(
                page.extract_text() or "" for page in reader.pages
            ).strip()
        except Exception:
            native_text = ""

        # 有文本层则返回
        has_text = text_content and len(text_content.strip()) > 100
        if has_text:
            return text_content

        # 文本层为空 → 扫描版PDF → OCR
        if config.ocr_enabled:
            return self._ocr_pdf(path)

        return text_content or native_text or None

    def _ocr_pdf(self, path: Path) -> Optional[str]:
        """PaddleOCR 逐页识别扫描版PDF"""
        ocr = self._get_ocr()
        if ocr is False:
            return None

        # OCR结果缓存
        cache_dir = config.data_dir / "ocr_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        file_hash = hashlib.md5(str(path).encode()).hexdigest()
        cache_file = cache_dir / f"{file_hash}.txt"
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")

        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            page_count = len(reader.pages)
        except Exception:
            return None

        all_texts = []
        for i in range(page_count):
            try:
                result = ocr.ocr(str(path), cls=False)
                if result and result[0]:
                    page_text = " ".join(
                        line[1][0] for group in result for line in group
                        if line and len(line) > 1
                    )
                    all_texts.append(page_text)
            except Exception:
                continue

        combined = "\n".join(all_texts).strip()
        if combined:
            cache_file.write_text(combined, encoding="utf-8")
        return combined or None

    def _convert_epub(self, path: Path) -> Optional[str]:
        md = self._get_md()
        if md is not None:
            try:
                result = md.convert(str(path))
                if result and result.text_content:
                    return result.text_content
            except Exception:
                pass
        return None


class ContentCleaner:
    """内容清洗层: 去广告、去水印、换行合并、去乱码"""

    # 水印/广告模式
    WATERMARK_PATTERNS = [
        re.compile(r"好又全资源网.*加微信.*送.*电子书", re.IGNORECASE),
        re.compile(r"AAKK\d+加微信进群聊", re.IGNORECASE),
        re.compile(r"获取更多.*资料.*加微信.*", re.IGNORECASE),
    ]

    CONTACT_PATTERNS = [
        re.compile(r"微信[号:：]?\s*[a-zA-Z0-9_\-]{5,}"),
        re.compile(r"QQ[群号]?[：:]\s*\d{5,}"),
        re.compile(r"公众号[：:]\s*\S+"),
        re.compile(r"购.*教材.*微信[：:]\s*\S+"),
    ]

    @classmethod
    def clean(cls, markdown_text: str) -> str:
        """执行完整的清洗流程"""
        text = markdown_text

        # 1. 去水印/页眉页脚
        for pattern in cls.WATERMARK_PATTERNS:
            text = pattern.sub("", text)

        # 2. 去广告/联系方式
        for pattern in cls.CONTACT_PATTERNS:
            text = pattern.sub("", text)

        # 3. 换行合并
        text = cls._merge_broken_lines(text)

        # 4. 去除重复空行
        text = re.sub(r"\n{4,}", "\n\n\n", text)

        # 5. 去除乱码行
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            if cls._is_garbled(line):
                continue
            cleaned_lines.append(line)
        text = "\n".join(cleaned_lines)

        return text

    @classmethod
    def _merge_broken_lines(cls, text: str) -> str:
        """合并因PDF提取等原因被强制换行的中文文本行"""
        lines = text.split("\n")
        if len(lines) <= 1:
            return text

        merged = []
        i = 0
        while i < len(lines):
            current = lines[i]
            next_line = lines[i + 1] if i + 1 < len(lines) else None

            if next_line is None:
                merged.append(current)
                break

            # 判断是否合并
            if cls._should_merge(current, next_line):
                merged.append(current + next_line)
                i += 2
            else:
                merged.append(current)
                i += 1

        return "\n".join(merged)

    @staticmethod
    def _should_merge(line1: str, line2: str) -> bool:
        """判断两行是否应该合并"""
        if not line1 or not line2:
            return False

        # 上一行以句末标点结尾 → 不合并
        if re.search(r"[。！？…―]$", line1.rstrip()):
            return False

        # 下一行以 Markdown 标记开头 → 不合并
        if re.match(r"^[#\-\*>]", line2.lstrip()):
            return False

        # 上一行以中文字符结尾
        ends_with_cjk = bool(re.search(r"[\u4e00-\u9fff\uff00-\uffef]$", line1.rstrip()))

        # 下一行以中文字符开头
        starts_with_cjk = bool(re.search(r"^[\u4e00-\u9fff\uff00-\uffef]", line2.lstrip()))

        if not (ends_with_cjk and starts_with_cjk):
            return False

        # 合并后不超过 80 字
        combined_len = len(line1.rstrip()) + len(line2.lstrip())
        return combined_len <= 80

    @staticmethod
    def _is_garbled(line: str) -> bool:
        """判断一行是否为乱码"""
        if len(line) <= 20:
            return False

        # 统计非中文字符占比
        non_cjk = sum(1 for c in line if not re.match(r"[\u4e00-\u9fff\uff00-\uffef]", c))
        total = max(len(line), 1)
        return non_cjk / total > 0.7


class StructureParser:
    """结构提取层: 解析 Markdown 标题层级，提取章节边界"""

    @staticmethod
    def parse(markdown_text: str) -> list[tuple[Optional[str], list[str]]]:
        """解析 Markdown，返回 [(section_path, [paragraphs]), ...]"""
        if not markdown_text.strip():
            return [(None, [])]

        lines = markdown_text.split("\n")
        sections = []
        current_path = None
        current_paras = []

        # 当前各级标题
        h1 = h2 = h3 = None

        for line in lines:
            stripped = line.strip()

            # H1: #
            m1 = re.match(r"^#\s+(.+)$", stripped)
            if m1:
                if current_paras:
                    sections.append((current_path, current_paras))
                h1 = m1.group(1).strip()
                h2 = h3 = None
                current_path = h1
                current_paras = []
                continue

            # H2: ##
            m2 = re.match(r"^##\s+(.+)$", stripped)
            if m2:
                if current_paras:
                    sections.append((current_path, current_paras))
                h2 = m2.group(1).strip()
                h3 = None
                parts = [p for p in [h1, h2] if p]
                current_path = " / ".join(parts) if parts else None
                current_paras = []
                continue

            # H3: ###
            m3 = re.match(r"^###\s+(.+)$", stripped)
            if m3:
                if current_paras:
                    sections.append((current_path, current_paras))
                h3 = m3.group(1).strip()
                parts = [p for p in [h1, h2, h3] if p]
                current_path = " / ".join(parts) if parts else None
                current_paras = []
                continue

            # 普通段落
            if stripped:
                current_paras.append(stripped)

        # 最后一个section
        if current_path is not None or current_paras:
            sections.append((current_path, current_paras))

        # 如果没有任何section（无标题文档），整篇作为一个section
        if not sections:
            sections.append((None, current_paras))

        return sections


class SemanticChunker:
    """语义分块层: 在章节边界内按自然段 + 句号兜底进行分块

    优先级: 章节边界 > 自然段 > 句号拆分
    """

    @classmethod
    def chunk(cls, sections: list[tuple[Optional[str], list[str]]],
              book_id: str, source_book: str) -> list[TextBlock]:
        """对解析后的章节进行语义分块"""
        blocks = []
        block_index = 0

        for section_path, paragraphs in sections:
            if not paragraphs:
                continue

            current_texts = []
            current_len = 0

            for para in paragraphs:
                para_len = len(para)

                # 长段拆分: > config.chunk_max_size
                if para_len > config.chunk_max_size:
                    # 先累积当前
                    if current_texts:
                        blocks.append(cls._make_block(
                            current_texts, book_id, block_index, section_path, source_book))
                        block_index += 1
                        current_texts = []
                        current_len = 0

                    # 按句号拆分长段
                    sub_blocks = cls._split_long_para(para)
                    for sub in sub_blocks:
                        blocks.append(cls._make_block(
                            [sub], book_id, block_index, section_path, source_book))
                        block_index += 1
                    continue

                # 加入当前段落会导致超标
                if current_len + para_len > config.chunk_max_size and current_texts:
                    blocks.append(cls._make_block(
                        current_texts, book_id, block_index, section_path, source_book))
                    block_index += 1
                    current_texts = [para]
                    current_len = para_len
                else:
                    current_texts.append(para)
                    current_len += para_len

            # 章节末尾，输出剩余
            if current_texts:
                # 短段：如果不足 chunk_min_size 且不是最后章节，留到与下一章节合并
                # 简化：直接输出
                blocks.append(cls._make_block(
                    current_texts, book_id, block_index, section_path, source_book))
                block_index += 1

        return blocks

    @staticmethod
    def _make_block(texts: list[str], book_id: str, idx: int,
                    section: Optional[str], source: str) -> TextBlock:
        return TextBlock(
            block_id=f"{book_id}_{idx:04d}",
            text="\n\n".join(texts),
            section=section,
            source=source,
        )

    @staticmethod
    def _split_long_para(para: str) -> list[str]:
        """将超长段落按句末标点拆分"""
        # 按 。! ？ 切分
        sentences = re.split(r"(?<=[。！？])", para)
        chunks = []
        current = ""

        for sent in sentences:
            if len(current) + len(sent) <= config.chunk_max_size:
                current += sent
            else:
                if current:
                    chunks.append(current)
                # 如果单个句段还是太长，强制截断
                current = sent
                while len(current) > config.chunk_max_size:
                    chunks.append(current[:config.chunk_max_size])
                    current = current[config.chunk_max_size:]

        if current:
            chunks.append(current)

        return chunks
