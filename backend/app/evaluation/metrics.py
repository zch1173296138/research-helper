from __future__ import annotations

import re
from typing import Any

from backend.app.evaluation.types import EvaluationCase, StrategyMetrics, StrategyOutput


INSUFFICIENT_PATTERNS = (
    "missing",
    "insufficient evidence",
    "not enough evidence",
    "not found",
    "未找到",
    "没有找到",
    "证据不足",
    "依据不足",
    "未在",
)


REFERENCE_PATTERNS = ("references", "bibliography", "参考文献")


def score_output(case: EvaluationCase, output: StrategyOutput, known_chunk_ids: set[str] | None = None) -> StrategyMetrics:
    known_chunk_ids = known_chunk_ids or set()
    support_ids = set(case.supporting_chunk_ids)
    citation_ids = citation_chunk_ids(output)
    answer_source_ids = answer_source_chunk_ids(output)
    final_ids = set(output.final_context_chunk_ids or output.retrieved_chunk_ids)
    candidate_ids = set(output.candidate_chunk_ids)
    accepted_ids = set(output.accepted_chunk_ids)

    metrics = StrategyMetrics(
        latency_ms=output.latency_ms,
        error=output.error,
        judge_source=str(output.raw_metadata.get("judge_source") or "") or None,
    )
    metrics.expected_points_found = expected_points_found(case.expected_points, output.answer)
    metrics.expected_point_coverage = ratio(len(metrics.expected_points_found), len(case.expected_points))
    metrics.missing_evidence_correct = score_missing_evidence(case, output)
    metrics.citation_validity = citation_validity(output, known_chunk_ids)
    metrics.citation_count = len(citation_ids)
    metrics.answer_source_count = len(answer_source_ids)
    metrics.candidate_recall = recall(support_ids, candidate_ids) if support_ids and candidate_ids else None
    metrics.final_context_recall = recall(support_ids, final_ids) if support_ids and final_ids else None
    metrics.citation_recall = recall(support_ids, citation_ids) if support_ids and citation_ids else None
    metrics.citation_precision = precision(citation_ids, support_ids) if support_ids and citation_ids else None
    metrics.answer_source_recall = recall(support_ids, answer_source_ids) if support_ids else None
    metrics.answer_source_precision = precision(answer_source_ids, support_ids) if support_ids and answer_source_ids else None
    metrics.quote_support_recall = quote_support_recall(case, output)
    metrics.reference_contamination = has_reference_contamination(output)
    if output.evidence_decisions:
        metrics.accepted_evidence_precision = precision(accepted_ids, support_ids) if support_ids else None
        metrics.accepted_evidence_recall = recall(support_ids, accepted_ids) if support_ids else None
    return metrics


def aggregate_metrics(results: list[dict[str, StrategyMetrics]]) -> dict[str, Any]:
    by_strategy: dict[str, list[StrategyMetrics]] = {}
    for result in results:
        for strategy, metrics in result.items():
            by_strategy.setdefault(strategy, []).append(metrics)

    aggregate: dict[str, Any] = {}
    for strategy, rows in by_strategy.items():
        metrics = {
            "case_count": len(rows),
            "error_count": sum(1 for row in rows if row.error),
            "avg_latency_ms": average([row.latency_ms for row in rows]),
            "avg_expected_point_coverage": average_not_none([row.expected_point_coverage for row in rows]),
            "missing_evidence_accuracy": bool_rate([row.missing_evidence_correct for row in rows]),
            "avg_candidate_recall": average_not_none([row.candidate_recall for row in rows]),
            "avg_final_context_recall": average_not_none([row.final_context_recall for row in rows]),
            "avg_citation_count": average([float(row.citation_count) for row in rows]),
            "avg_citation_recall": average_not_none([row.citation_recall for row in rows]),
            "avg_citation_precision": average_not_none([row.citation_precision for row in rows]),
            "avg_answer_source_count": average([float(row.answer_source_count) for row in rows]),
            "avg_answer_source_recall": average_not_none([row.answer_source_recall for row in rows]),
            "avg_answer_source_precision": average_not_none([row.answer_source_precision for row in rows]),
            "avg_quote_support_recall": average_not_none([row.quote_support_recall for row in rows]),
            "reference_contamination_rate": average([1.0 if row.reference_contamination else 0.0 for row in rows]),
            "avg_accepted_evidence_precision": average_not_none([row.accepted_evidence_precision for row in rows]),
            "avg_accepted_evidence_recall": average_not_none([row.accepted_evidence_recall for row in rows]),
        }
        metrics["avg_citation_f1"] = f1_score(metrics["avg_citation_recall"], metrics["avg_citation_precision"])
        aggregate[strategy] = metrics
    return aggregate


