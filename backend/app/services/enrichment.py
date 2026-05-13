import re
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.db.models import Paper, PaperAsset


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")
ARXIV_RE = re.compile(r"\b(?:arxiv[:_\s-]*)?(\d{4}\.\d{4,5})(?:v\d+)?\b", re.IGNORECASE)
IMAGE_MD_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
CAPTION_RE = re.compile(r"\b(?:fig(?:ure)?|table)\s*[\dA-Za-z.-]*\s*[:：.-]\s*(.+)", re.IGNORECASE)


FRONT_MATTER_LIMIT = 160
AUTHOR_BLOCK_LIMIT = 90

AFFILIATION_KEYWORDS = (
    "academy",
    "automation",
    "beihang",
    "beijing",
    "china",
    "college",
    "computing",
    "department",
    "engineering",
    "faculty",
    "global science",
    "hangzhou",
    "institute",
    "jiaotong",
    "laboratory",
    "mechanical",
    "northwestern",
    "polytechnical",
    "public health",
    "school",
    "science",
    "shanghai",
    "singapore",
    "technology",
    "university",
    "xian",
    "zhejiang",
)
AUTHOR_STOP_KEYWORDS = (
    "abstract",
    "acm reference format",
    "article info",
    "ccs concepts",
    "copyright",
    "keywords",
    "permission to make",
)


