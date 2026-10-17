import pytest

from core.tags import count_notes_per_tag, inline_tags, note_tags, parse_tag_field, tag_matches


def test_inline_tags_follow_obsidian_rules():
    text = """Tarefa #urgente #projeto/api #2026 #v2
Link https://x.com/page#ancora e [[Nota#Seção]] e &#123;
Código `#naotag` fim
```
#dentro_do_bloco
```
# Título não é tag
#fim"""
    assert inline_tags(text) == ["urgente", "projeto/api", "v2", "fim"]


@pytest.mark.parametrize("value, expected", [
    (["a", "#b"], ["a", "b"]),
    ("a, b c", ["a", "b", "c"]),
    (None, []),
    (2026, ["2026"]),
])
def test_parse_tag_field(value, expected):
    assert parse_tag_field(value) == expected


def test_note_tags_merge_frontmatter_and_inline_ignoring_case():
    assert note_tags({"tags": ["API"], "tag": "web"}, "texto #api #Novo") == ["api", "web", "novo"]


def test_tag_matches_parent_tags():
    assert tag_matches("projeto/oloroke", "Projeto")
    assert tag_matches("projeto", "#projeto")
    assert not tag_matches("projetos", "projeto")
    assert not tag_matches("projeto", "projeto/oloroke")


def test_count_notes_per_tag_orders_by_usage():
    assert count_notes_per_tag([["a", "b"], ["b"], ["c", "b", "a"]]) == [("b", 3), ("a", 2), ("c", 1)]
