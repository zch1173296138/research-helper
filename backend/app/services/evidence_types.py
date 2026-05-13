from dataclasses import dataclass, field
from typing import Any, Literal

from backend.app.services.vector_store import RetrievedChunk


EvidenceDecisionValue = Literal["accept", "maybe", "reject"]
SupportLevel = Literal["direct", "partial", "background", "none"]


@dataclass
class EvidenceDecision:
    chunk_id: str
    decision: EvidenceDecisionValue
    reason: str = ""
    support_level: SupportLevel = "none"
    answerable_claims: list[str] = field(default_factory=list)
    concise_summary: str = ""
    judge_source: str = "fallback_ranked"

    def is_accepted(self) -> bool:
        return self.decision == "accept"

    def to_metadata(self, snippet_limit: int = 500) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "decision": self.decision,
            "reason": self.reason[:snippet_limit],
            "support_level": self.support_level,
            "answerable_claims": [claim[:snippet_limit] for claim in self.answerable_claims[:5]],
            "concise_summary": self.concise_summary[:snippet_limit],
            "judge_source": self.judge_source,
        }


@dataclass
class EvidenceRagResult:
    question: str
    candidates: list[RetrievedChunk]
    decisions: list[EvidenceDecision]
    accepted_chunks: list[RetrievedChunk]
    final_context_chunks: list[RetrievedChunk]
    retrieval_metadata: dict[str, Any]
    judge_source: str

    @property
    def rejected_chunk_ids(self) -> list[str]:
        return [decision.chunk_id for decision in self.decisions if decision.decision == "reject"]

    @property
    def accepted_chunk_ids(self) -> list[str]:
        return [chunk.chunk_id for chunk in self.accepted_chunks]

    @property
    def final_context_chunk_ids(self) -> list[str]:
        return [chunk.chunk_id for chunk in self.final_context_chunks]

    def metadata(self) -> dict[str, Any]:
        candidate_ids = [chunk.chunk_id for chunk in self.candidates]
        return {
            **self.retrieval_metadata,
            "evidence_pipeline": "paperqa_style",
            "candidate_chunk_ids": candidate_ids,
            "accepted_chunk_ids": self.accepted_chunk_ids,
            "rejected_chunk_ids": self.rejected_chunk_ids,
            "final_context_chunk_ids": self.final_context_chunk_ids,
            "judge_source": self.judge_source,
            "evidence_decisions": [decision.to_metadata() for decision in self.decisions],
            "evidence_summary_source": self.judge_source,
        }
