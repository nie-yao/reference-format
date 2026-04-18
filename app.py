from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.routes import router
from runtime_paths import get_static_dir
from services.bibliography_service import ProcessingError


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = get_static_dir()

app = FastAPI(title="BibTeX to LaTeX Formatter")
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(router)


@app.exception_handler(ProcessingError)
async def processing_error_handler(_: Request, exc: ProcessingError):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "output_text": "",
            "stats": {},
            "errors": [{"stage": "process", "message": str(exc)}],
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "output_text": "",
            "stats": {},
            "errors": [{"stage": "server", "message": str(exc)}],
        },
    )


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