def expected_points_found(expected_points: list[str], answer: str) -> list[str]:
    answer_normalized = normalize_text(answer)
    found: list[str] = []
    for point in expected_points:
        if matches_expected_point(point, answer_normalized):
            found.append(point)
    return found


def matches_expected_point(point: str, answer_normalized: str) -> bool:
    if point.startswith("re:"):
        pattern = point[3:]
        return re.search(pattern, answer_normalized, flags=re.IGNORECASE) is not None
    return normalize_text(point) in answer_normalized


def score_missing_evidence(case: EvaluationCase, output: StrategyOutput) -> bool | None:
    if case.should_answer:
        return None
    answer = normalize_text(output.answer)
    says_insufficient = output.missing_evidence or any(pattern in answer for pattern in INSUFFICIENT_PATTERNS)
    return bool(says_insufficient)


def citation_validity(output: StrategyOutput, known_chunk_ids: set[str]) -> float | None:
    ids = citation_chunk_ids(output)
    if not ids:
        return None
    if known_chunk_ids:
        valid = [chunk_id for chunk_id in ids if chunk_id in known_chunk_ids]
    elif output.accepted_chunk_ids:
        accepted = set(output.accepted_chunk_ids)
        valid = [chunk_id for chunk_id in ids if chunk_id in accepted]
    else:
        valid = [chunk_id for chunk_id in ids if chunk_id]
    return ratio(len(valid), len(ids))


def quote_support_recall(case: EvaluationCase, output: StrategyOutput) -> float | None:
    if not case.supporting_quotes:
        return None
    haystack = normalize_text(
        "\n".join(
            [output.answer]
            + [str(citation.get("quote") or "") for citation in output.citations]
            + [str(chunk.get("text") or "") for chunk in returned_chunk_metadata(output)]
        )
    )
    found = sum(1 for quote in case.supporting_quotes if normalize_text(quote) in haystack)
    return ratio(found, len(case.supporting_quotes))


def has_reference_contamination(output: StrategyOutput) -> bool:
    for citation in output.citations:
        section = " ".join(
            str(citation.get(key) or "")
            for key in ("section_title", "section_path", "section_type")
        ).lower()
        if any(pattern in section for pattern in REFERENCE_PATTERNS):
            return True
    for decision in output.evidence_decisions:
        section = str(decision.get("section") or decision.get("section_title") or "").lower()
        if any(pattern in section for pattern in REFERENCE_PATTERNS):
            return True
    for chunk in returned_chunk_metadata(output):
        section = " ".join(
            str(chunk.get(key) or "")
            for key in ("section_title", "section_path", "section_type")
        ).lower()
        if any(pattern in section for pattern in REFERENCE_PATTERNS):
            return True
    return False


def citation_chunk_ids(output: StrategyOutput) -> set[str]:
    return {str(citation.get("chunk_id")) for citation in output.citations if citation.get("chunk_id")}


def answer_source_chunk_ids(output: StrategyOutput) -> set[str]:
    ids = {str(item).strip() for item in output.answer_source_chunk_ids if str(item).strip()}
    metadata_value = output.raw_metadata.get("answer_source_chunk_ids")
    if isinstance(metadata_value, list):
        ids.update(str(item).strip() for item in metadata_value if str(item).strip())
    return ids


def returned_chunk_metadata(output: StrategyOutput) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for key in ("returned_chunks", "candidate_chunks", "accepted_chunks", "final_context_chunks"):
        value = output.raw_metadata.get(key)
        if isinstance(value, list):
            chunks.extend(item for item in value if isinstance(item, dict))
    return chunks


def recall(expected: set[str], observed: set[str]) -> float:
    return ratio(len(expected.intersection(observed)), len(expected))


def precision(observed: set[str], expected: set[str]) -> float:
    return ratio(len(expected.intersection(observed)), len(observed))


def f1_score(recall_value: float | None, precision_value: float | None) -> float | None:
    if recall_value is None or precision_value is None:
        return None
    denominator = recall_value + precision_value
    if denominator <= 0:
        return 0.0
    return round(2 * recall_value * precision_value / denominator, 4)


def ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def average_not_none(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return average(present)


def bool_rate(values: list[bool | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return round(sum(1 for value in present if value) / len(present), 4)
