import pytest

from core.errors import SearchError
from core.search import (
    LineMatch,
    NoteMatch,
    SearchQuery,
    compile_search_pattern,
    excerpt_around,
    find_matching_lines,
    metadata_matches,
    rank_by_relevance,
)


def test_pattern_escapes_text_and_validates_regex():
    assert compile_search_pattern("a.b").search("a.b")
    assert not compile_search_pattern("a.b").search("axb")
    assert compile_search_pattern("a.b", regex=True).search("axb")
    assert not compile_search_pattern("A", case_sensitive=True).search("a")

    with pytest.raises(SearchError):
        compile_search_pattern("(", regex=True)
    with pytest.raises(SearchError):
        compile_search_pattern("a" * 501)


def test_find_matching_lines():
    pattern = compile_search_pattern("oauth")
    assert find_matching_lines("oauth\nnada\n  OAuth  ", pattern) == [LineMatch(0, "oauth"), LineMatch(2, "OAuth")]


def test_excerpt_is_centered_on_the_match():
    line = "x" * 300 + "ALVO" + "y" * 300
    excerpt = excerpt_around(line, 300, 304)
    assert "ALVO" in excerpt
    assert excerpt.startswith("…") and excerpt.endswith("…")
    assert len(excerpt) <= 242


def test_excerpt_at_the_start_of_a_long_line():
    excerpt = excerpt_around("ALVO" + "y" * 300, 0, 4)
    assert excerpt.startswith("ALVO") and excerpt.endswith("…")


def test_metadata_matches():
    metadata = {"status": "Draft", "tags": ["api", "web"], "ano": 2026}
    assert metadata_matches(metadata, {"status": "draft", "tags": "api", "ano": "2026"})
    assert metadata_matches(metadata, {"tags": ["api", "web"]})
    assert not metadata_matches(metadata, {"tags": "mobile"})
    assert not metadata_matches(metadata, {"inexistente": "x"})


def test_query_requires_a_filter_and_clamps_limits():
    with pytest.raises(SearchError):
        SearchQuery().validate()

    query = SearchQuery(tags=["a"], max_results=0, max_matches_per_note=999)
    assert query.results_limit == 1
    assert query.matches_per_note_limit == 100


def test_rank_by_relevance_orders_by_matches_then_path():
    notes = [NoteMatch("b.md", [], 1), NoteMatch("a.md", [], 1), NoteMatch("c.md", [], 5)]
    result = rank_by_relevance(notes, limit=2)
    assert [note.file for note in result.notes] == ["c.md", "a.md"]
    assert result.total_notes_matched == 3
    assert result.truncated
