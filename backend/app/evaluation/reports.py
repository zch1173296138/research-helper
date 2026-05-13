from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.evaluation.metrics import aggregate_metrics
from backend.app.evaluation.types import CaseResult, RunConfig


def write_reports(results: list[CaseResult], config: RunConfig, output_dir: str | Path) -> dict[str, str]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    raw_path = target / "case_results.jsonl"
    aggregate_path = target / "aggregate_metrics.json"
    report_path = target / "report.md"
    config_path = target / "run_config.json"

    raw_path.write_text(
        "\n".join(json.dumps(result.to_dict(), ensure_ascii=False) for result in results) + ("\n" if results else ""),
        encoding="utf-8",
    )
    aggregate = aggregate_case_results(results)
    aggregate_path.write_text(json.dumps(aggregate, ensure_ascii=False, indent=2), encoding="utf-8")
    config_path.write_text(json.dumps(config.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(render_markdown_report(results, config, aggregate), encoding="utf-8")
    return {
        "raw_results": str(raw_path),
        "aggregate_metrics": str(aggregate_path),
        "report": str(report_path),
        "run_config": str(config_path),
    }


def aggregate_case_results(results: list[CaseResult]) -> dict[str, Any]:
    by_category: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        by_category.setdefault(result.case.category, []).append(result.metrics)
    return {
        "by_strategy": aggregate_metrics([result.metrics for result in results]),
        "by_category": {
            category: aggregate_metrics(rows)
            for category, rows in sorted(by_category.items())
        },
    }


def render_markdown_report(results: list[CaseResult], config: RunConfig, aggregate: dict[str, Any]) -> str:
    lines = [
        "# RAG A/B Evaluation Report",
        "",
        "## Run Configuration",
        "",
        f"- Cases: `{config.case_file}`",
        f"- Baseline: `{config.baseline_strategy}`",
        f"- Comparison: `{config.comparison_strategy}`",
        f"- Mode: `{config.mode}`",
        f"- Current API URL: `{config.current_api_url or 'n/a'}`",
        f"- Old-code API URL: `{config.old_code_api_url or 'n/a'}`",
        f"- Deterministic local: `{config.deterministic_local}`",
        f"- LLM judge: `{config.llm_judge}`",
        f"- top_k: `{config.top_k}`",
        f"- Output directory: `{config.output_dir}`",
        f"- Case file sha256: `{config.case_file_sha256 or 'unknown'}`",
        f"- Timestamp: `{config.timestamp}`",
        f"- Git revision: `{config.git_revision or 'unknown'}`",
        f"- Notes: {config.notes or 'n/a'}",
        "",
        "## Aggregate Metrics",
        "",
    ]
    for strategy, metrics in aggregate.get("by_strategy", aggregate).items():
        lines.extend(
            [
                f"### {strategy}",
                "",
                "| Metric | Value |",
                "| --- | --- |",
            ]
        )
        for key, value in metrics.items():
            lines.append(f"| `{key}` | {format_value(value)} |")
        lines.append("")

    if aggregate.get("by_category"):
        lines.extend(["## Metrics By Category", ""])
        for category, strategy_metrics in aggregate["by_category"].items():
            lines.extend([f"### {category}", ""])
            for strategy, metrics in strategy_metrics.items():
                lines.extend([f"**{strategy}**", "", "| Metric | Value |", "| --- | --- |"])
                for key, value in metrics.items():
                    lines.append(f"| `{key}` | {format_value(value)} |")
                lines.append("")

    lines.extend(["## A/B Deltas", ""])
    baseline_metrics = aggregate.get("by_strategy", aggregate).get(config.baseline_strategy, {})
    comparison_metrics = aggregate.get("by_strategy", aggregate).get(config.comparison_strategy, {})
    if baseline_metrics and comparison_metrics:
        lines.extend(["| Metric | Baseline | Comparison | Delta |", "| --- | ---: | ---: | ---: |"])
        for key in (
            "avg_expected_point_coverage",
            "missing_evidence_accuracy",
            "avg_candidate_recall",
            "avg_final_context_recall",
            "avg_citation_recall",
            "avg_quote_support_recall",
            "avg_accepted_evidence_precision",
            "avg_accepted_evidence_recall",
            "reference_contamination_rate",
            "avg_latency_ms",
            "error_count",
        ):
            baseline_value = baseline_metrics.get(key)
            comparison_value = comparison_metrics.get(key)
            lines.append(
                f"| `{key}` | {format_value(baseline_value)} | {format_value(comparison_value)} | {format_delta(baseline_value, comparison_value)} |"
            )
    else:
        lines.append("Not enough aggregate data to calculate deltas.")
    lines.append("")

    failed = [
        (result, strategy, metrics)
        for result in results
        for strategy, metrics in result.metrics.items()
        if metrics.error
        or metrics.expected_point_coverage == 0
        or metrics.missing_evidence_correct is False
        or metrics.citation_validity == 0
    ]
    lines.extend(["## Failed Or Weak Cases", ""])
    if failed:
        lines.extend(["| Case | Strategy | Reason |", "| --- | --- | --- |"])
        for result, strategy, metrics in failed:
            reasons: list[str] = []
            if metrics.error:
                reasons.append(f"error: {metrics.error}")
            if metrics.expected_point_coverage == 0:
                reasons.append("expected coverage 0")
            if metrics.missing_evidence_correct is False:
                reasons.append("no-answer behavior failed")
            if metrics.citation_validity == 0:
                reasons.append("citation validity 0")
            lines.append(f"| `{result.case.id}` | `{strategy}` | {', '.join(reasons)} |")
    else:
        lines.append("No failed or weak cases detected by deterministic checks.")
    lines.append("")

    lines.extend(["## Case Results", ""])
    for result in results:
        lines.extend(
            [
                f"### {result.case.id} ({result.case.category})",
                "",
                f"Question: {result.case.question}",
                "",
                "| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |",
                "| --- | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for strategy, metrics in result.metrics.items():
            lines.append(
                "| "
                + " | ".join(
                    [
                        strategy,
                        format_value(metrics.expected_point_coverage),
                        format_value(metrics.citation_validity),
                        format_value(metrics.final_context_recall),
                        format_value(metrics.quote_support_recall),
                        format_value(metrics.missing_evidence_correct),
                        metrics.error or "",
                    ]
                )
                + " |"
            )
        lines.append("")
        for strategy, output in result.outputs.items():
            preview = " ".join(output.answer.split())[:500]
            lines.extend([f"**{strategy} answer preview:**", "", preview or "(empty)", ""])
            if output.citations:
                citation = output.citations[0]
                lines.extend(
                    [
                        f"Representative citation: `{citation.get('chunk_id') or 'unknown'}` "
                        f"{citation.get('section_title') or citation.get('section_type') or ''}".strip(),
                        "",
                    ]
                )
    return "\n".join(lines).strip() + "\n"


def format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def format_delta(baseline_value: Any, comparison_value: Any) -> str:
    if isinstance(baseline_value, (int, float)) and isinstance(comparison_value, (int, float)):
        return f"{comparison_value - baseline_value:+.4f}"
    return "n/a"
