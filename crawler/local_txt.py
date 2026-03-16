# -*- coding: utf-8 -*-
"""从本地 TXT 解析小说：按章节标题切分。"""
import re
from pathlib import Path
from .models import Novel, Chapter
from .clean import clean_content


# 常见章节标题模式
CHAPTER_PATTERNS = [
    re.compile(r"^\s*第[一二三四五六七八九十百千万零\d]+[章回节集卷]\s*.*$", re.MULTILINE),
    re.compile(r"^\s*[Chapter\s]*\d+\s*[\.\-\s].*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*【.*?】\s*$", re.MULTILINE),
    re.compile(r"^\s*[零一二三四五六七八九十百千\d]+\s*[\.、．]\s*.*$", re.MULTILINE),
]


def _find_chapter_starts(text: str) -> list:
    """返回 (start_pos, title) 列表。"""
    lines = text.splitlines()
    results = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        for pat in CHAPTER_PATTERNS:
            if pat.match(stripped):
                # 行首在全文中的位置
                pos = sum(len(l) + 1 for l in lines[:i])
                results.append((pos, stripped))
                break
    # 若没有任何匹配，整本当作一章
    if not results:
        results.append((0, "正文"))
    return results


def crawl_novel_from_txt(
    path: str | Path,
    title: str = "",
    author: str = "",
    encoding: str = "utf-8",
) -> Novel:
    """
    从本地 TXT 解析小说。
    - path: 文件路径
    - title/author: 若为空则尝试从文件名/首行推断
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    raw = path.read_text(encoding=encoding)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")

    if not title:
        title = path.stem

    starts = _find_chapter_starts(raw)
    chapters = []
    for idx, (pos, ch_title) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(raw)
        content = raw[pos:end]
        # 去掉首行（章节标题）再取正文
        first_line = content.split("\n", 1)[0].strip()
        if first_line == ch_title and "\n" in content:
            content = content.split("\n", 1)[1]
        content = clean_content(content)
        if content or ch_title:
            chapters.append(Chapter(index=idx + 1, title=ch_title, content=content))

    return Novel(title=title, author=author, source="local_txt", chapters=chapters)
