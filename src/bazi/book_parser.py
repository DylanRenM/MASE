"""阶段1: 电子书批量解析与统一分块"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import chardet


@dataclass
class Block:
    """文本块"""
    block_id: str
    text: str
    source_book: str
    chapter: str = ""
    book_id: str = ""

    def to_payload(self) -> dict:
        """转为 Qdrant payload 格式"""
        return {
            "book_id": self.book_id,
            "source_book": self.source_book,
            "chapter": self.chapter,
            "block_text": self.text,
            "block_id": self.block_id,
        }


def _detect_encoding(file_path: str) -> str:
    """检测文件编码"""
    with open(file_path, "rb") as f:
        raw = f.read(100000)  # 读前100KB做检测
    result = chardet.detect(raw)
    return result.get("encoding", "utf-8") or "utf-8"


def _smart_chunk_text(text: str, source_book: str, chapter: str, book_id: str,
                      min_size: int = 300, max_size: int = 500, overlap: int = 50) -> list[Block]:
    """智能分块：按段落边界分割，保持语义完整性"""
    if not text or not text.strip():
        return []

    # 按段落分割
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    blocks = []
    current_chunk = ""
    block_index = 0

    for para in paragraphs:
        # 如果当前段落加入后超过max_size，先输出当前块
        if len(current_chunk) + len(para) > max_size and current_chunk:
            block_id = f"{book_id}_{block_index:04d}"
            blocks.append(Block(
                block_id=block_id,
                text=current_chunk.strip(),
                source_book=source_book,
                chapter=chapter,
                book_id=book_id,
            ))
            block_index += 1
            # 保留重叠部分
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + "\n\n" + para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

        # 处理超长段落：按句子继续切分
        while len(current_chunk) > max_size:
            # 找到max_size附近最近的句子边界
            split_pos = max_size
            for sep in ["。", "！", "？", "；", "\n"]:
                pos = current_chunk.rfind(sep, min_size, max_size)
                if pos > 0:
                    split_pos = pos + 1
                    break

            block_id = f"{book_id}_{block_index:04d}"
            blocks.append(Block(
                block_id=block_id,
                text=current_chunk[:split_pos].strip(),
                source_book=source_book,
                chapter=chapter,
                book_id=book_id,
            ))
            block_index += 1
            # 重叠
            overlap_start = max(0, split_pos - overlap)
            current_chunk = current_chunk[overlap_start:]

    # 处理最后剩余的内容
    if current_chunk.strip():
        block_id = f"{book_id}_{block_index:04d}"
        blocks.append(Block(
            block_id=block_id,
            text=current_chunk.strip(),
            source_book=source_book,
            chapter=chapter,
            book_id=book_id,
        ))

    return blocks


def _parse_txt(file_path: str, source_book: str, book_id: str) -> list[Block]:
    """解析 TXT 文件"""
    encoding = _detect_encoding(file_path)
    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        text = f.read()
    return _smart_chunk_text(text, source_book, "", book_id)


def _parse_docx(file_path: str, source_book: str, book_id: str) -> list[Block]:
    """解析 DOCX 文件"""
    from docx import Document

    doc = Document(file_path)
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text.strip())
    text = "\n\n".join(paragraphs)
    return _smart_chunk_text(text, source_book, "", book_id)


def _parse_doc(file_path: str, source_book: str, book_id: str) -> list[Block]:
    """解析旧版 DOC 文件（尝试使用 python-docx 或 antiword）"""
    # DOC 格式较旧，尝试常见处理方式
    try:
        # 尝试用 python-docx（某些 .doc 实际上是 docx 格式）
        return _parse_docx(file_path, source_book, book_id)
    except Exception:
        pass

    # 尝试使用 textract 或直接读取
    try:
        with open(file_path, "rb") as f:
            raw = f.read()
        # 尝试从二进制中提取可读文本
        text = raw.decode("utf-8", errors="replace")
        # 过滤掉过多的乱码字符
        import unicodedata
        clean_chars = []
        for ch in text:
            cat = unicodedata.category(ch)
            if cat.startswith(('L', 'N', 'P', 'Z')) or ch in '\n\r\t ':
                clean_chars.append(ch)
        text = ''.join(clean_chars)
        # 只保留中英文常见字符
        text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9\s\.\,\!\?\;\:\"\'\(\)\[\]\{\}\-\+\=\/\@\#\$\%\^\&\*\_\~]', ' ', text)
        if len(text.strip()) > 100:
            return _smart_chunk_text(text, source_book, "", book_id)
    except Exception:
        pass

    raise ValueError(f"无法解析 DOC 文件: {file_path}，请尝试将其转换为 DOCX 格式")


def _parse_pdf(file_path: str, source_book: str, book_id: str) -> list[Block]:
    """解析 PDF 文件"""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages_text.append(text.strip())

    if not pages_text:
        raise ValueError(f"PDF 文件无文本内容，可能需要 OCR: {file_path}")

    text = "\n\n".join(pages_text)
    return _smart_chunk_text(text, source_book, "", book_id)


# 公开函数
smart_chunk = _smart_chunk_text


_SUPPORTED_FORMATS = {
    ".txt": _parse_txt,
    ".epub": None,  # 暂不实现
    ".pdf": _parse_pdf,
    ".docx": _parse_docx,
    ".doc": _parse_doc,
}


def parse_file(file_path: str, source_book: str = "", book_id: str = "") -> list[Block]:
    """解析电子书文件，返回文本块列表

    Args:
        file_path: 文件路径
        source_book: 来源书名
        book_id: 书籍数据库ID

    Returns:
        Block 列表

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不支持的文件格式
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix not in _SUPPORTED_FORMATS:
        raise ValueError(f"不支持的文件格式: {suffix}，支持的格式: {list(_SUPPORTED_FORMATS.keys())}")

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if source_book == "":
        source_book = path.stem

    parser = _SUPPORTED_FORMATS[suffix]
    if parser is None:
        raise ValueError(f"格式 {suffix} 尚未实现")

    return parser(file_path, source_book, book_id)
