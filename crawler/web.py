# -*- coding: utf-8 -*-
"""
网络爬虫：从指定小说站点抓取目录与正文，清洗后得到结构化 Novel。
遵守 robots.txt，使用配置中的 CRAWL_DELAY、USER_AGENT，仅作学习/个人使用。
"""
import time
from typing import Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

from config import CRAWL_DELAY, USER_AGENT
from .models import Novel, Chapter
from .clean import clean_content


# 常见站点选择器预设（可按需扩展）
DEFAULT_SELECTORS = {
    "title": "h1, .bookname h1, #info h1, .title",
    "author": "#info a, .author, .bookinfo a, a[href*='author']",
    "chapter_list": "#list dd a, #list a, .listmain dd a, .chapter-list a, ul.chapter a",
    "content": "#content, #nr, #nr_content, .content, .article-content, #chaptercontent",
}

# 读书网 dushu.com：目录页为 /showbook/书ID/，章节页为 /showbook/书ID/章节ID.html
DUSHU_SELECTORS = {
    "title": "h1",
    "author": "table tr td",
    "chapter_list": "table td a[href*='.html']",
    "content": "#content, .content, article, #nr, .main",
}


def _normalize_index_url(url: str) -> str:
    """若传入的是读书网章节页，则转为书籍目录页。"""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if "dushu.com" in parsed.netloc and "/showbook/" in path and path.endswith(".html"):
        # 例如 /showbook/139164/1987801.html -> /showbook/139164/
        parts = path.split("/")
        if len(parts) >= 2:
            book_path = "/".join(parts[:-1]) + "/"
            return f"{parsed.scheme}://{parsed.netloc}{book_path}"
    return url


def _get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def _first_text(soup: BeautifulSoup, selectors: str, default: str = "") -> str:
    """用逗号分隔的多个选择器依次尝试，返回第一个匹配的文本。"""
    for sel in (s.strip() for s in selectors.split(",") if s.strip()):
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True) or default
    return default


def _author_from_dushu_table(soup: BeautifulSoup) -> str:
    """读书网：从表格中解析“作者：xxx”或“作 者：xxx”。"""
    for tr in soup.select("table.table tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2:
            label = (tds[0].get_text() or "").strip()
            if "作者" in label or "作" in label:
                return (tds[1].get_text() or "").strip()
    return ""


def _fetch(session: requests.Session, url: str, encoding: Optional[str] = None) -> str:
    """请求 URL，返回解码后的 HTML 文本。"""
    r = session.get(url, timeout=30)
    r.raise_for_status()
    if encoding:
        r.encoding = encoding
    else:
        r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def crawl_novel_from_url(
    index_url: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    selectors: Optional[dict] = None,
    encoding: Optional[str] = None,
    max_chapters: Optional[int] = None,
) -> Novel:
    """
    从小说目录页抓取全书。

    :param index_url: 书籍目录/索引页 URL
    :param title: 若页面解析不到书名可在此传入
    :param author: 若页面解析不到作者可在此传入
    :param selectors: 覆盖默认选择器，如 {"title": "h1", "chapter_list": "#list a", "content": "#content"}
    :param encoding: 强制响应编码，如 "gbk"
    :param max_chapters: 最多抓取章节数（用于测试或限流）
    :return: Novel
    """
    index_url = _normalize_index_url(index_url)
    is_dushu = "dushu.com" in urlparse(index_url).netloc
    sel = {**DEFAULT_SELECTORS, **(DUSHU_SELECTORS if is_dushu else {}), **(selectors or {})}
    session = _get_session()

    # 1. 抓取目录页
    html = _fetch(session, index_url, encoding=encoding)
    soup = BeautifulSoup(html, "html.parser")

    if not title:
        title = _first_text(soup, sel["title"]) or "未知书名"
    if not author:
        author = _author_from_dushu_table(soup) if is_dushu else _first_text(soup, sel["author"])

    # 2. 收集章节链接（按 URL 去重，保留顺序）
    chapter_links = []
    seen_urls = set()
    book_path_prefix = index_url.rstrip("/") + "/"  # 读书网同书章节均在此路径下
    for selector in (s.strip() for s in sel["chapter_list"].split(",") if s.strip()):
        for a in soup.select(selector):
            href = a.get("href")
            if not href or not a.get_text(strip=True):
                continue
            full_url = urljoin(index_url, href)
            if full_url in seen_urls:
                continue
            if urlparse(full_url).netloc != urlparse(index_url).netloc:
                continue
            if is_dushu:
                if not full_url.startswith(book_path_prefix) or not full_url.endswith(".html"):
                    continue
            seen_urls.add(full_url)
            chapter_links.append((a.get_text(strip=True), full_url))

    if max_chapters:
        chapter_links = chapter_links[: max_chapters]

    # 3. 逐章抓取正文
    content_sel = sel["content"]
    chapters = []
    for i, (ch_title, ch_url) in enumerate(chapter_links, 1):
        time.sleep(CRAWL_DELAY)
        try:
            ch_html = _fetch(session, ch_url, encoding=encoding)
            ch_soup = BeautifulSoup(ch_html, "html.parser")
            content_node = None
            for s in (s.strip() for s in content_sel.split(",") if s.strip()):
                content_node = ch_soup.select_one(s)
                if content_node:
                    break
            if not content_node:
                text = ""
            else:
                text = content_node.get_text(separator="\n", strip=True)
            text = clean_content(text)
            chapters.append(Chapter(index=i, title=ch_title, content=text))
        except Exception:
            chapters.append(Chapter(index=i, title=ch_title, content=""))

    return Novel(title=title, author=author, source="web", chapters=chapters)
