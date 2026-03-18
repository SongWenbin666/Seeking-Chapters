# -*- coding: utf-8 -*-
"""Embedding 封装：本地 sentence-transformers 或 OpenAI。"""
from typing import List
from functools import lru_cache

from config import (
    EMBEDDING_TYPE,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
)


@lru_cache(maxsize=1)
def get_embedding_model():
    """返回 LangChain 可用的 Embeddings 实例。"""
    if EMBEDDING_TYPE == "openai":
        from langchain_openai import OpenAIEmbeddings
        kwargs = {"model": EMBEDDING_MODEL}
        if OPENAI_API_KEY:
            kwargs["openai_api_key"] = OPENAI_API_KEY
        if OPENAI_BASE_URL:
            kwargs["openai_api_base"] = OPENAI_BASE_URL
        return OpenAIEmbeddings(**kwargs)
    else:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=LOCAL_EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
        )
