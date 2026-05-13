from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import Settings
from backend.app.db.models import Base, Library, Paper, PaperAsset, PaperChunk
from backend.app.services.enrichment import PaperEnrichmentService
from backend.app.services.evidence import EvidenceRagService
from backend.app.services.evidence_types import EvidenceDecision
from backend.app.services.llm import LLMService
from backend.app.services.vector_store import RetrievedChunk


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def seed_library(db, tmp_path: Path) -> Paper:
    db.add(Library(id="library-1", name="Library"))
    paper = Paper(
        id="paper-1",
        library_id="library-1",
        original_filename="10.1234_example_2024.pdf",
        input_path="paper.pdf",
        output_dir=str(tmp_path),
        status="processed",
    )
    db.add(paper)
    rows = [
        ("chunk-method", 0, "Method", "method", "The method uses staged evidence screening."),
        ("chunk-results", 1, "Results", "results", "The evaluation reports 91 percent accuracy."),
        ("chunk-ref", 2, "References", "references", "Reference entry about unrelated work."),
    ]
    for chunk_id, index, title, section_type, text in rows:
        db.add(
            PaperChunk(
                id=chunk_id,
                library_id="library-1",
                paper_id="paper-1",
                chunk_index=index,
                section_title=title,
                section_path=f"Paper > {title}",
                section_type=section_type,
                text=text,
                source_md_path="full.md",
                is_reference=section_type == "references",
            )
        )
    db.commit()
    return paper


def test_evidence_rag_fallback_records_candidates_and_accepts_ranked_chunks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    seed_library(db, tmp_path)
    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb", openai_api_key="")

    result = EvidenceRagService(settings).gather(db, "library-1", "What is the method?", ["paper-1"], top_k=1)
    metadata = result.metadata()

    assert metadata["evidence_pipeline"] == "paperqa_style"
    assert metadata["judge_source"] == "fallback_ranked"
    assert metadata["candidate_chunk_ids"]
    assert metadata["accepted_chunk_ids"] == [result.final_context_chunks[0].chunk_id]
    assert metadata["evidence_decisions"][0]["decision"] == "accept"
    assert all("ref" not in chunk.chunk_id for chunk in result.candidates)


def test_llm_judge_evidence_parses_json_and_rejects_invalid_values() -> None:
    class JudgeCompletions:
        def create(self, **_: object) -> object:
            content = {
                "decisions": [
                    {
                        "chunk_id": "chunk-1",
                        "decision": "accept",
                        "reason": "Directly answers the question.",
                        "support_level": "direct",
                        "answerable_claims": ["Uses staged screening"],
                        "concise_summary": "The method uses staged screening.",
                    },
                    {"chunk_id": "chunk-2", "decision": "bad", "support_level": "bad"},
                ]
            }
            import json

            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(content)))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=JudgeCompletions()))
    chunks = [
        RetrievedChunk("chunk-1", "paper-1", "paper.pdf", "Method", "The method uses staged screening."),
        RetrievedChunk("chunk-2", "paper-1", "paper.pdf", "Other", "Unrelated background."),
    ]

    decisions = service.judge_evidence("What is the method?", chunks)

    assert decisions[0].decision == "accept"
    assert decisions[0].support_level == "direct"
    assert decisions[1].decision == "reject"
    assert decisions[1].support_level == "none"


def test_answer_with_evidence_cites_only_accepted_chunks() -> None:
    class BadCitationCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Unsupported [C99]."))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=BadCitationCompletions()))
    chunks = [RetrievedChunk("chunk-1", "paper-1", "paper.pdf", "Method", "The method uses staged screening.")]
    decisions = [EvidenceDecision("chunk-1", "accept", concise_summary="The method uses staged screening.")]

    result = service.answer_with_evidence("What is the method?", chunks, decisions)

    assert "[C1]" in result["answer"]
    assert result["citations"][0]["chunk_id"] == "chunk-1"
    assert all(citation["citation_id"] != "C99" for citation in result["citations"])


def test_library_chat_uses_evidence_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    seed_library(db, tmp_path)
    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb", openai_api_key="")

    result = EvidenceRagService(settings).answer_library_chat(db, "library-1", "What is the method?", ["paper-1"], top_k=1)

    assert result["retrieval_metadata"]["evidence_pipeline"] == "paperqa_style"
    assert result["retrieval_metadata"]["accepted_chunk_ids"]
    assert result["citations"]


def test_enrichment_marks_local_metadata_and_asset_provenance(tmp_path: Path) -> None:
    db = make_session()
    paper = seed_library(db, tmp_path)
    md_path = tmp_path / "full.md"
    md_path.write_text("![Figure 1](images/fig1.png)\nFigure 1: Evidence pipeline overview.", encoding="utf-8")
    paper.md_path = str(md_path)
    db.add(
        PaperAsset(
            paper_id=paper.id,
            asset_type="image",
            path=str(tmp_path / "images" / "fig1.png"),
            relative_path="images/fig1.png",
        )
    )
    db.commit()

    result = PaperEnrichmentService(Settings(openai_api_key="")).enrich_paper(db, paper)
    asset = db.query(PaperAsset).filter(PaperAsset.paper_id == paper.id).one()

    assert result["metadata"]["status"] == "enriched"
    assert paper.doi == "10.1234_example_2024.pdf" or paper.normalized_title
    assert asset.caption.startswith("Figure 1")
    assert asset.is_original_text is False
    assert asset.enrichment_metadata["caption_source"] == "markdown"


def test_enrichment_reads_authors_and_identifiers_from_markdown_front_matter(tmp_path: Path) -> None:
    db = make_session()
    paper = seed_library(db, tmp_path)
    paper.original_filename = "2504.07378v3.pdf"
    md_path = tmp_path / "full.md"
    md_path.write_text(
        "\n".join(
            [
                "# BRepFormer: Transformer-Based B-rep Geometric Feature Recognition",
                "",
                "Yongkang Dai",
                "",
                "School of Software, Northwestern Polytechnical University",
                "",
                "Hao Guo",
                "",
                "School of Software, Northwestern Polytechnical University",
                "",
                "Yilei Shi\\*",
                "",
                "yilei_shi@nwpu.edu.cn",
                "",
                "https://doi.org/10.1145/3731715.3733283",
                "",
                "# ABSTRACT",
                "We propose BRepFormer.",
            ]
        ),
        encoding="utf-8",
    )
    paper.md_path = str(md_path)
    db.commit()

    PaperEnrichmentService(Settings(openai_api_key="")).enrich_paper(db, paper)

    assert paper.normalized_title == "BRepFormer: Transformer-Based B-rep Geometric Feature Recognition"
    assert paper.normalized_authors == ["Yongkang Dai", "Hao Guo", "Yilei Shi"]
    assert paper.doi == "10.1145/3731715.3733283"
    assert paper.external_ids["arxiv"] == "2504.07378"
    assert paper.enrichment_metadata["sources"] == ["filename", "markdown_front_matter"]
