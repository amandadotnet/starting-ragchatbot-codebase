"""
Tests for RAGSystem.

DocumentProcessor, VectorStore, AIGenerator, and SessionManager are patched
at construction time so RAGSystem is tested in isolation from ChromaDB,
the Anthropic client, and the filesystem. ToolManager/CourseSearchTool are
left real since they're cheap and RAGSystem's wiring of them is worth
covering directly.
"""

import pytest
from unittest.mock import MagicMock, patch
from rag_system import RAGSystem
from models import Course, Lesson, CourseChunk


@pytest.fixture
def config():
    cfg = MagicMock()
    cfg.CHUNK_SIZE = 800
    cfg.CHUNK_OVERLAP = 100
    cfg.CHROMA_PATH = "/tmp/chroma"
    cfg.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    cfg.MAX_RESULTS = 5
    cfg.ANTHROPIC_API_KEY = "test-key"
    cfg.ANTHROPIC_MODEL = "claude-test"
    cfg.MAX_HISTORY = 2
    return cfg


@pytest.fixture
def rag(config):
    with patch("rag_system.DocumentProcessor") as MockDP, \
         patch("rag_system.VectorStore") as MockVS, \
         patch("rag_system.AIGenerator") as MockAI, \
         patch("rag_system.SessionManager") as MockSM:
        system = RAGSystem(config)
        yield system


def _course(title="Course A"):
    return Course(title=title, lessons=[Lesson(lesson_number=1, title="Intro")])


def _chunks(title="Course A", n=2):
    return [
        CourseChunk(content=f"chunk {i}", course_title=title, chunk_index=i)
        for i in range(n)
    ]


# ── construction / wiring ───────────────────────────────────────────────────

