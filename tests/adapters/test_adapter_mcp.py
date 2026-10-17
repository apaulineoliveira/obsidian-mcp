import asyncio
import datetime
import json

from adapters.filesystem import FileSystemVault
from adapters.mcp_server import TOOL_NAMES, create_server, json_compatible
from adapters.yaml_codec import RuamelYamlCodec
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


def test_server_registers_every_tool(vault_dir):
    server = create_server(build_services(FileSystemVault(vault_dir), RuamelYamlCodec()))
    tools = {tool.name: tool for tool in asyncio.run(server.list_tools())}

    def parameters(name):
        return set(tools[name].input_schema["properties"])

    assert tuple(tools) == TOOL_NAMES
    assert all(tool.description for tool in tools.values())
    assert parameters("update_frontmatter") == {"note_path", "set_values", "remove_keys"}
    assert parameters("update_todo") == {"note_path", "line_number", "completed"}
    assert "self" not in parameters("search_notes")


def test_get_todos_response(tools, write):
    write("Projects/x.md", NOTE)

    response = call(tools.get_todos, tag="projeto", priority="high")

    assert response["count"] == 1
    assert response["todos"][0] == {
        "file": "Projects/x.md",
        "line": 7,
        "completed": False,
        "text": "- [ ]  tarefa",
        "raw_text": "- [ ] 🔴 tarefa #backend",
        "tags": ["projeto/api", "backend"],
        "priority": "high",
        "project": "oloroke",
    }


def test_update_todo(tools, write):
    note = write("Projects/x.md", NOTE)

    assert call(tools.update_todo, "Projects/x.md", 7, True)["success"]
    assert note.read_text().endswith("- [x] 🔴 tarefa #backend\n")
    assert call(tools.update_todo, "Projects/x.md", 6, True) == {"error": "A linha 6 não é um to-do (- [ ] / - [x])"}


def test_frontmatter_tools(tools, write):
    note = write("Projects/x.md", NOTE)

    assert call(tools.get_frontmatter, "Projects/../Projects/x.md") == {
        "file": "Projects/x.md",
        "frontmatter": {"projeto": "oloroke", "tags": ["projeto/api"], "criado": "2026-01-15"},
    }

    updated = call(tools.update_frontmatter, "Projects/x.md", set_values={"status": "done"})
    assert updated["frontmatter"]["status"] == "done"
    assert "# comentário do usuário" in note.read_text()


def test_search_notes_response(tools, write):
    write("Projects/x.md", NOTE)
    write("Diario/hoje.md", "Reunião sobre OAuth #backend\n")

    response = call(tools.search_notes, query="oauth", max_results=1)

    assert response["results"] == [{
        "file": "Diario/hoje.md",
        "tags": ["backend"],
        "match_count": 1,
        "matches": [{"line": 0, "text": "Reunião sobre OAuth #backend"}],
    }]
    assert (response["count"], response["total_notes_matched"], response["truncated"]) == (1, 2, True)


def test_listing_tools(tools, write):
    write("Projects/x.md", NOTE)
    write("Diario/hoje.md", "Reunião sobre OAuth #backend\n")

    assert call(tools.list_tags)["tags"][0] == {"tag": "backend", "notes": 2}
    assert call(tools.list_projects) == {"projects": ["oloroke"], "count": 1}
    assert call(tools.get_supported_languages)["count"] == 6
    assert tools.get_note_content("Diario/hoje.md") == "Reunião sobre OAuth #backend\n"


def test_every_tool_returns_domain_errors_as_json(tools, write, vault_dir):
    write("secret.md", "- [ ] segredo", root=vault_dir.parent)

    responses = [
        tools.get_note_content("../secret.md"),
        tools.update_todo("../secret.md", 0, True),
        tools.get_todos(folder=".."),
        tools.get_frontmatter("/etc/passwd"),
        tools.update_frontmatter("../secret.md", set_values={"a": 1}),
        tools.update_frontmatter("secret.md"),
        tools.search_notes(query="x", folder="../"),
        tools.search_notes(),
        tools.list_tags(folder="nada"),
    ]

    assert all(set(json.loads(response)) == {"error"} for response in responses)
    assert (vault_dir.parent / "secret.md").read_text() == "- [ ] segredo"


def test_json_compatible_converts_dates_and_collections():
    value = {"data": datetime.date(2026, 1, 15), "itens": ({1},)}
    assert json_compatible(value) == {"data": "2026-01-15", "itens": [[1]]}
