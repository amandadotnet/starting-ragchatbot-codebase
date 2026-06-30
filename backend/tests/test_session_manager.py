import pytest
from session_manager import SessionManager


@pytest.fixture
def sm():
    return SessionManager(max_history=2)


def test_create_session_returns_string(sm):
    assert isinstance(sm.create_session(), str)


def test_create_session_returns_unique_ids(sm):
    assert sm.create_session() != sm.create_session()


def test_new_session_has_no_history(sm):
    sid = sm.create_session()
    assert sm.get_conversation_history(sid) is None


def test_add_exchange_stores_messages(sm):
    sid = sm.create_session()
    sm.add_exchange(sid, "What is X?", "X is Y.")
    history = sm.get_conversation_history(sid)
    assert "What is X?" in history
    assert "X is Y." in history


def test_get_conversation_history_format(sm):
    sid = sm.create_session()
    sm.add_exchange(sid, "Hello?", "Hi!")
    assert sm.get_conversation_history(sid) == "User: Hello?\nAssistant: Hi!"


def test_get_conversation_history_unknown_session(sm):
    assert sm.get_conversation_history("nonexistent") is None


def test_get_conversation_history_none_session(sm):
    assert sm.get_conversation_history(None) is None


def test_history_trimmed_to_max(sm):
    # max_history=2 keeps last 2 exchanges (4 messages)
    sid = sm.create_session()
    sm.add_exchange(sid, "q1", "a1")
    sm.add_exchange(sid, "q2", "a2")
    sm.add_exchange(sid, "q3", "a3")  # pushes out q1/a1

    history = sm.get_conversation_history(sid)
    assert "q1" not in history
    assert "q2" in history
    assert "q3" in history


def test_sessions_are_isolated(sm):
    s1 = sm.create_session()
    s2 = sm.create_session()
    sm.add_exchange(s1, "only in s1", "answer")
    assert sm.get_conversation_history(s2) is None


def test_clear_session(sm):
    sid = sm.create_session()
    sm.add_exchange(sid, "question", "answer")
    sm.clear_session(sid)
    assert sm.get_conversation_history(sid) is None


def test_add_message_to_unknown_session(sm):
    # add_message auto-creates a session bucket for unknown ids
    sm.add_message("unknown_id", "user", "hello")
    history = sm.get_conversation_history("unknown_id")
    assert "hello" in history


def test_multiple_exchanges_in_order(sm):
    sid = sm.create_session()
    sm.add_exchange(sid, "first question", "first answer")
    sm.add_exchange(sid, "second question", "second answer")
    history = sm.get_conversation_history(sid)
    assert history.index("first question") < history.index("second question")
