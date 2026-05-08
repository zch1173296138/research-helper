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


class Citation(BaseModel):
    paper_id: str
    filename: str
    chunk_id: str | None = None
    section_title: str = ""
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

