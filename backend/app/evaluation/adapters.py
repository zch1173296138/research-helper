from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Protocol

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.evaluation.types import EvaluationCase, StrategyOutput
from backend.app.services.evidence import EvidenceRagService
from backend.app.services.llm import LLMService
from backend.app.services.retrieval import HybridRetriever
from backend.app.services.vector_store import RetrievedChunk


class StrategyAdapter(Protocol):
    name: str

    def run(self, db: Session, case: EvaluationCase, top_k: int) -> StrategyOutput:
        ...


class BaselineCurrentAdapter:
    name = "baseline-current"

    def __init__(self, settings: Settings, retriever: HybridRetriever | None = None, llm: LLMService | None = None):
        self.settings = settings
        self.retriever = retriever or HybridRetriever(settings)
        self.llm = llm or LLMService(settings)

    def run(self, db: Session, case: EvaluationCase, top_k: int) -> StrategyOutput:
        started = time.perf_counter()
        try:
            library_id = require_library_id(case)
            retrieval = self.retriever.search(
                db,
                library_id,
                case.question,
                paper_ids=case.paper_ids,
                top_k=top_k,
            )
            answer = self.llm.answer_with_citations(case.question, retrieval.chunks)
            metadata = dict(retrieval.metadata)
            metadata["returned_chunks"] = [chunk_to_metadata(chunk) for chunk in retrieval.chunks]
            return StrategyOutput(
                strategy=self.name,
                answer=str(answer.get("answer") or ""),
                citations=list(answer.get("citations") or []),
                retrieved_chunk_ids=[chunk.chunk_id for chunk in retrieval.chunks],
                final_context_chunk_ids=[chunk.chunk_id for chunk in retrieval.chunks],
                missing_evidence=bool(answer.get("missing_evidence")),
                latency_ms=elapsed_ms(started),
                raw_metadata=metadata,
            )
        except Exception as exc:
            return StrategyOutput(strategy=self.name, latency_ms=elapsed_ms(started), error=str(exc))


class CurrentEvidenceAdapter:
    name = "current-evidence"

    def __init__(self, settings: Settings, llm: LLMService | None = None):
        self.settings = settings
        self.llm = llm or LLMService(settings)

    def run(self, db: Session, case: EvaluationCase, top_k: int) -> StrategyOutput:
        started = time.perf_counter()
        try:
            library_id = require_library_id(case)
            result = EvidenceRagService(self.settings, llm=self.llm).answer_library_chat(
                db,
                library_id,
                case.question,
                case.paper_ids,
                top_k=top_k,
            )
            metadata = dict(result.get("retrieval_metadata") or {})
            evidence = result.get("evidence")
            if evidence is not None:
                metadata["candidate_chunks"] = [chunk_to_metadata(chunk) for chunk in getattr(evidence, "candidates", [])]
                metadata["accepted_chunks"] = [chunk_to_metadata(chunk) for chunk in getattr(evidence, "accepted_chunks", [])]
                metadata["final_context_chunks"] = [chunk_to_metadata(chunk) for chunk in getattr(evidence, "final_context_chunks", [])]
            candidate_ids = list(metadata.get("candidate_chunk_ids") or [])
            accepted_ids = list(metadata.get("accepted_chunk_ids") or [])
            final_ids = list(metadata.get("final_context_chunk_ids") or [])
            decisions = list(metadata.get("evidence_decisions") or [])
            return StrategyOutput(
                strategy=self.name,
                answer=str(result.get("answer") or ""),
                citations=list(result.get("citations") or []),
                retrieved_chunk_ids=final_ids or [citation.get("chunk_id") for citation in result.get("citations", []) if citation.get("chunk_id")],
                candidate_chunk_ids=candidate_ids,
                accepted_chunk_ids=accepted_ids,
                final_context_chunk_ids=final_ids,
                evidence_decisions=decisions,
                missing_evidence=bool(result.get("missing_evidence")),
                latency_ms=elapsed_ms(started),
                raw_metadata=metadata,
            )
        except Exception as exc:
            return StrategyOutput(strategy=self.name, latency_ms=elapsed_ms(started), error=str(exc))


