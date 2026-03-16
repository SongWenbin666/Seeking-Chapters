# -*- coding: utf-8 -*-
"""长篇小说 RAG 问答 - Streamlit 可视化界面。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from config import ensure_dirs, VECTOR_STORE_DIR, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K
from crawler import list_novels, load_novel
from rag import index_novel, answer_question

st.set_page_config(page_title="小说 RAG 问答", page_icon="📖", layout="wide")
ensure_dirs()


def has_index(novel_id: str) -> bool:
    return (VECTOR_STORE_DIR / novel_id).exists()


def main():
    st.title("📖 长篇小说 RAG 问答")
    st.caption("选择已导入的小说，建索引后可对书中内容提问，答案仅基于检索片段。")

    novels = list_novels()
    if not novels:
        st.info("尚未导入小说。请先用脚本导入：`python scripts/crawl_novel.py <txt或epub路径>`")
        return

    # 侧边：选书 + 元信息 + 统计
    with st.sidebar:
        st.header("已导入的小说")
        options = [f"{n['title']}（{n['novel_id']}）" for n in novels]
        choice = st.selectbox("选择一本书", options, key="novel_choice")
        if not choice:
            st.stop()
        novel_id = next(n["novel_id"] for n in novels if n["novel_id"] in choice)
        novel = load_novel(novel_id)
        if novel:
            st.write("**作者**：", novel.author or "—")
            st.write("**章节数**：", len(novel.chapters))
            st.write("**总字数**：", f"{novel.total_chars:,}")
        indexed = has_index(novel_id)
        if indexed:
            st.success("已建索引，可提问")
        else:
            st.warning("未建索引")
            if st.button("立即建索引"):
                with st.spinner("正在建索引…"):
                    try:
                        n_chunks = index_novel(novel_id, force_rebuild=False)
                        st.success(f"完成，共 {n_chunks} 个片段")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # 主区：章节列表（可折叠）+ 问答
    tab_browse, tab_qa = st.tabs(["📑 章节列表", "💬 问答"])

    with tab_browse:
        if novel:
            st.subheader(novel.title)
            for ch in novel.chapters[:50]:  # 预览前 50 章
                with st.expander(f"第{ch.index}章 {ch.title}", expanded=False):
                    st.text(ch.content[:800] + ("…" if len(ch.content) > 800 else ""))
            if len(novel.chapters) > 50:
                st.caption(f"仅展示前 50 章，共 {len(novel.chapters)} 章")

    with tab_qa:
        if not indexed:
            st.warning("请先在侧边栏为该书建索引后再提问。")
            st.stop()

        question = st.text_input("输入你的问题", placeholder="例如：主角是谁？第三章讲了什么？")
        if question:
            if st.button("提交"):
                with st.spinner("检索并生成答案中…"):
                    try:
                        result = answer_question(novel_id, question, top_k=TOP_K)
                        st.markdown("### 答案")
                        st.markdown(result["answer"])
                        st.markdown("---")
                        st.markdown("### 引用片段")
                        for i, c in enumerate(result["citations"], 1):
                            with st.expander(f"片段 {i}：{c['chapter_title']}（第{c.get('chapter_index', '?')}章）"):
                                st.text(c["content"])
                    except Exception as e:
                        st.error(str(e))


if __name__ == "__main__":
    main()
