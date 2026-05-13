import json
import shutil
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.db.models import Paper, PaperAsset, PaperChunk, PaperSummary, ReviewMatrix
from backend.app.services.ids import new_id
from backend.app.services.markdown import clean_markdown, split_markdown
from backend.app.services.retrieval import delete_fts_for_paper, sync_fts_for_paper
from backend.app.services.mineru import MinerUClient
from backend.app.services.vector_store import RetrievedChunk, VectorStore


class PaperService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.mineru = MinerUClient(settings)
        self.vector_store = VectorStore(settings)

    def ingest_upload(
        self,
        db: Session,
        library_id: str,
        filename: str,
        file_obj: BinaryIO,
        is_ocr: bool = True,
        enable_formula: bool = True,
        enable_table: bool = True,
        language: str = "ch",
        layout_model: str = "doclayout_yolo",
    ) -> Paper:
        paper_id = new_id("paper")
        extension = Path(filename).suffix.lower() or ".pdf"
        input_path = self.settings.input_dir / f"{paper_id}{extension}"
        output_dir = self.settings.libraries_output_dir / library_id / paper_id
        output_dir.mkdir(parents=True, exist_ok=True)

        with input_path.open("wb") as target:
            while chunk := file_obj.read(1024 * 1024):
                target.write(chunk)

        paper = Paper(
            id=paper_id,
            library_id=library_id,
            original_filename=filename,
            input_path=str(input_path),
            output_dir=str(output_dir),
            status="processing",
        )
        db.add(paper)
        db.commit()

        try:
            md_path, parser = self.mineru.process(
                input_path,
                output_dir,
                paper_id,
                filename,
                is_ocr=is_ocr,
                enable_formula=enable_formula,
                enable_table=enable_table,
                language=language,
                layout_model=layout_model,
            )
            raw = md_path.read_text(encoding="utf-8", errors="ignore")
            cleaned = clean_markdown(raw)
            md_path.write_text(cleaned, encoding="utf-8")
            paper.md_path = str(md_path)
            paper.parser = parser
            paper.status = "processed"
            paper.needs_ocr = "_No extractable text" in cleaned
            db.commit()

            self._sync_assets(db, paper)
            chunks = self._replace_chunks(db, paper, md_path)
            try:
                self.vector_store.index_chunks(db, chunks)
            except Exception as index_error:
                # Markdown parsing succeeded, so keep the paper visible. The user can
                # fix model config and rebuild the index without re-importing the PDF.
                paper.error = f"Vector indexing failed: {index_error}"
                db.commit()
            return paper
        except Exception as exc:
            paper.status = "failed"
            paper.error = str(exc)
            db.commit()
            return paper

    def rebuild_index(self, db: Session, library_id: str) -> int:
        papers = db.query(Paper).filter(Paper.library_id == library_id, Paper.status == "processed").all()
        count = 0
        for paper in papers:
            if not paper.md_path:
                continue
            try:
                chunks = self._replace_chunks(db, paper, Path(paper.md_path))
                self.vector_store.index_chunks(db, chunks)
                if paper.error:
                    paper.error = None
                    db.commit()
                count += len(chunks)
            except Exception as index_error:
                paper.error = f"Vector indexing failed: {index_error}"
                db.commit()
        return count

    def summarize(self, db: Session, paper: Paper, llm) -> dict:
        chunks = [
            RetrievedChunk(
                chunk_id=chunk.id,
                paper_id=paper.id,
                filename=paper.original_filename,
                section_title=chunk.section_title,
                section_path=chunk.section_path,
                section_type=chunk.section_type,
                text=chunk.text,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
            )
            for chunk in db.query(PaperChunk).filter(PaperChunk.paper_id == paper.id).order_by(PaperChunk.chunk_index)
        ]
        summary_json = llm.summarize_paper(paper.original_filename, chunks)
        existing = db.query(PaperSummary).filter(PaperSummary.paper_id == paper.id).one_or_none()
        if existing:
            existing.summary_json = summary_json
        else:
            db.add(PaperSummary(paper_id=paper.id, summary_json=summary_json))
        db.commit()
        return summary_json

    def delete_paper(self, db: Session, paper: Paper) -> None:
        input_path = Path(paper.input_path)
        output_dir = Path(paper.output_dir)

        self.vector_store.delete_paper(paper.id)
        delete_fts_for_paper(db, paper.id)
        self._remove_paper_from_matrices(db, paper)
        db.delete(paper)
        db.commit()

        self._delete_file_if_safe(input_path, self.settings.input_dir)
        self._delete_dir_if_safe(output_dir, self.settings.libraries_output_dir)

    def _replace_chunks(self, db: Session, paper: Paper, md_path: Path) -> list[PaperChunk]:
        db.query(PaperChunk).filter(PaperChunk.paper_id == paper.id).delete()
        markdown = clean_markdown(md_path.read_text(encoding="utf-8", errors="ignore"))
        chunks = split_markdown(markdown, md_path)
        records: list[PaperChunk] = []
        for chunk in chunks:
            record = PaperChunk(
                id=f"{paper.id}_chunk_{chunk.chunk_index}",
                library_id=paper.library_id,
                paper_id=paper.id,
                chunk_index=chunk.chunk_index,
                section_title=chunk.section_title,
                section_path=chunk.section_path,
                section_type=chunk.section_type,
                text=chunk.text,
                source_md_path=str(md_path),
                token_count=chunk.token_count,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                is_reference=chunk.is_reference,
            )
            db.add(record)
            records.append(record)
        db.commit()
        sync_fts_for_paper(db, paper.id)
        return records

    def _sync_assets(self, db: Session, paper: Paper) -> None:
        db.query(PaperAsset).filter(PaperAsset.paper_id == paper.id).delete()
        output_dir = Path(paper.output_dir)
        for path in output_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            db.add(
                PaperAsset(
                    paper_id=paper.id,
                    asset_type="image",
                    path=str(path),
                    relative_path=str(path.relative_to(output_dir)).replace("\\", "/"),
                )
            )
        db.commit()

    def read_filename_info(self, paper: Paper) -> dict:
        info_path = Path(paper.output_dir) / "filename_info.json"
        if not info_path.exists():
            return {}
        return json.loads(info_path.read_text(encoding="utf-8"))

    def _remove_paper_from_matrices(self, db: Session, paper: Paper) -> None:
        matrices = db.query(ReviewMatrix).filter(ReviewMatrix.library_id == paper.library_id).all()
        for matrix in matrices:
            matrix_json = matrix.matrix_json if isinstance(matrix.matrix_json, dict) else {}
            rows = matrix_json.get("rows", [])
            if not isinstance(rows, list):
                continue
            filtered_rows = [
                row for row in rows if not (isinstance(row, dict) and row.get("paper_id") == paper.id)
            ]
            if len(filtered_rows) != len(rows):
                matrix.matrix_json = {**matrix_json, "rows": filtered_rows}

    def _delete_file_if_safe(self, path: Path, root: Path) -> None:
        resolved = path.resolve()
        if not self._is_within(resolved, root.resolve()):
            return
        if resolved.exists() and resolved.is_file():
            resolved.unlink()

    def _delete_dir_if_safe(self, path: Path, root: Path) -> None:
        resolved = path.resolve()
        if not self._is_within(resolved, root.resolve()):
            return
        if resolved.exists() and resolved.is_dir():
            shutil.rmtree(resolved)

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
        except ValueError:
            return False
        return True
