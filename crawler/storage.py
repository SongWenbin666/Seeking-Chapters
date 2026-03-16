# -*- coding: utf-8 -*-
"""结构化落盘：JSON 存储，按书 ID 存单文件。"""
import json
import re
from pathlib import Path
from typing import List, Optional

from config import ensure_dirs, NOVELS_DIR
from .models import Novel


def _slug(s: str) -> str:
    """生成安全文件名。"""
    s = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")[:80]
    return s or "unnamed"


def _novel_path(novel_id: str) -> Path:
    ensure_dirs()
    return NOVELS_DIR / f"{novel_id}.json"


def save_novel(novel: Novel, novel_id: Optional[str] = None) -> str:
    """保存小说到 data/novels/{novel_id}.json，返回 novel_id。"""
    novel_id = novel_id or _slug(novel.title)
    path = _novel_path(novel_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(novel.to_dict(), f, ensure_ascii=False, indent=2)
    return novel_id


def load_novel(novel_id: str) -> Optional[Novel]:
    """从 data/novels 加载一本小说。"""
    path = _novel_path(novel_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return Novel.from_dict(json.load(f))


def list_novels() -> List[dict]:
    """列出已导入的小说：novel_id, title, author（从文件读）。"""
    ensure_dirs()
    result = []
    for p in NOVELS_DIR.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            result.append({
                "novel_id": p.stem,
                "title": d.get("title", p.stem),
                "author": d.get("author", ""),
            })
        except Exception:
            result.append({"novel_id": p.stem, "title": p.stem, "author": ""})
    return sorted(result, key=lambda x: x["title"])
