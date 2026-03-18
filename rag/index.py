# -*- coding: utf-8 -*-
"""向量索引：按书建 Chroma 集合，支持增量。"""
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

from config import ensure_dirs, VECTOR_STORE_DIR, TOP_K
from .chunk import split_novel_into_chunks, ChunkWithMeta
from .embedding import get_embedding_model


def _chunks_to_documents(chunks: List[ChunkWithMeta]) -> List[Document]:
    return [
        Document(
            page_content=c.content,
            metadata={
                "chapter_index": c.chapter_index,
                "chapter_title": c.chapter_title,
                "chunk_index": c.chunk_index,
            },
        )
        for c in chunks
    ]


def _collection_path(novel_id: str) -> Path:
    ensure_dirs()
    return VECTOR_STORE_DIR / novel_id


def build_index(
    novel_id: str,
    chunks: List[ChunkWithMeta],
    force_rebuild: bool = False,
):
    """
    为小说 novel_id 创建或重建 Chroma 索引。
    force_rebuild=True 时先删旧库再建。
    """
    path = _collection_path(novel_id)
    if force_rebuild and path.exists():
        import shutil
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

    docs = _chunks_to_documents(chunks)
    embeddings = get_embedding_model()
    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=str(path),
        collection_name="novel",
    )
    return path


def get_retriever(novel_id: str, top_k: int = None):
    """获取该小说的检索器（用于 RAG）。"""
    vs = _get_vectorstore(novel_id)
    return vs.as_retriever(search_kwargs={"k": top_k or TOP_K})


@lru_cache(maxsize=8)
def _get_vectorstore(novel_id: str) -> Chroma:
    """缓存每本书的向量库句柄，避免每次提问重复打开与初始化。"""
    path = _collection_path(novel_id)
    if not path.exists():
        raise FileNotFoundError(f"未找到小说索引，请先建索引: {novel_id}")
    embeddings = get_embedding_model()
    return Chroma(
        persist_directory=str(path),
        embedding_function=embeddings,
        collection_name="novel",
    )


def index_novel(novel_id: str, force_rebuild: bool = False) -> int:
    """
    从已存储的小说 JSON 建索引，返回 chunk 数量。
    """
    from crawler import load_novel
    novel = load_novel(novel_id)
    if not novel:
        raise FileNotFoundError(f"未找到小说数据: {novel_id}")
    chunks = split_novel_into_chunks(novel.chapters)
    build_index(novel_id, chunks, force_rebuild=force_rebuild)
    return len(chunks)
