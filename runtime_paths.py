from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_bundle_root() -> Path:
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_project_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_templates_dir() -> Path:
    return get_bundle_root() / "templates"


def get_static_dir() -> Path:
    return get_bundle_root() / "static"


def get_jobs_root() -> Path:
    if is_frozen():
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            root = Path(local_appdata) / "BibTeXFormatter" / "jobs"
        else:
            root = Path(tempfile.gettempdir()) / "BibTeXFormatter" / "jobs"
    else:
        root = get_project_root() / ".web_jobs"

    root.mkdir(parents=True, exist_ok=True)
    return root
