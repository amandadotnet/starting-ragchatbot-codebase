# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
uv sync
```

**Run the app** (from repo root, using Git Bash on Windows):
```bash
./run.sh
```

Or manually (must run from `backend/` so relative paths resolve):
```bash
cd backend && uv run uvicorn app:app --reload --port 8000
```

The app serves at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

**Environment setup:** Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`.

There is no test suite. To verify behavior, run the server and exercise `POST /api/query` or the web UI.

## Architecture

This is a full-stack RAG system: FastAPI backend + static HTML/JS/CSS frontend. The backend serves the frontend as static files from `../frontend` (relative to `backend/`), so the server must start from the `backend/` directory.

### Request flow

```
POST /api/query
  → RAGSystem.query()
    → AIGenerator.generate_response()   # calls Claude with search tool
      → Claude invokes search_course_content tool
        → ToolManager.execute_tool()
          → CourseSearchTool.execute()
            → VectorStore.search()      # ChromaDB semantic search
      → Claude synthesizes final answer from tool results
  → SessionManager.add_exchange()       # persist to in-memory history
```

### Key components

- **`backend/app.py`** — FastAPI entrypoint. Loads all docs from `../docs/` on startup (skips courses already in the vector store). Serves frontend static files.
- **`backend/rag_system.py`** — Orchestrator. Wires together all components; the only place that knows about all of them.
- **`backend/ai_generator.py`** — Wraps the Anthropic SDK. Handles the two-turn tool-use loop: initial response with `tool_use` stop reason → execute tool → follow-up call for final answer.
- **`backend/vector_store.py`** — ChromaDB wrapper with two collections: `course_catalog` (course titles/metadata for fuzzy course name resolution) and `course_content` (chunked text for semantic search). ChromaDB is persisted at `backend/chroma_db/`.
- **`backend/search_tools.py`** — Defines the `search_course_content` Anthropic tool and the `ToolManager` registry. Adding a new tool means implementing `Tool` ABC and calling `tool_manager.register_tool()`.
- **`backend/document_processor.py`** — Parses `.txt`, `.pdf`, `.docx` files from `docs/` into `Course`/`Lesson`/`CourseChunk` models and splits content into chunks.
- **`backend/session_manager.py`** — In-memory conversation history. Sessions are lost on server restart. Keeps last `MAX_HISTORY` (default: 2) exchanges per session.
- **`backend/config.py`** — All tuneable settings: model (`claude-sonnet-4-20250514`), embedding model (`all-MiniLM-L6-v2`), chunk size (800), overlap (100), max results (5), max history (2), ChromaDB path.
- **`backend/models.py`** — Pydantic models: `Course`, `Lesson`, `CourseChunk`.

### Data model

`course_catalog` stores one document per course (the title), with metadata: `title`, `instructor`, `course_link`, `lessons_json` (serialized list), `lesson_count`. Course title is used as the ChromaDB document ID.

`course_content` stores one document per text chunk, with metadata: `course_title`, `lesson_number`, `chunk_index`. IDs are `{course_title_underscored}_{chunk_index}`.

Course name filtering uses semantic search on `course_catalog` first to resolve a fuzzy name to an exact title, then filters `course_content` by that title.
