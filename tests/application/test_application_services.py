from typing import Optional

import pytest

from adapters.yaml_codec import RuamelFrontmatterCodec
from application import build_services
from application.languages import supported_languages
from core.errors import FrontmatterError, InvalidPathError, NoteNotFoundError, NoteReadError, SearchError, TodoError
from core.search import LineMatch, SearchQuery
from core.todos import TodoFilter


class InMemoryRepository:
    def __init__(self, notes: dict[str, str]):
        self.notes = dict(notes)
        self.writes: list[str] = []

    def list_notes(self, folder: Optional[str] = None) -> list[str]:
        if folder and not any(p.startswith(folder + "/") for p in self.notes):
            raise InvalidPathError(f"Caminho não encontrado: {folder}")
        return sorted(p for p in self.notes if not folder or p.startswith(folder + "/"))

    def read(self, note_path: str) -> str:
        if note_path not in self.notes:
            raise NoteNotFoundError(f"Nota não encontrada: {note_path}")
        if self.notes[note_path] is None:
            raise NoteReadError("ilegível")
        return self.notes[note_path]

    def write(self, note_path: str, content: str) -> None:
        self.read(note_path)
        self.notes[note_path] = content
        self.writes.append(note_path)


NOTES = {
    "Projects/api.md": "---\nprojeto: oloroke\ntags: [projeto/api]\nstatus: draft\n---\nOAuth aqui\n- [ ] oauth ali #backend\n",
    "Projects/web.md": "---\ntags: projeto/web\nproject: site\n---\nSem nada #frontend\n- [x] 🔴 Publicar\n",
    "Diario/hoje.md": "Reunião sobre OAuth #backend\n",
    "quebrada.md": "---\nfoo: [unclosed\n---\n- [ ] Ainda listada\n",
    "ilegivel.md": None,
}


@pytest.fixture
def repo():
    return InMemoryRepository(NOTES)


@pytest.fixture
def services(repo):
    return build_services(repo, RuamelFrontmatterCodec())


def test_note_content_and_frontmatter(services):
    assert services.notes.get_content("Diario/hoje.md") == NOTES["Diario/hoje.md"]
    assert services.notes.get_frontmatter("Projects/api.md")["status"] == "draft"
    with pytest.raises(FrontmatterError):
        services.notes.get_frontmatter("quebrada.md")
    with pytest.raises(NoteNotFoundError):
        services.notes.get_content("x.md")


def test_update_frontmatter_writes_only_on_change(services, repo):
    assert services.notes.update_frontmatter("Projects/api.md", {"status": "done"})["status"] == "done"
    services.notes.update_frontmatter("Projects/api.md", {"status": "done"})
    assert repo.writes == ["Projects/api.md"]
    assert repo.notes["Projects/api.md"].endswith("OAuth aqui\n- [ ] oauth ali #backend\n")

    with pytest.raises(FrontmatterError):
        services.notes.update_frontmatter("Projects/api.md")
    with pytest.raises(FrontmatterError):
        services.notes.update_frontmatter("quebrada.md", {"a": 1})


def test_list_tags_and_projects_skip_unreadable_notes(services):
    assert services.notes.list_tags()[0] == ("backend", 2)
    assert services.notes.list_projects() == ["oloroke", "site"]


def test_list_todos_with_absolute_lines_and_filters(services):
    todos = services.todos.list_todos()
    assert [(t.file, t.line) for t in todos] == [("Projects/api.md", 6), ("Projects/web.md", 5), ("quebrada.md", 3)]
    assert [t.file for t in services.todos.list_todos(todo_filter=TodoFilter(priority="high"))] == ["Projects/web.md"]
    assert [t.file for t in services.todos.list_todos("Projects", TodoFilter(tag="projeto", completed=False))] == ["Projects/api.md"]


def test_set_completed(services, repo):
    services.todos.set_completed("Projects/api.md", 6, True)
    assert repo.notes["Projects/api.md"].endswith("- [x] oauth ali #backend\n")
    with pytest.raises(TodoError):
        services.todos.set_completed("Projects/api.md", 5, True)


def test_search_ranks_and_filters(services):
    result = services.search.search(SearchQuery(query="oauth"))
    assert [m.file for m in result.results] == ["Projects/api.md", "Diario/hoje.md"]
    assert result.results[0].matches == [LineMatch(5, "OAuth aqui"), LineMatch(6, "- [ ] oauth ali #backend")]

    files = lambda **kw: [m.file for m in services.search.search(SearchQuery(**kw)).results]
    assert files(tags=["projeto"]) == ["Projects/api.md", "Projects/web.md"]
    assert files(tags=["projeto", "backend"]) == ["Projects/api.md"]
    assert files(frontmatter={"status": "draft"}) == ["Projects/api.md"]
    assert files(query="oauth", folder="Diario") == ["Diario/hoje.md"]

    limited = services.search.search(SearchQuery(tags=["projeto"], max_results=1))
    assert len(limited.results) == 1 and limited.truncated


def test_search_errors(services):
    with pytest.raises(SearchError):
        services.search.search(SearchQuery())
    with pytest.raises(SearchError):
        services.search.search(SearchQuery(query="(", regex=True))
    with pytest.raises(InvalidPathError):
        services.search.search(SearchQuery(query="x", folder="nada"))


def test_supported_languages():
    assert supported_languages()["pt"] == "Português (Portuguese)"
