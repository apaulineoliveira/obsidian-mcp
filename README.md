# Obsidian MCP Server

An [MCP](https://modelcontextprotocol.io) server that connects your Obsidian vault to Claude Desktop and Cursor, so the AI can read, filter and complete your to-dos without you copying and pasting them.

🇧🇷 [Versão em português](README.pt.md)

## What it can do

| Tool | Description |
|------|-------------|
| `get_todos` | Lists to-dos (`- [ ]` / `- [x]`) from the whole vault, filterable by `folder`, `tag`, `priority`, `completed` and `language` |
| `update_todo` | Marks a to-do as done/undone (by note path and line number) |
| `get_note_content` | Returns the full content of a note |
| `list_projects` | Lists projects found in notes' frontmatter |
| `get_supported_languages` | Lists languages accepted for priority keywords |

### Organizing your to-dos (all optional, can be combined)

- **Inline tags:** `- [ ] Fix login #urgent #backend`
- **Priority emoji:** 🔴 high · 🟡 medium · 🟢 low · ⚫ blocked
- **YAML frontmatter:** `projeto`/`project`, `prioridade`/`priority`, `tags`

```markdown
---
project: oloroke
priority: high
tags: [backend]
---
- [ ] 🔴 Implement OAuth #urgent
```

Priority keywords work in **pt, en, es, fr, de, it**. To add another language, see [src/examples/add_custom_language.py](src/examples/add_custom_language.py).

Example prompts: *"Show my high-priority #backend tasks"* · *"What's blocked in Projects/oloroke?"* · *"Mark line 5 of Projects/x.md as done"*

## Requirements

- macOS, Python 3.11+
- Claude Desktop or Cursor
- An Obsidian vault

## Setup

```bash
git clone git@github.com:apaulineoliveira/obsidian-mcp.git
cd obsidian-mcp
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set OBSIDIAN_VAULT_PATH to your vault's full path
```

Register the server in your client config, using **absolute paths**:

- Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Cursor: `~/.cursor/mcp.json`

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

Fully quit (Cmd+Q) and reopen the client. Then just ask: *"What are my to-dos in Obsidian?"*

## Troubleshooting

- **Claude can't see the server:** check that the config JSON is valid, the paths exist, and you restarted the client.
- **`ModuleNotFoundError: mcp`:** `command` must point to `venv/bin/python3`, not the system Python.
- **No to-dos returned:** check `OBSIDIAN_VAULT_PATH` and that tasks use the `- [ ]` format.

## Found a bug?

Open an [issue](https://github.com/apaulineoliveira/obsidian-mcp/issues) with: what you did, what you expected, what happened, your OS/Python version, and any error output.

## Contributing

1. Fork the repo and create a branch (`git checkout -b feature/my-change`)
2. Make your change and test it locally
3. Commit using [Conventional Commits](https://www.conventionalcommits.org) (e.g. `feat(filtering): ...`)
4. Open a pull request describing what and why

## License

MIT — created by Pauline Oliveira.
