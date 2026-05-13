from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.evaluation.types import CaseValidationError, EvaluationCase


REQUIRED_FIELDS = ("id", "category", "question", "should_answer")
LIST_FIELDS = ("paper_ids", "expected_points", "supporting_quotes", "supporting_chunk_ids", "tags")


class EvaluationCaseLoadError(ValueError):
    def __init__(self, errors: list[CaseValidationError]):
        self.errors = errors
        message = "; ".join(f"line {error.line_number}: {error.message}" for error in errors)
        super().__init__(message)


def load_cases(path: str | Path, case_filter: list[str] | None = None) -> list[EvaluationCase]:
    case_path = Path(path)
    errors: list[CaseValidationError] = []
    cases: list[EvaluationCase] = []
    selected = set(case_filter or [])

    for line_number, line in enumerate(case_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            errors.append(CaseValidationError(line_number, f"invalid JSON: {exc.msg}"))
            continue
        if not isinstance(payload, dict):
            errors.append(CaseValidationError(line_number, "case must be a JSON object"))
            continue
        case_errors = validate_case_payload(payload)
        errors.extend(CaseValidationError(line_number, error) for error in case_errors)
        if case_errors:
            continue
        case = case_from_payload(payload)
        if selected and case.id not in selected and case.category not in selected and not selected.intersection(case.tags):
            continue
        cases.append(case)

    if errors:
        raise EvaluationCaseLoadError(errors)
    return cases


def validate_case_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"missing required field `{field}`")
    for field in ("id", "category", "question"):
        if field in payload and not str(payload.get(field) or "").strip():
            errors.append(f"`{field}` must be a non-empty string")
    if "should_answer" in payload and not isinstance(payload["should_answer"], bool):
        errors.append("`should_answer` must be a boolean")
    if payload.get("library_id") is not None and not isinstance(payload.get("library_id"), str):
        errors.append("`library_id` must be a string when provided")
    for field in LIST_FIELDS:
        if field in payload and not _is_string_list(payload[field]):
            errors.append(f"`{field}` must be a list of strings")
    return errors


def case_from_payload(payload: dict[str, Any]) -> EvaluationCase:
    return EvaluationCase(
        id=str(payload["id"]).strip(),
        category=str(payload["category"]).strip(),
        question=str(payload["question"]).strip(),
        should_answer=bool(payload["should_answer"]),
        library_id=_optional_str(payload.get("library_id")),
        paper_ids=_string_list(payload.get("paper_ids")),
        expected_points=_string_list(payload.get("expected_points")),
        supporting_quotes=_string_list(payload.get("supporting_quotes")),
        supporting_chunk_ids=_string_list(payload.get("supporting_chunk_ids")),
        tags=_string_list(payload.get("tags")),
        notes=str(payload.get("notes") or ""),
        raw=dict(payload),
    )


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None
