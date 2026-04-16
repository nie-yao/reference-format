from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from services.bibliography_service import (
    BibliographyProcessingService,
    ProcessOptions,
    ProcessingError,
)


BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
service = BibliographyProcessingService()

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "BibTeX to LaTeX Formatter",
        },
    )


@router.get("/api/health")
async def health():
    return {"success": True, "status": "ok"}


@router.post("/api/process")
async def process_bibliography(
    bib_file: UploadFile = File(...),
    tex_file: Optional[UploadFile] = File(None),
    deduplicate: bool = Form(True),
    sort: bool = Form(True),
    remove_uncited: bool = Form(False),
):
    if not bib_file.filename:
        raise ProcessingError("Please upload a .bib file.")

    if not bib_file.filename.lower().endswith(".bib"):
        raise ProcessingError("The bibliography file must be a .bib file.")

    if tex_file and tex_file.filename and not tex_file.filename.lower().endswith(".tex"):
        raise ProcessingError("The optional main text file must be a .tex file.")

    options = ProcessOptions(
        deduplicate=deduplicate,
        sort=sort,
        remove_uncited=remove_uncited,
    )

    try:
        return service.process(
            bib_stream=bib_file.file,
            bib_filename=bib_file.filename,
            tex_stream=tex_file.file if tex_file else None,
            tex_filename=tex_file.filename if tex_file else None,
            options=options,
        )
    finally:
        await bib_file.close()
        if tex_file:
            await tex_file.close()


@router.get("/api/download/{job_id}")
async def download_result(job_id: str):
    try:
        output_path = service.get_download_path(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(
        path=output_path,
        filename="reference_formatted.txt",
        media_type="text/plain; charset=utf-8",
    )
