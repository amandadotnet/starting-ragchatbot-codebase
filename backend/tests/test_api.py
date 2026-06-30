"""
FastAPI endpoint tests.

app.py is imported inside a module-scoped fixture so that conftest.py's
sys.modules mocks are guaranteed to be in place first. Each test gets a
fresh mock_rag and a patched app.rag_system so endpoint behaviour is fully
controlled without touching ChromaDB or the Anthropic API.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(scope="module")
def app_module():
    import app  # noqa: PLC0415 — intentional deferred import
    return app


@pytest.fixture
def mock_rag():
    mock = MagicMock()
    mock.query.return_value = ("Test answer", ["Course A - Lesson 1"])
    mock.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course A", "Course B"],
    }
    mock.session_manager.create_session.return_value = "new_session"
    return mock


@pytest.fixture
def client(app_module, mock_rag):
    from fastapi.testclient import TestClient

    with patch.object(app_module, "rag_system", mock_rag):
        yield TestClient(app_module.app), mock_rag


# ── GET /api/courses ──────────────────────────────────────────────────────────

def test_get_courses_status_ok(client):
    tc, _ = client
    assert tc.get("/api/courses").status_code == 200


def test_get_courses_shape(client):
    tc, _ = client
    data = tc.get("/api/courses").json()
    assert "total_courses" in data
    assert "course_titles" in data


def test_get_courses_values(client):
    tc, _ = client
    data = tc.get("/api/courses").json()
    assert data["total_courses"] == 2
    assert "Course A" in data["course_titles"]
    assert "Course B" in data["course_titles"]


# ── POST /api/query ───────────────────────────────────────────────────────────

def test_post_query_status_ok(client):
    tc, _ = client
    r = tc.post("/api/query", json={"query": "What is Python?", "session_id": "s1"})
    assert r.status_code == 200


def test_post_query_returns_answer(client):
    tc, _ = client
    data = tc.post("/api/query", json={"query": "What is Python?", "session_id": "s1"}).json()
    assert data["answer"] == "Test answer"


def test_post_query_returns_sources(client):
    tc, _ = client
    data = tc.post("/api/query", json={"query": "What is Python?", "session_id": "s1"}).json()
    assert "Course A - Lesson 1" in data["sources"]


def test_post_query_echoes_session_id(client):
    tc, _ = client
    data = tc.post("/api/query", json={"query": "Hello", "session_id": "my_session"}).json()
    assert data["session_id"] == "my_session"


def test_post_query_creates_session_when_none_provided(client):
    tc, mock = client
    data = tc.post("/api/query", json={"query": "Hello"}).json()
    assert data["session_id"] == "new_session"
    mock.session_manager.create_session.assert_called_once()


def test_post_query_skips_session_creation_when_id_provided(client):
    tc, mock = client
    tc.post("/api/query", json={"query": "Hello", "session_id": "existing"})
    mock.session_manager.create_session.assert_not_called()


def test_post_query_calls_rag_with_correct_args(client):
    tc, mock = client
    tc.post("/api/query", json={"query": "Tell me about Python", "session_id": "s1"})
    mock.query.assert_called_once_with("Tell me about Python", "s1")


def test_post_query_returns_500_on_rag_error(client):
    tc, mock = client
    mock.query.side_effect = RuntimeError("Something went wrong")
    r = tc.post("/api/query", json={"query": "Hello", "session_id": "s1"})
    assert r.status_code == 500
