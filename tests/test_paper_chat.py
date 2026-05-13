from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import Settings
from backend.app.db.models import Base, ChatMessage, ChatSession, Library, Paper, PaperChunk
from backend.app.services.paper_chat import PaperChatService


class FakePaperChatLLM:
    def __init__(self) -> None:
        self.summary_calls: list[tuple[list[dict[str, str]], str]] = []
        self.answer_calls: list[tuple[str, list[dict[str, str]], str]] = []

    def summarize_chat_memory(self, messages: list[dict[str, str]], previous_summary: str = "") -> str:
        self.summary_calls.append((messages, previous_summary))
        contents = " | ".join(message["content"] for message in messages)
        return f"{previous_summary} compressed: {contents}".strip()

    def rewrite_paper_chat_query(
        self,
        question: str,
        memory_summary: str = "",
        history: list[dict[str, str]] | None = None,
        paper_title: str = "",
    ) -> dict[str, str]:
        suffix = " ".join(message["content"] for message in (history or [])[-2:])
        query = " ".join(part for part in [question, memory_summary, suffix, paper_title] if part)
        return {"query": query, "source": "fake"}

    def answer_paper_chat(
        self,
        question: str,
        chunks: list,
        history: list[dict[str, str]] | None = None,
        memory_summary: str = "",
    ) -> dict:
        self.answer_calls.append((question, history or [], memory_summary))
        return {
            "answer": "The paper discusses staged scheduling. [C1]",
            "citations": [
                {
                    "citation_id": "C1",
                    "paper_id": chunks[0].paper_id,
                    "filename": chunks[0].filename,
                    "chunk_id": chunks[0].chunk_id,
                    "section_title": chunks[0].section_title,
                    "section_path": chunks[0].section_path,
                    "section_type": chunks[0].section_type,
                    "quote": chunks[0].text,
                    "page_start": chunks[0].page_start,
                    "page_end": chunks[0].page_end,
                }
            ],
            "missing_evidence": False,
        }


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def seed_paper(db) -> Paper:
    db.add(Library(id="library-1", name="Library"))
    paper = Paper(
        id="paper-1",
        library_id="library-1",
        original_filename="paper.pdf",
        input_path="paper.pdf",
        output_dir="paper",
        status="processed",
    )
    db.add(paper)
    db.add(
        PaperChunk(
            id="chunk-1",
            library_id="library-1",
            paper_id="paper-1",
            chunk_index=0,
            section_title="Method",
            section_path="Paper > Method",
            section_type="method",
            text="The method uses a staged scheduler and reports traceable evidence.",
            source_md_path="full.md",
        )
    )
    db.commit()
    return paper


def test_paper_chat_saves_messages_citations_and_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    paper = seed_paper(db)
    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb", openai_api_key="")

    service = PaperChatService(settings)
    session = service.get_or_create_session(db, paper)
    result = service.ask(db, session, "这篇论文的方法是什么？")

    assert result["assistant_message"].citations
    assert result["retrieval_metadata"]["strategy"] == "hybrid"
    assert result["retrieval_metadata"]["original_question"]
    assert result["retrieval_metadata"]["rewritten_query"]
    assert result["retrieval_metadata"]["rewrite_source"] == "fallback"
    assert db.query(ChatMessage).filter(ChatMessage.session_id == session.id).count() == 2


def test_paper_chat_does_not_compress_small_recent_history(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    paper = seed_paper(db)
    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb", openai_api_key="")
    service = PaperChatService(settings)
    fake_llm = FakePaperChatLLM()
    service.llm = fake_llm
    session = service.get_or_create_session(db, paper)
    for index in range(4):
        db.add(ChatMessage(session_id=session.id, role="user", content=f"recent topic {index}"))
    db.commit()

    result = service.ask(db, session, "What is the method?")

    db.refresh(session)
    assert session.memory_summary == ""
    assert session.compressed_until_message_id is None
    assert fake_llm.summary_calls == []
    assert result["retrieval_metadata"]["recent_message_ids"] == [1, 2, 3, 4]


def test_paper_chat_compresses_once_and_then_extends_boundary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    paper = seed_paper(db)
    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb", openai_api_key="")
    service = PaperChatService(settings)
    fake_llm = FakePaperChatLLM()
    service.llm = fake_llm
    session = service.get_or_create_session(db, paper)
    for index in range(11):
        role = "user" if index % 2 == 0 else "assistant"
        db.add(ChatMessage(session_id=session.id, role=role, content=f"turn {index + 1}"))
    db.commit()

    first = service.ask(db, session, "Explain the method.")
    db.refresh(session)

    assert session.compressed_until_message_id == 5
    assert session.memory_updated_at is not None
    assert len(fake_llm.summary_calls) == 1
    assert [message["content"] for message in fake_llm.summary_calls[0][0]] == [f"turn {index}" for index in range(1, 6)]
    assert first["retrieval_metadata"]["recent_message_ids"] == [6, 7, 8, 9, 10, 11]

    for index in range(3):
        db.add(ChatMessage(session_id=session.id, role="user", content=f"new turn {index + 1}"))
    db.commit()

    second = service.ask(db, session, "Continue with the result.")
    db.refresh(session)

    assert session.compressed_until_message_id == 10
    assert len(fake_llm.summary_calls) == 2
    assert second["retrieval_metadata"]["compressed_until_message_id"] == 10
    assert fake_llm.summary_calls[1][1]


def test_old_session_without_boundary_is_compatible(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    paper = seed_paper(db)
    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb", openai_api_key="")
    service = PaperChatService(settings)
    service.llm = FakePaperChatLLM()
    session = ChatSession(
        id="chat-old",
        library_id=paper.library_id,
        paper_id=paper.id,
        title="old",
        memory_summary="old summary",
        compressed_until_message_id=None,
    )
    db.add(session)
    for index in range(11):
        db.add(ChatMessage(session_id=session.id, role="user", content=f"legacy turn {index + 1}"))
    db.commit()

    result = service.ask(db, session, "What did we discuss?")
    db.refresh(session)

    assert result["answer"]
    assert session.compressed_until_message_id == 5
    assert session.memory_summary.startswith("old summary")


def test_paper_chat_rewrite_metadata_uses_recent_context(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.services.vector_store.lancedb", None)
    db = make_session()
    paper = seed_paper(db)
    settings = Settings(storage_dir=tmp_path / "storage", lancedb_path=tmp_path / "storage" / "lancedb", openai_api_key="")
    service = PaperChatService(settings)
    session = service.get_or_create_session(db, paper)
    db.add(ChatMessage(session_id=session.id, role="user", content="We were discussing TinyBench accuracy."))
    db.commit()

    result = service.ask(db, session, "What about that metric?")

    assert result["retrieval_metadata"]["original_question"] == "What about that metric?"
    assert "TinyBench" in result["retrieval_metadata"]["rewritten_query"]
    assert result["retrieval_metadata"]["rewrite_source"] == "fallback"
    assert result["retrieval_metadata"]["recent_message_ids"] == [1]


def test_delete_paper_cascades_chat_records(tmp_path: Path) -> None:
    db = make_session()
    paper = seed_paper(db)
    session = ChatSession(id="chat-1", library_id="library-1", paper_id=paper.id, title="paper.pdf")
    db.add(session)
    db.add(ChatMessage(session_id="chat-1", role="user", content="question"))
    db.commit()

    db.delete(paper)
    db.commit()

    assert db.query(ChatSession).filter(ChatSession.paper_id == "paper-1").count() == 0
    assert db.query(ChatMessage).filter(ChatMessage.session_id == "chat-1").count() == 0
