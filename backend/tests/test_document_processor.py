import pytest
from document_processor import DocumentProcessor


MINIMAL_COURSE = """\
Course Title: Test Course
Course Link: https://example.com/test
Course Instructor: Jane Doe

Lesson 1: Introduction
Lesson Link: https://example.com/lesson1
Welcome to the course. This is the first lesson content.

Lesson 2: Advanced Topics
Lesson Link: https://example.com/lesson2
Now we cover advanced material. This lesson is more complex.
"""


@pytest.fixture
def proc():
    return DocumentProcessor(chunk_size=200, chunk_overlap=50)


@pytest.fixture
def small_proc():
    """Small chunk size to force multi-chunk output with short test text."""
    return DocumentProcessor(chunk_size=80, chunk_overlap=20)


# ── chunk_text ────────────────────────────────────────────────────────────────

def test_chunk_text_empty_returns_empty(proc):
    assert proc.chunk_text("") == []


def test_chunk_text_whitespace_only_returns_empty(proc):
    assert proc.chunk_text("   \n\n  ") == []


def test_chunk_text_short_text_single_chunk(proc):
    chunks = proc.chunk_text("This is a short sentence.")
    assert chunks == ["This is a short sentence."]


def test_chunk_text_preserves_all_sentences(small_proc):
    sentences = [
        "First sentence here.",
        "Second sentence here.",
        "Third sentence here.",
        "Fourth sentence here.",
        "Fifth sentence here.",
    ]
    chunks = small_proc.chunk_text(" ".join(sentences))
    combined = " ".join(chunks)
    for s in sentences:
        assert s in combined


def test_chunk_text_produces_multiple_chunks_for_long_text(small_proc):
    # chunk_size=80; sentences ~25 chars each — 10 sentences should need multiple chunks
    sentences = [f"Sentence number {i:02d} here." for i in range(10)]
    chunks = small_proc.chunk_text(" ".join(sentences))
    assert len(chunks) > 1


def test_chunk_text_no_empty_chunks(small_proc):
    sentences = [f"Sentence {i}." for i in range(20)]
    chunks = small_proc.chunk_text(" ".join(sentences))
    assert all(len(c) > 0 for c in chunks)


# ── process_course_document ───────────────────────────────────────────────────

def test_extracts_course_title(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    course, _ = proc.process_course_document(str(f))
    assert course.title == "Test Course"


def test_extracts_course_link(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    course, _ = proc.process_course_document(str(f))
    assert course.course_link == "https://example.com/test"


def test_extracts_instructor(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    course, _ = proc.process_course_document(str(f))
    assert course.instructor == "Jane Doe"


def test_extracts_lesson_count(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    course, _ = proc.process_course_document(str(f))
    assert len(course.lessons) == 2


def test_extracts_lesson_numbers_and_titles(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    course, _ = proc.process_course_document(str(f))
    assert course.lessons[0].lesson_number == 1
    assert course.lessons[0].title == "Introduction"
    assert course.lessons[1].lesson_number == 2
    assert course.lessons[1].title == "Advanced Topics"


def test_extracts_lesson_links(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    course, _ = proc.process_course_document(str(f))
    assert course.lessons[0].lesson_link == "https://example.com/lesson1"
    assert course.lessons[1].lesson_link == "https://example.com/lesson2"


def test_creates_chunks(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    _, chunks = proc.process_course_document(str(f))
    assert len(chunks) > 0


def test_chunks_carry_course_title(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    _, chunks = proc.process_course_document(str(f))
    for chunk in chunks:
        assert chunk.course_title == "Test Course"


def test_chunks_carry_lesson_number(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    _, chunks = proc.process_course_document(str(f))
    assert all(chunk.lesson_number is not None for chunk in chunks)


def test_first_chunk_of_lesson_has_context_prefix(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    _, chunks = proc.process_course_document(str(f))

    lesson1_chunks = sorted(
        [c for c in chunks if c.lesson_number == 1], key=lambda c: c.chunk_index
    )
    assert len(lesson1_chunks) > 0
    # First chunk should contain a lesson context label
    assert "Lesson" in lesson1_chunks[0].content
    assert "1" in lesson1_chunks[0].content


def test_lesson_link_line_excluded_from_content(proc, tmp_path):
    f = tmp_path / "course.txt"
    f.write_text(MINIMAL_COURSE, encoding="utf-8")
    _, chunks = proc.process_course_document(str(f))
    all_content = " ".join(c.content for c in chunks)
    assert "Lesson Link:" not in all_content


def test_missing_title_falls_back_to_first_line(proc, tmp_path):
    doc = "No metadata here\nLine two\nLine three\n\nSome standalone content."
    f = tmp_path / "myfile.txt"
    f.write_text(doc, encoding="utf-8")
    course, _ = proc.process_course_document(str(f))
    assert course.title == "No metadata here"


def test_no_lessons_still_creates_chunks(proc, tmp_path):
    doc = """\
Course Title: Standalone
Course Link: https://example.com
Course Instructor: Bob

This course has no lesson markers. Content is chunked as a single block.
"""
    f = tmp_path / "standalone.txt"
    f.write_text(doc, encoding="utf-8")
    _, chunks = proc.process_course_document(str(f))
    assert len(chunks) > 0
