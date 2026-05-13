import json
from pathlib import Path
from typing import Any

from backend.app.core.config import Settings
from backend.app.evaluation.adapters import BaselineCurrentAdapter, CurrentEvidenceAdapter
from backend.app.evaluation.cases import EvaluationCaseLoadError, load_cases
from backend.app.evaluation.metrics import score_output
from backend.app.evaluation.reports import write_reports
from backend.app.evaluation.runner import execute_cases
from backend.app.evaluation.types import CaseResult, EvaluationCase, RunConfig, StrategyMetrics, StrategyOutput
from backend.app.services.retrieval import RetrievalResult
from backend.app.services.vector_store import RetrievedChunk


def test_load_cases_validates_required_fields(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text('{"id":"missing-question","category":"method","should_answer":true}\n', encoding="utf-8")

    try:
        load_cases(path)
    except EvaluationCaseLoadError as exc:
        assert "line 1" in str(exc)
        assert "question" in str(exc)
    else:
        raise AssertionError("Expected EvaluationCaseLoadError")


def test_load_cases_preserves_metadata_and_filters(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "case-1",
                        "category": "method",
                        "question": "What is the method?",
                        "should_answer": True,
                        "library_id": "library-1",
                        "paper_ids": ["paper-1"],
                        "expected_points": ["graph"],
                        "supporting_quotes": ["graph representation"],
                        "tags": ["smoke"],
                    }
                ),
                json.dumps({"id": "case-2", "category": "result", "question": "Result?", "should_answer": True}),
            ]
        ),
        encoding="utf-8",
    )

    cases = load_cases(path, ["smoke"])

    assert len(cases) == 1
    assert cases[0].id == "case-1"
    assert cases[0].paper_ids == ["paper-1"]
    assert cases[0].raw["library_id"] == "library-1"


def test_score_output_marks_not_applicable_evidence_metrics_for_baseline() -> None:
    case = EvaluationCase(
        id="case-1",
        category="method",
        question="What is the method?",
        should_answer=True,
        expected_points=["graph"],
        supporting_chunk_ids=["chunk-1"],
    )
    output = StrategyOutput(
        strategy="baseline-current",
        answer="The method uses a graph representation.",
        citations=[{"chunk_id": "chunk-1", "section_type": "method", "quote": "graph representation"}],
        retrieved_chunk_ids=["chunk-1"],
        final_context_chunk_ids=["chunk-1"],
    )

    metrics = score_output(case, output, {"chunk-1"})

    assert metrics.expected_point_coverage == 1.0
    assert metrics.final_context_recall == 1.0
    assert metrics.citation_validity == 1.0
    assert metrics.accepted_evidence_precision is None
    assert metrics.accepted_evidence_recall is None


def test_score_output_scores_current_evidence_and_reference_contamination() -> None:
    case = EvaluationCase(
        id="case-1",
        category="method",
        question="What is the method?",
        should_answer=True,
        supporting_chunk_ids=["chunk-1"],
    )
    output = StrategyOutput(
        strategy="current-evidence",
        answer="The method uses evidence screening. [C1]",
        citations=[{"chunk_id": "chunk-ref", "section_type": "references", "quote": "Reference entry"}],
        candidate_chunk_ids=["chunk-1", "chunk-ref"],
        accepted_chunk_ids=["chunk-1"],
        final_context_chunk_ids=["chunk-1"],
        evidence_decisions=[{"chunk_id": "chunk-1", "decision": "accept"}],
    )

    metrics = score_output(case, output, {"chunk-1", "chunk-ref"})

    assert metrics.candidate_recall == 1.0
    assert metrics.accepted_evidence_precision == 1.0
    assert metrics.accepted_evidence_recall == 1.0
    assert metrics.reference_contamination is True


def test_score_no_answer_behavior() -> None:
    case = EvaluationCase(id="case-1", category="no-answer", question="Unsupported?", should_answer=False)
    output = StrategyOutput(strategy="current-evidence", answer="Insufficient evidence was found.", missing_evidence=True)

    metrics = score_output(case, output)

    assert metrics.missing_evidence_correct is True


def test_write_reports_creates_all_outputs(tmp_path: Path) -> None:
    case = EvaluationCase(id="case-1", category="method", question="What?", should_answer=True)
    output = StrategyOutput(strategy="baseline-current", answer="Answer")
    metrics = StrategyMetrics(expected_point_coverage=1.0)
    result = CaseResult(case=case, outputs={output.strategy: output}, metrics={output.strategy: metrics})
    config = RunConfig(
        case_file="cases.jsonl",
        output_dir=str(tmp_path),
        baseline_strategy="baseline-current",
        comparison_strategy="current-evidence",
        mode="in-process",
        timestamp="2026-05-13T00:00:00Z",
    )

    paths = write_reports([result], config, tmp_path)

    assert Path(paths["raw_results"]).exists()
    assert Path(paths["aggregate_metrics"]).exists()
    assert Path(paths["report"]).read_text(encoding="utf-8").startswith("# RAG A/B Evaluation Report")
    assert Path(paths["run_config"]).exists()


