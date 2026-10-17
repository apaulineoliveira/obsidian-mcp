import pytest

from core.errors import TodoError
from core.todos import TodoFilter, parse_todos, set_checkbox


BODY = """# Título
- [ ] Deploy 🔴 #projeto/api
  * [x] Revisar PR #backend
Texto com [ ] solto
+ [ ] Herdada
"""


@pytest.fixture
def todos():
    return parse_todos("x.md", {"projeto": "oloroke", "prioridade": "baixa", "tags": ["web"]}, BODY, 4, "pt")


def test_parse_todos_extracts_fields(todos):
    assert [(t.line, t.completed, t.text) for t in todos] == [
        (5, False, "- [ ] Deploy"),
        (6, True, "* [x] Revisar PR"),
        (8, False, "+ [ ] Herdada"),
    ]
    assert todos[0].tags == ["web", "projeto/api"]
    assert todos[0].priority == "high"
    assert todos[2].priority == "low"
    assert todos[0].project == "oloroke"


def test_todo_filter(todos):
    pick = lambda **kw: [t.line for t in todos if TodoFilter(**kw).accepts(t)]
    assert pick(tag="projeto") == [5]
    assert pick(tag="web") == [5, 6, 8]
    assert pick(priority="low") == [6, 8]
    assert pick(completed=True) == [6]


def test_set_checkbox_only_touches_checkbox_lines():
    content = "Texto com [ ] solto\r\n  * [ ] tarefa [ ] fim\r\n"
    assert set_checkbox(content, 1, True) == "Texto com [ ] solto\r\n  * [x] tarefa [ ] fim\r\n"
    with pytest.raises(TodoError):
        set_checkbox(content, 0, True)
    with pytest.raises(TodoError):
        set_checkbox(content, 5, True)
