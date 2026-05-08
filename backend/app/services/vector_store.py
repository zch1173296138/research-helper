from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.db.models import Paper, PaperChunk
from backend.app.services.embeddings import EmbeddingService

try:
    import lancedb
except Exception:  # pragma: no cover - dependency may be unavailable during partial setup
    lancedb = None


@dataclass
class RetrievedChunk:
    chunk_id: str
    paper_id: str
    filename: str
    section_title: str
    text: str
    score: float = 0.0
    page_start: int | None = None
    page_end: int | None = None


class VectorStore:
    table_name = "paper_chunks"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedding_service = EmbeddingService(settings)

    def index_chunks(self, db: Session, chunks: list[PaperChunk]) -> None:
        if not chunks:
            return
        vectors = self.embedding_service.embed_texts([chunk.text for chunk in chunks])
        if lancedb is None:
            return

        records = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            paper = db.get(Paper, chunk.paper_id)
            records.append(
                {
                    "chunk_id": chunk.id,
                    "library_id": chunk.library_id,
                    "paper_id": chunk.paper_id,
                    "filename": paper.original_filename if paper else "",
                    "section_title": chunk.section_title or "",
                    "text": chunk.text,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "vector": vector,
                }
            )

        Path(self.settings.lancedb_path).mkdir(parents=True, exist_ok=True)
        conn = lancedb.connect(str(self.settings.lancedb_path))
        if self.table_name in conn.table_names():
            table = conn.open_table(self.table_name)
            paper_ids = sorted({record["paper_id"] for record in records})
            quoted_ids = ", ".join("'" + str(paper_id).replace("'", "''") + "'" for paper_id in paper_ids)
            table.delete(f"paper_id IN ({quoted_ids})")
            table.add(records)
        else:
            conn.create_table(self.table_name, data=records)

    def delete_paper(self, paper_id: str) -> None:
        if lancedb is None:
            return

        conn = lancedb.connect(str(self.settings.lancedb_path))
        if self.table_name not in conn.table_names():
            return

        safe_paper_id = paper_id.replace("'", "''")
        conn.open_table(self.table_name).delete(f"paper_id = '{safe_paper_id}'")

    def search(
        self,
        db: Session,
        library_id: str,
        query: str,
        paper_ids: list[str] | None = None,
        top_k: int = 8,
        diversify_by_paper: bool = False,
    ) -> list[RetrievedChunk]:
        if lancedb is not None:
            try:
                return self._search_lancedb(db, library_id, query, paper_ids, top_k, diversify_by_paper)
            except Exception:
                pass
        return self._search_sqlite(db, library_id, query, paper_ids, top_k, diversify_by_paper)

    def _search_lancedb(
        self,
        db: Session,
        library_id: str,
        query: str,
        paper_ids: list[str] | None,
        top_k: int,
        diversify_by_paper: bool,
    ) -> list[RetrievedChunk]:
        conn = lancedb.connect(str(self.settings.lancedb_path))
        if self.table_name not in conn.table_names():
            return []
        vector = self.embedding_service.embed_query(query)
        where = f"library_id = '{library_id}'"
        if paper_ids:
            quoted = ", ".join(f"'{paper_id}'" for paper_id in paper_ids)
            where += f" AND paper_id IN ({quoted})"
        table = conn.open_table(self.table_name)
        row_limit = max(top_k * 5, 50) if diversify_by_paper else max(top_k, 20)
        rows = table.search(vector).where(where, prefilter=True).limit(row_limit).to_list()
        chunks = [
            RetrievedChunk(
                chunk_id=row["chunk_id"],
                paper_id=row["paper_id"],
                filename=row.get("filename", ""),
                section_title=row.get("section_title") or "",
                text=row["text"],
                score=float(row.get("_distance", 0.0)),
                page_start=row.get("page_start"),
                page_end=row.get("page_end"),
            )
            for row in rows
        ]
        if diversify_by_paper:
            return self._diversify_by_paper(db, library_id, chunks, paper_ids, top_k)
        return chunks[:top_k]

    def _search_sqlite(
        self,
        db: Session,
        library_id: str,
        query: str,
        paper_ids: list[str] | None,
        top_k: int,
        diversify_by_paper: bool,
    ) -> list[RetrievedChunk]:
        terms = [term.lower() for term in query.split() if len(term) > 1]
        sql_query = db.query(PaperChunk).filter(PaperChunk.library_id == library_id)
        if paper_ids:
            sql_query = sql_query.filter(PaperChunk.paper_id.in_(paper_ids))
        candidates = sql_query.order_by(PaperChunk.paper_id, PaperChunk.chunk_index).limit(500).all()

        scored: list[tuple[float, PaperChunk]] = []
        for chunk in candidates:
            text_lower = chunk.text.lower()
            score = sum(text_lower.count(term) for term in terms)
            if score:
                scored.append((float(score), chunk))

        if not scored:
            scored = [(0.0, chunk) for chunk in candidates[:top_k]]

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[RetrievedChunk] = []
        for score, chunk in scored:
            paper = db.get(Paper, chunk.paper_id)
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    paper_id=chunk.paper_id,
                    filename=paper.original_filename if paper else "",
                    section_title=chunk.section_title,
                    text=chunk.text,
                    score=score,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                )
            )
        if diversify_by_paper:
            return self._diversify_by_paper(db, library_id, results, paper_ids, top_k)
        return results[:top_k]

    def _diversify_by_paper(
        self,
        db: Session,
        library_id: str,
        chunks: list[RetrievedChunk],
        paper_ids: list[str] | None,
        top_k: int,
    ) -> list[RetrievedChunk]:
        target_paper_ids = paper_ids or [
            paper.id for paper in db.query(Paper).filter(Paper.library_id == library_id).order_by(Paper.created_at.asc())
        ]
        target_paper_ids = [paper_id for paper_id in target_paper_ids if paper_id]
        if top_k <= 0 or len(target_paper_ids) <= 1:
            return chunks[:top_k]

        grouped: dict[str, list[RetrievedChunk]] = {paper_id: [] for paper_id in target_paper_ids}
        for chunk in chunks:
            if chunk.paper_id in grouped:
                grouped[chunk.paper_id].append(chunk)

        per_paper = max(1, top_k // len(target_paper_ids))
        extra_slots = top_k % len(target_paper_ids)
        selected: list[RetrievedChunk] = []
        selected_ids: set[str] = set()

        for index, paper_id in enumerate(target_paper_ids):
            quota = per_paper + (1 if index < extra_slots else 0)
            paper_chunks = grouped[paper_id] or self._paper_fallback_chunks(db, paper_id, quota)
            for chunk in paper_chunks[:quota]:
                if chunk.chunk_id not in selected_ids:
                    selected.append(chunk)
                    selected_ids.add(chunk.chunk_id)

        for chunk in chunks:
            if len(selected) >= top_k:
                break
            if chunk.chunk_id not in selected_ids:
                selected.append(chunk)
                selected_ids.add(chunk.chunk_id)

        return selected[:top_k]

    def _paper_fallback_chunks(self, db: Session, paper_id: str, limit: int) -> list[RetrievedChunk]:
        paper = db.get(Paper, paper_id)
        rows = (
            db.query(PaperChunk)
            .filter(PaperChunk.paper_id == paper_id)
            .order_by(PaperChunk.chunk_index.asc())
            .limit(limit)
            .all()
        )
        return [
            RetrievedChunk(
                chunk_id=chunk.id,
                paper_id=chunk.paper_id,
                filename=paper.original_filename if paper else "",
                section_title=chunk.section_title,
                text=chunk.text,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
            )
            for chunk in rows
        ]
