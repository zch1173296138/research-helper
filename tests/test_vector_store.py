from collections import Counter
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import Settings
from backend.app.db.models import Base, Library, Paper, PaperChunk
from backend.app.services.vector_store import VectorStore


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_search_can_diversify_context_across_papers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    db.add(Library(id="library-1", name="Library"))
    for paper_id, filename in (("paper-1", "first.pdf"), ("paper-2", "second.pdf")):
        db.add(
            Paper(
                id=paper_id,
                library_id="library-1",
                original_filename=filename,
                input_path=f"{paper_id}.pdf",
                output_dir=paper_id,
                status="processed",
            )
        )
        for index in range(4):
            db.add(
                PaperChunk(
                    id=f"{paper_id}_chunk_{index}",
                    library_id="library-1",
                    paper_id=paper_id,
                    chunk_index=index,
                    section_title="Intro",
                    text=f"{filename} context {index}",
                    source_md_path=f"{paper_id}.md",
                )
            )
    db.commit()

    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb")
    chunks = VectorStore(settings).search(
        db,
        "library-1",
        "这些论文的差异",
        top_k=4,
        diversify_by_paper=True,
    )

    assert Counter(chunk.paper_id for chunk in chunks) == {"paper-1": 2, "paper-2": 2}
