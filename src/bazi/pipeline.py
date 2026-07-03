"""管道编排器: 串联四个阶段，管理管线执行"""

import asyncio
import threading
import uuid
import time
from pathlib import Path

from qdrant_client.models import PointStruct

from .config import config
from .database import (
    add_book, get_book, get_all_books, get_pending_books,
    update_book_status, update_block_count, add_pipeline_log, init_db,
)
from .book_parser import parse_file, Block
from .content_vectorizer import Vectorizer, LLMClassifier, RuleClassifier
from .qdrant_store import get_client, init_collection, upsert_points
from .dedup_pipeline import DedupPipeline
from .preprocessor import FormatBridge, StructureParser, SemanticChunker, LLMNormalizer, TextBlock


class PipelineOrchestrator:
    """管道编排器，管理四阶段管线"""

    def __init__(self):
        init_db()
        self.client = init_collection()
        self._vectorizer = None
        self._classifier = None
        self._dedup = None
        self._format_bridge = None
        self._llm_classifier = None
        self._normalizer = None

        # 进度跟踪
        self._progress = {}
        self._running = {}

    @property
    def vectorizer(self):
        if self._vectorizer is None:
            self._vectorizer = Vectorizer()
        return self._vectorizer

    @property
    def classifier(self):
        if self._classifier is None:
            if config.classifier_backend == "rule":
                self._classifier = RuleClassifier()
                print(f"[Pipeline] 使用规则分类器")
            else:
                self._classifier = LLMClassifier()
                print(f"[Pipeline] 使用LLM分类器: {config.llm_model}")
        return self._classifier

    @property
    def llm_classifier(self):
        """LLM分类器（用于兜底）"""
        if self._llm_classifier is None:
            self._llm_classifier = LLMClassifier()
        return self._llm_classifier

    @property
    def format_bridge(self):
        if self._format_bridge is None:
            self._format_bridge = FormatBridge()
        return self._format_bridge

    @property
    def dedup(self):
        if self._dedup is None:
            self._dedup = DedupPipeline()
        return self._dedup

    @property
    def normalizer(self):
        if self._normalizer is None:
            self._normalizer = LLMNormalizer()
        return self._normalizer

    def run_pipeline(self, file_path: str, filename: str, fmt: str, title: str = None, author: str = None):
        """同步运行完整管线（集成预处理层）"""
        # 添加书籍记录
        book_id = add_book(filename, file_path, fmt, title, author)
        self._running[book_id] = True

        try:
            # 阶段1: 预处理 — 格式统一 + 清洗 + 结构提取 + 语义分块
            print(f"[Pipeline] 阶段1: 预处理 {filename}")
            self._set_progress(book_id, 1, 0.0, "格式转换...")
            add_pipeline_log(book_id, "parse", "running", f"开始预处理: {filename}")

            # 1a. FormatBridge: 格式统一
            t0 = time.time()
            md_text = self.format_bridge.convert(file_path, fmt)
            if md_text is None:
                # 回退到旧解析器
                print(f"[Pipeline] 预处理失败，回退到旧解析器")
                blocks = parse_file(file_path, source_book=title or filename, book_id=book_id)
                # 转换为TextBlock
                text_blocks = [
                    TextBlock(
                        block_id=b.block_id, text=b.text,
                        source=b.source_book, source_file=file_path
                    ) for b in blocks
                ]
            else:
                self._set_progress(book_id, 1, 0.25, "结构提取...")
                add_pipeline_log(book_id, "parse", "running",
                                f"格式转换完成 ({time.time()-t0:.1f}s), 结构提取...")

                # 1c. StructureParser: 结构提取
                self._set_progress(book_id, 1, 0.50, "结构提取...")
                t2 = time.time()
                sections = StructureParser.parse(md_text)
                add_pipeline_log(book_id, "parse", "running",
                                f"结构提取完成 ({time.time()-t2:.1f}s), {len(sections)}个章节, 语义分块...")

                # 1d. SemanticChunker: 语义分块
                self._set_progress(book_id, 1, 0.75, "语义分块...")
                t3 = time.time()
                text_blocks = SemanticChunker.chunk(
                    sections, book_id, title or filename
                )
                for tb in text_blocks:
                    tb.source_file = file_path
                add_pipeline_log(book_id, "parse", "running",
                                f"分块完成 ({time.time()-t3:.1f}s)")

            update_block_count(book_id, len(text_blocks))
            add_pipeline_log(book_id, "parse", "done",
                            f"预处理完成: {len(text_blocks)} 个文本块 (总耗时 {time.time()-t0:.1f}s)")
            self._set_progress(book_id, 1, 1.0, f"预处理完成: {len(text_blocks)}个块")
            print(f"[Pipeline] 阶段1完成: {len(text_blocks)} 个块")

            # 规范化: LLM文本规范化 + 去广告标注
            t_norm = time.time()
            print(f"[Pipeline] 文本规范化...")
            text_blocks = self.normalizer.normalize(text_blocks)
            norm_elapsed = time.time() - t_norm
            add_pipeline_log(book_id, "normalize", "done",
                            f"规范化完成 ({norm_elapsed:.1f}s)")
            print(f"[Pipeline] 规范化完成 ({norm_elapsed:.1f}s)")

            if not text_blocks or not self._running.get(book_id):
                if not text_blocks:
                    update_book_status(book_id, "done", 1.0)
                    add_pipeline_log(book_id, "parse", "done", "文件无可用内容")
                return

            # 阶段2: 向量化 + 分类
            print(f"[Pipeline] 阶段2: 向量化 ({len(text_blocks)}块)...")
            self._set_progress(book_id, 2, 0.0, "向量化")
            add_pipeline_log(book_id, "vectorize", "running", f"向量化 {len(text_blocks)} 个块")

            texts = [tb.text for tb in text_blocks]
            vectors = self.vectorizer.encode_batch(texts)
            add_pipeline_log(book_id, "vectorize", "done", f"向量化完成")
            print(f"[Pipeline] 向量化完成, 开始分类...")

            # 分类: 优先单主标签 + LLM兜底
            self._set_progress(book_id, 2, 0.5, "分类...")
            add_pipeline_log(book_id, "classify", "running",
                            f"分类 {len(text_blocks)} 个块")

            if isinstance(self.classifier, RuleClassifier):
                # 规则分类 + LLM兜底
                llm_fallback = self.llm_classifier if config.llm_fallback_enabled else None
                classifications = []
                for i, text in enumerate(texts):
                    cls = self.classifier.classify_with_fallback(text, llm_fallback)
                    classifications.append(cls)
                    if (i + 1) % 50 == 0:
                        print(f"  分类进度: {i+1}/{len(texts)}", flush=True)
            else:
                classifications = self.classifier.classify_batch(texts)

            # 检查综合兜底占比
            fallback_count = sum(1 for c in classifications if "综合" in c.get("genre_tags", []))
            if fallback_count > 0:
                print(f"[Pipeline] LLM兜底分类: {fallback_count}/{len(texts)} 块归入综合")
            add_pipeline_log(book_id, "classify", "done", f"分类完成")
            self._set_progress(book_id, 2, 1.0, "向量化+分类完成")
            if not self._running.get(book_id):
                return

            # 阶段3: 写入 Qdrant（含 secondary 标签）
            print(f"[Pipeline] 阶段3: 写入 Qdrant ({len(text_blocks)}条)...")
            self._set_progress(book_id, 3, 0.0, "写入向量库")
            add_pipeline_log(book_id, "qdrant", "running",
                            f"写入 {len(text_blocks)} 条向量记录")
            points = []
            for i, (tb, vec, cls) in enumerate(zip(text_blocks, vectors, classifications)):
                points.append(PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{book_id}_{i:06d}")),
                    vector=vec,
                    payload={
                        "book_id": book_id,
                        "source_book": tb.source,
                        "chapter": tb.section or "",
                        "block_id": tb.block_id,
                        "block_text": tb.text,
                        "genre_tags": cls.get("genre_tags", []),
                        "topic_tags": cls.get("topic_tags", []),
                        "content_type": cls.get("content_type", ""),
                        "secondary_genres": cls.get("secondary_genres", []),
                        "secondary_topics": cls.get("secondary_topics", []),
                    },
                ))
            upsert_points(self.client, points)
            add_pipeline_log(book_id, "qdrant", "done", f"写入完成")
            self._set_progress(book_id, 3, 1.0, "写入完成")
            print(f"[Pipeline] Qdrant 写入完成")
            if not self._running.get(book_id):
                return

            # 更新状态为完成
            self._set_progress(book_id, 4, 1.0, "完成")
            update_book_status(book_id, "done", 1.0)
            add_pipeline_log(book_id, "merge", "done", f"全管线完成")
            print(f"[Pipeline] 全管线完成! book_id={book_id}, 块数={len(text_blocks)}")

        except Exception as e:
            update_book_status(book_id, "failed", 0.0)
            add_pipeline_log(book_id, "error", "failed", str(e))
            self._set_progress(book_id, 0, 0.0, f"失败: {e}")
            raise
        finally:
            self._running.pop(book_id, None)

    def run_pipeline_async(self, file_path: str, filename: str, fmt: str, title: str = None, author: str = None):
        """异步运行管线（在后台线程中）"""
        thread = threading.Thread(
            target=self.run_pipeline,
            args=(file_path, filename, fmt, title, author),
            daemon=True,
        )
        thread.start()

    def rebuild_encyclopedia(self):
        """全量重构百科全书（对已有全部向量做去重+编排）"""
        from .encyclopedia_builder import EncyclopediaBuilder

        add_pipeline_log("global", "rebuild", "running", "开始全量去重")
        knowledge_pool = self.dedup.run_full_dedup()
        add_pipeline_log("global", "rebuild_dedup", "done",
                        f"去重完成: {len(knowledge_pool.get('unique_blocks',[]))} 唯一条目")

        add_pipeline_log("global", "rebuild_build", "running", "开始生成百科")
        builder = EncyclopediaBuilder()
        encyclopedia = builder.build_encyclopedia(knowledge_pool)
        cases = builder.build_case_database(knowledge_pool.get("unique_blocks", []))
        builder.save(encyclopedia, cases)
        add_pipeline_log("global", "rebuild_build", "done",
                        f"百科生成完成: {len(encyclopedia)} 流派")

        return encyclopedia

    def get_progress(self, book_id: str) -> dict:
        """查询管线进度"""
        return self._progress.get(book_id, {"stage": 0, "progress": 0.0, "message": "未知"})

    def _set_progress(self, book_id: str, stage: int, progress: float, message: str):
        """更新进度"""
        self._progress[book_id] = {"stage": stage, "progress": progress, "message": message}
        update_book_status(book_id, "processing", progress if stage > 0 else 0.0)


# 全局编排器实例
orchestrator = PipelineOrchestrator()
