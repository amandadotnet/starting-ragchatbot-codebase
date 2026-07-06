import pytest
from unittest.mock import MagicMock
from search_tools import CourseSearchTool, ToolManager
from vector_store import SearchResults


def _results(docs, metas, error=None):
    return SearchResults(
        documents=docs,
        metadata=metas,
        distances=[0.1] * len(docs),
        error=error,
    )


@pytest.fixture
def store():
    return MagicMock()


@pytest.fixture
def tool(store):
    return CourseSearchTool(store)


# ── CourseSearchTool ──────────────────────────────────────────────────────────

def test_tool_definition_name(tool):
    assert tool.get_tool_definition()["name"] == "search_course_content"


def test_tool_definition_query_is_required(tool):
    schema = tool.get_tool_definition()["input_schema"]
    assert "query" in schema["required"]


def test_execute_no_results_returns_message(tool, store):
    store.search.return_value = _results([], [])
    assert "No relevant content found" in tool.execute(query="anything")


def test_execute_no_results_with_course_filter_mentions_course(tool, store):
    store.search.return_value = _results([], [])
    result = tool.execute(query="anything", course_name="My Course")
    assert "My Course" in result


def test_execute_error_propagates(tool, store):
    store.search.return_value = _results([], [], error="DB unavailable")
    assert "DB unavailable" in tool.execute(query="anything")


def test_execute_formats_result_header(tool, store):
    store.search.return_value = _results(
        ["Lesson body text"],
        [{"course_title": "Python 101", "lesson_number": 1}],
    )
    result = tool.execute(query="python")
    assert "[Python 101 - Lesson 1]" in result
    assert "Lesson body text" in result


def test_execute_header_omits_lesson_when_absent(tool, store):
    store.search.return_value = _results(
        ["Body text"],
        [{"course_title": "Python 101"}],
    )
    result = tool.execute(query="python")
    assert "[Python 101]" in result
    assert "Lesson" not in result.split("[Python 101]")[0]


def test_execute_tracks_sources(tool, store):
    store.search.return_value = _results(
        ["content"],
        [{"course_title": "My Course", "lesson_number": 2}],
    )
    store.get_lesson_link.return_value = None
    store.get_course_link.return_value = None
    tool.execute(query="something")
    assert "My Course - Lesson 2" in tool.last_sources


def test_execute_passes_filters_to_store(tool, store):
    store.search.return_value = _results([], [])
    tool.execute(query="topic", course_name="Course A", lesson_number=3)
    store.search.assert_called_once_with(
        query="topic", course_name="Course A", lesson_number=3
    )


def test_execute_multiple_results(tool, store):
    store.search.return_value = _results(
        ["doc one", "doc two"],
        [
            {"course_title": "Course A", "lesson_number": 1},
            {"course_title": "Course B", "lesson_number": 2},
        ],
    )
    result = tool.execute(query="q")
    assert "[Course A - Lesson 1]" in result
    assert "[Course B - Lesson 2]" in result
    assert len(tool.last_sources) == 2


# ── ToolManager ───────────────────────────────────────────────────────────────

def test_tool_manager_register_appears_in_definitions(store):
    tm = ToolManager()
    tm.register_tool(CourseSearchTool(store))
    defs = tm.get_tool_definitions()
    assert len(defs) == 1
    assert defs[0]["name"] == "search_course_content"


def test_tool_manager_execute_unknown_tool_returns_message():
    tm = ToolManager()
    assert "not found" in tm.execute_tool("no_such_tool")


def test_tool_manager_execute_routes_to_tool(store):
    store.search.return_value = _results([], [])
    tm = ToolManager()
    tm.register_tool(CourseSearchTool(store))
    result = tm.execute_tool("search_course_content", query="test")
    assert "No relevant content found" in result


def test_tool_manager_get_last_sources(store):
    store.search.return_value = _results(
        ["content"], [{"course_title": "Course A", "lesson_number": 1}]
    )
    store.get_lesson_link.return_value = None
    store.get_course_link.return_value = None
    tm = ToolManager()
    tm.register_tool(CourseSearchTool(store))
    tm.execute_tool("search_course_content", query="test")
    assert "Course A - Lesson 1" in tm.get_last_sources()


def test_tool_manager_reset_sources(store):
    store.search.return_value = _results(
        ["content"], [{"course_title": "Course A", "lesson_number": 1}]
    )
    tm = ToolManager()
    ct = CourseSearchTool(store)
    tm.register_tool(ct)
    tm.execute_tool("search_course_content", query="test")

    tm.reset_sources()
    assert ct.last_sources == []
    assert tm.get_last_sources() == []
