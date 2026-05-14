from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

from backend.app.core.config import Settings


DEFAULT_INPUT = "evals/rag_ab/qasper_validation_local_subset.jsonl"
DEFAULT_OUTPUT = "evals/rag_ab/qasper_validation_local_subset_chunked.jsonl"
DEFAULT_MIN_SCORE = 0.45
DEFAULT_MAX_ALTERNATES = 3

PLACEHOLDER_RE = re.compile(r"\b(?:BIB|FIG|TAB)REF\d+\b|\bINLINEFORM\d+\b", re.IGNORECASE)
HTML_RE = re.compile(r"<[^>]+>")
LATEX_RE = re.compile(r"\$[^$]*\$")
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "between",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "these",
    "this",
    "those",
    "to",
    "was",
    "we",
    "were",
    "with",
}


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    chunk_index: int
    section_title: str
    text: str


@dataclass(frozen=True)
class ChunkMatch:
    chunk_id: str
    score: float
    section_title: str


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cases = load_jsonl(Path(args.input))
    database_url = args.database_url or Settings().database_url
    engine = create_engine(database_url)
    with engine.connect() as conn:
        aligned_cases, report = align_cases(
            cases,
            conn,
            min_score=args.min_score,
            max_alternates=args.max_alternates,
        )

    unmatched = [item for item in report["quote_matches"] if not item.get("accepted")]
    if unmatched and args.fail_on_unmatched:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(aligned_cases, output_path)
    if args.report_output:
        report_path = Path(args.report_output)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "input": str(args.input),
                "output": str(output_path),
                "report_output": str(args.report_output or ""),
                "case_count": len(aligned_cases),
                "matched_quotes": report["matched_quotes"],
                "total_quotes": report["total_quotes"],
                "unmatched_quotes": len(unmatched),
                "min_score": args.min_score,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Align QASPER support quotes to local Research Helper chunks.")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    parser.add_argument("--max-alternates", type=int, default=DEFAULT_MAX_ALTERNATES)
    parser.add_argument("--report-output", default=None)
    parser.add_argument("--fail-on-unmatched", action="store_true")
    return parser.parse_args(argv)


