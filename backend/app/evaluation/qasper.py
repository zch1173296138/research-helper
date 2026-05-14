from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DATASET = "allenai/qasper"
CONFIG = "qasper"
SPLIT = "validation"
DATASET_SERVER = "https://datasets-server.huggingface.co"
DEFAULT_OUTPUT = "evals/rag_ab/qasper_validation_cases.jsonl"
DEFAULT_LIMIT = 30
DEFAULT_NO_ANSWER_TARGET = 5


@dataclass(frozen=True)
class QasperSource:
    dataset: str = DATASET
    config: str = CONFIG
    split: str = SPLIT
    paper_id: str = ""
    question_id: str = ""
    annotation_ids: tuple[str, ...] = ()
    title: str = ""


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rows = fetch_qasper_rows(args.dataset_server, args.dataset, args.config, args.split)
    cases = convert_qasper_rows(
        rows,
        limit=args.limit,
        no_answer_target=args.no_answer_target,
        dataset=args.dataset,
        config=args.config,
        split=args.split,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(cases, output_path)
    print(json.dumps({"output": str(output_path), "case_count": len(cases)}, ensure_ascii=False, indent=2))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert QASPER validation examples into RAG A/B JSONL cases.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--no-answer-target", type=int, default=DEFAULT_NO_ANSWER_TARGET)
    parser.add_argument("--dataset-server", default=DATASET_SERVER)
    parser.add_argument("--dataset", default=DATASET)
    parser.add_argument("--config", default=CONFIG)
    parser.add_argument("--split", default=SPLIT)
    return parser.parse_args(argv)


def fetch_qasper_rows(
    dataset_server: str = DATASET_SERVER,
    dataset: str = DATASET,
    config: str = CONFIG,
    split: str = SPLIT,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        params = urllib.parse.urlencode(
            {
                "dataset": dataset,
                "config": config,
                "split": split,
                "offset": offset,
                "length": page_size,
            }
        )
        url = f"{dataset_server.rstrip('/')}/rows?{params}"
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for item in payload.get("rows", []):
            row = item.get("row")
            if isinstance(row, dict):
                rows.append(row)
        total = int(payload.get("num_rows_total") or len(rows))
        if len(rows) >= total or not payload.get("rows"):
            break
        offset += page_size
    return rows


def convert_qasper_rows(
    rows: list[dict[str, Any]],
    limit: int = DEFAULT_LIMIT,
    no_answer_target: int = DEFAULT_NO_ANSWER_TARGET,
    dataset: str = DATASET,
    config: str = CONFIG,
    split: str = SPLIT,
) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be positive")
    answerable: list[dict[str, Any]] = []
    no_answer: list[dict[str, Any]] = []

    for row in rows:
        for qas_item in iter_qasper_questions(row):
            source = QasperSource(
                dataset=dataset,
                config=config,
                split=split,
                paper_id=str(row.get("id") or ""),
                question_id=qas_item["question_id"],
                annotation_ids=tuple(qas_item["annotation_ids"]),
                title=str(row.get("title") or ""),
            )
            converted = convert_qasper_question(qas_item, source)
            if converted is None:
                continue
            if converted["should_answer"]:
                answerable.append(converted)
            else:
                no_answer.append(converted)

    selected_no_answer_count = min(max(no_answer_target, 0), len(no_answer), limit)
    selected_answerable_count = limit - selected_no_answer_count
    selected = answerable[:selected_answerable_count] + no_answer[:selected_no_answer_count]
    return assign_case_ids(selected[:limit])


def iter_qasper_questions(row: dict[str, Any]) -> list[dict[str, Any]]:
    qas = row.get("qas")
    if not isinstance(qas, dict):
        return []
    questions = qas.get("question") or []
    question_ids = qas.get("question_id") or []
    answers = qas.get("answers") or []
    items: list[dict[str, Any]] = []
    for index, question in enumerate(questions):
        answer_group = answers[index] if index < len(answers) and isinstance(answers[index], dict) else {}
        annotation_ids = [str(item) for item in answer_group.get("annotation_id", []) if str(item).strip()]
        items.append(
            {
                "question": str(question or "").strip(),
                "question_id": str(question_ids[index] if index < len(question_ids) else "").strip(),
                "answers": answer_group.get("answer", []) if isinstance(answer_group.get("answer"), list) else [],
                "annotation_ids": annotation_ids,
            }
        )
    return items


def convert_qasper_question(qas_item: dict[str, Any], source: QasperSource) -> dict[str, Any] | None:
    question = str(qas_item.get("question") or "").strip()
    if not question or len(question) > 240:
        return None
    answers = [answer for answer in qas_item.get("answers", []) if isinstance(answer, dict)]
    if answers and all(bool(answer.get("unanswerable")) for answer in answers):
        return base_case(question, False, source, category="no-answer")

    expected_points = collect_expected_points(answers)
    supporting_quotes = collect_supporting_quotes(answers)
    if not expected_points or not supporting_quotes:
        return None

    case = base_case(question, True, source, category=classify_question(question))
    case["expected_points"] = expected_points[:4]
    case["supporting_quotes"] = supporting_quotes[:3]
    return case


def base_case(question: str, should_answer: bool, source: QasperSource, category: str) -> dict[str, Any]:
    tags = ["qasper", "public-benchmark", category]
    if not should_answer:
        tags.append("no-answer")
    notes = (
        f"QASPER {source.split} case from paper {source.paper_id}; "
        f"question {source.question_id}; title: {source.title}"
    )
    return {
        "id": "qasper-val-pending",
        "category": category,
        "question": question,
        "should_answer": should_answer,
        "paper_ids": [],
        "expected_points": [],
        "supporting_quotes": [],
        "supporting_chunk_ids": [],
        "tags": tags,
        "notes": notes,
        "source_dataset": source.dataset,
        "source_config": source.config,
        "source_split": source.split,
        "source_paper_id": source.paper_id,
        "source_question_id": source.question_id,
        "source_annotation_ids": list(source.annotation_ids),
        "source_title": source.title,
    }


def collect_expected_points(answers: list[dict[str, Any]]) -> list[str]:
    points: list[str] = []
    for answer in answers:
        if answer.get("unanswerable"):
            continue
        for span in answer.get("extractive_spans") or []:
            append_unique(points, clean_answer_point(span), max_length=180)
        free_form = clean_answer_point(answer.get("free_form_answer"))
        append_unique(points, free_form, max_length=180)
        yes_no = answer.get("yes_no")
        if yes_no is True:
            append_unique(points, "yes", max_length=180)
        elif yes_no is False:
            append_unique(points, "no", max_length=180)
    return points


def collect_supporting_quotes(answers: list[dict[str, Any]]) -> list[str]:
    quotes: list[str] = []
    for answer in answers:
        if answer.get("unanswerable"):
            continue
        for field in ("highlighted_evidence", "evidence"):
            for quote in answer.get(field) or []:
                cleaned = clean_text(quote)
                if is_textual_support(cleaned):
                    append_unique(quotes, cleaned, max_length=600)
    return quotes


def classify_question(question: str) -> str:
    lowered = question.lower()
    if any(token in lowered for token in ("result", "perform", "score", "accuracy", "improvement", "outperform")):
        return "result"
    if any(token in lowered for token in ("dataset", "data set", "corpus", "benchmark")):
        return "dataset"
    if any(token in lowered for token in ("method", "model", "approach", "architecture", "algorithm")):
        return "method"
    if any(token in lowered for token in ("why", "how", "what")):
        return "paper-qa"
    return "paper-qa"


def assign_case_ids(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assigned: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        updated = dict(case)
        updated["id"] = f"qasper-val-{index:04d}"
        assigned.append(updated)
    return assigned


def write_jsonl(cases: list[dict[str, Any]], output_path: Path) -> None:
    payload = "\n".join(json.dumps(case, ensure_ascii=False, sort_keys=True) for case in cases)
    output_path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def append_unique(items: list[str], value: str, max_length: int) -> None:
    cleaned = clean_text(value)
    if not cleaned or len(cleaned) > max_length:
        return
    if cleaned.lower() in {item.lower() for item in items}:
        return
    items.append(cleaned)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def clean_answer_point(value: Any) -> str:
    text = clean_text(value)
    text = re.sub(r"\b(?:BIB|FIG|TAB)REF\d+\b", "", text)
    text = re.sub(r"\s+", " ", text).strip(" ,;:.")
    if not text:
        return ""
    if len(text) < 3:
        return ""
    if not re.search(r"[A-Za-z0-9]", text):
        return ""
    return text


def is_textual_support(value: str) -> bool:
    if not value:
        return False
    lowered = value.lower()
    if lowered.startswith("float selected:"):
        return False
    if re.fullmatch(r".*\.(png|jpg|jpeg|gif)", lowered):
        return False
    return len(value.split()) >= 5


if __name__ == "__main__":
    raise SystemExit(main())
