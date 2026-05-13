from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings
from backend.app.db.models import Base


settings = get_settings()

if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "", 1)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        _ensure_sqlite_schema()


def _ensure_sqlite_schema() -> None:
    """Keep local SQLite databases compatible when models gain columns."""
    with engine.begin() as conn:
        _add_missing_columns(
            conn,
            "paper_chunks",
            {
                "section_path": "TEXT DEFAULT ''",
                "section_type": "VARCHAR(64) DEFAULT 'unknown'",
                "is_reference": "BOOLEAN DEFAULT 0",
            },
        )
        _add_missing_columns(
            conn,
            "chat_sessions",
            {
                "paper_id": "VARCHAR(64)",
                "memory_summary": "TEXT DEFAULT ''",
                "compressed_until_message_id": "INTEGER",
                "memory_updated_at": "DATETIME",
                "context_mode": "VARCHAR(32) DEFAULT 'hybrid'",
                "updated_at": "DATETIME",
            },
        )
        _add_missing_columns(
            conn,
            "papers",
            {
                "normalized_title": "TEXT",
                "normalized_authors": "JSON DEFAULT '[]'",
                "normalized_venue": "TEXT",
                "normalized_year": "INTEGER",
                "doi": "VARCHAR(255)",
                "external_ids": "JSON DEFAULT '{}'",
                "source_url": "TEXT",
                "enrichment_provider": "VARCHAR(64)",
                "enrichment_confidence": "FLOAT",
                "enrichment_status": "VARCHAR(32) DEFAULT 'pending'",
                "enrichment_metadata": "JSON DEFAULT '{}'",
            },
        )
        _add_missing_columns(
            conn,
            "paper_assets",
            {
                "caption": "TEXT DEFAULT ''",
                "page_start": "INTEGER",
                "page_end": "INTEGER",
                "source": "VARCHAR(64) DEFAULT 'mineru'",
                "generated_description": "TEXT DEFAULT ''",
                "is_original_text": "BOOLEAN DEFAULT 0",
                "enrichment_metadata": "JSON DEFAULT '{}'",
            },
        )
        _add_missing_columns(conn, "chat_messages", {"retrieval_metadata": "JSON DEFAULT '{}'"})
        try:
            conn.execute(
                text(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS paper_chunks_fts USING fts5(
                        chunk_id UNINDEXED,
                        library_id UNINDEXED,
                        paper_id UNINDEXED,
                        section_title,
                        section_path,
                        section_type,
                        text
                    )
                    """
                )
            )
            conn.execute(text("DELETE FROM paper_chunks_fts"))
            conn.execute(
                text(
                    """
                    INSERT INTO paper_chunks_fts(
                        chunk_id, library_id, paper_id, section_title, section_path, section_type, text
                    )
                    SELECT id, library_id, paper_id, section_title, section_path, section_type, text
                    FROM paper_chunks
                    WHERE COALESCE(is_reference, 0) = 0
                    """
                )
            )
        except Exception:
            # Some SQLite builds omit FTS5. Retrieval has a keyword fallback.
            pass


def _add_missing_columns(conn, table_name: str, columns: dict[str, str]) -> None:
    existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()}
    for column, definition in columns.items():
        if column not in existing:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column} {definition}"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
