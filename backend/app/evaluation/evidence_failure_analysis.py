from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = "evals/rag_ab/runs/latest/case_results.jsonl"
DEFAULT_JSON_OUTPUT = "evals/rag_ab/runs/latest/evidence_failure_analysis.json"
DEFAULT_MARKDOWN_OUTPUT = "evals/rag_ab/runs/latest/evidence_failure_analysis.md"

FAILURE_STAGES = {
    "retrieval_miss",
    "evidence_rejected_gold",
    "final_context_truncated_gold",
    "citation_selection_missed_gold",
    "ok",
    "not_applicable",
}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input)
    rows = load_case_results(input_path)
    analysis = analyze_results(rows)
    write_json_report(analysis, Path(args.json_output), input_path)
    write_markdown_report(analysis, Path(args.markdown_output), input_path)
    print(
        json.dumps(
            {
                "input": str(input_path),
                "json_output": args.json_output,
                "markdown_output": args.markdown_output,
                "case_count": len(rows),
                "row_count": len(analysis),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose where gold evidence is lost in RAG evaluation outputs.")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT)
    return parser.parse_args(argv)


def load_case_results(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def analyze_results(case_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in case_results:
        case = result.get("case") or {}
        outputs = result.get("outputs") or {}
        for strategy, output in sorted(outputs.items()):
            if isinstance(output, dict):
                rows.append(analyze_strategy(case, strategy, output))
    return rows


def analyze_strategy(case: dict[str, Any], strategy: str, output: dict[str, Any]) -> dict[str, Any]:
    supporting_chunk_ids = string_list(case.get("supporting_chunk_ids"))
    candidate_chunk_ids = output_ids(output, "candidate_chunk_ids")
    accepted_chunk_ids = output_ids(output, "accepted_chunk_ids")
    final_context_chunk_ids = output_ids(output, "final_context_chunk_ids") or output_ids(output, "retrieved_chunk_ids")
    citation_ids = citation_chunk_ids(output)

    gold = set(supporting_chunk_ids)
    final_context_hit_ids = ordered_hits(supporting_chunk_ids, final_context_chunk_ids)
    citation_hit_ids = ordered_hits(supporting_chunk_ids, citation_ids)
    gold_in_candidates = intersects(gold, candidate_chunk_ids)
    gold_in_accepted = intersects(gold, accepted_chunk_ids)
    gold_in_final_context = intersects(gold, final_context_chunk_ids)
    gold_in_citations = intersects(gold, citation_ids)

    return {
        "case_id": str(case.get("id") or ""),
        "strategy": strategy,
        "question": str(case.get("question") or ""),
        "supporting_chunk_ids": supporting_chunk_ids,
        "candidate_chunk_ids": candidate_chunk_ids,
        "accepted_chunk_ids": accepted_chunk_ids,
        "final_context_chunk_ids": final_context_chunk_ids,
        "citation_chunk_ids": citation_ids,
        "gold_position_in_final_context": gold_positions(supporting_chunk_ids, final_context_chunk_ids),
        "final_context_hit_ids": final_context_hit_ids,
        "citation_hit_ids": citation_hit_ids,
        "answer_preview": answer_preview(output),
        "citation_count": len(citation_ids),
        "final_context_count": len(final_context_chunk_ids),
        "gold_in_candidates": gold_in_candidates,
        "gold_in_accepted": gold_in_accepted,
        "gold_in_final_context": gold_in_final_context,
        "gold_in_citations": gold_in_citations,
        "failure_stage": classify_failure_stage(
            supporting_chunk_ids=supporting_chunk_ids,
            candidate_chunk_ids=candidate_chunk_ids,
            accepted_chunk_ids=accepted_chunk_ids,
            final_context_chunk_ids=final_context_chunk_ids,
            citation_chunk_ids=citation_ids,
        ),
    }


def classify_failure_stage(
    supporting_chunk_ids: list[str],
    candidate_chunk_ids: list[str],
    accepted_chunk_ids: list[str],
    final_context_chunk_ids: list[str],
    citation_chunk_ids: list[str],
) -> str:
    gold = set(supporting_chunk_ids)
    if not gold:
        return "not_applicable"

    gold_in_candidates = intersects(gold, candidate_chunk_ids)
    gold_in_accepted = intersects(gold, accepted_chunk_ids)
    gold_in_final_context = intersects(gold, final_context_chunk_ids)
    gold_in_citations = intersects(gold, citation_chunk_ids)

    if candidate_chunk_ids:
        if not gold_in_candidates:
            return "retrieval_miss"
        if not gold_in_accepted:
            return "evidence_rejected_gold"
        if not gold_in_final_context:
            return "final_context_truncated_gold"
        if not gold_in_citations:
            return "citation_selection_missed_gold"
        return "ok"

    if final_context_chunk_ids:
        if not gold_in_final_context:
            return "retrieval_miss"
        if not gold_in_citations:
            return "citation_selection_missed_gold"
        return "ok"

    return "not_applicable"


def output_ids(output: dict[str, Any], key: str) -> list[str]:
    values = string_list(output.get(key))
    if values:
        return values
    metadata = output.get("raw_metadata")
    if isinstance(metadata, dict):
        return string_list(metadata.get(key))
    return []


def citation_chunk_ids(output: dict[str, Any]) -> list[str]:
    citations = output.get("citations") or []
    if not isinstance(citations, list):
        return []
    ids: list[str] = []
    for citation in citations:
        if not isinstance(citation, dict):
            continue
        chunk_id = str(citation.get("chunk_id") or "").strip()
        if chunk_id and chunk_id not in ids:
            ids.append(chunk_id)
    return ids


def intersects(expected: set[str], observed: list[str]) -> bool:
    return bool(expected.intersection(observed))


def ordered_hits(expected_ids: list[str], observed_ids: list[str]) -> list[str]:
    expected = set(expected_ids)
    return [chunk_id for chunk_id in observed_ids if chunk_id in expected]


def gold_positions(expected_ids: list[str], final_context_ids: list[str]) -> dict[str, int | None]:
    final_positions = {chunk_id: index for index, chunk_id in enumerate(final_context_ids, start=1)}
    return {chunk_id: final_positions.get(chunk_id) for chunk_id in expected_ids}


def answer_preview(output: dict[str, Any], limit: int = 240) -> str:
    answer = " ".join(str(output.get("answer") or "").split())
    if len(answer) <= limit:
        return answer
    return answer[:limit].rsplit(" ", 1)[0] + "..."


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def write_json_report(analysis: list[dict[str, Any]], output_path: Path, input_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "input": str(input_path),
        "row_count": len(analysis),
        "stage_counts": stage_counts(analysis),
        "rows": analysis,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown_report(analysis: list[dict[str, Any]], output_path: Path, input_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Evidence Failure Analysis",
        "",
        f"- Input: `{input_path}`",
        f"- Rows: `{len(analysis)}`",
        "",
        "## Stage Counts",
        "",
        "| Failure stage | Count |",
        "| --- | ---: |",
    ]
    for stage, count in stage_counts(analysis).items():
        lines.append(f"| `{stage}` | {count} |")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Case | Strategy | Stage | Gold positions | Final hits | Citation hits | Final count | Citation count |",
            "| --- | --- | --- | --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in analysis:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['case_id']}`",
                    f"`{row['strategy']}`",
                    f"`{row['failure_stage']}`",
                    format_positions(row["gold_position_in_final_context"]),
                    format_ids(row["final_context_hit_ids"]),
                    format_ids(row["citation_hit_ids"]),
                    str(row["final_context_count"]),
                    str(row["citation_count"]),
                ]
            )
            + " |"
        )
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def stage_counts(analysis: list[dict[str, Any]]) -> dict[str, int]:
    counts = {stage: 0 for stage in sorted(FAILURE_STAGES)}
    for row in analysis:
        stage = str(row.get("failure_stage") or "not_applicable")
        counts[stage] = counts.get(stage, 0) + 1
    return counts


def format_ids(ids: list[str]) -> str:
    if not ids:
        return ""
    if len(ids) <= 3:
        return ", ".join(f"`{item}`" for item in ids)
    preview = ", ".join(f"`{item}`" for item in ids[:3])
    return f"{preview}, +{len(ids) - 3}"


def format_positions(positions: dict[str, int | None]) -> str:
    if not positions:
        return ""
    return ", ".join(f"`{chunk_id}`={position or '-'}" for chunk_id, position in positions.items())


if __name__ == "__main__":
    raise SystemExit(main())
