# -*- coding: utf-8 -*-
"""从本地 EPUB 解析小说。"""
from pathlib import Path
from ebooklib import epub
from bs4 import BeautifulSoup

from .models import Novel, Chapter
from .clean import clean_content


def _epub_item_to_text(item) -> str:
    if item is None:
        return ""
    soup = BeautifulSoup(item.get_content(), "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return clean_content(text)


def crawl_novel_from_epub(
    path: str | Path,
    title: str = "",
    author: str = "",
) -> Novel:
    """
    从本地 EPUB 解析小说，按 TOC 或 item 顺序得到章节。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    book = epub.read_epub(str(path))

    if not title:
        titles = book.get_metadata("DC", "title")
        title = titles[0][0].strip() if titles and titles[0][0] else path.stem
    if not author:
        creators = book.get_metadata("DC", "creator")
        author = creators[0][0].strip() if creators and creators[0][0] else ""

    chapters = []
    # 按 spine 顺序遍历
    for i, (item_id, _) in enumerate(book.spine):
        item = book.get_item_with_id(item_id)
        if item is None:
            continue
        content = _epub_item_to_text(item)
        if not content.strip():
            continue
        # 取前 50 字作为标题（或从 TOC 取，这里简化）
        ch_title = content[:50].replace("\n", " ").strip()
        if len(content) > 50:
            ch_title = ch_title + "…"
        chapters.append(Chapter(index=i + 1, title=ch_title, content=content))

    return Novel(title=title, author=author, source="local_epub", chapters=chapters)
