# Research Helper

本地科研文献综述助手 v1。它借鉴 ArborVista 的 PDF 导入思路：优先使用 MinerU 生成 Markdown、图片、表格和公式解析结果；如果没有配置 MinerU，则自动使用 PyMuPDF 做文本兜底解析。后续 RAG、结构化摘要、证据表都基于解析后的 `full.md`。

## Stack

- Backend: FastAPI, SQLAlchemy 2.x, SQLite, LanceDB, PyMuPDF, OpenAI-compatible API
- Frontend: React, TypeScript, Vite, TanStack Query, lucide-react
- Storage: local `storage/` directory

## Quick Start

```powershell
cd E:\python\research-helper
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```

In another terminal:

```powershell
cd E:\python\research-helper\frontend
npm.cmd install
npm.cmd run dev -- --port 5173
```

Open `http://localhost:5173`.

## MinerU Modes

Default `MINERU_MODE=auto`:

- If `MINERU_API_TOKEN` is set, backend uses MinerU online API.
- If `MINERU_USE_LOCAL=true`, backend calls local MinerU CLI.
- Otherwise it falls back to PyMuPDF and still generates `full.md`.

Local MinerU mode uses:

```powershell
mineru -p <pdf> -o <output> -b vlm-http-client -u <MINERU_LOCAL_URL>
```

## Environment

See `.env.example` for all settings.

Without an API key, the app still runs with deterministic local embeddings and extractive placeholder answers. Configure an OpenAI-compatible API for higher quality summaries and answers.

