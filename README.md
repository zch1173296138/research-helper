# Research Helper

Research Helper 是一个本地科研文献综述助手。它用于管理论文库、解析 PDF、构建可追溯证据索引，并围绕已导入文献进行问答、单篇论文对话和综述矩阵生成。

## 项目范围

仓库只保留当前项目需要的源码、测试、评测数据和启动配置：

```text
backend/              FastAPI 后端、数据库模型、检索和 RAG 服务
frontend/             React + Vite 前端
tests/                后端服务和评测流程测试
evals/rag_ab/         RAG A/B 评测用例和说明
old_code/             历史代码快照，用于对比旧实现
.env.example          环境变量模板
alembic.ini           数据库迁移配置
pytest.ini            测试配置
requirements.txt      Python 依赖
```

`.gitignore` 默认忽略未列入清单的新增顶层路径。OpenSpec 变更说明、Codex/IDE 配置、本地进度记录、运行日志、`storage/` 数据、前端构建产物和评测运行输出都属于本地过程文件，不需要上传到 GitHub。已经被 Git 跟踪过的历史文件不会因为 `.gitignore` 自动移除，需要从索引中移除后才会在后续提交里消失。

## 主要功能

- 文献库管理：创建综述项目，批量导入 PDF，查看每篇论文的处理状态。
- PDF 解析：通过 MinerU 生成结构化 Markdown、图片、表格和公式结果。
- 本地索引：将解析后的 `full.md` 切分为章节片段，写入 SQLite，并用 LanceDB 建立向量索引。
- 混合检索：结合向量检索、SQLite FTS/关键词检索和章节结构信息，返回带页码和片段来源的证据。
- 论文阅读：前端支持 PDF 分页图片预览、缩放、结构化摘要和引用页码跳转。
- 证据问答：围绕整个文献库或单篇论文提问，回答附带引用片段。
- 论文对话：为单篇论文保存聊天记录，并压缩上下文记忆。
- 综述矩阵：根据多篇论文生成 research question、method、dataset、findings、limitations 等字段，并导出 Markdown。

## 技术栈

- Backend: FastAPI, SQLAlchemy 2.x, SQLite, LanceDB, PyMuPDF, OpenAI-compatible API
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

前端默认请求 `http://localhost:8000`。如需修改后端地址，可在前端环境中设置 `VITE_API_BASE_URL`。

## 配置

主要配置放在 `.env`，可以从 `.env.example` 复制后修改。

```env
APP_NAME=Research Helper
APP_ENV=development

DATABASE_URL=sqlite:///./storage/research_helper.sqlite3
STORAGE_DIR=./storage
LANCEDB_PATH=./storage/lancedb

OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=
CHAT_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=60
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BATCH_SIZE=8

MINERU_MODE=auto
MINERU_API_TOKEN=
MINERU_API_BASE_URL=https://mineru.net/api/v4
MINERU_USE_LOCAL=false
MINERU_LOCAL_URL=http://127.0.0.1:30000
MINERU_TIMEOUT_SECONDS=600
```

没有配置 `OPENAI_API_KEY` 时，系统仍可运行：会使用本地确定性 embedding 和抽取式兜底回答。配置 OpenAI-compatible API 后，摘要、问答和聊天质量会更好。

## MinerU 模式

`MINERU_MODE` 支持：

- `auto`：有 API token 时使用 MinerU API；开启本地模式时调用本地 MinerU；都不可用时上传失败并提示配置 MinerU。
- `api`：只尝试 MinerU API，失败后写入错误信息并标记上传失败。
- `local`：只尝试本地 MinerU，失败后写入错误信息并标记上传失败。
- `disabled`：禁用 MinerU 解析。

本地 MinerU 命令格式：

```powershell
mineru -p <pdf> -o <output> -b vlm-http-client -u <MINERU_LOCAL_URL>
```

## 数据目录

```text
storage/
  input/                 上传的原始 PDF
  output/libraries/      每个文献库、每篇论文的解析结果
  lancedb/               向量索引
  research_helper.sqlite3
```

每篇论文会生成独立目录，核心文件是 `full.md`。导入后，系统会同步图片资源、章节片段、全文检索表和向量索引。

## 常用 API

- `GET /api/health`
- `GET /api/libraries`
- `POST /api/libraries`
- `GET /api/libraries/{library_id}/papers`
- `POST /api/libraries/{library_id}/papers/upload`
- `GET /api/papers/{paper_id}`
- `DELETE /api/papers/{paper_id}`
- `GET /api/papers/{paper_id}/content`
- `GET /api/papers/{paper_id}/pdf`
- `GET /api/papers/{paper_id}/pdf-info`
- `GET /api/papers/{paper_id}/pages/{page_number}.png`
- `POST /api/libraries/{library_id}/build-index`
- `POST /api/papers/{paper_id}/summarize`
- `POST /api/papers/{paper_id}/enrich`
- `GET /api/papers/{paper_id}/chat/session`
- `GET /api/chat/sessions/{session_id}/messages`
- `POST /api/chat/sessions/{session_id}/messages`
- `POST /api/chat`
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

本地评测入口在 `evals/rag_ab/`。默认可以比较旧的 hybrid retrieval answer path 和当前 PaperQA-style evidence path：

```powershell
.\.venv\Scripts\python -m backend.app.evaluation.runner `
  --cases evals/rag_ab/starter_cases.jsonl `
  --output-dir evals/rag_ab/runs/latest `
  --baseline baseline-current `
  --comparison current-evidence `
  --deterministic-local `
  --top-k 8
```

评测会写出 case 结果、聚合指标、Markdown 报告和可复现配置。更多用例格式、QASPER 样本和 old-code API baseline 说明见 `evals/rag_ab/README.md`。
