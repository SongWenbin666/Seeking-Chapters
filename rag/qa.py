# -*- coding: utf-8 -*-
"""检索 + LLM 生成，答案仅基于检索片段，并带引用。"""
from typing import List, Optional
import time
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from config import (
    LLM_PROVIDER,
    LLM_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OLLAMA_BASE_URL,
    ZHIPUAI_API_KEY,
    ZHIPUAI_BASE_URL,
)


# 严格要求不瞎编的 prompt
SYSTEM_PROMPT = """你是一个基于给定小说片段的问答助手。请严格遵守以下规则：
1. 仅根据下面「检索到的片段」中的内容回答问题。
2. 若片段中没有相关信息，请明确回答「根据现有内容无法确定」或「书中未提及」，不要编造。
3. 回答要简洁，并尽量指出依据的章节或段落（可用「见第X章」等）。
4. 不要复述整段原文，用概括或摘录关键句即可。"""


def _format_docs(docs):
    parts = []
    for i, d in enumerate(docs, 1):
        meta = d.metadata
        ch = meta.get("chapter_title", "") or f"第{meta.get('chapter_index', '?')}章"
        parts.append(f"[片段{i}]（{ch}）\n{d.page_content}")
    return "\n\n".join(parts)


_ACT_SCENE_RE = re.compile(r"(第[一二三四五六七八九十0-9]+幕)(第[一二三四五六七八九十0-9]+场)?")


def _filter_docs_by_act_scene(question: str, docs: list):
    """
    简单规则：如果问题里明确提到“第X幕/第X场”，则优先保留章节标题里包含该幕的片段。
    若过滤后为空，则回退原 docs。
    """
    m = _ACT_SCENE_RE.search(question)
    if not m:
        return docs
    act = m.group(1)
    if not act:
        return docs
    filtered = [d for d in docs if act in (d.metadata.get("chapter_title") or "")]
    return filtered or docs


def get_llm():
    """根据配置返回 LLM（key 等均从环境变量/config 导入）。"""
    if LLM_PROVIDER == "ollama":
        from langchain_community.llms import Ollama
        return Ollama(base_url=OLLAMA_BASE_URL, model=LLM_MODEL)
    if LLM_PROVIDER == "zhipuai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=ZHIPUAI_API_KEY,
            openai_api_base=ZHIPUAI_BASE_URL,
        )
    # openai 或默认
    from langchain_openai import ChatOpenAI
    kwargs = {"model": LLM_MODEL}
    if OPENAI_API_KEY:
        kwargs["openai_api_key"] = OPENAI_API_KEY
    if OPENAI_BASE_URL:
        kwargs["openai_api_base"] = OPENAI_BASE_URL
    return ChatOpenAI(**kwargs)


def answer_question(
    novel_id: str,
    question: str,
    top_k: Optional[int] = None,
) -> dict:
    """
    对指定小说提问：检索 Top-K 片段，用 LLM 生成答案。
    返回 {"answer": str, "citations": [{"chapter_title", "chapter_index", "content"}, ...]}
    """
    t0 = time.perf_counter()

    from .index import get_retriever
    retriever = get_retriever(novel_id, top_k=top_k)

    t_retrieval_start = time.perf_counter()
    docs = retriever.invoke(question)
    t_retrieval_end = time.perf_counter()
    docs = _filter_docs_by_act_scene(question, docs)

    context = _format_docs(docs)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "检索到的片段：\n\n{context}\n\n用户问题：{question}"),
    ])
    llm = get_llm()
    chain = prompt | llm | StrOutputParser()
    t_generation_start = time.perf_counter()
    answer = chain.invoke({"context": context, "question": question})
    t_generation_end = time.perf_counter()

    citations = [
        {
            "chapter_index": d.metadata.get("chapter_index"),
            "chapter_title": d.metadata.get("chapter_title", ""),
            "content": d.page_content[:500] + ("…" if len(d.page_content) > 500 else ""),
        }
        for d in docs
    ]

    t1 = time.perf_counter()
    timings = {
        "retrieval_s": round(t_retrieval_end - t_retrieval_start, 4),
        "generation_s": round(t_generation_end - t_generation_start, 4),
        "total_s": round(t1 - t0, 4),
    }

    return {"answer": answer, "citations": citations, "timings": timings}
