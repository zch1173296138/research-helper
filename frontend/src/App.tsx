import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, ChevronLeft, ChevronRight, Database, FileText, MessageSquareText, Minus, Plus, Search, Trash2, UploadCloud } from "lucide-react";
import { useDropzone } from "react-dropzone";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import { api, Citation, Library, Paper } from "./api";

type Tab = "library" | "paper" | "chat" | "matrix";

export function App() {
  const queryClient = useQueryClient();
  const [selectedLibraryId, setSelectedLibraryId] = useState<string>("");
  const [selectedPaperId, setSelectedPaperId] = useState<string>("");
  const [tab, setTab] = useState<Tab>("library");

  const librariesQuery = useQuery({ queryKey: ["libraries"], queryFn: api.libraries });
  const libraries = librariesQuery.data ?? [];
  const selectedLibrary = libraries.find((library) => library.id === selectedLibraryId) ?? libraries[0];
  const activeLibraryId = selectedLibrary?.id ?? "";

  const papersQuery = useQuery({
    queryKey: ["papers", activeLibraryId],
    queryFn: () => api.papers(activeLibraryId),
    enabled: Boolean(activeLibraryId),
  });
  const papers = papersQuery.data ?? [];
  const selectedPaper = papers.find((paper) => paper.id === selectedPaperId) ?? papers[0];

  const createLibrary = useMutation({
    mutationFn: api.createLibrary,
    onSuccess: (library) => {
      queryClient.invalidateQueries({ queryKey: ["libraries"] });
      setSelectedLibraryId(library.id);
    },
  });

  const navItems = [
    { id: "library" as Tab, label: "文献库", icon: Database },
    { id: "paper" as Tab, label: "论文详情", icon: FileText },
    { id: "chat" as Tab, label: "证据问答", icon: MessageSquareText },
    { id: "matrix" as Tab, label: "证据表", icon: BookOpen },
  ];

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Search size={18} /></div>
          <div>
            <h1>Research Helper</h1>
            <p>本地可信文献综述</p>
          </div>
        </div>

        <section className="sidebar-section">
          <div className="section-title">综述项目</div>
          <LibraryPicker
            libraries={libraries}
            selectedId={activeLibraryId}
            onSelect={(id) => {
              setSelectedLibraryId(id);
              setSelectedPaperId("");
            }}
          />
          <button
            className="secondary-button full-width"
            onClick={() => {
              const name = window.prompt("新文库名称", "我的文献综述");
              if (name) createLibrary.mutate({ name });
            }}
          >
            <Plus size={16} /> 新建文库
          </button>
        </section>

        <nav className="nav-list">
          {navItems.map((item) => (
            <button key={item.id} className={tab === item.id ? "active" : ""} onClick={() => setTab(item.id)}>
              <item.icon size={17} />
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <h2>{selectedLibrary?.name ?? "创建一个文库开始"}</h2>
            <p>{papers.length} 篇论文 · 本地 SQLite + LanceDB</p>
          </div>
          <div className="status-line">
            <span>MinerU 优先</span>
            <span>PyMuPDF 兜底</span>
          </div>
        </header>

        {tab === "library" && (
          <LibraryView
            libraryId={activeLibraryId}
            papers={papers}
            onDeletePaper={(paperId) => {
              if (paperId === selectedPaperId) setSelectedPaperId("");
            }}
            onSelectPaper={(paper) => {
              setSelectedPaperId(paper.id);
              setTab("paper");
            }}
          />
        )}
        {tab === "paper" && <PaperDetail paper={selectedPaper} />}
        {tab === "chat" && <ChatView libraryId={activeLibraryId} papers={papers} />}
        {tab === "matrix" && <MatrixView libraryId={activeLibraryId} papers={papers} />}
      </section>
    </main>
  );
}

function LibraryPicker({ libraries, selectedId, onSelect }: { libraries: Library[]; selectedId: string; onSelect: (id: string) => void }) {
  if (!libraries.length) {
    return <div className="empty-small">还没有文库</div>;
  }
  return (
    <select value={selectedId} onChange={(event) => onSelect(event.target.value)}>
      {libraries.map((library) => (
        <option key={library.id} value={library.id}>
          {library.name}
        </option>
      ))}
    </select>
  );
}

type LibraryViewProps = {
  libraryId: string;
  papers: Paper[];
  onSelectPaper: (paper: Paper) => void;
  onDeletePaper: (paperId: string) => void;
};

function LibraryView({ libraryId, papers, onSelectPaper, onDeletePaper }: LibraryViewProps) {
  const queryClient = useQueryClient();
  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => api.upload(libraryId, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["papers", libraryId] });
      queryClient.invalidateQueries({ queryKey: ["libraries"] });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: api.deletePaper,
    onSuccess: (_, paperId) => {
      queryClient.invalidateQueries({ queryKey: ["papers", libraryId] });
      queryClient.invalidateQueries({ queryKey: ["libraries"] });
      onDeletePaper(paperId);
    },
  });

  const onDrop = (acceptedFiles: File[]) => {
    if (!libraryId || !acceptedFiles.length) return;
    const formData = new FormData();
    acceptedFiles.forEach((file) => formData.append("files", file));
    formData.append("is_ocr", "true");
    formData.append("enable_formula", "true");
    formData.append("enable_table", "true");
    formData.append("language", "ch");
    formData.append("layout_model", "doclayout_yolo");
    uploadMutation.mutate(formData);
  };
  const dropzone = useDropzone({ onDrop, accept: { "application/pdf": [".pdf"] }, multiple: true });

  const handleDeletePaper = (paper: Paper) => {
    const confirmed = window.confirm(`删除论文 "${paper.original_filename}"？这会同时删除数据库记录、索引和本地文件。`);
    if (confirmed) deleteMutation.mutate(paper.id);
  };

  return (
    <div className="content-grid two-columns">
      <section className="panel upload-panel" {...dropzone.getRootProps()}>
        <input {...dropzone.getInputProps()} />
        <UploadCloud size={32} />
        <h3>导入 PDF</h3>
        <p>批量上传论文。后端优先调用 MinerU 生成 full.md，没有配置时自动用 PyMuPDF 兜底。</p>
        <button className="primary-button" disabled={!libraryId || uploadMutation.isPending}>
          {uploadMutation.isPending ? "解析中..." : "选择 PDF"}
        </button>
        {uploadMutation.error && <div className="error-text">{uploadMutation.error.message}</div>}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h3>文献列表</h3>
          <span>{papers.length} papers</span>
        </div>
        <div className="paper-list">
          {papers.map((paper) => (
            <article key={paper.id} className="paper-row">
              <button className="paper-main" onClick={() => onSelectPaper(paper)}>
                <FileText size={18} />
                <span>
                  <strong>{paper.original_filename}</strong>
                  <small>{paper.status} · {paper.parser}</small>
                </span>
              </button>
              <button
                className="icon-button danger-button"
                title="删除论文"
                aria-label={`删除 ${paper.original_filename}`}
                disabled={deleteMutation.isPending}
                onClick={() => handleDeletePaper(paper)}
              >
                <Trash2 size={16} />
              </button>
            </article>
          ))}
          {deleteMutation.error && <div className="error-text">{deleteMutation.error.message}</div>}
          {!papers.length && <div className="empty-state">上传 PDF 后会出现在这里。</div>}
        </div>
      </section>
    </div>
  );
}

