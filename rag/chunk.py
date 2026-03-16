# -*- coding: utf-8 -*-
"""按长度切分，带 overlap，并保留章节/段落元信息。"""
from dataclasses import dataclass
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class ChunkWithMeta:
    """带元数据的一段文本，用于向量化与引用。"""
    content: str
    chapter_index: int
    chapter_title: str
    chunk_index: int  # 在该章内的片段序号


def split_novel_into_chunks(
    chapters: list,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[ChunkWithMeta]:
    """
    将小说按章切分后，每章再按长度切分（可重叠）。
    chapters: 元素需有 .title, .content, .index
    """
    chunk_size = chunk_size or CHUNK_SIZE
    chunk_overlap = chunk_overlap or CHUNK_OVERLAP
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
    )
    result = []
    for ch in chapters:
        parts = splitter.split_text(ch.content)
        for i, text in enumerate(parts):
            if not text.strip():
                continue
            result.append(ChunkWithMeta(
                content=text,
                chapter_index=getattr(ch, "index", 0),
                chapter_title=getattr(ch, "title", ""),
                chunk_index=i + 1,
            ))
    return result
