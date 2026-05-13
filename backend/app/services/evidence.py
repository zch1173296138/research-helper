from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.services.evidence_types import EvidenceDecision, EvidenceRagResult
from backend.app.services.llm import LLMService
from backend.app.services.retrieval import HybridRetriever
from backend.app.services.vector_store import RetrievedChunk


class EvidenceRagService:
    def __init__(
        self,
        settings: Settings,
        retriever: HybridRetriever | None = None,
        llm: LLMService | None = None,
    ):
        self.settings = settings
        self.retriever = retriever or HybridRetriever(settings)
        self.llm = llm or LLMService(settings)

    def gather(
        self,
        db: Session,
        library_id: str,
        question: str,
        paper_ids: list[str] | None = None,
        top_k: int = 8,
        enable_second_pass: bool = True,
    ) -> EvidenceRagResult:
        candidate_k = max(top_k * 3, 20)
        retrieval = self.retriever.search(
            db,
            library_id,
            question,
            paper_ids=paper_ids,
            top_k=candidate_k,
            enable_second_pass=enable_second_pass,
        )
        candidates = retrieval.chunks
        decisions, judge_source = self._judge(question, candidates, top_k)
        by_id = {chunk.chunk_id: chunk for chunk in candidates}
        accepted_chunks = [
            by_id[decision.chunk_id]
            for decision in decisions
            if decision.decision == "accept" and decision.chunk_id in by_id
        ]
        final_context_chunks = accepted_chunks[:top_k]
        return EvidenceRagResult(
            question=question,
            candidates=candidates,
            decisions=decisions,
            accepted_chunks=accepted_chunks,
            final_context_chunks=final_context_chunks,
            retrieval_metadata={
                **retrieval.metadata,
                "candidate_k": candidate_k,
                "requested_top_k": top_k,
            },
            judge_source=judge_source,
        )

    def answer_paper_chat(
        self,
        db: Session,
        library_id: str,
        retrieval_question: str,
        original_question: str,
        paper_ids: list[str],
        top_k: int,
        history: list[dict[str, str]],
        memory_summary: str,
    ) -> dict[str, Any]:
        evidence = self.gather(
            db,
            library_id,
            retrieval_question,
            paper_ids=paper_ids,
            top_k=top_k,
            enable_second_pass=True,
        )
        if hasattr(self.llm, "answer_paper_chat_with_evidence"):
            answer = self.llm.answer_paper_chat_with_evidence(
                original_question,
                evidence.final_context_chunks,
                evidence.decisions,
                history,
                memory_summary,
            )
        else:
            answer = self.llm.answer_paper_chat(
                original_question,
                evidence.final_context_chunks,
                history,
                memory_summary,
            )
        return {
            **answer,
            "evidence": evidence,
            "retrieval_metadata": evidence.metadata(),
        }

    def answer_library_chat(
        self,
        db: Session,
        library_id: str,
        question: str,
        paper_ids: list[str] | None,
        top_k: int,
    ) -> dict[str, Any]:
        evidence = self.gather(
            db,
            library_id,
            question,
            paper_ids=paper_ids,
            top_k=top_k,
            enable_second_pass=True,
        )
        if hasattr(self.llm, "answer_with_evidence"):
            answer = self.llm.answer_with_evidence(question, evidence.final_context_chunks, evidence.decisions)
        else:
            answer = self.llm.answer_with_citations(question, evidence.final_context_chunks)
        return {
            **answer,
            "evidence": evidence,
            "retrieval_metadata": evidence.metadata(),
        }

    def _judge(
        self,
        question: str,
        candidates: list[RetrievedChunk],
        top_k: int,
    ) -> tuple[list[EvidenceDecision], str]:
        if not candidates:
            return [], "empty_candidates"
        if not getattr(self.llm, "client", None) or not hasattr(self.llm, "judge_evidence"):
            return self._fallback_decisions(candidates, top_k), "fallback_ranked"
        try:
            decisions = self.llm.judge_evidence(question, candidates)
        except Exception:
            return self._fallback_decisions(candidates, top_k), "fallback_ranked"
        normalized = self._normalize_decisions(decisions, candidates)
        if not normalized:
            return self._fallback_decisions(candidates, top_k), "fallback_ranked"
        return normalized, "llm_json"

    def _fallback_decisions(self, candidates: list[RetrievedChunk], top_k: int) -> list[EvidenceDecision]:
        accepted_limit = max(1, min(top_k, len(candidates)))
        decisions: list[EvidenceDecision] = []
        for index, chunk in enumerate(candidates):
            accepted = index < accepted_limit
            summary = self._summary_from_chunk(chunk)
            decisions.append(
                EvidenceDecision(
                    chunk_id=chunk.chunk_id,
                    decision="accept" if accepted else "reject",
                    reason="Accepted by ranked fallback." if accepted else "Outside ranked fallback context.",
                    support_level="partial" if accepted else "none",
                    answerable_claims=[summary] if accepted and summary else [],
                    concise_summary=summary if accepted else "",
                    judge_source="fallback_ranked",
                )
            )
        return decisions

    def _normalize_decisions(
        self,
        decisions: list[EvidenceDecision],
        candidates: list[RetrievedChunk],
    ) -> list[EvidenceDecision]:
        valid_ids = {chunk.chunk_id for chunk in candidates}
        seen: set[str] = set()
        normalized: list[EvidenceDecision] = []
        for decision in decisions:
            if decision.chunk_id not in valid_ids or decision.chunk_id in seen:
                continue
            seen.add(decision.chunk_id)
            decision.judge_source = "llm_json"
            normalized.append(decision)
        decided = {decision.chunk_id for decision in normalized}
        for chunk in candidates:
            if chunk.chunk_id not in decided:
                normalized.append(
                    EvidenceDecision(
                        chunk_id=chunk.chunk_id,
                        decision="reject",
                        reason="LLM judge omitted this candidate.",
                        support_level="none",
                        concise_summary="",
                        judge_source="llm_json",
                    )
                )
        return normalized

    def _summary_from_chunk(self, chunk: RetrievedChunk) -> str:
        text = " ".join(chunk.text.split())
        if len(text) > 500:
            text = text[:500].rsplit(" ", 1)[0] + "..."
        section = chunk.section_path or chunk.section_title or chunk.section_type
        return f"{section}: {text}" if section else text
