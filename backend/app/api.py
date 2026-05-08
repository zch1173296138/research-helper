import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, Response
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import Library, Paper, PaperChunk, ReviewMatrix
from backend.app.db.session import get_db
from backend.app.schemas import (
    ChatRequest,
    ChatResponse,
    ExportRequest,
    LibraryCreate,
    LibraryRead,
    MatrixRequest,
    MatrixResponse,
    PaperRead,
)
from backend.app.services.ids import new_id, slugify
from backend.app.services.llm import LLMService
from backend.app.services.markdown import format_markdown_for_display, rewrite_image_paths
from backend.app.services.papers import PaperService
from backend.app.services.vector_store import VectorStore


router = APIRouter(prefix="/api")


def settings_dep() -> Settings:
    return get_settings()


def paper_to_read(paper: Paper) -> PaperRead:
    return PaperRead(
        id=paper.id,
        library_id=paper.library_id,
        original_filename=paper.original_filename,
        status=paper.status,
        parser=paper.parser,
        error=paper.error,
        needs_ocr=paper.needs_ocr,
        md_path=paper.md_path,
    )


def paper_pdf_path(paper: Paper) -> Path:
    pdf_path = Path(paper.input_path)
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="Paper PDF not found")
    return pdf_path


def needs_cross_paper_context(question: str) -> bool:
    normalized = question.lower()
    keywords = (
        "差异",
        "区别",
        "不同",
        "异同",
        "比较",
        "对比",
        "这些论文",
        "这些文献",
        "多篇",
        "之间",
        "compare",
        "comparison",
        "contrast",
        "difference",
        "different",
    )
    return any(keyword in normalized for keyword in keywords)


@router.get("/health")
def health() -> dict:
    return {"ok": True}


@router.get("/libraries", response_model=list[LibraryRead])
def list_libraries(db: Session = Depends(get_db)) -> list[LibraryRead]:
    libraries = db.query(Library).order_by(Library.created_at.desc()).all()
    return [
        LibraryRead(
            id=library.id,
            name=library.name,
            description=library.description,
            paper_count=len(library.papers),
        )
        for library in libraries
    ]


@router.post("/libraries", response_model=LibraryRead)
def create_library(payload: LibraryCreate, db: Session = Depends(get_db)) -> LibraryRead:
    library_id = slugify(payload.name, "library")
    base_id = library_id
    counter = 2
    while db.get(Library, library_id):
        library_id = f"{base_id}_{counter}"
        counter += 1
    library = Library(id=library_id, name=payload.name, description=payload.description)
    db.add(library)
    db.commit()
    return LibraryRead(id=library.id, name=library.name, description=library.description, paper_count=0)


@router.get("/libraries/{library_id}/papers", response_model=list[PaperRead])
def list_papers(library_id: str, db: Session = Depends(get_db)) -> list[PaperRead]:
    papers = db.query(Paper).filter(Paper.library_id == library_id).order_by(Paper.created_at.desc()).all()
    return [paper_to_read(paper) for paper in papers]


