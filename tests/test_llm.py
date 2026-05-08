import time
from types import SimpleNamespace

from backend.app.core.config import Settings
from backend.app.services.llm import LLMService
from backend.app.services.vector_store import RetrievedChunk


def test_answer_without_evidence_refuses() -> None:
    service = LLMService(Settings(openai_api_key=""))
    result = service.answer_with_citations("What is the method?", [])
    assert result["missing_evidence"] is True
    assert "未在已导入文献中找到依据" in result["answer"]


def test_summarize_falls_back_when_llm_times_out() -> None:
    class SlowCompletions:
        def create(self, **_: object) -> object:
            time.sleep(2)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=SlowCompletions()))
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            filename="paper.pdf",
            section_title="Abstract",
            text="This paper studies networked sensors and TinyOS.",
        )
    ]

    started = time.monotonic()
    summary = service.summarize_paper("paper.pdf", chunks)

    assert time.monotonic() - started < 1.8
    assert summary["filename"] == "paper.pdf"
    assert "networked sensors" in summary["research_question"]
