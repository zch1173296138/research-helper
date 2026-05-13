from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import Settings
from backend.app.db.models import Base, Library, Paper, PaperChunk
from backend.app.services.retrieval import HybridRetriever


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def seed_chunks(db) -> None:
    db.add(Library(id="library-1", name="Library"))
    db.add(
        Paper(
            id="paper-1",
            library_id="library-1",
            original_filename="paper.pdf",
            input_path="paper.pdf",
            output_dir="paper",
            status="processed",
        )
    )
    rows = [
        ("chunk-abstract", 0, "Abstract", "abstract", "The paper introduces TinyOS.", "TinyOS overview."),
        ("chunk-method", 1, "Method", "method", "The method has three scheduling stages.", "method details."),
        ("chunk-results", 2, "Results", "results", "TinyBench accuracy reaches 91 percent.", "metric result."),
        ("chunk-ref", 3, "References", "references", "TinyBench reference entry.", "reference."),
    ]
    for chunk_id, index, title, section_type, text, extra in rows:
        db.add(
            PaperChunk(
                id=chunk_id,
                library_id="library-1",
                paper_id="paper-1",
                chunk_index=index,
                section_title=title,
                section_path=f"Paper > {title}",
                section_type=section_type,
                text=f"{text} {extra}",
                source_md_path="full.md",
                is_reference=section_type == "references",
            )
        )
    db.commit()


def test_hybrid_retrieval_prioritizes_section_intent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    seed_chunks(db)

    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb")
    result = HybridRetriever(settings).search(db, "library-1", "这篇论文的方法是什么？", ["paper-1"], top_k=3)

    assert result.chunks[0].section_type == "method"
    assert all(chunk.section_type != "references" for chunk in result.chunks)


def test_hybrid_retrieval_uses_keyword_branch_for_exact_terms(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    seed_chunks(db)

    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb")
    result = HybridRetriever(settings).search(db, "library-1", "TinyBench 指标是多少？", ["paper-1"], top_k=3)

    assert any(chunk.chunk_id == "chunk-results" for chunk in result.chunks)
    assert result.metadata["passes"][0]["keyword_source"] in {"fts5_bm25", "sqlite_keyword"}


def test_second_pass_only_for_key_questions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    seed_chunks(db)

    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb")
    key_question = HybridRetriever(settings).search(db, "library-1", "实验结果支持什么结论？", ["paper-1"], top_k=3)
    simple_question = HybridRetriever(settings).search(db, "library-1", "TinyOS 是什么？", ["paper-1"], top_k=3)

    assert key_question.metadata["second_pass"] is True
    assert simple_question.metadata["second_pass"] is False


def test_hybrid_retrieval_falls_back_to_paper_overview_when_query_misses(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    monkeypatch.setattr("backend.app.services.retrieval.VectorStore.search", lambda *args, **kwargs: [])
    db = make_session()
    seed_chunks(db)

    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb")
    result = HybridRetriever(settings).search(db, "library-1", "2504.07378v3 论文主要内容", ["paper-1"], top_k=3)

    assert result.chunks
    assert result.chunks[0].chunk_id == "chunk-abstract"
    assert result.metadata["passes"][0]["fallback"] == "paper_overview"


def test_hybrid_retrieval_filters_reference_title_even_when_flag_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    seed_chunks(db)
    reference = db.get(PaperChunk, "chunk-ref")
    reference.section_type = "unknown"
    reference.is_reference = False
    db.commit()

    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb")
    result = HybridRetriever(settings).search(db, "library-1", "TinyBench reference entry", ["paper-1"], top_k=4)

    assert result.chunks
    assert all("reference" not in chunk.section_title.lower() for chunk in result.chunks)