def test_baseline_adapter_bypasses_evidence_decisions() -> None:
    case = EvaluationCase(
        id="case-1",
        category="method",
        question="What is the method?",
        should_answer=True,
        library_id="library-1",
    )
    chunk = RetrievedChunk(
        chunk_id="chunk-1",
        paper_id="paper-1",
        filename="paper.pdf",
        section_title="Method",
        text="The method uses a graph representation.",
        section_type="method",
    )

    class FakeRetriever:
        def search(self, *_args: Any, **_kwargs: Any) -> RetrievalResult:
            return RetrievalResult(chunks=[chunk], metadata={"returned_chunk_ids": ["chunk-1"]})

    class FakeLlm:
        def answer_with_citations(self, question: str, chunks: list[RetrievedChunk]) -> dict[str, Any]:
            assert question == case.question
            assert chunks == [chunk]
            return {"answer": "The method uses a graph representation.", "citations": [{"chunk_id": "chunk-1"}]}

    output = BaselineCurrentAdapter(Settings(), retriever=FakeRetriever(), llm=FakeLlm()).run(None, case, top_k=4)

    assert output.error is None
    assert output.retrieved_chunk_ids == ["chunk-1"]
    assert output.final_context_chunk_ids == ["chunk-1"]
    assert output.evidence_decisions == []


def test_current_evidence_adapter_preserves_evidence_metadata(monkeypatch) -> None:
    case = EvaluationCase(
        id="case-1",
        category="method",
        question="What is the method?",
        should_answer=True,
        library_id="library-1",
    )

    class FakeEvidenceRagService:
        def __init__(self, *_args: Any, **_kwargs: Any):
            pass

        def answer_library_chat(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {
                "answer": "The accepted evidence supports the answer.",
                "citations": [{"chunk_id": "chunk-accepted"}],
                "missing_evidence": False,
                "retrieval_metadata": {
                    "candidate_chunk_ids": ["chunk-candidate", "chunk-accepted"],
                    "accepted_chunk_ids": ["chunk-accepted"],
                    "final_context_chunk_ids": ["chunk-accepted"],
                    "evidence_decisions": [
                        {"chunk_id": "chunk-accepted", "decision": "accept"},
                        {"chunk_id": "chunk-candidate", "decision": "reject"},
                    ],
                    "judge_source": "fake",
                },
            }

    monkeypatch.setattr("backend.app.evaluation.adapters.EvidenceRagService", FakeEvidenceRagService)

    output = CurrentEvidenceAdapter(Settings(), llm=object()).run(None, case, top_k=4)

    assert output.error is None
    assert output.candidate_chunk_ids == ["chunk-candidate", "chunk-accepted"]
    assert output.accepted_chunk_ids == ["chunk-accepted"]
    assert output.final_context_chunk_ids == ["chunk-accepted"]
    assert output.evidence_decisions == [
        {"chunk_id": "chunk-accepted", "decision": "accept"},
        {"chunk_id": "chunk-candidate", "decision": "reject"},
    ]


def test_execute_cases_keeps_running_when_one_strategy_fails() -> None:
    case = EvaluationCase(
        id="case-1",
        category="method",
        question="What is the method?",
        should_answer=True,
        expected_points=["graph"],
        supporting_chunk_ids=["chunk-1"],
    )

    class SuccessfulAdapter:
        name = "baseline-current"

        def run(self, *_args: Any, **_kwargs: Any) -> StrategyOutput:
            return StrategyOutput(
                strategy=self.name,
                answer="The method uses a graph representation.",
                retrieved_chunk_ids=["chunk-1"],
                final_context_chunk_ids=["chunk-1"],
            )

    class FailingAdapter:
        name = "current-evidence"

        def run(self, *_args: Any, **_kwargs: Any) -> StrategyOutput:
            raise RuntimeError("adapter failed")

    results = execute_cases([case], SuccessfulAdapter(), FailingAdapter(), db=None, top_k=4)

    assert len(results) == 1
    assert set(results[0].outputs) == {"baseline-current", "current-evidence"}
    assert results[0].outputs["baseline-current"].error is None
    assert results[0].outputs["current-evidence"].error == "adapter failed"
    assert results[0].metrics["baseline-current"].accepted_evidence_precision is None
    assert results[0].metrics["current-evidence"].error == "adapter failed"
