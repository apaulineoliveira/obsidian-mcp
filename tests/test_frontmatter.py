import json

import pytest

from conftest import write
from frontmatter import (
    FrontmatterError,
    extract_frontmatter,
    parse_frontmatter,
    split_frontmatter,
    update_frontmatter,
)


NOTE = """---
# comentário do usuário
projeto: oloroke
tags: [backend, api]
criado: 2026-01-15
---
# Título

- [ ] tarefa
"""


def test_parse_returns_metadata_body_and_offset():
    metadata, body, offset = parse_frontmatter(NOTE)
    assert metadata["projeto"] == "oloroke"
    assert metadata["tags"] == ["backend", "api"]
    assert body.startswith("# Título")
    assert offset == 6


def test_horizontal_rule_is_not_frontmatter():
    content = "----\ntexto\n---\n"
    assert split_frontmatter(content) == (None, content, 0)


def test_unclosed_block_is_not_frontmatter():
    content = "---\nfoo: bar\n"
    assert parse_frontmatter(content) == ({}, content, 0)


def test_invalid_yaml_raises_but_extract_is_lenient():
    content = "---\nfoo: [unclosed\n---\ncorpo\n"
    with pytest.raises(FrontmatterError):
        parse_frontmatter(content)
    assert extract_frontmatter(content) == ({}, "corpo\n", 3)


def test_non_mapping_frontmatter_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("---\n- a\n- b\n---\n")


def test_update_preserves_comments_order_style_and_body():
    updated = update_frontmatter(NOTE, {"status": "done", "projeto": "novo"}, ["criado"])
    assert updated == """---
# comentário do usuário
projeto: novo
tags: [backend, api]
status: done
---
# Título

- [ ] tarefa
"""


def test_update_creates_block_when_missing():
    assert update_frontmatter("corpo\n", {"tags": ["a"]}) == "---\ntags:\n  - a\n---\ncorpo\n"


def test_removing_last_key_drops_block():
    assert update_frontmatter("---\na: 1\n---\ncorpo\n", remove_keys=["a"]) == "corpo\n"


def test_update_keeps_crlf():
    content = "---\r\na: 1\r\n---\r\ncorpo\r\n"
    assert update_frontmatter(content, {"b": 2}) == "---\r\na: 1\r\nb: 2\r\n---\r\ncorpo\r\n"


def test_update_refuses_invalid_yaml():
    with pytest.raises(FrontmatterError):
        update_frontmatter("---\nfoo: [unclosed\n---\n", {"a": 1})


def test_tools_read_and_write_frontmatter(server, vault_dir):
    path = write(vault_dir, "Projects/x.md", NOTE)

    data = json.loads(server.get_frontmatter("Projects/x.md"))
    assert data["frontmatter"]["criado"] == "2026-01-15"

    result = json.loads(server.update_frontmatter("Projects/x.md", set_values={"status": "done"}))
    assert result["frontmatter"]["status"] == "done"
    assert "# comentário do usuário" in path.read_text()

    assert "error" in json.loads(server.update_frontmatter("Projects/x.md"))
    assert "error" in json.loads(server.update_frontmatter("../x.md", set_values={"a": 1}))


def test_todo_lines_account_for_frontmatter(server, vault_dir):
    path = write(vault_dir, "x.md", NOTE)

    todo = json.loads(server.get_todos())["todos"][0]
    assert todo["line"] == 8
    assert todo["project"] == "oloroke"

    server.update_todo("x.md", todo["line"], True)
    assert path.read_text().endswith("- [x] tarefa\n")
