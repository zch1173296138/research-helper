import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

try:
    import tiktoken
except Exception:  # pragma: no cover - optional dependency fallback
    tiktoken = None


HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
PAGE_RE = re.compile(r"<!--\s*page:(\d+)\s*-->")
REFERENCE_HEADING_RE = re.compile(r"^(#{1,6})\s+(?:\d+\.?\s*)?(references|参考文献)\s*$", re.IGNORECASE)
REFERENCE_ENTRY_RE = re.compile(r"^\[(\d+)\]\s*(.*)$")
NOISE_BLOCK_START_RE = re.compile(
    r"^(?:\*+\s*)?(?:"
    r"this work (?:is|was) supported\b|"
    r"permission to make digital or hard copies\b|"
    r"to copy otherwise\b"
    r")",
    re.IGNORECASE,
)
NOISE_LINE_RE = re.compile(
    r"^(?:"
    r"[A-Z][A-Z0-9-]+(?:-[A-Z0-9]+)?\s+\d{1,2}/\d{2}\b|"
    r"\$?\d+(?:\.\d{2})?$"
    r")",
    re.IGNORECASE,
)


@dataclass
class Chunk:
    chunk_index: int
    section_title: str
    text: str
    token_count: int
    page_start: int | None = None
    page_end: int | None = None


