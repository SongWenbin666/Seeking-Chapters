# -*- coding: utf-8 -*-
"""正文清洗：去广告、乱码、无关内容。"""
import re


# 常见干扰模式（可按需扩展）
AD_PATTERNS = [
    r"请收藏本站|请记住本站|最新网址|www\.\w+\.(com|net|org)",
    r"本章未完.*点击下一页",
    r"\[广告\].*?\[/广告\]",
    r"（?\s*本章.*?未完\s*）?",
    r"\s*——\s*（.*?更新.*?）\s*——",
    r"【.*?】\s*$",  # 末尾站名等
]
# 乱码：连续非中文、非标点、非常见英文
GARBAGE = re.compile(r"[^\u4e00-\u9fff\w\s.,;:!?，。；：！？、\"'\-\n\r]{20,}")


def clean_paragraph(line: str) -> str:
    """清洗单行。"""
    line = line.strip()
    if not line:
        return ""
    for pat in AD_PATTERNS:
        line = re.sub(pat, "", line, flags=re.IGNORECASE)
    line = GARBAGE.sub("", line)
    return line.strip()


def clean_content(content: str) -> str:
    """清洗整段正文：去广告、乱码，合并多余空行。"""
    lines = content.splitlines()
    cleaned = []
    for line in lines:
        line = clean_paragraph(line)
        if line:
            cleaned.append(line)
    return "\n\n".join(cleaned)
