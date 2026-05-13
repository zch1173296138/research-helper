from typing import Any

from pydantic import BaseModel, Field


class LibraryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""


class LibraryRead(BaseModel):
    id: str
    name: str
    description: str
    paper_count: int = 0


class PaperRead(BaseModel):
    id: str
    library_id: str
    original_filename: str
    status: str
    parser: str
    error: str | None = None
    needs_ocr: bool = False
    md_path: str | None = None
    normalized_title: str | None = None
    normalized_authors: list[Any] = Field(default_factory=list)
    normalized_venue: str | None = None
    normalized_year: int | None = None
    doi: str | None = None
    external_ids: dict[str, Any] = Field(default_factory=dict)
    source_url: str | None = None
    enrichment_status: str = "pending"
    enrichment_metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    citation_id: str | None = None
    paper_id: str
    filename: str
    chunk_id: str | None = None
    asset_id: int | None = None
    asset_type: str | None = None
    provenance: str | None = None
    section_title: str = ""
    section_path: str = ""
    section_type: str = "unknown"
    quote: str
    page_start: int | None = None
    page_end: int | None = None


class ChatRequest(BaseModel):
    library_id: str
    question: str = Field(min_length=1)
    paper_ids: list[str] = Field(default_factory=list)
    top_k: int = 8


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    missing_evidence: bool = False
    retrieval_metadata: dict[str, Any] = Field(default_factory=dict)


class ChatSessionRead(BaseModel):
    id: str
    library_id: str
    paper_id: str | None = None
    title: str
    memory_summary: str = ""
    compressed_until_message_id: int | None = None
    memory_updated_at: str | None = None
    context_mode: str = "hybrid"


class ChatMessageRead(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    citations: list[Citation] = Field(default_factory=list)
    retrieval_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class PaperChatRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=20)
    context_mode: str = "hybrid"


class PaperChatResponse(BaseModel):
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead
    answer: str
    citations: list[Citation]
    missing_evidence: bool = False
    memory_summary: str = ""
    compressed_until_message_id: int | None = None
    memory_updated_at: str | None = None
    retrieval_metadata: dict[str, Any] = Field(default_factory=dict)


class MatrixRequest(BaseModel):
    library_id: str
    topic: str = ""
    paper_ids: list[str] = Field(default_factory=list)


class MatrixResponse(BaseModel):
    id: str
    rows: list[dict[str, Any]]


class ExportRequest(BaseModel):
    library_id: str
    matrix_id: str | None = None