class PaperEnrichmentService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def enrich_paper(self, db: Session, paper: Paper) -> dict[str, Any]:
        metadata = self.enrich_metadata(db, paper)
        assets = self.enrich_assets(db, paper)
        return {"metadata": metadata, "assets": assets}

    def enrich_metadata(self, db: Session, paper: Paper) -> dict[str, Any]:
        filename_info = self._read_filename_info(paper)
        markdown_info = self._read_markdown_metadata(paper)
        source_text = " ".join(
            str(value)
            for value in [
                paper.original_filename,
                filename_info.get("title"),
                filename_info.get("doi"),
                filename_info.get("arxiv_id"),
                markdown_info.get("text"),
                markdown_info.get("identifier_text"),
            ]
            if value
        )
        year_text = " ".join(
            str(value)
            for value in [
                paper.original_filename,
                filename_info.get("year"),
                markdown_info.get("year_text"),
            ]
            if value
        )
        doi = self._clean_identifier(
            str(filename_info.get("doi") or "").strip()
            or str(markdown_info.get("doi") or "").strip()
            or (self._first_match(DOI_RE, source_text) or "")
        )
        arxiv_id = self._first_arxiv_id(source_text)
        title = (
            str(filename_info.get("title") or "").strip()
            or str(markdown_info.get("title") or "").strip()
            or self._title_from_filename(paper.original_filename)
        )
        authors = filename_info.get("authors")
        if not isinstance(authors, list) or not authors:
            authors = markdown_info.get("authors") if isinstance(markdown_info.get("authors"), list) else []
        metadata_sources = ["filename"]
        if markdown_info.get("text"):
            metadata_sources.append("markdown_front_matter")
        external_ids = dict(paper.external_ids or {})
        if arxiv_id:
            external_ids["arxiv"] = arxiv_id

        paper.normalized_title = title or paper.normalized_title
        paper.normalized_authors = authors
        paper.normalized_venue = filename_info.get("venue") or paper.normalized_venue
        paper.normalized_year = self._year_from_text(year_text) or paper.normalized_year
        paper.doi = doi or paper.doi
        paper.external_ids = external_ids
        paper.source_url = (
            f"https://doi.org/{doi}"
            if doi
            else (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else paper.source_url)
        )
        paper.enrichment_provider = "local_metadata"
        paper.enrichment_confidence = self._metadata_confidence(title, authors, doi or paper.doi, external_ids)
        paper.enrichment_status = "enriched" if paper.enrichment_confidence else "skipped"
        paper.enrichment_metadata = {
            "provider": "local_metadata",
            "status": paper.enrichment_status,
            "external_lookup": "not_configured",
            "sources": metadata_sources,
            "author_count": len(authors),
        }
        db.commit()
        return paper.enrichment_metadata

    def enrich_assets(self, db: Session, paper: Paper) -> dict[str, Any]:
        captions = self._captions_by_path(paper)
        assets = db.query(PaperAsset).filter(PaperAsset.paper_id == paper.id).all()
        updated = 0
        for asset in assets:
            caption = captions.get(asset.relative_path) or captions.get(Path(asset.relative_path).name) or ""
            if caption:
                asset.caption = caption
                asset.asset_type = "table" if caption.lower().startswith("table") else "figure"
                asset.source = "markdown_caption"
                asset.generated_description = self._generated_description(asset)
                asset.is_original_text = False
                asset.enrichment_metadata = {
                    "caption_source": "markdown",
                    "generated_description_source": "local_caption",
                    "is_original_text": False,
                }
                updated += 1
            elif not asset.enrichment_metadata:
                asset.enrichment_metadata = {"caption_source": "unavailable", "is_original_text": False}
        db.commit()
        return {"asset_count": len(assets), "updated_count": updated}

    def _captions_by_path(self, paper: Paper) -> dict[str, str]:
        if not paper.md_path or not Path(paper.md_path).exists():
            return {}
        lines = Path(paper.md_path).read_text(encoding="utf-8", errors="ignore").splitlines()
        captions: dict[str, str] = {}
        for index, line in enumerate(lines):
            match = IMAGE_MD_RE.search(line)
            if not match:
                continue
            image_path = match.group(2).strip().replace("\\", "/").lstrip("./")
            candidates = [match.group(1).strip()]
            candidates.extend(lines[next_index].strip() for next_index in range(index + 1, min(index + 4, len(lines))))
            caption = self._best_caption(candidates)
            if caption:
                captions[image_path] = caption
                captions[Path(image_path).name] = caption
        return captions

    def _best_caption(self, candidates: list[str]) -> str:
        for candidate in candidates:
            if not candidate:
                continue
            match = CAPTION_RE.search(candidate)
            if match:
                return candidate[:800]
        return ""

    def _generated_description(self, asset: PaperAsset) -> str:
        if not asset.caption:
            return ""
        return f"{asset.asset_type.title()} asset described by extracted caption: {asset.caption}"

    def _read_filename_info(self, paper: Paper) -> dict[str, Any]:
        path = Path(paper.output_dir) / "filename_info.json"
        if not path.exists():
            return {}
        try:
            import json

            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _read_markdown_metadata(self, paper: Paper) -> dict[str, Any]:
        if not paper.md_path or not Path(paper.md_path).exists():
            return {}
        lines = Path(paper.md_path).read_text(encoding="utf-8", errors="ignore").splitlines()
        front_matter = self._metadata_block_lines(lines)
        text = "\n".join(front_matter)
        identifier_text = "\n".join(lines[:FRONT_MATTER_LIMIT])
        title, title_index = self._title_from_markdown_lines(front_matter)
        return {
            "title": title,
            "authors": self._authors_from_markdown_lines(front_matter, title_index),
            "doi": self._clean_identifier(self._first_match(DOI_RE, identifier_text) or ""),
            "arxiv_id": self._first_arxiv_id(identifier_text),
            "text": text,
            "identifier_text": identifier_text,
            "year_text": self._publication_year_text(lines[:FRONT_MATTER_LIMIT]),
        }

    def _metadata_block_lines(self, lines: list[str]) -> list[str]:
        block: list[str] = []
        for line in lines[:FRONT_MATTER_LIMIT]:
            stripped = line.strip().strip("# ").lower()
            if stripped == "abstract":
                break
            block.append(line)
        return block

    def _publication_year_text(self, lines: list[str]) -> str:
        candidates = []
        for line in lines:
            lowered = line.lower()
            if any(keyword in lowered for keyword in ("copyright", "published", "proceedings", "received", "accepted")):
                candidates.append(line)
        return "\n".join(candidates)

    def _title_from_markdown_lines(self, lines: list[str]) -> tuple[str, int]:
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("# "):
                continue
            title = stripped.lstrip("#").strip()
            if title.lower() not in {"abstract", "article info", "keywords"}:
                return title, index
        return "", -1

    def _authors_from_markdown_lines(self, lines: list[str], title_index: int) -> list[str]:
        if title_index < 0:
            return []
        authors: list[str] = []
        for line in lines[title_index + 1 : title_index + 1 + AUTHOR_BLOCK_LIMIT]:
            stripped = self._clean_markdown_line(line)
            if not stripped:
                continue
            lowered = stripped.lower()
            if any(keyword in lowered for keyword in AUTHOR_STOP_KEYWORDS):
                break
            if stripped.startswith("#"):
                break
            if IMAGE_MD_RE.search(stripped) or "@" in stripped or "doi.org" in lowered or "http" in lowered:
                continue
            for author in self._split_author_line(stripped):
                if author not in authors and self._is_author_candidate(author):
                    authors.append(author)
            if len(authors) >= 12:
                break
        return authors

    def _split_author_line(self, line: str) -> list[str]:
        line = re.sub(r"\band\b", ",", line, flags=re.IGNORECASE)
        pieces = re.split(r",|;", line)
        return [cleaned for piece in pieces if (cleaned := self._clean_author_name(piece))]

    def _clean_author_name(self, value: str) -> str:
        value = self._clean_markdown_line(value)
        value = re.sub(r"\$?\^\{?[A-Za-z0-9,* ]+\}?\$?", " ", value)
        value = re.sub(r"\\[*_]", " ", value)
        value = re.sub(r"\b[a-z]\b$", "", value.strip())
        value = re.sub(r"[*†‡]+", "", value)
        return re.sub(r"\s+", " ", value).strip(" ,")

    def _clean_markdown_line(self, value: str) -> str:
        value = re.sub(r"!\[[^\]]*]\([^)]+\)", " ", value)
        value = re.sub(r"\\([_*])", r"\1", value)
        value = re.sub(r"\$?\^\{?[^}]+\}?\$?", " ", value)
        value = value.strip().strip("|")
        return re.sub(r"\s+", " ", value).strip()

    def _is_author_candidate(self, value: str) -> bool:
        lowered = value.lower()
        if any(keyword in lowered for keyword in AFFILIATION_KEYWORDS):
            return False
        if any(char.isdigit() for char in value) or len(value) > 80:
            return False
        words = [word for word in re.split(r"\s+", value) if word]
        if len(words) < 2 or len(words) > 5:
            return False
        capitalized_words = [word for word in words if re.match(r"^[A-Z][A-Za-z'.-]+$", word)]
        return len(capitalized_words) >= 2

    def _title_from_filename(self, filename: str) -> str:
        stem = Path(filename).stem
        stem = re.sub(r"[_-]+", " ", stem)
        stem = re.sub(r"\s+", " ", stem).strip()
        return stem

    def _first_match(self, pattern: re.Pattern[str], text: str) -> str | None:
        match = pattern.search(text)
        return match.group(0) if match else None

    def _first_arxiv_id(self, text: str) -> str | None:
        match = ARXIV_RE.search(text)
        return match.group(1) if match else None

    def _year_from_text(self, text: str) -> int | None:
        match = re.search(r"\b(19|20)\d{2}\b", text)
        return int(match.group(0)) if match else None

    def _clean_identifier(self, value: str) -> str | None:
        value = value.strip().rstrip(".,;)")
        return value or None

    def _metadata_confidence(
        self,
        title: str,
        authors: list[Any],
        doi: str | None,
        external_ids: dict[str, Any],
    ) -> float:
        score = 0.0
        if title:
            score += 0.35
        if authors:
            score += 0.3
        if doi or external_ids:
            score += 0.25
        return min(score, 0.9)
