from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.core.config import Settings
from backend.app.db.session import SessionLocal, init_db
from backend.app.evaluation.adapters import OldCodeApiAdapter, StrategyAdapter, make_adapter
from backend.app.evaluation.cases import EvaluationCaseLoadError, load_cases
from backend.app.evaluation.judges import AnswerJudge, make_answer_judge
from backend.app.evaluation.metrics import score_output
from backend.app.evaluation.reports import write_reports
from backend.app.evaluation.types import CaseResult, EvaluationCase, RunConfig, StrategyOutput
from backend.app.services.llm import LLMService


DEFAULT_CASE_FILE = "evals/rag_ab/starter_cases.jsonl"
DEFAULT_OUTPUT_DIR = "evals/rag_ab/runs/latest"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_evaluation(args)
    except EvaluationCaseLoadError as exc:
        print(f"Invalid case file: {exc}")
        return 2
    except Exception as exc:
        print(f"Evaluation failed: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local RAG A/B evaluation.")
    parser.add_argument("--cases", default=DEFAULT_CASE_FILE, help="Path to JSONL evaluation cases.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory for reports and raw results.")
    parser.add_argument("--baseline", default="baseline-current", choices=["baseline-current", "old-code-api"])
    parser.add_argument("--comparison", default="current-evidence", choices=["current-evidence", "baseline-current"])
    parser.add_argument("--mode", default="in-process", choices=["in-process", "api"], help="Execution mode label recorded in reports.")
    parser.add_argument("--current-api-url", default=None, help="Explicit current API URL for API-mode runs.")
    parser.add_argument("--old-code-api-url", default=None, help="Explicit old-code API URL when baseline is old-code-api.")
    parser.add_argument(
        "--deterministic-local",
        action="store_true",
        help="Disable configured model clients for deterministic local smoke runs.",
    )
    parser.add_argument(
        "--llm-judge",
        action="store_true",
        help="Optionally run an LLM-as-judge pass and record it separately from deterministic metrics.",
    )
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--filter", action="append", default=[], help="Case id, category, or tag filter. Can be repeated.")
    parser.add_argument("--notes", default="")
    return parser.parse_args(argv)


def run_evaluation(args: argparse.Namespace) -> dict[str, Any]:
    case_path = Path(args.cases)
    cases = load_cases(case_path, args.filter)
    validate_runtime_args(args)
    init_db()
    settings = Settings()
    if args.deterministic_local:
        settings.openai_api_key = ""
    config = RunConfig(
        case_file=str(case_path),
        output_dir=str(args.output_dir),
        baseline_strategy=args.baseline,
        comparison_strategy=args.comparison,
        mode=args.mode,
        current_api_url=args.current_api_url,
        old_code_api_url=args.old_code_api_url,
        deterministic_local=args.deterministic_local,
        llm_judge=bool(args.llm_judge and not args.deterministic_local),
        top_k=args.top_k,
        case_filter=list(args.filter or []),
        git_revision=git_revision(),
        case_file_sha256=file_sha256(case_path),
        timestamp=datetime.now(UTC).isoformat(),
        notes=args.notes,
    )

    baseline = make_adapter(args.baseline, settings, old_code_api_url=args.old_code_api_url, library_id=default_library_id(cases))
    comparison = make_adapter(args.comparison, settings, old_code_api_url=args.old_code_api_url, library_id=default_library_id(cases))
    judge = make_answer_judge(args.llm_judge and not args.deterministic_local, LLMService(settings))

    db = SessionLocal()
    try:
        results = execute_cases(cases, baseline, comparison, db, args.top_k, judge=judge)
    finally:
        db.close()

    paths = write_reports(results, config, args.output_dir)
    return {"case_count": len(results), "paths": paths, "config": config.to_dict()}


def execute_cases(
    cases: list[EvaluationCase],
    baseline: StrategyAdapter,
    comparison: StrategyAdapter,
    db: Any,
    top_k: int,
    judge: AnswerJudge | None = None,
) -> list[CaseResult]:
    results: list[CaseResult] = []
    for case in cases:
        outputs: dict[str, StrategyOutput] = {}
        for adapter in (baseline, comparison):
            try:
                outputs[adapter.name] = adapter.run(db, case, top_k)
            except Exception as exc:
                outputs[adapter.name] = StrategyOutput(strategy=adapter.name, error=str(exc))
        known_ids = set(case.supporting_chunk_ids)
        for output in outputs.values():
            known_ids.update(output.retrieved_chunk_ids)
            known_ids.update(output.candidate_chunk_ids)
            known_ids.update(output.accepted_chunk_ids)
            known_ids.update(output.final_context_chunk_ids)
            known_ids.update(output.answer_source_chunk_ids)
        metrics = {
            strategy: score_output(case, output, {str(chunk_id) for chunk_id in known_ids if chunk_id})
            for strategy, output in outputs.items()
        }
        if judge is not None:
            for strategy, output in outputs.items():
                metrics[strategy].judge_source = judge.source
                metrics[strategy].llm_judge = judge.judge(case, output)
        results.append(CaseResult(case=case, outputs=outputs, metrics=metrics))
    return results


def validate_runtime_args(args: argparse.Namespace) -> None:
    if args.mode == "api" and not args.current_api_url:
        raise ValueError("--current-api-url is required when --mode api")
    if args.baseline == "old-code-api":
        if not args.old_code_api_url:
            raise ValueError("--old-code-api-url is required when --baseline old-code-api")
        health = OldCodeApiAdapter(args.old_code_api_url).health()
        if not health.get("ok"):
            raise ValueError(f"old-code API health check failed: {health}")


def default_library_id(cases: list[EvaluationCase]) -> str | None:
    for case in cases:
        if case.library_id:
            return case.library_id
    return None


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
