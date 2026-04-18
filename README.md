# BibTeX to LaTeX Formatter

This project now supports both the original CLI flow and a web application built on top of the existing bibliography logic.

## Project structure

- `api/`: HTTP routes for the page and processing endpoints
- `core/bibliography/`: core domain logic for formatting and managing bibliography entries
- `services/`: web-facing service layer that wraps the core pipeline
- `cli/`: CLI entrypoint
- `templates/`: web UI template
- `app.py`: FastAPI web entrypoint

## Run the web app

```bash
uv sync
uv run python app.py
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Run on Windows

- Double-click `install_and_start.bat` the first time to create `.venv`, install dependencies, and launch the app.
- After that, you can use `start_app.bat` for one-click startup.

## Build a Windows executable

1. Install dependencies in your environment.
2. Build the app:

```bash
python build_windows.py --mode onedir
```

For a single-file executable:

```bash
python build_windows.py --mode onefile
```

After the build finishes:

- `dist/BibTeXFormatter/` contains the one-directory app
- or `dist/BibTeXFormatter.exe` contains the single-file app

The packaged app starts the local FastAPI server and opens the browser automatically.

## Available API endpoints

- `GET /api/health`
- `POST /api/process`
- `GET /api/download/{job_id}`

## Notes

- The core formatting, deduplication, sorting, and uncited-removal logic now lives in `core/bibliography/formatter.py` and `core/bibliography/manager.py`.
- The web layer only wraps the existing `BibliographyManager` pipeline.
