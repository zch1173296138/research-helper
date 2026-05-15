from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


StrategyName = Literal["baseline-current", "current-evidence", "old-code-api"]


@dataclass
class EvaluationCase:
    id: str
    category: str
    question: str
    should_answer: bool
    library_id: str | None = None
    paper_ids: list[str] = field(default_factory=list)
    expected_points: list[str] = field(default_factory=list)
    supporting_quotes: list[str] = field(default_factory=list)
    supporting_chunk_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("raw", None)
        return payload


@dataclass
class CaseValidationError:
    line_number: int
    message: str


@dataclass
class StrategyOutput:
    strategy: str
    answer: str = ""
    citations: list[dict[str, Any]] = field(default_factory=list)
    retrieved_chunk_ids: list[str] = field(default_factory=list)
    candidate_chunk_ids: list[str] = field(default_factory=list)
    accepted_chunk_ids: list[str] = field(default_factory=list)
    final_context_chunk_ids: list[str] = field(default_factory=list)
    evidence_decisions: list[dict[str, Any]] = field(default_factory=list)
    missing_evidence: bool = False
    latency_ms: float = 0.0
    error: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    health: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StrategyMetrics:
    expected_point_coverage: float | None = None
    expected_points_found: list[str] = field(default_factory=list)
    missing_evidence_correct: bool | None = None
    citation_validity: float | None = None
    candidate_recall: float | None = None
    final_context_recall: float | None = None
    citation_recall: float | None = None
    citation_precision: float | None = None
    quote_support_recall: float | None = None
    reference_contamination: bool = False
    accepted_evidence_precision: float | None = None
    accepted_evidence_recall: float | None = None
    latency_ms: float = 0.0
    error: str | None = None
    judge_source: str | None = None
    llm_judge: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CaseResult:
    case: EvaluationCase
    outputs: dict[str, StrategyOutput]
    metrics: dict[str, StrategyMetrics]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case.to_dict(),
            "outputs": {name: output.to_dict() for name, output in self.outputs.items()},
            "metrics": {name: metrics.to_dict() for name, metrics in self.metrics.items()},
        }


@dataclass
class RunConfig:
    case_file: str
    output_dir: str
    baseline_strategy: str
    comparison_strategy: str
    mode: str
    current_api_url: str | None = None
    old_code_api_url: str | None = None
    deterministic_local: bool = False
    llm_judge: bool = False
    top_k: int = 8
    case_filter: list[str] = field(default_factory=list)
    git_revision: str | None = None
    case_file_sha256: str | None = None
    timestamp: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