function PaperDetail({ paper }: { paper?: Paper }) {
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const summarizeMutation = useMutation({
    mutationFn: () => api.summarize(paper!.id),
    onSuccess: (result) => setSummary(result.summary),
  });

  useEffect(() => {
    setSummary(null);
    summarizeMutation.reset();
  }, [paper?.id]);

  if (!paper) return <div className="empty-state fill">请选择一篇论文。</div>;

  return (
    <div className="content-grid two-columns wide-left">
      <section className="panel">
        <div className="panel-heading">
          <h3>{paper.original_filename}</h3>
          <span>{paper.status}</span>
        </div>
        {paper.error && <div className="error-text">{paper.error}</div>}
        <PdfPreview paperId={paper.id} title={paper.original_filename} />
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h3>结构化摘要</h3>
          <button
            className="secondary-button"
            onClick={() => summarizeMutation.mutate()}
            disabled={!paper.id || summarizeMutation.isPending}
          >
            {summarizeMutation.isPending ? "生成中..." : "生成摘要"}
          </button>
        </div>
        <SummaryBlock summary={summary} loading={summarizeMutation.isPending} error={summarizeMutation.error} />
      </section>
    </div>
  );
}

function PdfPreview({ paperId, title }: { paperId: string; title: string }) {
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.6);
  const [imageFailed, setImageFailed] = useState(false);
  const infoQuery = useQuery({
    queryKey: ["paper-pdf-info", paperId],
    queryFn: () => api.paperPdfInfo(paperId),
    enabled: Boolean(paperId),
  });

  useEffect(() => {
    setPageNumber(1);
    setScale(1.6);
    setImageFailed(false);
  }, [paperId]);

  useEffect(() => {
    setImageFailed(false);
  }, [paperId, pageNumber, scale]);

  const pageCount = infoQuery.data?.page_count ?? 0;
  const pageImageUrl = api.paperPageImageUrl(paperId, pageNumber, scale);

  if (infoQuery.isLoading) return <div className="empty-state">正在加载 PDF 页面...</div>;
  if (infoQuery.error) return <div className="error-text">{infoQuery.error.message}</div>;
  if (!pageCount) return <div className="empty-state">暂无可预览页面。</div>;

  return (
    <div className="pdf-preview">
      <div className="pdf-preview-toolbar">
        <button
          className="icon-button"
          title="上一页"
          aria-label="上一页"
          disabled={pageNumber <= 1}
          onClick={() => setPageNumber((current) => Math.max(1, current - 1))}
        >
          <ChevronLeft size={16} />
        </button>
        <span className="page-indicator">{pageNumber} / {pageCount}</span>
        <button
          className="icon-button"
          title="下一页"
          aria-label="下一页"
          disabled={pageNumber >= pageCount}
          onClick={() => setPageNumber((current) => Math.min(pageCount, current + 1))}
        >
          <ChevronRight size={16} />
        </button>
        <span className="toolbar-divider" />
        <button
          className="icon-button"
          title="缩小"
          aria-label="缩小"
          disabled={scale <= 0.8}
          onClick={() => setScale((current) => Math.max(0.8, Number((current - 0.2).toFixed(1))))}
        >
          <Minus size={16} />
        </button>
        <span className="page-indicator">{Math.round((scale / 1.6) * 100)}%</span>
        <button
          className="icon-button"
          title="放大"
          aria-label="放大"
          disabled={scale >= 3}
          onClick={() => setScale((current) => Math.min(3, Number((current + 0.2).toFixed(1))))}
        >
          <Plus size={16} />
        </button>
      </div>
      <div className="pdf-page-stage">
        {imageFailed ? (
          <div className="error-text">PDF 页面渲染失败。</div>
        ) : (
          <img src={pageImageUrl} alt={`${title} 第 ${pageNumber} 页`} onError={() => setImageFailed(true)} />
        )}
      </div>
    </div>
  );
}

