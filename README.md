# 长篇小说 RAG 问答系统

以 RAG 为核心的长篇小说问答应用：爬虫抓取/导入小说 → 切分与向量化 → 检索 + LLM 生成答案，并提供可视化界面浏览与提问。

## 环境要求

- Python 3.10+

## 安装

项目已包含虚拟环境配置，建议在 venv 中运行：

```bash
cd "Seeking Chapters"

# 若尚未创建虚拟环境：
# python -m venv venv

# 激活虚拟环境（Windows PowerShell）
.\venv\Scripts\Activate.ps1

# 安装依赖（已安装可跳过）
pip install -r requirements.txt
```

复制配置模板并按需修改：

```bash
copy .env.example .env
# 编辑 .env：API Key、模型名、向量库路径等
```

## 配置项说明（.env）

| 变量 | 说明 | 默认 |
|------|------|------|
| `DATA_DIR` | 数据根目录（小说 JSON、向量库） | `./data` |
| `EMBEDDING_TYPE` | `local` 本地模型 / `openai` API | `local` |
| `OPENAI_API_KEY` | OpenAI API Key（用 OpenAI 时必填） | - |
| `LOCAL_EMBEDDING_MODEL` | 本地 Embedding 模型名 | `paraphrase-multilingual-MiniLM-L12-v2` |
| `LLM_PROVIDER` | `openai` / `ollama` | `openai` |
| `LLM_MODEL` | 模型名，如 `gpt-4o-mini` | `gpt-4o-mini` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 切分长度与重叠 | 1024 / 128 |
| `TOP_K` | 检索返回片段数 | 5 |

## 快速开始（示例小说）

项目根目录自带 `sample_novel.txt`，可快速跑通全流程。**请先激活虚拟环境**（见上方安装步骤），再执行：

```bash
# 1. 导入
python scripts/crawl_novel.py sample_novel.txt --title "寻章" --author "示例"

# 2. 建索引（首次会下载 Embedding 模型，需等待）
python scripts/build_index.py "寻章"

# 3. 命令行提问（需配置 LLM，见下方 .env）
python scripts/ask_cli.py "寻章" 主角叫什么名字

# 4. 或启动 Web 界面
streamlit run app.py
```

### Phase 1：导入小说

支持本地 **TXT**、**EPUB** 与 **网络 URL**：

```bash
# 从 TXT 导入（自动识别章节）
python scripts/crawl_novel.py path/to/novel.txt --title "书名" --author "作者"

# 从 EPUB 导入
python scripts/crawl_novel.py path/to/novel.epub

# 从网络目录页抓取（需遵守目标站 robots.txt 与版权，仅作学习/个人使用）
python scripts/crawl_novel.py --url "https://example.com/book/123/"
# 读书网：可填目录页或任意章节页，会自动转到目录页并解析
python scripts/crawl_novel.py --url "https://www.dushu.com/showbook/139164/"
python scripts/crawl_novel.py --url "https://www.dushu.com/showbook/139164/1987801.html"
python scripts/crawl_novel.py --url "https://..." --encoding gbk --max-chapters 10
```

结构化数据会保存在 `data/novels/<novel_id>.json`。网络爬虫使用 `config` 中的 `CRAWL_DELAY`、`USER_AGENT`。

### Phase 2：建索引与命令行问答

```bash
# 为已导入的小说建向量索引（首次会下载本地 Embedding 模型，较慢）
python scripts/build_index.py <novel_id>

# 提问（答案 + 引用片段会打印到终端）
python scripts/ask_cli.py <novel_id> 主角叫什么名字
```

### Phase 3：可视化界面

```bash
streamlit run app.py
```

在浏览器中可：

- 查看已导入小说列表与元信息（书名、作者、章节数、总字数）
- 浏览章节列表（可折叠）
- 为未建索引的书「建索引」
- **Agent 聊天**：通用对话；与本书相关时由大模型**按需调用**工具 `novel_rag_query`（工具内检索 + LLM 短答，模式 A）；未建索引时仍可闲聊，查书会提示先建索引
- **本书问答（强制 RAG）**：每问必走检索 + 生成，并展示引用片段与耗时

## 示例问题

- 「这本书的主角是谁？」
- 「第三章主要讲了什么？」
- 「文中提到过某某事件吗？」

答案仅基于检索到的片段生成；若片段中无相关信息，会明确说明「根据现有内容无法确定」或「书中未提及」，避免幻觉。

## 项目结构

```
Seeking Chapters/
├── config.py           # 配置（与 .env 配合）
├── .env.example
├── requirements.txt
├── app.py              # Streamlit 入口
├── agent/              # Agent 聊天（工具调用 novel_rag_query）
├── crawler/            # 爬虫与存储
│   ├── models.py       # Novel, Chapter
│   ├── storage.py      # JSON 落盘、列表
│   ├── clean.py        # 正文清洗
│   ├── local_txt.py    # 本地 TXT 解析
│   └── local_epub.py   # 本地 EPUB 解析
├── rag/                # RAG 核心
│   ├── chunk.py        # 按长度切分 + overlap
│   ├── embedding.py    # 本地/OpenAI Embedding
│   ├── index.py        # Chroma 索引、检索器
│   └── qa.py           # 检索 + LLM 生成与引用
├── scripts/
│   ├── crawl_novel.py  # 导入小说
│   ├── build_index.py  # 建索引
│   └── ask_cli.py      # CLI 问答
└── data/               # 运行时生成
    ├── novels/         # 小说 JSON
    └── vector_store/   # 向量库（按 novel_id 分子目录）
```

## 注意事项

- 长篇小说可百万字级：索引会按章切分后再按块切分，建索引可能较慢；向量库支持按书增量（重新建索引用 `--force`）。
- 爬取网站时请遵守 robots.txt 与版权，本仓库仅提供本地 TXT/EPUB 导入示例。
- 若使用 OpenAI，请勿将 `.env` 提交到版本库。
