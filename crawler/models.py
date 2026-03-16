# -*- coding: utf-8 -*-
"""小说与章节数据结构。"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Chapter:
    """单章"""
    title: str
    content: str
    index: int = 0  # 章节序号，从 1 开始


@dataclass
class Novel:
    """一本书：元信息 + 章节列表"""
    title: str
    author: str = ""
    source: str = ""  # 来源描述，如 "local_txt", "epub", "url"
    chapters: List[Chapter] = field(default_factory=list)

    @property
    def total_chars(self) -> int:
        return sum(len(c.content) for c in self.chapters)

    def to_dict(self):
        return {
            "title": self.title,
            "author": self.author,
            "source": self.source,
            "chapters": [
                {"index": c.index, "title": c.title, "content": c.content}
                for c in self.chapters
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Novel":
        chapters = [
            Chapter(index=ch.get("index", i + 1), title=ch["title"], content=ch["content"])
            for i, ch in enumerate(d.get("chapters", []))
        ]
        return cls(
            title=d.get("title", ""),
            author=d.get("author", ""),
            source=d.get("source", ""),
            chapters=chapters,
        )
