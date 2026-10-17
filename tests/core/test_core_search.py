import pytest

from core.errors import SearchError
from core.search import (
    LineMatch,
    NoteMatch,
    SearchQuery,
    compile_query,
    find_matches,
    matches_frontmatter,
    rank,
    snippet,
)


def test_compile_query_escapes_text_and_validates_regex():
    assert compile_query("a.b").search("a.b") and not compile_query("a.b").search("axb")
    assert compile_query("a.b", regex=True).search("axb")
    assert not compile_query("A", case_sensitive=True).search("a")
    with pytest.raises(SearchError):
        compile_query("(", regex=True)
    with pytest.raises(SearchError):
        compile_query("a" * 501)


def test_find_matches_limits_snippets_but_counts_all():
    matches, total = find_matches("oauth\nnada\nOAuth\noauth", compile_query("oauth"), 2)
    assert matches == [LineMatch(0, "oauth"), LineMatch(2, "OAuth")]
    assert total == 3


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


def test_query_requires_a_filter_and_clamps_limits():
    with pytest.raises(SearchError):
        SearchQuery().validate()
    query = SearchQuery(tags=["a"], max_results=0, max_matches_per_note=999)
    assert (query.result_limit, query.match_limit) == (1, 100)
    assert query.pattern() is None


def test_rank_orders_by_matches_then_path_and_truncates():
    result = rank([NoteMatch("b.md", [], 1), NoteMatch("a.md", [], 1), NoteMatch("c.md", [], 5)], 2)
    assert [m.file for m in result.results] == ["c.md", "a.md"]
    assert result.total == 3 and result.truncated