class OldCodeApiAdapter:
    name = "old-code-api"

    def __init__(self, api_url: str, library_id: str | None = None):
        self.api_url = api_url.rstrip("/")
        self.library_id = library_id

    def health(self) -> dict[str, Any]:
        try:
            payload = self._request("GET", "/api/health", None)
            return {"ok": bool(payload.get("ok")), "url": self.api_url}
        except Exception as exc:
            return {"ok": False, "url": self.api_url, "error": str(exc)}

    def run(self, db: Session, case: EvaluationCase, top_k: int) -> StrategyOutput:
        del db
        started = time.perf_counter()
        health = self.health()
        if not health.get("ok"):
            return StrategyOutput(strategy=self.name, latency_ms=elapsed_ms(started), error="old-code API health check failed", health=health)
        try:
            library_id = case.library_id or self.library_id
            if not library_id:
                raise ValueError("library_id is required for old-code API mode")
            payload = {
                "library_id": library_id,
                "question": case.question,
                "paper_ids": case.paper_ids,
                "top_k": top_k,
            }
            result = self._request("POST", "/api/chat", payload)
            metadata = dict(result.get("retrieval_metadata") or {})
            return StrategyOutput(
                strategy=self.name,
                answer=str(result.get("answer") or ""),
                citations=list(result.get("citations") or []),
                retrieved_chunk_ids=list(metadata.get("returned_chunk_ids") or []),
                final_context_chunk_ids=list(metadata.get("returned_chunk_ids") or []),
                missing_evidence=bool(result.get("missing_evidence")),
                latency_ms=elapsed_ms(started),
                raw_metadata=metadata,
                health=health,
            )
        except Exception as exc:
            return StrategyOutput(strategy=self.name, latency_ms=elapsed_ms(started), error=str(exc), health=health)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_url}{path}",
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def make_adapter(
    name: str,
    settings: Settings,
    old_code_api_url: str | None = None,
    library_id: str | None = None,
) -> StrategyAdapter:
    if name == BaselineCurrentAdapter.name:
        return BaselineCurrentAdapter(settings)
    if name == CurrentEvidenceAdapter.name:
        return CurrentEvidenceAdapter(settings)
    if name == OldCodeApiAdapter.name:
        if not old_code_api_url:
            raise ValueError("old-code-api strategy requires --old-code-api-url")
        return OldCodeApiAdapter(old_code_api_url, library_id=library_id)
    raise ValueError(f"Unknown RAG evaluation strategy: {name}")


def require_library_id(case: EvaluationCase) -> str:
    if not case.library_id:
        raise ValueError(f"case {case.id} requires library_id for in-process evaluation")
    return case.library_id


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)


def chunk_to_metadata(chunk: RetrievedChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "paper_id": chunk.paper_id,
        "filename": chunk.filename,
        "section_title": chunk.section_title,
        "section_path": chunk.section_path,
        "section_type": chunk.section_type,
        "text": chunk.text,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "retrieval_source": chunk.retrieval_source,
        "score": chunk.score,
    }


def retrieved_chunk_from_citation(citation: dict[str, Any]) -> RetrievedChunk | None:
    chunk_id = citation.get("chunk_id")
    if not chunk_id:
        return None
    return RetrievedChunk(
        chunk_id=str(chunk_id),
        paper_id=str(citation.get("paper_id") or ""),
        filename=str(citation.get("filename") or ""),
        section_title=str(citation.get("section_title") or ""),
        section_path=str(citation.get("section_path") or ""),
        section_type=str(citation.get("section_type") or "unknown"),
        text=str(citation.get("quote") or ""),
        page_start=citation.get("page_start"),
        page_end=citation.get("page_end"),
    )
