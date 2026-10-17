import pytest

from core.errors import FrontmatterError
from core.frontmatter import FrontmatterParser, split_frontmatter, to_jsonable


class FakeCodec:
    def load(self, yaml_text):
        if "!!" in yaml_text:
            raise FrontmatterError("YAML inválido")
        if yaml_text.strip().startswith("-"):
            return ["lista"]
        return dict(line.split(": ", 1) for line in yaml_text.splitlines() if line)

    def update(self, yaml_text, set_values, remove_keys):
        data = self.load(yaml_text)
        for key in remove_keys:
            data.pop(key, None)
        data.update(set_values)
        return "".join(f"{k}: {v}\n" for k, v in data.items())


@pytest.fixture
def parser():
    return FrontmatterParser(FakeCodec())


def test_split_returns_yaml_body_and_offset():
    assert split_frontmatter("---\na: 1\n---\ncorpo\n") == ("a: 1\n", "corpo\n", 3)


@pytest.mark.parametrize("content", ["----\ntexto\n---\n", "---\nfoo: bar\n", "texto\n", ""])
def test_split_ignores_content_without_closed_block(content):
    assert split_frontmatter(content) == (None, content, 0)


def test_parse_and_lenient_parse(parser):
    note = parser.parse("---\na: 1\n---\ncorpo\n")
    assert (note.metadata, note.body, note.line_offset) == ({"a": "1"}, "corpo\n", 3)

    with pytest.raises(FrontmatterError):
        parser.parse("---\n!!x\n---\ncorpo\n")
    with pytest.raises(FrontmatterError):
        parser.parse("---\n- a\n---\n")

    lenient = parser.parse_lenient("---\n!!x\n---\ncorpo\n")
    assert (lenient.metadata, lenient.body, lenient.line_offset) == ({}, "corpo\n", 3)


def test_update_creates_changes_and_drops_block(parser):
    assert parser.update("corpo\n", {"a": "1"}) == "---\na: 1\n---\ncorpo\n"
    assert parser.update("---\na: 1\n---\ncorpo\n", {"b": "2"}) == "---\na: 1\nb: 2\n---\ncorpo\n"
    assert parser.update("---\na: 1\n---\ncorpo\n", remove_keys=["a"]) == "corpo\n"


def test_update_keeps_crlf(parser):
    assert parser.update("---\r\na: 1\r\n---\r\ncorpo\r\n", {"b": "2"}) == "---\r\na: 1\r\nb: 2\r\n---\r\ncorpo\r\n"


def test_update_refuses_invalid_yaml(parser):
    with pytest.raises(FrontmatterError):
        parser.update("---\n!!x\n---\n", {"a": "1"})


def test_to_jsonable_converts_dates():
    import datetime
    assert to_jsonable({"d": datetime.date(2026, 1, 15), "l": ({1},)}) == {"d": "2026-01-15", "l": [[1]]}
