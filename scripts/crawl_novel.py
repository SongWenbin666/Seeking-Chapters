# -*- coding: utf-8 -*-
"""爬虫入口：从本地 TXT/EPUB 或网络 URL 导入小说并落盘。"""
import sys
from pathlib import Path

# 项目根加入 path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from crawler import crawl_novel_from_txt, crawl_novel_from_epub, crawl_novel_from_url, save_novel


def main():
    import argparse
    p = argparse.ArgumentParser(description="导入小说到 data/novels")
    p.add_argument("path_or_url", nargs="?", help="本地文件路径（.txt/.epub）或小说目录页 URL")
    p.add_argument("--url", action="store_true", help="表示 path_or_url 为小说目录页 URL")
    p.add_argument("--title", default="", help="书名（可选）")
    p.add_argument("--author", default="", help="作者（可选）")
    p.add_argument("--id", dest="novel_id", default=None, help="存储 ID（默认用书名 slug）")
    p.add_argument("--encoding", default="", help="网页编码，如 gbk（仅 URL 时有效）")
    p.add_argument("--max-chapters", type=int, default=None, help="最多抓取章节数（仅 URL 时有效，用于测试）")
    args = p.parse_args()

    if not args.path_or_url:
        p.print_help()
        sys.exit(1)

    if args.url:
        novel = crawl_novel_from_url(
            args.path_or_url,
            title=args.title or None,
            author=args.author or None,
            encoding=args.encoding or None,
            max_chapters=args.max_chapters,
        )
    else:
        path = Path(args.path_or_url)
        suffix = path.suffix.lower()
        if suffix == ".txt":
            novel = crawl_novel_from_txt(path, title=args.title, author=args.author)
        elif suffix == ".epub":
            novel = crawl_novel_from_epub(path, title=args.title, author=args.author)
        else:
            print("本地文件仅支持 .txt 或 .epub；网络抓取请用 --url")
            sys.exit(1)

    nid = save_novel(novel, novel_id=args.novel_id)
    print(f"已保存: {nid}")
    print(f"  书名: {novel.title}, 作者: {novel.author}, 章节数: {len(novel.chapters)}, 总字数: {novel.total_chars}")


if __name__ == "__main__":
    main()
