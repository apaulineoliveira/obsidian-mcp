import pytest

from core.errors import FrontmatterError
from core.frontmatter import Frontmatter, SplitNote, split_frontmatter


class FakeCodec:
    def load(self, yaml_text):
        if "!!" in yaml_text:
            raise FrontmatterError("YAML inválido")
        if yaml_text.strip().startswith("-"):
            return ["lista"]
        return dict(line.split(": ", 1) for line in yaml_text.splitlines() if line)

    def update(self, yaml_text, set_values, remove_keys):
        metadata = self.load(yaml_text)
        for key in remove_keys:
            metadata.pop(key, None)
        metadata.update(set_values)
        return "".join(f"{key}: {value}\n" for key, value in metadata.items())


@pytest.fixture
def frontmatter():
    return Frontmatter(FakeCodec())


def test_split_finds_yaml_body_and_body_start_line():
    assert split_frontmatter("---\na: 1\n---\ncorpo\n") == SplitNote("a: 1\n", "corpo\n", 3)


@pytest.mark.parametrize("content", ["----\ntexto\n---\n", "---\nfoo: bar\n", "texto\n", ""])
def test_split_ignores_content_without_a_closed_block(content):
    assert split_frontmatter(content) == SplitNote(None, content, 0)


def test_parse(frontmatter):
    parsed = frontmatter.parse("---\na: 1\n---\ncorpo\n")
    assert parsed.metadata == {"a": "1"}
    assert parsed.body == "corpo\n"
    assert parsed.body_start_line == 3


def test_parse_rejects_invalid_or_non_mapping_yaml(frontmatter):
    with pytest.raises(FrontmatterError):
        frontmatter.parse("---\n!!x\n---\ncorpo\n")
    with pytest.raises(FrontmatterError):
        frontmatter.parse("---\n- a\n---\n")


def test_parse_ignoring_invalid_yaml_keeps_body(frontmatter):
    parsed = frontmatter.parse_ignoring_invalid_yaml("---\n!!x\n---\ncorpo\n")
    assert (parsed.metadata, parsed.body, parsed.body_start_line) == ({}, "corpo\n", 3)


def test_update_creates_changes_and_removes_block(frontmatter):
    assert frontmatter.update("corpo\n", {"a": "1"}) == "---\na: 1\n---\ncorpo\n"
    assert frontmatter.update("---\na: 1\n---\ncorpo\n", {"b": "2"}) == "---\na: 1\nb: 2\n---\ncorpo\n"
    assert frontmatter.update("---\na: 1\n---\ncorpo\n", remove_keys=["a"]) == "corpo\n"


def test_update_keeps_windows_line_endings(frontmatter):
    content = "---\r\na: 1\r\n---\r\ncorpo\r\n"
    assert frontmatter.update(content, {"b": "2"}) == "---\r\na: 1\r\nb: 2\r\n---\r\ncorpo\r\n"


def test_update_refuses_invalid_yaml(frontmatter):
    with pytest.raises(FrontmatterError):
        frontmatter.update("---\n!!x\n---\n", {"a": "1"})
