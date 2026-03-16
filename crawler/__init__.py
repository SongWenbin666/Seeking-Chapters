# -*- coding: utf-8 -*-
from .models import Novel, Chapter
from .storage import save_novel, load_novel, list_novels
from .local_txt import crawl_novel_from_txt
from .local_epub import crawl_novel_from_epub
from .web import crawl_novel_from_url

__all__ = [
    "Novel",
    "Chapter",
    "save_novel",
    "load_novel",
    "list_novels",
    "crawl_novel_from_txt",
    "crawl_novel_from_epub",
    "crawl_novel_from_url",
]