@router.post("/libraries/{library_id}/papers/upload", response_model=list[PaperRead])
def upload_papers(
    library_id: str,
    files: list[UploadFile] = File(...),
    is_ocr: bool = Form(True),
    enable_formula: bool = Form(True),
    enable_table: bool = Form(True),
    language: str = Form("ch"),
    layout_model: str = Form("doclayout_yolo"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> list[PaperRead]:
    library = db.get(Library, library_id)
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")

    service = PaperService(settings)
    results: list[Paper] = []
    for upload in files:
        if not upload.filename or not upload.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Only PDF files are supported: {upload.filename}")
        results.append(
            service.ingest_upload(
                db,
                library_id,
                upload.filename,
                upload.file,
                is_ocr=is_ocr,
                enable_formula=enable_formula,
                enable_table=enable_table,
                language=language,
                layout_model=layout_model,
            )
        )
    return [paper_to_read(paper) for paper in results]


@router.get("/papers/{paper_id}", response_model=PaperRead)
def get_paper(paper_id: str, db: Session = Depends(get_db)) -> PaperRead:
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper_to_read(paper)


@router.delete("/papers/{paper_id}")
def delete_paper(
    paper_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> dict:
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    PaperService(settings).delete_paper(db, paper)
    return {"success": True, "paper_id": paper_id}


@router.get("/papers/{paper_id}/content")
def get_paper_content(paper_id: str, db: Session = Depends(get_db)) -> dict:
    paper = db.get(Paper, paper_id)
    if not paper or not paper.md_path:
        raise HTTPException(status_code=404, detail="Paper content not found")
    content = Path(paper.md_path).read_text(encoding="utf-8", errors="ignore")
    content = format_markdown_for_display(content)
    return {"paper_id": paper_id, "content": rewrite_image_paths(content, paper.library_id, paper.id)}


@router.get("/papers/{paper_id}/pdf")
def get_paper_pdf(paper_id: str, db: Session = Depends(get_db)):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    pdf_path = paper_pdf_path(paper)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=paper.original_filename,
        content_disposition_type="inline",
    )


@router.get("/papers/{paper_id}/pdf-info")
def get_paper_pdf_info(paper_id: str, db: Session = Depends(get_db)) -> dict:
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    pdf_path = paper_pdf_path(paper)
    try:
        import fitz

        with fitz.open(pdf_path) as doc:
            return {"paper_id": paper_id, "page_count": doc.page_count}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to read PDF: {exc}") from exc


@router.get("/papers/{paper_id}/pages/{page_number}.png")
def get_paper_page_image(
    paper_id: str,
    page_number: int,
    scale: float = Query(1.6, ge=0.75, le=3.0),
    db: Session = Depends(get_db),
) -> Response:
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    pdf_path = paper_pdf_path(paper)
    try:
        import fitz

        with fitz.open(pdf_path) as doc:
            if page_number < 1 or page_number > doc.page_count:
                raise HTTPException(status_code=404, detail="Page not found")
            page = doc.load_page(page_number - 1)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            return Response(
                pixmap.tobytes("png"),
                media_type="image/png",
                headers={"Cache-Control": "public, max-age=3600"},
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to render PDF page: {exc}") from exc


@router.get("/libraries/{library_id}/papers/{paper_id}/assets/{asset_path:path}")
def get_paper_asset(library_id: str, paper_id: str, asset_path: str, db: Session = Depends(get_db)):
    paper = db.get(Paper, paper_id)
    if not paper or paper.library_id != library_id:
        raise HTTPException(status_code=404, detail="Paper not found")
    full_path = (Path(paper.output_dir) / asset_path).resolve()
    output_dir = Path(paper.output_dir).resolve()
    if output_dir not in full_path.parents and full_path != output_dir:
        raise HTTPException(status_code=400, detail="Invalid asset path")
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Asset not found")
    media_type = mimetypes.guess_type(str(full_path))[0] or "application/octet-stream"
    return FileResponse(full_path, media_type=media_type)


@router.post("/libraries/{library_id}/build-index")
def build_index(
    library_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> dict:
    if not db.get(Library, library_id):
        raise HTTPException(status_code=404, detail="Library not found")
    count = PaperService(settings).rebuild_index(db, library_id)
    return {"success": True, "chunk_count": count}


@router.post("/papers/{paper_id}/summarize")
def summarize_paper(
    paper_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> dict:
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    summary = PaperService(settings).summarize(db, paper, LLMService(settings))
    return {"paper_id": paper_id, "summary": summary}


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> ChatResponse:
    paper_count = db.query(Paper).filter(Paper.library_id == payload.library_id).count()
    diversify = not payload.paper_ids and paper_count > 1 and needs_cross_paper_context(payload.question)
    chunks = VectorStore(settings).search(
        db,
        payload.library_id,
        payload.question,
        payload.paper_ids,
        payload.top_k,
        diversify_by_paper=diversify,
    )
    result = LLMService(settings).answer_with_citations(payload.question, chunks)
    return ChatResponse(**result)


@router.post("/review/matrix", response_model=MatrixResponse)
def build_matrix(
    payload: MatrixRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> MatrixResponse:
    query = db.query(Paper).filter(Paper.library_id == payload.library_id)
    if payload.paper_ids:
        query = query.filter(Paper.id.in_(payload.paper_ids))
    papers = query.order_by(Paper.created_at.asc()).all()

    service = PaperService(settings)
    llm = LLMService(settings)
    rows = []
    for paper in papers:
        summary = paper.summary.summary_json if paper.summary else service.summarize(db, paper, llm)
        rows.append(
            {
                "paper_id": paper.id,
                "filename": paper.original_filename,
                "research_question": summary.get("research_question", "未在原文中找到"),
                "method": summary.get("method", "未在原文中找到"),
                "dataset_or_materials": summary.get("dataset_or_materials", "未在原文中找到"),
                "experiment_setup": summary.get("experiment_setup", "未在原文中找到"),
                "key_findings": summary.get("key_findings", "未在原文中找到"),
                "limitations": summary.get("limitations", "未在原文中找到"),
                "evidence": summary.get("citations", []),
            }
        )
    matrix_id = new_id("matrix")
    matrix = ReviewMatrix(id=matrix_id, library_id=payload.library_id, topic=payload.topic, matrix_json={"rows": rows})
    db.add(matrix)
    db.commit()
    return MatrixResponse(id=matrix_id, rows=rows)


@router.post("/export/markdown")
def export_markdown(payload: ExportRequest, db: Session = Depends(get_db)) -> PlainTextResponse:
    library = db.get(Library, payload.library_id)
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")
    papers = db.query(Paper).filter(Paper.library_id == payload.library_id).order_by(Paper.created_at.asc()).all()
    matrix = db.get(ReviewMatrix, payload.matrix_id) if payload.matrix_id else None

    lines = [f"# {library.name}", "", "## 文献列表", ""]
    for paper in papers:
        lines.append(f"- {paper.original_filename} (`{paper.id}`) - {paper.status}")
    if matrix:
        lines.extend(["", "## Evidence Matrix", ""])
        rows = matrix.matrix_json.get("rows", [])
        headers = ["论文", "研究问题", "方法", "数据/材料", "主要结论", "局限"]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows:
            values = [
                row.get("filename", ""),
                row.get("research_question", ""),
                row.get("method", ""),
                row.get("dataset_or_materials", ""),
                row.get("key_findings", ""),
                row.get("limitations", ""),
            ]
            safe_values = [str(value).replace("\n", " ").replace("|", "\\|") for value in values]
            lines.append("| " + " | ".join(safe_values) + " |")
    return PlainTextResponse("\n".join(lines), media_type="text/markdown; charset=utf-8")


@router.get("/debug/chunks/{paper_id}")
def debug_chunks(paper_id: str, db: Session = Depends(get_db)) -> dict:
    chunks = db.query(PaperChunk).filter(PaperChunk.paper_id == paper_id).order_by(PaperChunk.chunk_index).all()
    return {"chunks": [{"id": chunk.id, "section": chunk.section_title, "text": chunk.text[:300]} for chunk in chunks]}
