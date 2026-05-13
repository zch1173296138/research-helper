# Research Helper

Research Helper 是一个本地科研文献综述助手，用于管理论文库、解析 PDF、构建证据索引，并基于已导入文献进行可追溯问答、单篇论文对话和 evidence matrix 生成。

## 功能

- 文献库管理：创建综述项目，批量导入 PDF，查看每篇论文的处理状态。
- PDF 解析：使用 MinerU 输出结构化 Markdown、图片、表格和公式结果；未配置 MinerU 时上传会失败并返回明确错误。
- 本地索引：将解析后的 `full.md` 切分为章节片段，写入 SQLite，并用 LanceDB 构建向量索引。
- 混合检索：结合向量检索、SQLite FTS/关键词检索和章节结构检索，返回带页码和片段信息的证据。
- 论文阅读：前端支持后端渲染的 PDF 分页图片预览、缩放、结构化摘要和引用页码跳转。
- 证据问答：围绕整个文献库或单篇论文提问，回答会附带引用片段。
- 论文对话：为单篇论文保存聊天记录，并自动压缩上下文记忆。
- 综述矩阵：根据多篇论文生成 research question、method、dataset、findings、limitations 等字段，并导出 Markdown。

## 技术栈

- Backend: FastAPI, SQLAlchemy 2.x, SQLite, LanceDB, PyMuPDF（仅用于 PDF 预览渲染）, OpenAI-compatible API
- Frontend: React, TypeScript, Vite, TanStack Query, react-markdown, KaTeX, lucide-react
- Storage: 本地 `storage/` 目录

## 快速开始

后端：

```powershell
cd E:\python\research-helper
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```

前端：

```powershell
cd E:\python\research-helper\frontend
npm.cmd install
npm.cmd run dev -- --port 5173
```

打开：

```text
http://localhost:5173
```

## 配置

主要配置放在 `.env`，可以从 `.env.example` 复制后修改。

```env
DATABASE_URL=sqlite:///./storage/research_helper.sqlite3
STORAGE_DIR=./storage
LANCEDB_PATH=./storage/lancedb

OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

MINERU_MODE=auto
MINERU_API_TOKEN=
MINERU_USE_LOCAL=false
MINERU_LOCAL_URL=http://127.0.0.1:30000
```

没有配置 `OPENAI_API_KEY` 时，系统仍可运行：会使用本地确定性 embedding 和抽取式兜底回答。配置 OpenAI-compatible API 后，摘要、问答和聊天质量会更好。

## MinerU 模式

`MINERU_MODE` 支持：

- `auto`：有 API token 时使用 MinerU API；开启本地模式时调用本地 MinerU；都不可用时上传失败并提示配置 MinerU。
- `api`：只尝试 MinerU API，失败后写入错误信息并标记上传失败。
- `local`：只尝试本地 MinerU，失败后写入错误信息并标记上传失败。

本地 MinerU 命令格式：

```powershell
mineru -p <pdf> -o <output> -b vlm-http-client -u <MINERU_LOCAL_URL>
```

## 数据目录

```text
storage/
  input/                 # 上传的原始 PDF
  output/libraries/      # 每个文献库、每篇论文的解析结果
  lancedb/               # 向量索引
  research_helper.sqlite3
```

每篇论文会生成独立目录，核心文件是 `full.md`。导入后，系统会同步图片资源、章节片段、全文检索表和向量索引。

## 常用 API

- `GET /api/health`
- `GET /api/libraries`
- `POST /api/libraries`
- `GET /api/libraries/{library_id}/papers`
- `POST /api/libraries/{library_id}/papers/upload`
- `DELETE /api/papers/{paper_id}`
- `GET /api/papers/{paper_id}/pdf`
- `GET /api/papers/{paper_id}/pdf-info`
- `GET /api/papers/{paper_id}/pages/{page_number}.png`
- `POST /api/papers/{paper_id}/summarize`
- `POST /api/chat`
- `GET /api/papers/{paper_id}/chat/session`
- `POST /api/chat/sessions/{session_id}/messages`
- `POST /api/review/matrix`
- `POST /api/export/markdown`

## 测试

后端测试：

```powershell
cd E:\python\research-helper
.\.venv\Scripts\python -m pytest
```

前端构建：

```powershell
cd E:\python\research-helper\frontend
npm.cmd run build
```

## RAG A/B Evaluation

Run a local comparison between the previous hybrid retrieval answer path and the current PaperQA-style evidence path:

```powershell
.\.venv\Scripts\python -m backend.app.evaluation.runner `
  --cases evals/rag_ab/starter_cases.jsonl `
  --output-dir evals/rag_ab/runs/latest `
  --baseline baseline-current `
  --comparison current-evidence `
  --deterministic-local `
  --top-k 8
```

The runner writes raw case results, aggregate metrics, a Markdown report, and reproducibility metadata under the selected output directory. Use `--deterministic-local` for repeatable no-LLM smoke runs; omit it when you want to measure the configured model. See `evals/rag_ab/README.md` for the case format and optional `old-code-api` baseline mode.