def count_tokens(text: str) -> int:
    if tiktoken is not None:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            pass
    # Good enough for Chinese/English mixed chunk sizing.
    return max(1, len(text) // 3)


def clean_markdown(raw: str) -> str:
    lines = [line.rstrip() for line in raw.replace("\r\n", "\n").split("\n")]
    cleaned: list[str] = []
    blank_count = 0
    seen_short_lines: dict[str, int] = {}
    skipping_noise_block = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            skipping_noise_block = False
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
            continue

        if skipping_noise_block:
            continue

        normalized = re.sub(r"\s+", " ", stripped).strip("* ")
        if NOISE_BLOCK_START_RE.match(normalized):
            skipping_noise_block = True
            continue
        if _is_front_matter_noise_line(normalized):
            continue

        blank_count = 0
        if len(normalized) < 80 and not normalized.startswith(("#", "|", "!", "<!--")):
            seen_short_lines[normalized] = seen_short_lines.get(normalized, 0) + 1
            if seen_short_lines[normalized] > 3:
                continue

        cleaned.append(line)

    return "\n".join(cleaned).strip() + "\n"


def rewrite_image_paths(markdown: str, library_id: str, paper_id: str) -> str:
    def replace(match: re.Match[str]) -> str:
        alt = match.group(1)
        path = match.group(2)
        if path.startswith(("http://", "https://", "/api/")):
            return match.group(0)
        safe_path = path[2:] if path.startswith("./") else path
        safe_path = safe_path.replace("\\", "/")
        encoded_path = quote(safe_path, safe="/")
        return f"![{alt}](/api/libraries/{library_id}/papers/{paper_id}/assets/{encoded_path})"

    return IMAGE_RE.sub(replace, markdown)


def format_markdown_for_display(markdown: str) -> str:
    """Normalize noisy PDF Markdown for browser reading without changing stored files."""
    normalized = _dedupe_consecutive_headings(markdown.replace("\r\n", "\n"))
    normalized = _normalize_reference_section(normalized)
    return re.sub(r"\n{3,}", "\n\n", normalized).strip() + "\n"


def _is_front_matter_noise_line(line: str) -> bool:
    """Drop publisher boilerplate commonly extracted from the first PDF page."""
    if re.match(r"^copyright\s+\d{4}\s+(?:acm|ieee)\b", line, re.IGNORECASE):
        return True
    if re.match(r"^[A-Z][A-Z0-9-]+(?:-[A-Z0-9]+)?\s+\d{1,2}/\d{2}\b", line):
        return True
    if NOISE_LINE_RE.match(line) and any(token in line.lower() for token in ("acm", "ieee", "usenix", "sig")):
        return True
    return False


def _dedupe_consecutive_headings(markdown: str) -> str:
    lines = markdown.split("\n")
    output: list[str] = []
    previous_heading: str | None = None
    previous_nonblank_was_heading = False

    for line in lines:
        stripped = line.strip()
        heading_match = HEADER_RE.match(stripped)
        if heading_match:
            heading_text = heading_match.group(2).strip().lower()
            if previous_nonblank_was_heading and heading_text == previous_heading:
                continue
            previous_heading = heading_text
            previous_nonblank_was_heading = True
        elif stripped:
            previous_nonblank_was_heading = False

        output.append(line)

    return "\n".join(output)


def _normalize_reference_section(markdown: str) -> str:
    lines = markdown.split("\n")
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        heading_match = REFERENCE_HEADING_RE.match(line.strip())
        if not heading_match:
            output.append(line)
            index += 1
            continue

        heading_level = heading_match.group(1)
        output.append(f"{heading_level} References")
        output.append("")
        index += 1

        reference_lines: list[str] = []
        while index < len(lines):
            next_line = lines[index]
            if next_line.strip().startswith("#") and not REFERENCE_HEADING_RE.match(next_line.strip()):
                break
            reference_lines.append(next_line)
            index += 1

        references = _collect_references(reference_lines)
        if references:
            for number, text in sorted(references, key=lambda item: item[0]):
                output.append(f"- **[{number}]** {text}")
            output.append("")
        continue

    return "\n".join(output)


def _collect_references(lines: list[str]) -> list[tuple[int, str]]:
    references: list[tuple[int, str]] = []
    current_number: int | None = None
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_number, current_parts
        if current_number is None:
            return
        text = re.sub(r"\s+", " ", " ".join(current_parts)).strip()
        if text:
            references.append((current_number, text))
        current_number = None
        current_parts = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        entry_match = REFERENCE_ENTRY_RE.match(stripped)
        if entry_match:
            flush()
            current_number = int(entry_match.group(1))
            current_parts = [entry_match.group(2)]
        elif current_number is not None:
            current_parts.append(stripped)

    flush()
    return references


def split_markdown(markdown: str, source_path: Path, target_tokens: int = 1000, overlap_tokens: int = 180) -> list[Chunk]:
    paragraphs = re.split(r"\n\s*\n", markdown)
    chunks: list[Chunk] = []
    current: list[str] = []
    current_tokens = 0
    current_section = ""
    current_page: int | None = None
    chunk_pages: list[int] = []

    def flush() -> None:
        nonlocal current, current_tokens, chunk_pages
        text = "\n\n".join(part for part in current if part.strip()).strip()
        if not text:
            current = []
            current_tokens = 0
            chunk_pages = []
            return
        pages = sorted(set(chunk_pages))
        chunks.append(
            Chunk(
                chunk_index=len(chunks),
                section_title=current_section,
                text=text,
                token_count=count_tokens(text),
                page_start=pages[0] if pages else None,
                page_end=pages[-1] if pages else None,
            )
        )

        if overlap_tokens <= 0:
            current = []
            current_tokens = 0
            chunk_pages = []
            return

        overlap: list[str] = []
        overlap_count = 0
        for part in reversed(current):
            part_tokens = count_tokens(part)
            if overlap and overlap_count + part_tokens > overlap_tokens:
                break
            overlap.insert(0, part)
            overlap_count += part_tokens
        current = overlap
        current_tokens = overlap_count
        chunk_pages = pages[-1:] if pages else []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        page_match = PAGE_RE.search(paragraph)
        if page_match:
            current_page = int(page_match.group(1))

        header_match = HEADER_RE.match(paragraph)
        if header_match:
            current_section = header_match.group(2).strip()

        paragraph_tokens = count_tokens(paragraph)
        if current and current_tokens + paragraph_tokens > target_tokens:
            flush()

        current.append(paragraph)
        current_tokens += paragraph_tokens
        if current_page is not None:
            chunk_pages.append(current_page)

    flush()
    return chunks