def align_cases(
    cases: list[dict[str, Any]],
    conn: Any,
    min_score: float = DEFAULT_MIN_SCORE,
    max_alternates: int = DEFAULT_MAX_ALTERNATES,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aligned: list[dict[str, Any]] = []
    quote_matches: list[dict[str, Any]] = []

    for case in cases:
        paper_ids = [str(paper_id) for paper_id in case.get("paper_ids") or [] if str(paper_id).strip()]
        chunks = fetch_chunks(conn, paper_ids)
        updated, matches = align_case(case, chunks, min_score=min_score, max_alternates=max_alternates)
        aligned.append(updated)
        quote_matches.extend(matches)

    matched_quotes = sum(1 for item in quote_matches if item.get("accepted"))
    report = {
        "case_count": len(aligned),
        "total_quotes": len(quote_matches),
        "matched_quotes": matched_quotes,
        "quote_matches": quote_matches,
    }
    return aligned, report


def align_case(
    case: dict[str, Any],
    chunks: list[ChunkRecord],
    min_score: float = DEFAULT_MIN_SCORE,
    max_alternates: int = DEFAULT_MAX_ALTERNATES,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    updated = dict(case)
    support_ids: list[str] = []
    matches: list[dict[str, Any]] = []

    for quote_index, quote in enumerate(case.get("supporting_quotes") or [], start=1):
        ranked = rank_chunks(str(quote), chunks)[: max(max_alternates, 1)]
        best = ranked[0] if ranked else None
        accepted = bool(best and best.score >= min_score)
        if accepted and best and best.chunk_id not in support_ids:
            support_ids.append(best.chunk_id)
        matches.append(
            {
                "case_id": case.get("id"),
                "quote_index": quote_index,
                "accepted": accepted,
                "chunk_id": best.chunk_id if best else "",
                "score": best.score if best else 0.0,
                "section_title": best.section_title if best else "",
                "alternates": [match_to_dict(item) for item in ranked[1:]],
            }
        )

    updated["supporting_chunk_ids"] = support_ids
    if support_ids:
        tags = list(updated.get("tags") or [])
        if "chunk-aligned" not in tags:
            tags.append("chunk-aligned")
        updated["tags"] = tags
    updated["supporting_chunk_alignment"] = {
        "method": "qasper-fuzzy-local-v1",
        "min_score": min_score,
        "matches": [
            {
                "quote_index": item["quote_index"],
                "chunk_id": item["chunk_id"],
                "score": item["score"],
                "section_title": item["section_title"],
                "accepted": item["accepted"],
                "alternates": item["alternates"],
            }
            for item in matches
        ],
    }
    return updated, matches


def rank_chunks(quote: str, chunks: list[ChunkRecord]) -> list[ChunkMatch]:
    scored = [
        ChunkMatch(chunk.chunk_id, support_score(quote, chunk.text), chunk.section_title)
        for chunk in chunks
    ]
    return sorted(scored, key=lambda item: (-item.score, chunk_sort_key(item.chunk_id)))


def support_score(quote: str, chunk_text: str) -> float:
    quote_tokens = normalize_tokens(quote)
    chunk_tokens = normalize_tokens(chunk_text)
    if not quote_tokens or not chunk_tokens:
        return 0.0

    quote_joined = " ".join(quote_tokens)
    chunk_joined = " ".join(chunk_tokens)
    if quote_joined in chunk_joined:
        return 1.0

    quote_set = set(quote_tokens)
    chunk_set = set(chunk_tokens)
    content_tokens = {token for token in quote_tokens if token not in STOPWORDS}
    unique_coverage = len(quote_set & chunk_set) / len(quote_set)
    content_coverage = len(content_tokens & chunk_set) / len(content_tokens) if content_tokens else unique_coverage

    matcher = SequenceMatcher(None, quote_tokens, chunk_tokens, autojunk=False)
    block_sizes = [block.size for block in matcher.get_matching_blocks() if block.size]
    ordered_coverage = sum(size for size in block_sizes if size >= 2) / len(quote_tokens)
    longest_block = max(block_sizes) / len(quote_tokens) if block_sizes else 0.0
    sequence_ratio = matcher.ratio()

    weighted = (
        unique_coverage * 0.45
        + content_coverage * 0.25
        + ordered_coverage * 0.2
        + longest_block * 0.1
    )
    return round(max(weighted, sequence_ratio), 4)


def normalize_tokens(value: str) -> list[str]:
    text_value = PLACEHOLDER_RE.sub(" ", value or "")
    text_value = HTML_RE.sub(" ", text_value)
    text_value = LATEX_RE.sub(" ", text_value)
    return TOKEN_RE.findall(text_value.lower())


def fetch_chunks(conn: Any, paper_ids: list[str]) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    for paper_id in paper_ids:
        rows = conn.execute(
            text(
                """
                SELECT id, chunk_index, section_title, text
                FROM paper_chunks
                WHERE paper_id = :paper_id AND COALESCE(is_reference, 0) = 0
                ORDER BY chunk_index
                """
            ),
            {"paper_id": paper_id},
        ).mappings()
        chunks.extend(
            ChunkRecord(
                chunk_id=str(row["id"]),
                chunk_index=int(row["chunk_index"] or 0),
                section_title=str(row["section_title"] or ""),
                text=str(row["text"] or ""),
            )
            for row in rows
        )
    return chunks


def chunk_sort_key(chunk_id: str) -> int:
    match = re.search(r"_chunk_(\d+)$", chunk_id)
    return int(match.group(1)) if match else 0


def match_to_dict(match: ChunkMatch) -> dict[str, Any]:
    return {
        "chunk_id": match.chunk_id,
        "score": match.score,
        "section_title": match.section_title,
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(cases: list[dict[str, Any]], output_path: Path) -> None:
    payload = "\n".join(json.dumps(case, ensure_ascii=False, sort_keys=True) for case in cases)
    output_path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
