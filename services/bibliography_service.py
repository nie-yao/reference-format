from __future__ import annotations

import shutil
import sys
import uuid
from io import BytesIO
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional

from runtime_paths import get_jobs_root


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.bibliography import BibliographyManager  # noqa: E402


@dataclass
class ProcessOptions:
    deduplicate: bool = True
    sort: bool = True
    remove_uncited: bool = False


class ProcessingError(Exception):
    """Raised when the request cannot be processed into a usable result."""


class BibliographyProcessingService:
    def __init__(self, jobs_root: Optional[Path] = None):
        self.jobs_root = jobs_root or get_jobs_root()
        self.jobs_root.mkdir(parents=True, exist_ok=True)

    def process(
        self,
        bib_stream: Optional[BinaryIO] = None,
        bib_filename: Optional[str] = None,
        bib_text: Optional[str] = None,
        tex_stream: Optional[BinaryIO] = None,
        tex_filename: Optional[str] = None,
        tex_text: Optional[str] = None,
        options: Optional[ProcessOptions] = None,
    ) -> dict:
        options = options or ProcessOptions()
        self._validate_inputs(
            bib_stream=bib_stream,
            bib_text=bib_text,
            tex_stream=tex_stream,
            tex_text=tex_text,
            remove_uncited=options.remove_uncited,
        )

        job_id = uuid.uuid4().hex
        job_dir = self.jobs_root / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        bib_path = job_dir / self._safe_name(bib_filename, "references.bib")
        tex_path = job_dir / self._safe_name(tex_filename, "main.tex") if (tex_stream or tex_text) else None
        output_path = job_dir / "reference_formatted.txt"

        if bib_stream:
            self._write_upload(bib_stream, bib_path)
        elif bib_text is not None:
            self._write_text(bib_text, bib_path)

        if tex_stream and tex_path:
            self._write_upload(tex_stream, tex_path)
        elif tex_text is not None and tex_path:
            self._write_text(tex_text, tex_path)

        manager = BibliographyManager()
        manager.load_references(str(bib_path))

        if tex_path is not None:
            manager.load_main_text(str(tex_path))

        if not manager.entries and manager.get_error_count() > 0:
            raise ProcessingError("Failed to parse the uploaded .bib file.")

        manager.format_all()

        if options.deduplicate:
            manager.deduplicate()

        if options.sort:
            manager.sort()

        if options.remove_uncited:
            manager.remove_uncited()

        manager.save_to_file(str(output_path))
        output_text = output_path.read_text(encoding="utf-8")

        return {
            "success": True,
            "job_id": job_id,
            "output_text": output_text,
            "stats": manager.get_stats(),
            "errors": manager.errors,
            "download_url": f"/api/download/{job_id}",
        }

    def get_download_path(self, job_id: str) -> Path:
        path = self.jobs_root / job_id / "reference_formatted.txt"
        if not path.exists():
            raise FileNotFoundError(f"No generated result found for job '{job_id}'.")
        return path

    def cleanup_job(self, job_id: str) -> None:
        job_dir = self.jobs_root / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)

    @staticmethod
    def _safe_name(filename: Optional[str], fallback: str) -> str:
        if not filename:
            return fallback
        return Path(filename).name or fallback

    @staticmethod
    def _validate_inputs(
        bib_stream: Optional[BinaryIO],
        bib_text: Optional[str],
        tex_stream: Optional[BinaryIO],
        tex_text: Optional[str],
        remove_uncited: bool,
    ) -> None:
        has_bib_file = bib_stream is not None
        has_bib_text = bool((bib_text or "").strip())
        has_tex_file = tex_stream is not None
        has_tex_text = bool((tex_text or "").strip())

        if has_bib_file and has_bib_text:
            raise ProcessingError("Choose either a .bib file or pasted BibTeX text, not both.")
        if not has_bib_file and not has_bib_text:
            raise ProcessingError("Please upload a .bib file or paste BibTeX text.")

        if has_tex_file and has_tex_text:
            raise ProcessingError("Choose either a .tex file or pasted TeX text, not both.")

        if remove_uncited and not (has_tex_file or has_tex_text):
            raise ProcessingError("Remove uncited requires a .tex file or pasted TeX text.")

    @staticmethod
    def _write_upload(stream: BinaryIO, destination: Path) -> None:
        with destination.open("wb") as target:
            shutil.copyfileobj(stream, target)

    @staticmethod
    def _write_text(content: str, destination: Path) -> None:
        destination.write_text(content, encoding="utf-8")
