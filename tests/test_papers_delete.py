from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import Settings
from backend.app.db.models import Base, Library, Paper, PaperAsset, PaperChunk, PaperSummary, ReviewMatrix
from backend.app.services.papers import PaperService


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_delete_paper_removes_db_records_files_and_matrix_rows(tmp_path: Path) -> None:
    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb")
    settings.input_dir.mkdir(parents=True)
    settings.libraries_output_dir.mkdir(parents=True)

    input_path = settings.input_dir / "paper-1.pdf"
    input_path.write_bytes(b"%PDF-1.4")
    output_dir = settings.libraries_output_dir / "library-1" / "paper-1"
    output_dir.mkdir(parents=True)
    (output_dir / "full.md").write_text("# Paper", encoding="utf-8")

    db = make_session()
    db.add(Library(id="library-1", name="Library"))
    paper = Paper(
        id="paper-1",
        library_id="library-1",
        original_filename="paper.pdf",
        input_path=str(input_path),
        output_dir=str(output_dir),
        md_path=str(output_dir / "full.md"),
        status="processed",
    )
    db.add(paper)
    db.add(PaperChunk(id="chunk-1", library_id="library-1", paper_id="paper-1", chunk_index=0, text="body", source_md_path=str(output_dir / "full.md")))
    db.add(PaperAsset(paper_id="paper-1", asset_type="image", path=str(output_dir / "image.png"), relative_path="image.png"))
    db.add(PaperSummary(paper_id="paper-1", summary_json={"filename": "paper.pdf"}))
    db.add(
        ReviewMatrix(
            id="matrix-1",
            library_id="library-1",
            topic="topic",
            matrix_json={
                "rows": [
                    {"paper_id": "paper-1", "filename": "paper.pdf"},
                    {"paper_id": "paper-2", "filename": "other.pdf"},
                ]
            },
        )
    )
    db.commit()

    deleted_vectors: list[str] = []
    service = PaperService(settings)
    service.vector_store.delete_paper = deleted_vectors.append

    service.delete_paper(db, paper)

    assert deleted_vectors == ["paper-1"]
    assert db.get(Paper, "paper-1") is None
    assert db.query(PaperChunk).filter(PaperChunk.paper_id == "paper-1").count() == 0
    assert db.query(PaperAsset).filter(PaperAsset.paper_id == "paper-1").count() == 0
    assert db.query(PaperSummary).filter(PaperSummary.paper_id == "paper-1").count() == 0
    assert db.get(ReviewMatrix, "matrix-1").matrix_json["rows"] == [{"paper_id": "paper-2", "filename": "other.pdf"}]
    assert not input_path.exists()
    assert not output_dir.exists()
