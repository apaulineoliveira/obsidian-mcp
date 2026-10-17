import pytest

from core import priorities


@pytest.mark.parametrize("value, language, expected", [
    ("alta", "pt", "high"),
    ("HAUT", "fr", "high"),
    ("medio", "es", "medium"),
    ("low", "pt", "low"),
    ("🔴", "en", "high"),
    ("bloqueado", "pt", "blocked"),
    ("desconhecida", "pt", "desconhecida"),
    (None, "pt", None),
])
def test_normalize_priority(value, language, expected):
    assert priorities.normalize_priority(value, language) == expected


def test_priority_from_emoji():
    assert priorities.priority_from_emoji("- [ ] 🟡 tarefa") == "medium"
    assert priorities.priority_from_emoji("- [ ] tarefa") is None


def test_add_priority_keywords(monkeypatch):
    monkeypatch.setitem(priorities.PRIORITY_KEYWORDS, "high", dict(priorities.PRIORITY_KEYWORDS["high"]))
    priorities.add_priority_keywords("high", "ja", ["緊急"])

    assert priorities.normalize_priority("緊急", "ja") == "high"
    assert "ja" in priorities.supported_languages()
    with pytest.raises(ValueError):
        priorities.add_priority_keywords("enorme", "ja", ["x"])
