import pytest

from core.errors import TodoError
from core.todos import TodoFilter, note_defaults, parse_todos, set_todo_completed


BODY = """# Título
- [ ] Deploy 🔴 #projeto/api
  * [x] Revisar PR #backend
Texto com [ ] solto
+ [ ] Herdada
"""

METADATA = {"projeto": "oloroke", "prioridade": "baixa", "tags": ["web"]}


@pytest.fixture
def todos():
    return parse_todos("x.md", BODY, body_start_line=4, defaults=note_defaults(METADATA, "pt"))


def test_parse_todos_reads_checkbox_lines(todos):
    assert [(todo.line, todo.completed, todo.text) for todo in todos] == [
        (5, False, "- [ ] Deploy"),
        (6, True, "* [x] Revisar PR"),
        (8, False, "+ [ ] Herdada"),
    ]


def test_todos_inherit_note_metadata(todos):
    deploy, _, inherited = todos
    assert deploy.tags == ["web", "projeto/api"]
    assert deploy.priority == "high"
    assert inherited.priority == "low"
    assert deploy.project == "oloroke"


def test_todo_filter(todos):
    def lines_matching(**criteria):
        todo_filter = TodoFilter(**criteria)
        return [todo.line for todo in todos if todo_filter.matches(todo)]

    assert lines_matching(tag="projeto") == [5]
    assert lines_matching(tag="web") == [5, 6, 8]
    assert lines_matching(priority="low") == [6, 8]
    assert lines_matching(completed=True) == [6]


def test_set_todo_completed_only_changes_the_checkbox():
    content = "Texto com [ ] solto\r\n  * [ ] tarefa [ ] fim\r\n"
    assert set_todo_completed(content, 1, True) == "Texto com [ ] solto\r\n  * [x] tarefa [ ] fim\r\n"
    assert set_todo_completed("- [X] feito\n", 0, False) == "- [ ] feito\n"


def test_set_todo_completed_rejects_invalid_lines():
    with pytest.raises(TodoError):
        set_todo_completed("Texto com [ ] solto\n", 0, True)
    with pytest.raises(TodoError):
        set_todo_completed("- [ ] a\n", 5, True)
