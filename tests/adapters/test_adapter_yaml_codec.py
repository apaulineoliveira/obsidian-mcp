import pytest

from adapters.yaml_codec import RuamelYamlCodec
from core.errors import FrontmatterError
from core.frontmatter import Frontmatter


NOTE = """---
# comentário do usuário
projeto: oloroke
tags: [backend, api]
criado: 2026-01-15
---
# Título

- [ ] tarefa
"""


@pytest.fixture
def frontmatter():
    return Frontmatter(RuamelYamlCodec())


def test_load_parses_yaml_types(frontmatter):
    note = frontmatter.parse(NOTE)
    assert note.metadata["tags"] == ["backend", "api"]
    assert note.metadata["criado"].isoformat() == "2026-01-15"
    assert note.body_start_line == 6


def test_load_raises_domain_error_on_invalid_yaml():
    with pytest.raises(FrontmatterError):
        RuamelYamlCodec().load("foo: [unclosed")


def test_update_preserves_comments_order_style_and_body(frontmatter):
    updated = frontmatter.update(NOTE, {"status": "done", "projeto": "novo"}, ["criado"])
    assert updated == """---
# comentário do usuário
projeto: novo
tags: [backend, api]
status: done
---
# Título

- [ ] tarefa
"""


def test_update_uses_obsidian_list_style_for_new_lists(frontmatter):
    assert frontmatter.update("corpo\n", {"tags": ["a"]}) == "---\ntags:\n  - a\n---\ncorpo\n"


def test_update_keeps_crlf_and_drops_empty_block(frontmatter):
    assert frontmatter.update("---\r\na: 1\r\n---\r\ncorpo\r\n", {"b": 2}) == "---\r\na: 1\r\nb: 2\r\n---\r\ncorpo\r\n"
    assert frontmatter.update("---\na: 1\n---\ncorpo\n", remove_keys=["a"]) == "corpo\n"
