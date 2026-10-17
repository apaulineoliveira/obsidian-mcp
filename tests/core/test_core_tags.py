import pytest

from core.tags import count_tags, extract_inline_tags, normalize_tags, note_tags, tag_matches


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


def test_note_tags_merges_frontmatter_and_inline_case_insensitively():
    assert note_tags({"tags": ["API"], "tag": "web"}, "texto #api #Novo") == ["api", "web", "novo"]


def test_tag_matches_nested_tags():
    assert tag_matches("Projeto", "projeto/oloroke")
    assert tag_matches("#projeto", "projeto")
    assert not tag_matches("projeto", "projetos")
    assert not tag_matches("projeto/oloroke", "projeto")


def test_count_tags_orders_by_usage():
    assert count_tags([["a", "b"], ["b"], ["c", "b", "a"]]) == [("b", 3), ("a", 2), ("c", 1)]
