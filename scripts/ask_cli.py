# -*- coding: utf-8 -*-
"""Phase 2 CLI：对已建索引的小说提问，打印答案与引用。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag import answer_question


def main():
    import argparse
    p = argparse.ArgumentParser(description="对小说提问（需先建索引）")
    p.add_argument("novel_id", help="小说 ID（与 data/novels 下文件名一致）")
    p.add_argument("question", nargs="+", help="问题（多个词会拼成一句）")
    p.add_argument("--top-k", type=int, default=None, help="检索片段数，默认用配置")
    args = p.parse_args()

    question = " ".join(args.question)
    result = answer_question(args.novel_id, question, top_k=args.top_k)

    print("【答案】")
    print(result["answer"])
    print("\n【引用片段】")
    for i, c in enumerate(result["citations"], 1):
        print(f"  [{i}] {c['chapter_title']} (第{c.get('chapter_index', '?')}章)")
        print(f"      {c['content'][:200]}…" if len(c["content"]) > 200 else f"      {c['content']}")
        print()


if __name__ == "__main__":
    main()