function SummaryBlock({
  summary,
  loading,
  error,
}: {
  summary: Record<string, unknown> | null;
  loading: boolean;
  error: Error | null;
}) {
  const fields = [
    ["research_question", "研究问题"],
    ["method", "方法"],
    ["dataset_or_materials", "数据/材料"],
    ["experiment_setup", "实验设置"],
    ["key_findings", "主要结论"],
    ["limitations", "局限"],
    ["future_work", "未来工作"],
  ];
  if (loading) return <div className="empty-state">正在生成摘要，请稍候...</div>;
  if (error) return <div className="error-text">{error.message}</div>;
  if (!summary) return <div className="empty-state">点击生成摘要，结果会存入 SQLite。</div>;
  return (
    <div className="summary-list">
      {fields.map(([key, label]) => (
        <div key={key}>
          <span>{label}</span>
          <p>{formatSummaryValue(summary[key])}</p>
        </div>
      ))}
    </div>
  );
}

function formatSummaryValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "未在原文中找到";
  if (Array.isArray(value)) {
    return value
      .map((item) => (typeof item === "object" && item !== null ? JSON.stringify(item) : String(item)))
      .join("\n");
  }
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

function ChatView({ libraryId, papers }: { libraryId: string; papers: Paper[] }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const chatMutation = useMutation({
    mutationFn: () => api.chat({ library_id: libraryId, question, top_k: 8 }),
    onSuccess: (result) => {
      setAnswer(result.answer);
      setCitations(result.citations);
    },
  });

  return (
    <div className="content-grid two-columns">
      <section className="panel">
        <h3>证据链问答</h3>
        <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="例如：这些论文的方法差异是什么？" />
        <button className="primary-button" onClick={() => chatMutation.mutate()} disabled={!libraryId || !question || chatMutation.isPending}>
          {chatMutation.isPending ? "检索中..." : "基于文献回答"}
        </button>
        <div className="answer-box">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
            {answer || `当前文库有 ${papers.length} 篇论文。回答会强制附带证据片段。`}
          </ReactMarkdown>
        </div>
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h3>引用证据</h3>
          <span>{citations.length}</span>
        </div>
        <div className="citation-list">
          {citations.map((citation, index) => (
            <article key={`${citation.chunk_id}-${index}`} className="citation">
              <strong>{citation.filename}</strong>
              <span>{citation.section_title || "未识别章节"}{citation.page_start ? ` · p.${citation.page_start}` : ""}</span>
              <p>{citation.quote}</p>
            </article>
          ))}
          {!citations.length && <div className="empty-state">引用片段会在这里显示。</div>}
        </div>
      </section>
    </div>
  );
}

