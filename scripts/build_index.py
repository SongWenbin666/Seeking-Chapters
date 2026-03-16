# -*- coding: utf-8 -*-
"""为已导入的小说建 RAG 向量索引。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag import index_novel


def main():
    import argparse
    p = argparse.ArgumentParser(description="为小说建向量索引")
    p.add_argument("novel_id", help="小说 ID")
    p.add_argument("--force", action="store_true", help="重建索引（覆盖已有）")
    args = p.parse_args()

    n = index_novel(args.novel_id, force_rebuild=args.force)
    print(f"索引完成: {args.novel_id}, 共 {n} 个片段")


if __name__ == "__main__":
    main()
