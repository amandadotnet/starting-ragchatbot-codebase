from models import Course, CourseChunk, Lesson


def test_lesson_defaults():
    lesson = Lesson(lesson_number=1, title="Intro")
    assert lesson.lesson_number == 1
    assert lesson.title == "Intro"
    assert lesson.lesson_link is None


def test_lesson_with_link():
    lesson = Lesson(lesson_number=2, title="Part 2", lesson_link="https://example.com")
    assert lesson.lesson_link == "https://example.com"


def test_course_defaults():
    course = Course(title="My Course")
    assert course.title == "My Course"
    assert course.lessons == []
    assert course.course_link is None
    assert course.instructor is None


def test_course_with_fields():
    course = Course(
        title="Python 101", course_link="https://example.com", instructor="Alice"
    )
    assert course.course_link == "https://example.com"
    assert course.instructor == "Alice"


def test_course_chunk_defaults():
    chunk = CourseChunk(content="some text", course_title="My Course", chunk_index=0)
    assert chunk.content == "some text"
    assert chunk.lesson_number is None
    assert chunk.chunk_index == 0


def test_course_chunk_with_lesson():
    chunk = CourseChunk(
        content="text", course_title="My Course", lesson_number=3, chunk_index=1
    )
    assert chunk.lesson_number == 3