function MatrixView({ libraryId, papers }: { libraryId: string; papers: Paper[] }) {
  const [topic, setTopic] = useState("");
  const [matrixId, setMatrixId] = useState("");
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [exported, setExported] = useState("");
  const matrixMutation = useMutation({
    mutationFn: () => api.matrix({ library_id: libraryId, topic }),
    onSuccess: (result) => {
      setRows(result.rows);
      setMatrixId(result.id);
    },
  });
  const exportMutation = useMutation({
    mutationFn: () => api.exportMarkdown({ library_id: libraryId, matrix_id: matrixId || undefined }),
    onSuccess: setExported,
  });

  const columns = useMemo(
    () => ["filename", "research_question", "method", "dataset_or_materials", "key_findings", "limitations"],
    [],
  );

  return (
    <section className="panel matrix-panel">
      <div className="matrix-toolbar">
        <input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="综述主题，可选" />
        <button className="primary-button" onClick={() => matrixMutation.mutate()} disabled={!libraryId || !papers.length || matrixMutation.isPending}>
          {matrixMutation.isPending ? "生成中..." : "生成证据表"}
        </button>
        <button className="secondary-button" onClick={() => exportMutation.mutate()} disabled={!libraryId}>
          导出 Markdown
        </button>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((column) => <th key={column}>{column}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={String(row.paper_id ?? index)}>
                {columns.map((column) => <td key={column}>{String(row[column] ?? "")}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && <div className="empty-state">生成后展示多篇论文的 evidence matrix。</div>}
      </div>
      {exported && <pre className="export-box">{exported}</pre>}
    </section>
  );
}
