import json

import pytest

from conftest import write
from search import (
    SearchError,
    compile_query,
    extract_inline_tags,
    matches_frontmatter,
    normalize_tags,
    snippet,
    tag_matches,
)


def test_extract_inline_tags_follows_obsidian_rules():
    text = """Tarefa #urgente #projeto/api #2026 #v2
Link https://x.com/page#ancora e [[Nota#Seção]] e &#123;
Código `#naotag` fim
```
#dentro_do_bloco
```
# Título não é tag
#fim"""
    assert extract_inline_tags(text) == ["urgente", "projeto/api", "v2", "fim"]


@pytest.mark.parametrize("value, expected", [
    (["a", "#b"], ["a", "b"]),
    ("a, b c", ["a", "b", "c"]),
    (None, []),
    (2026, ["2026"]),
])
def test_normalize_tags(value, expected):
    assert normalize_tags(value) == expected


def test_tag_matches_nested_tags():
    assert tag_matches("Projeto", "projeto/oloroke")
    assert tag_matches("#projeto", "projeto")
    assert not tag_matches("projeto", "projetos")
    assert not tag_matches("projeto/oloroke", "projeto")


def test_compile_query_escapes_text_and_validates_regex():
    assert compile_query("a.b").search("a.b") and not compile_query("a.b").search("axb")
    assert compile_query("a.b", regex=True).search("axb")
    with pytest.raises(SearchError):
        compile_query("(", regex=True)
    with pytest.raises(SearchError):
        compile_query("a" * 501)


def test_snippet_truncates_around_match():
    line = "x" * 300 + "ALVO" + "y" * 300
    result = snippet(line, 300, 304)
    assert "ALVO" in result and result.startswith("…") and result.endswith("…")
    assert len(result) <= 242


def test_matches_frontmatter():
    metadata = {"status": "Draft", "tags": ["api", "web"], "ano": 2026}
    assert matches_frontmatter(metadata, {"status": "draft", "tags": "api", "ano": "2026"})
    assert matches_frontmatter(metadata, {"tags": ["api", "web"]})
    assert not matches_frontmatter(metadata, {"tags": "mobile"})
    assert not matches_frontmatter(metadata, {"inexistente": "x"})


@pytest.fixture
def notes(server, vault_dir):
    write(vault_dir, "Projects/api.md", "---\ntags: [projeto/api]\nstatus: draft\n---\nOAuth aqui\noauth ali #backend\n")
    write(vault_dir, "Projects/web.md", "---\ntags: projeto/web\n---\nSem nada #frontend\n")
    write(vault_dir, "Diario/hoje.md", "Reunião sobre OAuth #backend\n")
    return server


def search(server, **kwargs):
    return json.loads(server.search_notes(**kwargs))


def test_search_text_ranks_by_matches(notes):
    data = search(notes, query="oauth")
    assert [r["file"] for r in data["results"]] == ["Projects/api.md", "Diario/hoje.md"]
    assert data["results"][0]["matches"] == [
        {"line": 4, "text": "OAuth aqui"},
        {"line": 5, "text": "oauth ali #backend"},
    ]


def test_search_case_sensitive_and_regex(notes):
    assert search(notes, query="oauth", case_sensitive=True)["total_notes_matched"] == 1
    assert search(notes, query=r"^Reuni\w+", regex=True)["results"][0]["file"] == "Diario/hoje.md"


def test_search_by_tags_and_frontmatter(notes):
    files = lambda d: [r["file"] for r in d["results"]]
    assert files(search(notes, tags=["projeto"])) == ["Projects/api.md", "Projects/web.md"]
    assert files(search(notes, tags=["projeto", "backend"])) == ["Projects/api.md"]
    assert files(search(notes, frontmatter={"status": "draft"})) == ["Projects/api.md"]
    assert files(search(notes, query="oauth", folder="Diario")) == ["Diario/hoje.md"]


def test_search_limits_and_errors(notes):
    data = search(notes, tags=["projeto"], max_results=1)
    assert data["count"] == 1 and data["truncated"]

    assert "error" in search(notes)
    assert "error" in search(notes, query="(", regex=True)
    assert "error" in search(notes, query="x", folder="../")


def test_list_tags_counts_notes(notes):
    data = json.loads(notes.list_tags())
    assert data["tags"][0] == {"tag": "backend", "notes": 2}
    assert {t["tag"] for t in data["tags"]} == {"backend", "projeto/api", "projeto/web", "frontend"}


def test_get_todos_uses_nested_tags(server, vault_dir):
    write(vault_dir, "n.md", "- [ ] Deploy #projeto/api\n- [ ] Outra #outro\n")
    todos = json.loads(server.get_todos(tag="projeto"))["todos"]
    assert [t["text"] for t in todos] == ["- [ ] Deploy"]
