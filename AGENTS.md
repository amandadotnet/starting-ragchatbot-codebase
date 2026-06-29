# AGENTS.md — Agent instructions for this repository

Purpose
- Provide concise, actionable guidance for AI coding agents working on this repo.

Quick Start (for agents)
- Python: requires >= 3.13 (see `pyproject.toml`).
- Install deps: run the workspace's dependency manager:
  - `uv sync` (see [pyproject.toml](pyproject.toml))
- Run locally:
  - `./run.sh` (quick start)
  - or `cd backend && uv run uvicorn app:app --reload --port 8000`
- Env: create a `.env` with `ANTHROPIC_API_KEY` before running (see [README.md](README.md)).

Key files and responsibilities
- `backend/app.py`: FastAPI entrypoint and startup document loader.
- `backend/rag_system.py`: Core RAG orchestration (query, indexing, session handling).
- `backend/vector_store.py`: Chroma DB integration and vector storage helpers.
- `backend/document_processor.py`: Document parsing and chunking logic.
- `backend/session_manager.py`: Session lifecycle and storage.
- `docs/`: Source course materials used to build the vector DB.
- `frontend/`: Static web UI served by the backend.
- `pyproject.toml`: Python metadata and dependencies.

Agent guidance and conventions
- Prefer reading linked docs rather than copying them — follow the "link, don't embed" rule.
- Minimize scope: make the smallest change that solves the issue; preserve existing APIs.
- Avoid modifying unrelated files or upgrading dependencies unless explicitly requested.
- When adding or changing runtime behavior, update `README.md` with concise run steps.
- For tests or verification, run the server locally and exercise `/api/query` or the web UI.

Dev environment notes
- On Windows, use Git Bash for shell scripts (see [README.md](README.md)).
- The app loads documents from `docs/` at startup (see `backend/app.py`).

When to create additional agent customizations
- If work will focus on a specific area (frontend/backend/vector store), create a small
  skill or `.github/copilot-instructions.md` scoped to that area and link back to this file.

Suggested next customizations
- `create-skill backend` — focus on `backend/` conventions and testing steps.
- `create-skill docs` — instructions for adding new course materials and reindexing.
