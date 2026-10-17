import asyncio
import json

from adapters.filesystem import FileSystemVault
from adapters.mcp_server import TOOL_NAMES, create_server
from adapters.yaml_codec import RuamelFrontmatterCodec
from application import build_services


NOTE = """---
# comentário do usuário
projeto: oloroke
tags: [projeto/api]
criado: 2026-01-15
---
OAuth aqui
- [ ] 🔴 tarefa #backend
"""


def call(tool, *args, **kwargs):
    return json.loads(tool(*args, **kwargs))


def test_server_registers_all_tools_with_parameters(vault_dir):
    server = create_server(build_services(FileSystemVault(vault_dir), RuamelFrontmatterCodec()))
    tools = {t.name: t for t in asyncio.run(server.list_tools())}

    assert tuple(tools) == TOOL_NAMES
    assert all(tools[name].description for name in TOOL_NAMES)
    params = lambda name: set((getattr(tools[name], "input_schema", None) or tools[name].inputSchema)["properties"])
    assert params("update_frontmatter") == {"note_path", "set_values", "remove_keys"}
    assert params("update_todo") == {"note_path", "line_number", "completed"}
    assert "self" not in params("search_notes")


def test_todos_round_trip(tools, write):
    path = write("Projects/x.md", NOTE)

    data = call(tools.get_todos, tag="projeto", priority="high")
    todo = data["todos"][0]
    assert data["count"] == 1
    assert todo == {
        "file": "Projects/x.md",
        "line": 7,
        "completed": False,
        "text": "- [ ]  tarefa",
        "raw_text": "- [ ] 🔴 tarefa #backend",
        "tags": ["projeto/api", "backend"],
        "priority": "high",
        "project": "oloroke",
    }

    assert call(tools.update_todo, "Projects/x.md", todo["line"], True)["success"]
    assert path.read_text().endswith("- [x] 🔴 tarefa #backend\n")
    assert call(tools.update_todo, "Projects/x.md", 6, True) == {"error": "A linha 6 não é um to-do (- [ ] / - [x])"}


def test_frontmatter_tools(tools, write):
    path = write("Projects/x.md", NOTE)

    data = call(tools.get_frontmatter, "Projects/../Projects/x.md")
    assert data == {"file": "Projects/x.md", "frontmatter": {
        "projeto": "oloroke", "tags": ["projeto/api"], "criado": "2026-01-15"}}

    assert call(tools.update_frontmatter, "Projects/x.md", set_values={"status": "done"})["frontmatter"]["status"] == "done"
    assert "# comentário do usuário" in path.read_text()
    assert "error" in call(tools.update_frontmatter, "Projects/x.md")


def test_search_and_listing_tools(tools, write):
    write("Projects/x.md", NOTE)
    write("Diario/hoje.md", "Reunião sobre OAuth #backend\n")

    data = call(tools.search_notes, query="oauth", max_results=1)
    assert data["results"] == [{
        "file": "Diario/hoje.md", "tags": ["backend"], "match_count": 1,
        "matches": [{"line": 0, "text": "Reunião sobre OAuth #backend"}],
    }]
    assert (data["count"], data["total_notes_matched"], data["truncated"]) == (1, 2, True)

    assert call(tools.list_tags)["tags"][0] == {"tag": "backend", "notes": 2}
    assert call(tools.list_projects) == {"projects": ["oloroke"], "count": 1}
    assert call(tools.get_supported_languages)["count"] == 6
    assert tools.get_note_content("Diario/hoje.md") == "Reunião sobre OAuth #backend\n"


def test_every_tool_turns_domain_errors_into_json(tools, write, vault_dir):
    write("secret.md", "- [ ] segredo", root=vault_dir.parent)

    for result in (
        tools.get_note_content("../secret.md"),
        tools.update_todo("../secret.md", 0, True),
        tools.get_todos(folder=".."),
        tools.get_frontmatter("/etc/passwd"),
        tools.update_frontmatter("../secret.md", set_values={"a": 1}),
        tools.search_notes(query="x", folder="../"),
        tools.search_notes(),
        tools.list_tags(folder="nada"),
    ):
        assert set(json.loads(result)) == {"error"}

    assert (vault_dir.parent / "secret.md").read_text() == "- [ ] segredo"
