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

## Available API endpoints

- `GET /api/health`
- `POST /api/process`
- `GET /api/download/{job_id}`

## Notes

- The core formatting, deduplication, sorting, and uncited-removal logic now lives in `core/bibliography/formatter.py` and `core/bibliography/manager.py`.
- The web layer only wraps the existing `BibliographyManager` pipeline.
