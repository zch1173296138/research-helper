import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Database,
  FileText,
  MessageSquareText,
  Minus,
  Plus,
  Search,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { useDropzone } from "react-dropzone";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import "katex/dist/katex.min.css";
import { api, ChatMessage, Citation, EvidenceDecision, EvidenceMetadata, Library, Paper } from "./api";

type Tab = "library" | "paper" | "chat" | "matrix";
type DetailTab = "summary" | "chat";

const markdownRemarkPlugins = [remarkGfm, remarkMath];
const markdownRehypePlugins = [rehypeKatex];

export function App() {
  const queryClient = useQueryClient();
  const [selectedLibraryId, setSelectedLibraryId] = useState("");
  const [selectedPaperId, setSelectedPaperId] = useState("");
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
          <div className="brand-mark">
            <Search size={18} />
          </div>
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
          {librariesQuery.error && <div className="error-text">{librariesQuery.error.message}</div>}
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
            <p>
              {papers.length} 篇论文 · SQLite + LanceDB
              {papersQuery.isFetching ? "（刷新中）" : ""}
            </p>
          </div>
          <div className="status-line">
            <span>MinerU 解析</span>
            <span>PDF 页面图片预览</span>
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

function LibraryPicker({
  libraries,
  selectedId,
  onSelect,
}: {
  libraries: Library[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
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
        <p>
          批量上传论文。后端使用 MinerU 生成 Markdown，并为检索问答建立证据索引。
        </p>
        <button className="primary-button" disabled={!libraryId || uploadMutation.isPending}>
          {uploadMutation.isPending ? "解析中..." : "选择 PDF"}
        </button>
        {uploadMutation.error && <div className="error-text">{uploadMutation.error.message}</div>}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h3>文献列表</h3>
          <span>{papers.length} 篇</span>
        </div>
        <div className="paper-list">
          {papers.map((paper) => (
            <article key={paper.id} className="paper-row">
              <button className="paper-main" onClick={() => onSelectPaper(paper)}>
                <FileText size={18} />
                <span>
                  <strong>{paper.original_filename}</strong>
                  <small>
                    {paper.status} · {paper.parser}
                  </small>
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
  const queryClient = useQueryClient();
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [detailTab, setDetailTab] = useState<DetailTab>("summary");
  const [targetPage, setTargetPage] = useState<number | null>(null);
  const summarizeMutation = useMutation({
    mutationFn: () => api.summarize(paper!.id),
    onSuccess: (result) => setSummary(result.summary),
  });
  const enrichMutation = useMutation({
    mutationFn: () => api.enrichPaper(paper!.id),
    onSuccess: (updatedPaper) => {
      queryClient.setQueryData<Paper[]>(["papers", updatedPaper.library_id], (current) =>
        current?.map((existing) => (existing.id === updatedPaper.id ? updatedPaper : existing)),
      );
      queryClient.invalidateQueries({ queryKey: ["papers", updatedPaper.library_id] });
    },
  });

  useEffect(() => {
    setSummary(null);
    setDetailTab("summary");
    setTargetPage(null);
    summarizeMutation.reset();
    enrichMutation.reset();
  }, [paper?.id]);

  if (!paper) return <div className="empty-state fill">请选择一篇论文。</div>;

  return (
    <div className="content-grid two-columns wide-left paper-detail-grid">
      <section className="panel paper-detail-panel">
        <div className="panel-heading">
          <h3>{paper.original_filename}</h3>
          <span>{paper.status}</span>
        </div>
        {paper.error && <div className="error-text">{paper.error}</div>}
        <PdfPreview paperId={paper.id} title={paper.original_filename} targetPage={targetPage ?? undefined} />
      </section>
      <section className="panel paper-detail-panel">
        <div className="panel-heading">
          <div className="segmented-tabs">
            <button className={detailTab === "summary" ? "active" : ""} onClick={() => setDetailTab("summary")}>
              结构化摘要
            </button>
            <button className={detailTab === "chat" ? "active" : ""} onClick={() => setDetailTab("chat")}>
              论文问答
            </button>
          </div>
          {detailTab === "summary" && (
            <div className="toolbar-actions">
              <button
                className="secondary-button"
                onClick={() => enrichMutation.mutate()}
                disabled={!paper.id || enrichMutation.isPending}
              >
                {enrichMutation.isPending ? "Enriching..." : "Enrich"}
              </button>
              <button
                className="secondary-button"
                onClick={() => summarizeMutation.mutate()}
                disabled={!paper.id || summarizeMutation.isPending}
              >
              {summarizeMutation.isPending ? "生成中..." : "生成摘要"}
              </button>
            </div>
          )}
        </div>
        <div className="paper-detail-body">
          {detailTab === "summary" ? (
            <>
              <PaperEnrichmentStrip paper={paper} error={enrichMutation.error} />
              <SummaryBlock summary={summary} loading={summarizeMutation.isPending} error={summarizeMutation.error} />
            </>
          ) : (
            <PaperChatPanel paper={paper} onCitationPage={(page) => setTargetPage(page)} />
          )}
        </div>
      </section>
    </div>
  );
}

function PdfPreview({ paperId, title, targetPage }: { paperId: string; title: string; targetPage?: number }) {
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

  useEffect(() => {
    if (!targetPage || targetPage < 1 || !pageCount) return;
    setPageNumber(Math.min(pageCount, targetPage));
  }, [targetPage, pageCount]);

  if (infoQuery.isLoading) return <div className="empty-state">正在加载 PDF 预览...</div>;
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
        <span className="page-indicator">
          {pageNumber} / {pageCount}
        </span>
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

function PaperChatPanel({ paper, onCitationPage }: { paper: Paper; onCitationPage: (page: number) => void }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [memorySummary, setMemorySummary] = useState("");
  const [memoryBoundary, setMemoryBoundary] = useState<number | null>(null);
  const [memoryUpdatedAt, setMemoryUpdatedAt] = useState<string | null>(null);
  const messagesRef = useRef<HTMLDivElement | null>(null);

  const sessionQuery = useQuery({
    queryKey: ["paper-chat-session", paper.id],
    queryFn: () => api.paperChatSession(paper.id),
    enabled: Boolean(paper.id),
  });
  const sessionId = sessionQuery.data?.id ?? "";
  const messagesQuery = useQuery({
    queryKey: ["paper-chat-messages", sessionId],
    queryFn: () => api.paperChatMessages(sessionId, { limit: 50 }),
    enabled: Boolean(sessionId),
  });
  const loadOlderMutation = useMutation({
    mutationFn: () => api.paperChatMessages(sessionId, { limit: 50, before_id: messages[0]?.id }),
    onSuccess: (older) => {
      setMessages((current) => mergeMessages([...older, ...current]));
    },
  });
  const sendMutation = useMutation({
    mutationFn: (targetSessionId: string) =>
      api.sendPaperChatMessage(targetSessionId, { question: question.trim(), top_k: 8, context_mode: "hybrid" }),
    onSuccess: (result) => {
      setMessages((current) => mergeMessages([...current, result.user_message, result.assistant_message]));
      setMemorySummary(result.memory_summary);
      setMemoryBoundary(result.compressed_until_message_id ?? null);
      setMemoryUpdatedAt(result.memory_updated_at ?? null);
      setQuestion("");
    },
  });

  useEffect(() => {
    setMessages([]);
    setMemorySummary("");
    setMemoryBoundary(null);
    setMemoryUpdatedAt(null);
    setQuestion("");
  }, [paper.id]);

  useEffect(() => {
    if (!messagesQuery.data) return;
    setMessages(messagesQuery.data);
  }, [messagesQuery.data]);

  useEffect(() => {
    if (!sessionQuery.data) return;
    setMemorySummary(sessionQuery.data.memory_summary || "");
    setMemoryBoundary(sessionQuery.data.compressed_until_message_id ?? null);
    setMemoryUpdatedAt(sessionQuery.data.memory_updated_at ?? null);
  }, [sessionQuery.data]);

  useEffect(() => {
    const element = messagesRef.current;
    if (!element) return;
    element.scrollTop = element.scrollHeight;
  }, [messages.length, sendMutation.isPending]);

  const handleSend = async () => {
    if (!question.trim() || sendMutation.isPending || sessionQuery.isLoading) return;
    let targetSessionId = sessionId;
    if (!targetSessionId) {
      const refreshed = await sessionQuery.refetch();
      targetSessionId = refreshed.data?.id ?? "";
    }
    if (targetSessionId) {
      sendMutation.mutate(targetSessionId);
    }
  };

  const canSend = Boolean(question.trim() && !sendMutation.isPending && !sessionQuery.isLoading);
  const hasOlder = messages.length >= 50;
  const hasMemoryBoundary = memoryBoundary !== null && memoryBoundary !== undefined;
  const hasStatus =
    Boolean(memorySummary || hasMemoryBoundary) ||
    Boolean(messagesQuery.error || sessionQuery.error || sendMutation.error);

  return (
    <div className={`paper-chat-panel ${hasStatus ? "has-status" : ""}`}>
      {hasStatus && (
        <div className="paper-chat-status">
          {(memorySummary || hasMemoryBoundary) && (
            <div className="memory-strip">
              <span>对话记忆</span>
              {memorySummary && <p>{memorySummary}</p>}
              {hasMemoryBoundary && (
                <small>
                  已压缩到消息 #{memoryBoundary}
                  {memoryUpdatedAt ? ` · ${formatMemoryUpdatedAt(memoryUpdatedAt)}` : ""}
                </small>
              )}
            </div>
          )}
          {messagesQuery.error && <div className="error-text">{messagesQuery.error.message}</div>}
          {sessionQuery.error && (
            <div className="error-text chat-session-error">
              <span>{sessionQuery.error.message}</span>
              <button className="secondary-button" onClick={() => sessionQuery.refetch()} disabled={sessionQuery.isFetching}>
                重试
              </button>
            </div>
          )}
          {sendMutation.error && <div className="error-text">{sendMutation.error.message}</div>}
        </div>
      )}
      <div className="chat-message-list" ref={messagesRef}>
        {hasOlder && (
          <button
            className="secondary-button full-width"
            disabled={loadOlderMutation.isPending}
            onClick={() => loadOlderMutation.mutate()}
          >
            {loadOlderMutation.isPending ? "加载中..." : "加载更早消息"}
          </button>
        )}
        {messagesQuery.isLoading && <div className="empty-state">正在加载消息...</div>}
        {messages.map((message) => (
          <ChatBubble key={message.id} message={message} onCitationPage={onCitationPage} />
        ))}
        {sendMutation.isPending && <div className="chat-bubble assistant">正在检索证据并生成回答...</div>}
        {!messages.length && !messagesQuery.isLoading && (
          <div className="empty-state">可以围绕这篇论文提问。点击引用标签会跳转到对应 PDF 页。</div>
        )}
      </div>
      <div className="chat-input-row">
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="询问这篇论文，Ctrl+Enter 发送。"
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && canSend) {
              handleSend();
            }
          }}
        />
        <button className="primary-button" disabled={!canSend} onClick={handleSend}>
          {sessionQuery.isLoading ? "打开中..." : sendMutation.isPending ? "发送中..." : "发送"}
        </button>
      </div>
    </div>
  );
}

function ChatBubble({ message, onCitationPage }: { message: ChatMessage; onCitationPage: (page: number) => void }) {
  const isUser = message.role === "user";
  return (
    <article className={`chat-bubble ${isUser ? "user" : "assistant"}`}>
      <div className="chat-role">{isUser ? "你" : "研究助手"}</div>
      <MarkdownContent>{message.content}</MarkdownContent>
      {!isUser && Boolean(message.citations?.length) && (
        <div className="chat-citations">
          {message.citations.map((citation, index) => (
            <button
              key={`${message.id}-${citation.chunk_id ?? index}`}
              className="citation-chip"
              disabled={!citation.page_start}
              onClick={() => citation.page_start && onCitationPage(citation.page_start)}
              title={citation.quote}
            >
              {citation.citation_id ?? `C${index + 1}`} · {citation.section_title || citation.section_type}
              {citation.page_start ? ` · p.${citation.page_start}` : ""}
            </button>
          ))}
        </div>
      )}
      {!isUser && <EvidenceInspection metadata={message.retrieval_metadata as EvidenceMetadata} />}
    </article>
  );
}

function MarkdownContent({ children }: { children: string }) {
  return (
    <ReactMarkdown remarkPlugins={markdownRemarkPlugins} rehypePlugins={markdownRehypePlugins}>
      {children}
    </ReactMarkdown>
  );
}

function EvidenceInspection({ metadata }: { metadata: EvidenceMetadata }) {
  const decisions = Array.isArray(metadata.evidence_decisions) ? metadata.evidence_decisions : [];
  const accepted = decisions.filter((decision) => decision.decision === "accept");
  const lowConfidence = decisions.filter((decision) => decision.decision !== "accept");
  if (!metadata.evidence_pipeline && !decisions.length) return null;
  return (
    <details className="evidence-inspection">
      <summary>
        Evidence check
        <span>
          {accepted.length} accepted / {lowConfidence.length} low confidence
        </span>
      </summary>
      <div className="evidence-meta-grid">
        <span>Judge</span>
        <strong>{metadata.judge_source ?? "unknown"}</strong>
        <span>Candidates</span>
        <strong>{metadata.candidate_chunk_ids?.length ?? 0}</strong>
        <span>Final context</span>
        <strong>{metadata.final_context_chunk_ids?.length ?? 0}</strong>
      </div>
      <EvidenceDecisionList title="Accepted evidence" decisions={accepted} />
      <EvidenceDecisionList title="Low-confidence / rejected" decisions={lowConfidence.slice(0, 8)} />
    </details>
  );
}

function EvidenceDecisionList({ title, decisions }: { title: string; decisions: EvidenceDecision[] }) {
  if (!decisions.length) return null;
  return (
    <div className="evidence-decision-list">
      <h4>{title}</h4>
      {decisions.map((decision) => (
        <article key={`${title}-${decision.chunk_id}`}>
          <div>
            <strong>{decision.chunk_id}</strong>
            <span>{decision.decision} / {decision.support_level ?? "none"}</span>
          </div>
          {decision.concise_summary && <p>{decision.concise_summary}</p>}
          {decision.reason && <small>{decision.reason}</small>}
        </article>
      ))}
    </div>
  );
}

function mergeMessages(messages: ChatMessage[]): ChatMessage[] {
  const byId = new Map<number, ChatMessage>();
  messages.forEach((message) => byId.set(message.id, message));
  return Array.from(byId.values()).sort((first, second) => first.id - second.id);
}

function formatMemoryUpdatedAt(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

function formatIdentifiers(paper: Paper): string {
  const identifiers = new Set<string>();
  if (paper.doi) identifiers.add(`DOI: ${paper.doi}`);
  Object.entries(paper.external_ids ?? {}).forEach(([key, value]) => {
    if (value) identifiers.add(`${key.toUpperCase()}: ${String(value)}`);
  });
  if (!identifiers.size && paper.source_url) identifiers.add(paper.source_url);
  return identifiers.size ? Array.from(identifiers).join(" · ") : "Not available";
}

function PaperEnrichmentStrip({ paper, error }: { paper: Paper; error: Error | null }) {
  const authors = Array.isArray(paper.normalized_authors) ? paper.normalized_authors : [];
  return (
    <div className="enrichment-strip">
      <div>
        <span>Enrichment</span>
        <strong>{paper.enrichment_status || "pending"}</strong>
      </div>
      <div>
        <span>Title</span>
        <strong>{paper.normalized_title || paper.original_filename}</strong>
      </div>
      <div>
        <span>Identifiers</span>
        <strong>{formatIdentifiers(paper)}</strong>
      </div>
      <div>
        <span>Authors</span>
        <strong>{authors.length ? authors.map(String).join(", ") : "Not available"}</strong>
      </div>
      {error && <div className="error-text">{error.message}</div>}
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
    return value.map((item) => (typeof item === "object" && item !== null ? JSON.stringify(item) : String(item))).join("\n");
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

  const canAsk = Boolean(libraryId && question.trim() && !chatMutation.isPending);

  return (
    <div className="content-grid two-columns">
      <section className="panel">
        <h3>证据链问答</h3>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="例如：这些论文的方法差异是什么？"
        />
        <button className="primary-button" onClick={() => chatMutation.mutate()} disabled={!canAsk}>
          {chatMutation.isPending ? "检索中..." : "基于文献回答"}
        </button>
        {chatMutation.error && <div className="error-text">{chatMutation.error.message}</div>}
        <div className="answer-box">
          <MarkdownContent>
            {answer || `当前文库有 ${papers.length} 篇论文。回答会强制附带证据片段。`}
          </MarkdownContent>
        </div>
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h3>引用证据</h3>
          <span>{citations.length}</span>
        </div>
        <div className="citation-list">
          {citations.map((citation, index) => (
            <article key={`${citation.chunk_id ?? citation.paper_id}-${index}`} className="citation">
              <strong>{citation.filename}</strong>
              <span>
                {citation.section_title || "未识别章节"}
                {citation.page_start ? ` · p.${citation.page_start}` : ""}
              </span>
              <div className="citation-quote">
                <MarkdownContent>{citation.quote}</MarkdownContent>
              </div>
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
      setExported("");
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
        <button
          className="primary-button"
          onClick={() => matrixMutation.mutate()}
          disabled={!libraryId || !papers.length || matrixMutation.isPending}
        >
          {matrixMutation.isPending ? "生成中..." : "生成证据表"}
        </button>
        <button className="secondary-button" onClick={() => exportMutation.mutate()} disabled={!libraryId || exportMutation.isPending}>
          导出 Markdown
        </button>
      </div>
      {matrixMutation.error && <div className="error-text">{matrixMutation.error.message}</div>}
      {exportMutation.error && <div className="error-text">{exportMutation.error.message}</div>}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={String(row.paper_id ?? index)}>
                {columns.map((column) => (
                  <td key={column}>{String(row[column] ?? "")}</td>
                ))}
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