def test_init_constructs_components_from_config(config):
    with patch("rag_system.DocumentProcessor") as MockDP, \
         patch("rag_system.VectorStore") as MockVS, \
         patch("rag_system.AIGenerator") as MockAI, \
         patch("rag_system.SessionManager") as MockSM:
        system = RAGSystem(config)

    MockDP.assert_called_once_with(config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    MockVS.assert_called_once_with(
        config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS
    )
    MockAI.assert_called_once_with(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)
    MockSM.assert_called_once_with(config.MAX_HISTORY)
    assert system.document_processor is MockDP.return_value
    assert system.vector_store is MockVS.return_value
    assert system.ai_generator is MockAI.return_value
    assert system.session_manager is MockSM.return_value


def test_init_registers_search_tool(rag):
    defs = rag.tool_manager.get_tool_definitions()
    assert len(defs) == 1
    assert defs[0]["name"] == "search_course_content"


# ── add_course_document ─────────────────────────────────────────────────────

def test_add_course_document_returns_course_and_chunk_count(rag):
    course = _course()
    chunks = _chunks(n=3)
    rag.document_processor.process_course_document.return_value = (course, chunks)

    result_course, count = rag.add_course_document("some/path.txt")

    assert result_course is course
    assert count == 3


def test_add_course_document_adds_to_vector_store(rag):
    course = _course()
    chunks = _chunks(n=2)
    rag.document_processor.process_course_document.return_value = (course, chunks)

    rag.add_course_document("some/path.txt")

    rag.vector_store.add_course_metadata.assert_called_once_with(course)
    rag.vector_store.add_course_content.assert_called_once_with(chunks)


def test_add_course_document_handles_processing_error(rag):
    rag.document_processor.process_course_document.side_effect = ValueError("bad file")

    result_course, count = rag.add_course_document("bad/path.txt")

    assert result_course is None
    assert count == 0
    rag.vector_store.add_course_metadata.assert_not_called()


# ── add_course_folder ───────────────────────────────────────────────────────

def test_add_course_folder_missing_folder_returns_zero(rag):
    courses, chunks = rag.add_course_folder("/does/not/exist")
    assert (courses, chunks) == (0, 0)


def test_add_course_folder_adds_new_courses(rag, tmp_path):
    (tmp_path / "course1.txt").write_text("content")
    (tmp_path / "course2.pdf").write_text("content")
    (tmp_path / "ignore.png").write_text("content")

    rag.vector_store.get_existing_course_titles.return_value = []
    rag.document_processor.process_course_document.side_effect = [
        (_course("Course 1"), _chunks("Course 1", n=2)),
        (_course("Course 2"), _chunks("Course 2", n=3)),
    ]

    total_courses, total_chunks = rag.add_course_folder(str(tmp_path))

    assert total_courses == 2
    assert total_chunks == 5
    assert rag.vector_store.add_course_metadata.call_count == 2


def test_add_course_folder_skips_existing_courses(rag, tmp_path):
    (tmp_path / "course1.txt").write_text("content")

    rag.vector_store.get_existing_course_titles.return_value = ["Course 1"]
    rag.document_processor.process_course_document.return_value = (
        _course("Course 1"),
        _chunks("Course 1"),
    )

    total_courses, total_chunks = rag.add_course_folder(str(tmp_path))

    assert (total_courses, total_chunks) == (0, 0)
    rag.vector_store.add_course_metadata.assert_not_called()


def test_add_course_folder_clear_existing_clears_store(rag, tmp_path):
    rag.vector_store.get_existing_course_titles.return_value = []

    rag.add_course_folder(str(tmp_path), clear_existing=True)

    rag.vector_store.clear_all_data.assert_called_once()


def test_add_course_folder_skips_file_processing_errors(rag, tmp_path):
    (tmp_path / "course1.txt").write_text("content")
    (tmp_path / "course2.txt").write_text("content")

    rag.vector_store.get_existing_course_titles.return_value = []
    rag.document_processor.process_course_document.side_effect = [
        Exception("corrupt file"),
        (_course("Course 2"), _chunks("Course 2")),
    ]

    total_courses, total_chunks = rag.add_course_folder(str(tmp_path))

    assert total_courses == 1
    assert total_chunks == 2


# ── query ────────────────────────────────────────────────────────────────────

def test_query_returns_response_and_sources(rag):
    rag.ai_generator.generate_response.return_value = "The answer"
    with patch.object(rag.tool_manager, "get_last_sources", return_value=["Course A - Lesson 1"]):
        response, sources = rag.query("What is X?")

    assert response == "The answer"
    assert sources == ["Course A - Lesson 1"]


def test_query_includes_question_in_prompt(rag):
    rag.ai_generator.generate_response.return_value = "answer"
    rag.query("What is X?")

    call_kwargs = rag.ai_generator.generate_response.call_args.kwargs
    assert "What is X?" in call_kwargs["query"]


def test_query_passes_tools_and_tool_manager(rag):
    rag.ai_generator.generate_response.return_value = "answer"
    rag.query("What is X?")

    call_kwargs = rag.ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["tools"] == rag.tool_manager.get_tool_definitions()
    assert call_kwargs["tool_manager"] is rag.tool_manager


def test_query_without_session_id_skips_history(rag):
    rag.ai_generator.generate_response.return_value = "answer"
    rag.query("What is X?")

    rag.session_manager.get_conversation_history.assert_not_called()
    rag.session_manager.add_exchange.assert_not_called()


def test_query_with_session_id_uses_history(rag):
    rag.session_manager.get_conversation_history.return_value = "prior history"
    rag.ai_generator.generate_response.return_value = "answer"

    rag.query("What is X?", session_id="sess-1")

    rag.session_manager.get_conversation_history.assert_called_once_with("sess-1")
    call_kwargs = rag.ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["conversation_history"] == "prior history"


def test_query_with_session_id_updates_history(rag):
    rag.ai_generator.generate_response.return_value = "The answer"

    rag.query("What is X?", session_id="sess-1")

    rag.session_manager.add_exchange.assert_called_once_with(
        "sess-1", "What is X?", "The answer"
    )


def test_query_resets_sources_after_retrieving(rag):
    rag.ai_generator.generate_response.return_value = "answer"
    with patch.object(rag.tool_manager, "get_last_sources", return_value=["src"]), \
         patch.object(rag.tool_manager, "reset_sources") as mock_reset:
        rag.query("What is X?")

    mock_reset.assert_called_once()


# ── get_course_analytics ────────────────────────────────────────────────────

def test_get_course_analytics(rag):
    rag.vector_store.get_course_count.return_value = 4
    rag.vector_store.get_existing_course_titles.return_value = ["A", "B", "C", "D"]

    analytics = rag.get_course_analytics()

    assert analytics == {
        "total_courses": 4,
        "course_titles": ["A", "B", "C", "D"],
    }
