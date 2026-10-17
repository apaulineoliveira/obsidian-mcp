from typing import Optional

import pytest

from adapters.yaml_codec import RuamelYamlCodec
from application import build_services
from application.languages import supported_language_names
from core.errors import (
    FrontmatterError,
    InvalidPathError,
    NoteNotFoundError,
    NoteReadError,
    SearchError,
    TodoError,
)
from core.search import LineMatch, SearchQuery
from core.todos import TodoFilter


UNREADABLE = None


class InMemoryRepository:
    def __init__(self, notes: dict[str, Optional[str]]):
        self.notes = dict(notes)
        self.written_paths: list[str] = []

    def list_notes(self, folder: Optional[str] = None) -> list[str]:
        paths = sorted(path for path in self.notes if not folder or path.startswith(folder + "/"))
        if folder and not paths:
            raise InvalidPathError(f"Pasta não encontrada: {folder}")
        return paths

    def read(self, note_path: str) -> str:
        if note_path not in self.notes:
            raise NoteNotFoundError(f"Nota não encontrada: {note_path}")
        if self.notes[note_path] is UNREADABLE:
            raise NoteReadError(f"Não foi possível ler a nota {note_path}")
        return self.notes[note_path]

    def write(self, note_path: str, content: str) -> None:
        self.read(note_path)
        self.notes[note_path] = content
        self.written_paths.append(note_path)


API_NOTE = """---
projeto: oloroke
tags: [projeto/api]
status: draft
---
OAuth aqui
- [ ] oauth ali #backend
"""

WEB_NOTE = """---
tags: projeto/web
project: site
---
Sem nada #frontend
- [x] 🔴 Publicar
"""

NOTES = {
    "Projects/api.md": API_NOTE,
    "Projects/web.md": WEB_NOTE,
    "Diario/hoje.md": "Reunião sobre OAuth #backend\n",
    "quebrada.md": "---\nfoo: [unclosed\n---\n- [ ] Ainda listada\n",
    "ilegivel.md": UNREADABLE,
}


@pytest.fixture
def repository():
    return InMemoryRepository(NOTES)


@pytest.fixture
def services(repository):
    return build_services(repository, RuamelYamlCodec())


def found_files(services, **query_fields) -> list[str]:
    result = services.search.search(SearchQuery(**query_fields))
    return [note.file for note in result.notes]


def test_get_content_and_frontmatter(services):
    assert services.notes.get_content("Diario/hoje.md") == NOTES["Diario/hoje.md"]
    assert services.notes.get_frontmatter("Projects/api.md")["status"] == "draft"


def test_get_frontmatter_errors(services):
    with pytest.raises(FrontmatterError):
        services.notes.get_frontmatter("quebrada.md")
    with pytest.raises(NoteNotFoundError):
        services.notes.get_content("x.md")


def test_update_frontmatter_writes_only_when_something_changes(services, repository):
    assert services.notes.update_frontmatter("Projects/api.md", {"status": "done"})["status"] == "done"
    services.notes.update_frontmatter("Projects/api.md", {"status": "done"})

    assert repository.written_paths == ["Projects/api.md"]
    assert repository.notes["Projects/api.md"].endswith("OAuth aqui\n- [ ] oauth ali #backend\n")


def test_update_frontmatter_errors(services):
    with pytest.raises(FrontmatterError):
        services.notes.update_frontmatter("Projects/api.md")
    with pytest.raises(FrontmatterError):
        services.notes.update_frontmatter("quebrada.md", {"a": 1})


def test_listings_skip_unreadable_notes(services):
    assert services.notes.list_tags()[0] == ("backend", 2)
    assert services.notes.list_projects() == ["oloroke", "site"]


def test_list_todos_uses_line_numbers_of_the_whole_file(services):
    todos = services.todos.list_todos()
    assert [(todo.file, todo.line) for todo in todos] == [
        ("Projects/api.md", 6),
        ("Projects/web.md", 5),
        ("quebrada.md", 3),
    ]


def test_list_todos_with_filters(services):
    high_priority = services.todos.list_todos(todo_filter=TodoFilter(priority="high"))
    open_project_todos = services.todos.list_todos("Projects", TodoFilter(tag="projeto", completed=False))

    assert [todo.file for todo in high_priority] == ["Projects/web.md"]
    assert [todo.file for todo in open_project_todos] == ["Projects/api.md"]


def test_set_completed(services, repository):
    services.todos.set_completed("Projects/api.md", 6, True)
    assert repository.notes["Projects/api.md"].endswith("- [x] oauth ali #backend\n")

    with pytest.raises(TodoError):
        services.todos.set_completed("Projects/api.md", 5, True)


def test_search_by_text_ranks_notes_with_more_matches_first(services):
    result = services.search.search(SearchQuery(query="oauth"))

    assert [note.file for note in result.notes] == ["Projects/api.md", "Diario/hoje.md"]
    assert result.notes[0].matches == [LineMatch(5, "OAuth aqui"), LineMatch(6, "- [ ] oauth ali #backend")]


def test_search_by_tags_frontmatter_and_folder(services):
    assert found_files(services, tags=["projeto"]) == ["Projects/api.md", "Projects/web.md"]
    assert found_files(services, tags=["projeto", "backend"]) == ["Projects/api.md"]
    assert found_files(services, frontmatter={"status": "draft"}) == ["Projects/api.md"]
    assert found_files(services, query="oauth", folder="Diario") == ["Diario/hoje.md"]


def test_search_limits(services):
    result = services.search.search(SearchQuery(query="oauth", max_results=1, max_matches_per_note=1))

    assert len(result.notes) == 1 and result.truncated
    assert result.notes[0].match_count == 2
    assert len(result.notes[0].matches) == 1


def test_search_errors(services):
    with pytest.raises(SearchError):
        services.search.search(SearchQuery())
    with pytest.raises(SearchError):
        services.search.search(SearchQuery(query="(", regex=True))
    with pytest.raises(InvalidPathError):
        services.search.search(SearchQuery(query="x", folder="nada"))


def test_supported_language_names():
    assert supported_language_names()["pt"] == "Português (Portuguese)"
