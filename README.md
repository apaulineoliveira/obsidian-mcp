# Obsidian MCP Server

An [MCP](https://modelcontextprotocol.io) server that connects your Obsidian vault to Claude Desktop and Cursor, so the AI can search your notes, read and update their metadata, and manage your to-dos without you copying and pasting anything.

🇧🇷 [Versão em português](README.pt.md)

## What it can do

| Tool | Description |
|------|-------------|
| `search_notes` | Searches notes by text or regex, by tags and by frontmatter fields (all combinable), returning matching lines with their line numbers |
| `list_tags` | Lists every tag in the vault (inline and frontmatter) with how many notes use it |
| `get_frontmatter` | Returns a note's YAML frontmatter as JSON |
| `update_frontmatter` | Creates, changes or removes frontmatter keys, keeping comments, key order and the note body intact |
| `get_todos` | Lists to-dos (`- [ ]` / `- [x]`), filterable by `folder`, `tag`, `priority`, `completed` and `language` |
| `update_todo` | Marks a to-do as done/undone (by note path and line number) |
| `get_note_content` | Returns the full content of a note |
| `list_projects` | Lists projects found in notes' frontmatter |
| `get_supported_languages` | Lists languages accepted for priority keywords |

Example prompts:

- *"Find notes mentioning OAuth in Projects"* · *"Search for `TODO\(\w+\)` as a regex"*
- *"Which notes are tagged #project and have `status: draft`?"*
- *"Set `status: done` in the frontmatter of Projects/oloroke.md"*
- *"Show my high-priority #backend tasks"* · *"Mark line 5 of Projects/x.md as done"*

### Organizing your notes (all optional, can be combined)

- **Inline tags:** `- [ ] Fix login #urgent #backend`. Nested tags work like in Obsidian: filtering by `project` also matches `#project/api`. Tags inside code blocks, URLs (`page#anchor`) and links (`[[Note#Heading]]`) are ignored.
- **Priority emoji:** 🔴 high · 🟡 medium · 🟢 low · ⚫ blocked
- **YAML frontmatter:** `projeto`/`project`, `prioridade`/`priority`, `tags` (list or `"a, b"`) and any custom field you want to search on

```markdown
---
project: oloroke
priority: high
status: draft
tags: [backend]
---
- [ ] 🔴 Implement OAuth #urgent
```

Priority keywords work in **pt, en, es, fr, de, it**. To add another language, add its keywords to `PRIORITY_KEYWORDS` in [src/core/priorities.py](src/core/priorities.py); [src/examples/add_custom_language.py](src/examples/add_custom_language.py) shows ready-made keywords for ja, zh, ru, el and ko.

### Safety

The server only touches files inside `OBSIDIAN_VAULT_PATH`:

- Absolute paths, `..` that leave the vault, and symlinks pointing outside it are rejected.
- `.obsidian/`, `.trash/` and `.git/` are never read or written; only `.md` notes can be opened or edited.
- Writes are atomic (temp file + rename), keep the file's line endings, and are refused if the existing frontmatter is invalid YAML.

## Requirements

- Python 3.11+
- Claude Desktop or Cursor
- An Obsidian vault

## Setup

### 1. Install

```bash
git clone git@github.com:apaulineoliveira/obsidian-mcp.git
cd obsidian-mcp
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -e .
```

Get the absolute paths you will need in the next step:

```bash
echo "$PWD/venv/bin/python3"      # command
echo "$PWD/src/obsidian_mcp.py"   # script
```

### 2a. Claude Desktop

Open the config file (or go to *Settings → Developer → Edit Config*):

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

Add the server under `mcpServers` (keep any servers already there):

```json
{
  "mcpServers": {
    "obsidian-mcp": {
      "command": "/abs/path/to/obsidian-mcp/venv/bin/python3",
      "args": ["/abs/path/to/obsidian-mcp/src/obsidian_mcp.py"],
      "env": { "OBSIDIAN_VAULT_PATH": "/abs/path/to/your/vault" }
    }
  }
}
```

On Windows, use `venv\\Scripts\\python.exe` and escape backslashes (`C:\\Users\\me\\vault`).

Fully quit Claude Desktop (Cmd+Q / exit from the tray) and reopen it. The tools appear under the 🔨 / connectors menu in the chat box.

### 2b. Cursor

Use the same `mcpServers` block in one of these files:

- `~/.cursor/mcp.json` — available in every project
- `.cursor/mcp.json` in a project — only for that project

Then open *Cursor Settings → MCP*: `obsidian-mcp` should show a green dot and its list of tools. Tools are used by the **Agent** mode in chat.

### Configuring the vault path

`OBSIDIAN_VAULT_PATH` must be the absolute path of the vault folder (the one that contains `.obsidian/`). It is read, in order of priority, from:

1. The `env` block of the client config (recommended)
2. A `.env` file at the repository root (`cp .env.example .env`)
3. Default: `~/Obsidian`

## Troubleshooting

- **Server doesn't show up:** validate the config JSON, confirm both paths exist, and fully restart the client.
- **`ModuleNotFoundError: mcp`:** `command` must point to the venv's Python, not the system one.
- **`Vault não encontrado` / `Vault not found`:** `OBSIDIAN_VAULT_PATH` is wrong or not absolute.
- **`Caminho fora do vault` / path outside vault:** use paths relative to the vault, e.g. `Projects/x.md`.
- **Logs:** Claude Desktop writes them to `~/Library/Logs/Claude/mcp-server-obsidian-mcp.log` (macOS) or `%APPDATA%\Claude\logs` (Windows); Cursor shows them in *Output → MCP Logs*.
- **Inspect the server by hand:** `npx @modelcontextprotocol/inspector venv/bin/python3 src/obsidian_mcp.py`

## Architecture

The code follows a layered (clean / hexagonal) architecture. Dependencies only point inward: `adapters → application → core`.

```
src/
├── obsidian_mcp.py      Composition root: wires adapters and services, starts the server
├── core/                Domain rules. Standard library only; no MCP, disk or YAML
│   ├── paths.py         Vault path rules (traversal, internal folders, .md only)
│   ├── frontmatter.py   Frontmatter block split/assemble, via the FrontmatterCodec port
│   ├── tags.py          Obsidian tag rules (nested, case-insensitive, code blocks)
│   ├── search.py        Query, matching, snippets and ranking
│   ├── todos.py         Checkbox parsing, filters and toggling
│   ├── priorities.py    Priority keywords per language and emoji
│   ├── ports.py         NoteRepository and FrontmatterCodec interfaces
│   └── errors.py        Domain errors
├── application/         Use cases that orchestrate the core through the ports
│   ├── vault_notes.py   Reads every note once, already split into metadata and body
│   ├── notes.py         Content, frontmatter, tags and projects
│   ├── todos.py         List and complete to-dos
│   ├── search.py        Note search
│   └── languages.py     Supported languages
└── adapters/            The outside world
    ├── filesystem.py    NoteRepository on disk (symlinks, atomic writes)
    ├── yaml_codec.py    FrontmatterCodec with ruamel.yaml (round-trip)
    └── mcp_server.py    MCP tools: arguments → use cases → JSON
```

Where to put a change:

- **New rule about notes** (e.g. parsing wikilinks): a function in `core/`, tested with plain strings.
- **New capability**: a method in an `application/` service, tested with an in-memory repository.
- **New tool**: a method in `VaultTools` plus its name in `TOOL_NAMES` (`adapters/mcp_server.py`).
- **New storage** (e.g. Obsidian REST API): a class implementing `NoteRepository`, wired in `obsidian_mcp.py`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests mirror the layers: `tests/core` (pure functions), `tests/application` (in-memory repository) and `tests/adapters` (real disk, YAML and MCP).

## Found a bug?

Open an [issue](https://github.com/apaulineoliveira/obsidian-mcp/issues) with: what you did, what you expected, what happened, your OS/Python version, and any error output.

## Contributing

1. Fork the repo and create a branch (`git checkout -b feature/my-change`)
2. Make your change, add tests and run `pytest`
3. Commit using [Conventional Commits](https://www.conventionalcommits.org) (e.g. `feat(search): ...`)
4. Open a pull request describing what and why

## License

MIT — created by Pauline Oliveira.
