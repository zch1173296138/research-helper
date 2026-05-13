from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Library(Base):
    __tablename__ = "libraries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    papers: Mapped[list["Paper"]] = relationship(back_populates="library", cascade="all, delete-orphan")


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    library_id: Mapped[str] = mapped_column(ForeignKey("libraries.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    input_path: Mapped[str] = mapped_column(Text, nullable=False)
    output_dir: Mapped[str] = mapped_column(Text, nullable=False)
    md_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="uploaded", index=True)
    parser: Mapped[str] = mapped_column(String(64), default="unknown")
    error: Mapped[str | None] = mapped_column(Text)
    needs_ocr: Mapped[bool] = mapped_column(Boolean, default=False)
    normalized_title: Mapped[str | None] = mapped_column(Text)
    normalized_authors: Mapped[list] = mapped_column(JSON, default=list)
    normalized_venue: Mapped[str | None] = mapped_column(Text)
    normalized_year: Mapped[int | None] = mapped_column(Integer)
    doi: Mapped[str | None] = mapped_column(String(255), index=True)
    external_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    source_url: Mapped[str | None] = mapped_column(Text)
    enrichment_provider: Mapped[str | None] = mapped_column(String(64))
    enrichment_confidence: Mapped[float | None] = mapped_column(Float)
    enrichment_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    enrichment_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    library: Mapped[Library] = relationship(back_populates="papers")
    chunks: Mapped[list["PaperChunk"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    assets: Mapped[list["PaperAsset"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    summary: Mapped["PaperSummary"] = relationship(back_populates="paper", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="paper", cascade="all, delete-orphan")


class PaperAsset(Base):
    __tablename__ = "paper_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), index=True)
    asset_type: Mapped[str] = mapped_column(String(32), default="image")
    path: Mapped[str] = mapped_column(Text, nullable=False)
    relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[str] = mapped_column(Text, default="")
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(64), default="mineru")
    generated_description: Mapped[str] = mapped_column(Text, default="")
    is_original_text: Mapped[bool] = mapped_column(Boolean, default=False)
    enrichment_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    paper: Mapped[Paper] = relationship(back_populates="assets")


class PaperChunk(Base):
    __tablename__ = "paper_chunks"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    library_id: Mapped[str] = mapped_column(String(64), index=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, index=True)
    section_title: Mapped[str] = mapped_column(String(512), default="")
    section_path: Mapped[str] = mapped_column(Text, default="")
    section_type: Mapped[str] = mapped_column(String(64), default="unknown", index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source_md_path: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    is_reference: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    paper: Mapped[Paper] = relationship(back_populates="chunks")


class PaperSummary(Base):
    __tablename__ = "paper_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), unique=True, index=True)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    paper: Mapped[Paper] = relationship(back_populates="summary")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    library_id: Mapped[str] = mapped_column(ForeignKey("libraries.id"), index=True)
    paper_id: Mapped[str | None] = mapped_column(ForeignKey("papers.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="New chat")
    memory_summary: Mapped[str] = mapped_column(Text, default="")
    compressed_until_message_id: Mapped[int | None] = mapped_column(Integer)
    memory_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    context_mode: Mapped[str] = mapped_column(String(32), default="hybrid")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    paper: Mapped[Paper | None] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    retrieval_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class ReviewMatrix(Base):
    __tablename__ = "review_matrices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    library_id: Mapped[str] = mapped_column(ForeignKey("libraries.id"), index=True)
    topic: Mapped[str] = mapped_column(String(512), default="")
    matrix_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
