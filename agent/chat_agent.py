# -*- coding: utf-8 -*-
"""
Agent 聊天：大模型按需调用 novel_rag_query（模式 A：工具内检索 + 子链路 LLM 生成短答）。
"""
import json
from typing import List, Tuple

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool

from config import LLM_PROVIDER, LLM_MODEL, OLLAMA_BASE_URL, TOP_K
from rag.qa import answer_question, get_llm


AGENT_SYSTEM_PROMPT_TEMPLATE = """你是通用对话助手。用户正在使用「长篇小说阅读」应用，**侧边栏当前选中的书**如下（唯一默认书目）：
- 书名：{book_title}
- 作者：{book_author}

你可调用工具 novel_rag_query：只检索**上述这本书**的正文并生成基于片段的短答。

**必须优先调 novel_rag_query 的情况（不要先用通识瞎猜）：**
- 用户问「某某是谁」「某某做了什么」「某幕/某场/某章」「剧情」「人物关系」「书里有没有提到…」等，只要**可能与当前这本书**有关，就必须先调用 novel_rag_query。
- 即使用户**没有写出书名**，只要问题像在问**剧中人名、角色、情节**（例如「辛白林是谁」「第一幕讲什么」），一律先 novel_rag_query，再根据工具结果回答。
- 书名与当前书相同或用户说「这本小说」「书里」时，必须 novel_rag_query。

**不要调用工具的情况：**
- 明确与本书无关：写代码、纯数学、闲聊天气、且与书中内容无关等。

**其它：**
- 调用工具后，用自然话总结，可提章节/幕名；工具说未找到则如实说。
- 若工具返回未建索引，提醒用户先在侧边栏建索引。"""


def _tool_description(book_title: str) -> str:
    return (
        f"novel_rag_query：只针对当前选中的书《{book_title}》，从书中检索与问题最相关的片段，"
        "并基于片段生成短答（含章节/幕引用）。"
        "用户问书中人物是谁、某幕剧情、某角色行为等——必须先调用本工具。"
        "与编程/数学/与本书无关的闲聊不要调用。"
        "参数 question：用户原问或改写后的检索问句。"
    )


def _get_chat_model():
    """Agent 需要支持 tool_calls 的 Chat 模型。"""
    if LLM_PROVIDER == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.3)
        except Exception:
            pass
    return get_llm()


def _make_novel_rag_tool(
    novel_id: str, indexed: bool, top_k: int, book_title: str
) -> StructuredTool:
    def _run(question: str) -> str:
        if not question or not str(question).strip():
            return json.dumps({"error": "question 不能为空"}, ensure_ascii=False)
        if not indexed:
            return json.dumps(
                {
                    "error": "当前书籍尚未建立向量索引，请先在侧边栏点击「立即建索引」后再查询本书。",
                },
                ensure_ascii=False,
            )
        try:
            r = answer_question(novel_id, question.strip(), top_k=top_k)
            return json.dumps(
                {
                    "answer": r.get("answer", ""),
                    "citations": [
                        {
                            "chapter_title": c.get("chapter_title"),
                            "chapter_index": c.get("chapter_index"),
                            "excerpt": (c.get("content") or "")[:400],
                        }
                        for c in (r.get("citations") or [])
                    ],
                    "timings_s": r.get("timings"),
                },
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    return StructuredTool.from_function(
        func=_run,
        name="novel_rag_query",
        description=_tool_description(book_title),
    )


def run_agent_chat_turn(
    novel_id: str,
    indexed: bool,
    chat_history: List[Tuple[str, str]],
    user_input: str,
    top_k: int = None,
    book_title: str = "",
    book_author: str = "",
) -> str:
    """
    执行一轮 Agent 对话（含可选工具调用）。
    chat_history: [(\"user\", text), (\"assistant\", text), ...] 不含本轮 user_input。
    返回 assistant 最终回复文本。
    """
    top_k = top_k if top_k is not None else TOP_K
    title = (book_title or novel_id or "当前书目").strip()
    author = (book_author or "未知").strip()
    system_text = AGENT_SYSTEM_PROMPT_TEMPLATE.format(
        book_title=title, book_author=author
    )

    llm = _get_chat_model()
    tool = _make_novel_rag_tool(novel_id, indexed, top_k, title)
    tools = [tool]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_text),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
    )

    lc_history = []
    for role, content in chat_history:
        if role == "user":
            lc_history.append(HumanMessage(content=content))
        else:
            lc_history.append(AIMessage(content=content))

    out = executor.invoke(
        {
            "input": user_input.strip(),
            "chat_history": lc_history,
        }
    )
    return (out.get("output") or "").strip() or "（无回复）"
