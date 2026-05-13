import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.db.models import Paper, PaperChunk
from backend.app.services.vector_store import RetrievedChunk, VectorStore


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    metadata: dict[str, Any]


def sync_fts_for_paper(db: Session, paper_id: str) -> None:
    try:
        _ensure_fts_table(db)
        db.execute(text("DELETE FROM paper_chunks_fts WHERE paper_id = :paper_id"), {"paper_id": paper_id})
        db.execute(
            text(
                """
                INSERT INTO paper_chunks_fts(
                    chunk_id, library_id, paper_id, section_title, section_path, section_type, text
                )
                SELECT id, library_id, paper_id, section_title, section_path, section_type, text
                FROM paper_chunks
                WHERE paper_id = :paper_id AND COALESCE(is_reference, 0) = 0
                """
            ),
            {"paper_id": paper_id},
        )
        db.commit()
    except Exception:
        db.rollback()


def delete_fts_for_paper(db: Session, paper_id: str) -> None:
    try:
        _ensure_fts_table(db)
        db.execute(text("DELETE FROM paper_chunks_fts WHERE paper_id = :paper_id"), {"paper_id": paper_id})
    except Exception:
        db.rollback()


class HybridRetriever:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.vector_store = VectorStore(settings)

    def search(
        self,
        db: Session,
        library_id: str,
        question: str,
        paper_ids: list[str] | None = None,
        top_k: int = 8,
        enable_second_pass: bool = True,
    ) -> RetrievalResult:
        limit = max(top_k * 3, 16)
        preferred_sections = infer_section_types(question)
        first = self._retrieve_once(db, library_id, question, paper_ids, limit, preferred_sections)

        all_chunks = list(first.chunks)
        passes = [first.metadata]
        second_pass = enable_second_pass and should_second_pass(question)
        followup_queries: list[str] = []
        if second_pass:
            followup_queries = build_followup_queries(question, preferred_sections, first.chunks)
            for followup in followup_queries:
                second = self._retrieve_once(db, library_id, followup, paper_ids, max(top_k * 2, 10), preferred_sections)
                all_chunks.extend(second.chunks)
                passes.append({**second.metadata, "query": followup, "pass": "second"})
            all_chunks.extend(self._neighbor_chunks(db, first.chunks[:4]))

        chunks = self._dedupe(all_chunks)[:top_k]
        return RetrievalResult(
            chunks=chunks,
            metadata={
                "strategy": "hybrid",
                "preferred_sections": preferred_sections,
                "second_pass": second_pass,
                "followup_queries": followup_queries,
                "passes": passes,
                "returned_chunk_ids": [chunk.chunk_id for chunk in chunks],
            },
        )

    def _retrieve_once(
        self,
        db: Session,
        library_id: str,
        query: str,
        paper_ids: list[str] | None,
        limit: int,
        preferred_sections: list[str],
    ) -> RetrievalResult:
        vector_chunks = self.vector_store.search(db, library_id, query, paper_ids, limit)
        keyword_chunks, keyword_source = self._keyword_search(db, library_id, query, paper_ids, limit)
        structure_chunks = self._structure_search(db, library_id, paper_ids, preferred_sections, limit)
        ranked = self._rrf_merge(
            [vector_chunks, keyword_chunks, structure_chunks],
            ["vector", keyword_source, "structure"],
            preferred_sections,
            limit,
        )
        fallback_used = False
        if not ranked:
            ranked = self._overview_fallback_chunks(db, library_id, paper_ids, limit)
            fallback_used = bool(ranked)
        return RetrievalResult(
            chunks=ranked,
            metadata={
                "pass": "first",
                "query": query,
                "vector_count": len(vector_chunks),
                "keyword_count": len(keyword_chunks),
                "keyword_source": keyword_source,
                "structure_count": len(structure_chunks),
                "result_count": len(ranked),
                "fallback": "paper_overview" if fallback_used else None,
            },
        )

    def _keyword_search(
        self,
        db: Session,
        library_id: str,
        query: str,
        paper_ids: list[str] | None,
        limit: int,
    ) -> tuple[list[RetrievedChunk], str]:
        try:
            chunks = self._search_fts(db, library_id, query, paper_ids, limit)
            if chunks:
                return chunks, "fts5_bm25"
        except Exception:
            db.rollback()
        return self._search_sqlite_keywords(db, library_id, query, paper_ids, limit), "sqlite_keyword"

    def _search_fts(
        self,
        db: Session,
        library_id: str,
        query: str,
        paper_ids: list[str] | None,
        limit: int,
    ) -> list[RetrievedChunk]:
        _ensure_fts_table(db)
        _populate_fts_if_empty(db)
        terms = extract_terms(query)
        if not terms:
            return []
        quoted_terms = ['"' + term.replace('"', '""') + '"' for term in terms[:10]]
        fts_query = " OR ".join(quoted_terms)
        filters = "library_id = :library_id"
        params: dict[str, Any] = {"library_id": library_id, "query": fts_query, "limit": limit}
        if paper_ids:
            placeholders = []
            for index, paper_id in enumerate(paper_ids):
                key = f"paper_id_{index}"
                placeholders.append(f":{key}")
                params[key] = paper_id
            filters += f" AND paper_id IN ({', '.join(placeholders)})"

        rows = db.execute(
            text(
                f"""
                SELECT chunk_id, bm25(paper_chunks_fts) AS rank
                FROM paper_chunks_fts
                WHERE paper_chunks_fts MATCH :query AND {filters}
                ORDER BY rank
                LIMIT :limit
                """
            ),
            params,
        ).fetchall()
        if not rows:
            return []
        rank_by_id = {row[0]: float(row[1]) for row in rows}
        chunks = (
            db.query(PaperChunk)
            .filter(PaperChunk.id.in_(rank_by_id.keys()), PaperChunk.is_reference.is_(False))
            .all()
        )
        return [
            self._to_retrieved_chunk(db, chunk, score=rank_by_id[chunk.id], source="fts5_bm25")
            for chunk in sorted(chunks, key=lambda item: rank_by_id[item.id])
        ]

    def _search_sqlite_keywords(
        self,
        db: Session,
        library_id: str,
        query: str,
        paper_ids: list[str] | None,
        limit: int,
    ) -> list[RetrievedChunk]:
        terms = [term.lower() for term in extract_terms(query) if len(term) > 1]
        if not terms:
            return []
        sql_query = db.query(PaperChunk).filter(PaperChunk.library_id == library_id, PaperChunk.is_reference.is_(False))
        if paper_ids:
            sql_query = sql_query.filter(PaperChunk.paper_id.in_(paper_ids))
        candidates = sql_query.order_by(PaperChunk.chunk_index.asc()).limit(800).all()
        scored: list[tuple[float, PaperChunk]] = []
        for chunk in candidates:
            haystack = f"{chunk.section_title} {chunk.section_path} {chunk.text}".lower()
            score = sum(haystack.count(term) for term in terms)
            if score:
                scored.append((float(score), chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            self._to_retrieved_chunk(db, chunk, score=score, source="sqlite_keyword")
            for score, chunk in scored[:limit]
        ]

    def _structure_search(
        self,
        db: Session,
        library_id: str,
        paper_ids: list[str] | None,
        preferred_sections: list[str],
        limit: int,
    ) -> list[RetrievedChunk]:
        if not preferred_sections:
            return []
        query = db.query(PaperChunk).filter(
            PaperChunk.library_id == library_id,
            PaperChunk.section_type.in_(preferred_sections),
            PaperChunk.is_reference.is_(False),
        )
        if paper_ids:
            query = query.filter(PaperChunk.paper_id.in_(paper_ids))
        rows = query.order_by(PaperChunk.paper_id.asc(), PaperChunk.chunk_index.asc()).limit(limit).all()
        return [
            self._to_retrieved_chunk(db, chunk, score=1.0, source="structure")
            for chunk in rows
        ]

    def _neighbor_chunks(self, db: Session, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        neighbors: list[RetrievedChunk] = []
        seen: set[str] = {chunk.chunk_id for chunk in chunks}
        for chunk in chunks:
            current = db.get(PaperChunk, chunk.chunk_id)
            if not current:
                continue
            rows = (
                db.query(PaperChunk)
                .filter(
                    PaperChunk.paper_id == current.paper_id,
                    PaperChunk.chunk_index.in_([current.chunk_index - 1, current.chunk_index + 1]),
                    PaperChunk.is_reference.is_(False),
                )
                .all()
            )
            for row in rows:
                if row.id in seen:
                    continue
                neighbors.append(self._to_retrieved_chunk(db, row, score=0.2, source="second_pass_neighbor"))
                seen.add(row.id)
        return neighbors

    def _overview_fallback_chunks(
        self,
        db: Session,
        library_id: str,
        paper_ids: list[str] | None,
        limit: int,
    ) -> list[RetrievedChunk]:
        query = db.query(PaperChunk).filter(PaperChunk.library_id == library_id, PaperChunk.is_reference.is_(False))
        if paper_ids:
            query = query.filter(PaperChunk.paper_id.in_(paper_ids))
        rows = query.order_by(PaperChunk.paper_id.asc(), PaperChunk.chunk_index.asc()).limit(limit).all()
        return [self._to_retrieved_chunk(db, chunk, score=0.0, source="paper_overview_fallback") for chunk in rows]

    def _rrf_merge(
        self,
        rankings: list[list[RetrievedChunk]],
        sources: list[str],
        preferred_sections: list[str],
        limit: int,
    ) -> list[RetrievedChunk]:
        scores: dict[str, float] = {}
        chunks: dict[str, RetrievedChunk] = {}
        source_map: dict[str, set[str]] = {}
        for ranking, source in zip(rankings, sources, strict=True):
            for rank, chunk in enumerate(ranking, start=1):
                if is_reference_like(chunk):
                    continue
                chunks.setdefault(chunk.chunk_id, chunk)
                source_map.setdefault(chunk.chunk_id, set()).add(source)
                scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (60 + rank)
                if preferred_sections and chunk.section_type in preferred_sections:
                    scores[chunk.chunk_id] += 0.04

        ranked_ids = sorted(scores, key=lambda chunk_id: scores[chunk_id], reverse=True)
        merged: list[RetrievedChunk] = []
        for chunk_id in ranked_ids[:limit]:
            chunk = chunks[chunk_id]
            chunk.score = scores[chunk_id]
            chunk.retrieval_source = "+".join(sorted(source_map.get(chunk_id, set())))
            merged.append(chunk)
        return merged

    def _dedupe(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        deduped: list[RetrievedChunk] = []
        seen: set[str] = set()
        for chunk in chunks:
            if chunk.chunk_id in seen or is_reference_like(chunk):
                continue
            deduped.append(chunk)
            seen.add(chunk.chunk_id)
        return deduped

    def _to_retrieved_chunk(self, db: Session, chunk: PaperChunk, score: float, source: str) -> RetrievedChunk:
        paper = db.get(Paper, chunk.paper_id)
        return RetrievedChunk(
            chunk_id=chunk.id,
            paper_id=chunk.paper_id,
            filename=paper.original_filename if paper else "",
            section_title=chunk.section_title,
            section_path=chunk.section_path,
            section_type=chunk.section_type,
            text=chunk.text,
            score=score,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            retrieval_source=source,
        )


def _ensure_fts_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS paper_chunks_fts USING fts5(
                chunk_id UNINDEXED,
                library_id UNINDEXED,
                paper_id UNINDEXED,
                section_title,
                section_path,
                section_type,
                text
            )
            """
        )
    )


def _populate_fts_if_empty(db: Session) -> None:
    count = db.execute(text("SELECT count(*) FROM paper_chunks_fts")).scalar() or 0
    if count:
        return
    db.execute(
        text(
            """
            INSERT INTO paper_chunks_fts(chunk_id, library_id, paper_id, section_title, section_path, section_type, text)
            SELECT id, library_id, paper_id, section_title, section_path, section_type, text
            FROM paper_chunks
            WHERE COALESCE(is_reference, 0) = 0
            """
        )
    )


def extract_terms(query: str) -> list[str]:
    terms = re.findall(r"[A-Za-z][A-Za-z0-9_.-]{1,}|[\u4e00-\u9fff]{2,}|\d+(?:\.\d+)?%?", query)
    seen: set[str] = set()
    result: list[str] = []
    for term in terms:
        normalized = term.strip().lower()
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result


def infer_section_types(question: str) -> list[str]:
    text_lower = question.lower()
    rules = [
        (("method", "approach", "algorithm", "architecture", "how", "方法", "算法", "如何", "怎么"), ["method"]),
        (("dataset", "benchmark", "data", "material", "数据集", "数据", "材料"), ["experiment", "results"]),
        (("experiment", "evaluation", "metric", "accuracy", "result", "performance", "实验", "评估", "指标", "结果", "性能"), ["experiment", "results"]),
        (("limitation", "weakness", "threat", "局限", "限制", "不足"), ["limitations", "discussion"]),
        (("compare", "contrast", "difference", "different", "比较", "对比", "差异", "不同"), ["method", "experiment", "results", "limitations"]),
        (("conclusion", "finding", "contribution", "结论", "发现", "贡献"), ["abstract", "results", "conclusion"]),
        (("background", "motivation", "introduction", "背景", "动机", "引言"), ["abstract", "introduction"]),
    ]
    selected: list[str] = []
    for keywords, section_types in rules:
        if any(keyword in text_lower for keyword in keywords):
            selected.extend(section_types)
    return list(dict.fromkeys(selected))


def should_second_pass(question: str) -> bool:
    text_lower = question.lower()
    keywords = (
        "method",
        "algorithm",
        "experiment",
        "evaluation",
        "result",
        "dataset",
        "metric",
        "limitation",
        "compare",
        "difference",
        "cause",
        "why",
        "方法",
        "算法",
        "实验",
        "结果",
        "数据集",
        "指标",
        "局限",
        "比较",
        "对比",
        "差异",
        "原因",
        "为什么",
    )
    return any(keyword in text_lower for keyword in keywords)


def build_followup_queries(question: str, preferred_sections: list[str], chunks: list[RetrievedChunk]) -> list[str]:
    queries: list[str] = []
    section_terms = " ".join(preferred_sections)
    if section_terms:
        queries.append(f"{question} {section_terms}")
    entities = extract_terms(question)
    if entities:
        queries.append(" ".join(entities[:8]))
    top_sections = " ".join(chunk.section_title for chunk in chunks[:3] if chunk.section_title)
    if top_sections:
        queries.append(f"{question} {top_sections}")

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        normalized = re.sub(r"\s+", " ", query).strip()
        if normalized and normalized.lower() not in seen and normalized != question:
            deduped.append(normalized)
            seen.add(normalized.lower())
    return deduped[:3]


def is_reference_like(chunk: RetrievedChunk) -> bool:
    section = f"{chunk.section_type} {chunk.section_title} {chunk.section_path}".lower()
    return any(keyword in section for keyword in ("references", "bibliography", "参考文献"))
