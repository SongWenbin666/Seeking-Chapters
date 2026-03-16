# -*- coding: utf-8 -*-
"""配置：API Key、模型、向量库路径等与代码分离。"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent

# 小说数据目录（爬虫输出、RAG 文档库）
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
NOVELS_DIR = DATA_DIR / "novels"          # 结构化小说 JSON/按章节
VECTOR_STORE_DIR = DATA_DIR / "vector_store"  # 向量库持久化路径

# Embedding
EMBEDDING_TYPE = os.getenv("EMBEDDING_TYPE", "local")  # local | openai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")     # 国产/代理时可改
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")  # OpenAI 时
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai | ollama | zhipuai
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# 智谱 AI（LLM_PROVIDER=zhipuai 时，key 从环境变量导入）
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
ZHIPUAI_BASE_URL = os.getenv("ZHIPUAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
# RAG
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1024"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "128"))
TOP_K = int(os.getenv("TOP_K", "5"))

# 爬虫（若用网站源）
CRAWL_DELAY = float(os.getenv("CRAWL_DELAY", "1.0"))
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (compatible; NovelBot/1.0; +https://github.com/novel-rag)")


def ensure_dirs():
    """确保数据目录存在。"""
    NOVELS_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
