# Obsidian MCP Server 

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that connects your Obsidian vault directly to Claude and Cursor, allowing you to manage your to-dos without retyping tasks.

**Portuguese version:** [README.pt.md](README.pt.md)

## What is MCP?

**Model Context Protocol** is an open protocol that allows integrating external tools (like your Obsidian) with AIs (Claude, Cursor, etc). Think of it as a "universal adapter" that tells Claude: "Hey, you can use these tools to access my to-dos in Obsidian".

Without MCP, you'd have to copy and paste your tasks every time. With MCP, Claude accesses directly.

## Features

- ✅ **List all to-dos** from your Obsidian vault automatically
- ✅ **Mark tasks as complete** directly via Claude/Cursor
- ✅ **Read entire notes** for context
- ✅ **Works with Claude Desktop** and **Cursor** simultaneously
- ✅ Recursive search across all folders
- ✅ Support for standard Obsidian checkboxes (`- [ ]` and `- [x]`)

## Project Structure

```
obsidian-mcp-server/
├── src/
│   ├── __init__.py              # Marks folder as Python package
│   └── obsidian_mcp.py          # Main MCP server (critical file)
│
├── venv/                        # Python virtual environment (ignored in git)
│
├── requirements.txt             # Project dependencies
├── .env.example                 # Configuration template
├── .gitignore                   # Files ignored by git
├── README.md                    # Portuguese documentation
├── README.en.md                 # English documentation
└── setup.py                     # Package metadata (optional)
```

### What each file does:

| File | Function |
|------|----------|
| `src/obsidian_mcp.py` | **Heart of the project**. Defines 3 tools: `get_todos`, `get_note_content`, `update_todo`. Uses `MCPServer` to communicate with Claude/Cursor via MCP protocol |
| `venv/bin/python3` | Isolated Python with MCP packages installed. When Claude calls the server, it runs this Python |
| `requirements.txt` | Lists packages: `mcp>=0.2.0` and `python-dotenv>=1.0.0`. Installed with `pip install -r requirements.txt` |
| `.env` | Your local file (not committed) with `OBSIDIAN_VAULT_PATH=/Users/you/Documents` |
| `claude_desktop_config.json` | Config that Claude Desktop reads from `~/Library/Application Support/Claude/` to know about the server |
| `mcp.json` | Config that Cursor reads from `~/.cursor/` to know about the server |

## Installation

### Prerequisites

- macOS (tested on 11.0+)
- Python 3.11 or higher
- Homebrew (to install Python)
- Claude Desktop or Cursor installed
- An existing Obsidian vault

### Step 1: Clone or Create the Project

```bash
# If cloning from GitHub:
git clone git@github.com:YOUR-USER/obsidian-mcp.git
cd obsidian-mcp

# Or create from scratch:
mkdir obsidian-mcp
cd obsidian-mcp
```

### Step 2: Create Python Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

Your prompt should appear like this:
```
(venv) obsidian-mcp %
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- `mcp` (2.2.0+) — the MCP protocol
- `python-dotenv` — to read environment variables

### Step 4: Create `.env` File

```bash
# Copy the template:
cp .env.example .env

# Open and replace the path:
nano .env
```

Find your vault path:
1. Open Obsidian
2. Go to **Settings** → **About**
3. Look for **Vault location:**
4. Copy the full path and paste in `.env`

Example:
```env
OBSIDIAN_VAULT_PATH=/Users/pauline/Documents/MyVault
```

Save (Ctrl+X, then `y` and Enter).

### Step 5: Test the Server Locally

```bash
python3 src/obsidian_mcp.py
```

If it works, the terminal waits (no error should appear). Press **Ctrl+C** to exit.

## Configuration (Claude Desktop + Cursor)

### Claude Desktop

1. Create the configuration folder:
```bash
mkdir -p ~/Library/Application\ Support/Claude
```

2. Create the `claude_desktop_config.json` file:
```bash
cat > ~/Library/Application\ Support/Claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "obsidian-mcp": {
      "command": "/full/path/to/obsidian-mcp/venv/bin/python3",
      "args": [
        "/full/path/to/obsidian-mcp/src/obsidian_mcp.py"
      ],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/Users/your-username/Documents/your-vault"
      }
    }
  }
}
EOF
```

**Replace:**
- `/full/path/to/obsidian-mcp` → the real path (ex: `/Users/pauline/Documents/obsidian-mcp`)
- `/Users/your-username/Documents/your-vault` → your vault

3. Restart Claude Desktop (Cmd+Q and open again)

### Cursor

1. Create the folder:
```bash
mkdir -p ~/.cursor
```

2. Create the `mcp.json` file:
```bash
cat > ~/.cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "obsidian-mcp": {
      "command": "/full/path/to/obsidian-mcp/venv/bin/python3",
      "args": [
        "/full/path/to/obsidian-mcp/src/obsidian_mcp.py"
      ],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/Users/your-username/Documents/your-vault"
      }
    }
  }
}
EOF
```

3. Restart Cursor (Cmd+Q and open again)

## How to Use

### In Claude Desktop

Open a conversation and ask anything related to tasks:

```
What are my to-dos in Obsidian?
```

Claude will:
1. Call the `get_todos` tool
2. Receive JSON with all tasks (167 in your case!)
3. Format and display readably

You can also do:
```
Mark the task "Deploy the app" in Projects/project-x.md line 5 as complete
```

Claude will automatically call `update_todo`.

### In Cursor

Access the Claude tab (left side) and ask the same questions. Behavior is identical.

## How It Works Under the Hood

```
Claude/Cursor (AIs)
       ↓
claude_desktop_config.json / mcp.json (configs)
       ↓
OS Executor (reads config and runs Python command)
       ↓
/venv/bin/python3 src/obsidian_mcp.py (server running)
       ↓
MCPServer ("listens" for MCP requests)
       ↓
Functions decorated with @mcp.tool():
  - get_todos()         → Sweeps .rglob("*.md"), extracts checkboxes
  - get_note_content()  → Opens file and returns content
  - update_todo()       → Writes [ ] or [x] and saves file
       ↓
JSON responses
       ↓
Claude/Cursor displays to you
```

## Code Structure

### `src/obsidian_mcp.py` - The Jewel

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("obsidian-mcp")

@mcp.tool()
def get_todos(folder: Optional[str] = None) -> str:
    """Tool 1: Lists all to-dos"""
    # Sweeps vault_path recursively with .rglob("*.md")
    # Searches for lines with "- [ ]" or "- [x]"
    # Returns JSON with {file, line, completed, text}

@mcp.tool()
def get_note_content(note_path: str) -> str:
    """Tool 2: Reads entire note"""
    # Opens file and returns raw content

@mcp.tool()
def update_todo(note_path: str, line_number: int, completed: bool) -> str:
    """Tool 3: Marks task as done/not done"""
    # Reads file, replaces [ ] with [x] (or vice versa), saves

if __name__ == "__main__":
    mcp.run()  # Starts MCP server via stdio
```

### Task Flow

1. **User**: "Show me my to-dos"
2. **Claude**: Calls `get_todos()` via MCP
3. **Server** (your code):
   - Reads `OBSIDIAN_VAULT_PATH` variable
   - Traverses all folders with `.rglob("*.md")`
   - For each file, searches for lines with `"- [ ]"` or `"- [x]"`
   - Returns JSON: `{"todos": [...], "count": 167}`
4. **Claude**: Receives JSON, formats nicely and displays
5. **You**: See your 167 to-dos listed

## Troubleshooting

### "I don't have access to your Obsidian"

Means Claude couldn't connect to the server. Check:

1. **Config file exists?**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Python path is correct?**
   ```bash
   ls /path/you/put/venv/bin/python3
   ```
   If not found, use the real path (run `which python3` with venv activated)

3. **Vault path is correct?**
   ```bash
   ls /Users/your-username/your-vault
   ```

4. **Restarted Claude Desktop after editing config?**

### "ModuleNotFoundError: No module named 'mcp'"

Means it's running the wrong Python (not from venv). Check the path in `claude_desktop_config.json`:

```bash
# Must be THIS:
/Users/pauline/Documents/obsidian-mcp/venv/bin/python3

# Not this:
python3.11
```

## Next Steps

Ideas to expand the project:

- [ ] Filter to-dos by tags (`#urgent #work`)
- [ ] Schedule tasks (read creation date)
- [ ] Support subtasks (indentation)
- [ ] Bidirectional sync with Notion/Asana
- [ ] Own CLI (`obsidian-mcp list --completed`)
- [ ] Webhooks for real-time updates
- [ ] Support other formats (YAML frontmatter, etc)

## Resources

- [Model Context Protocol - Official Docs](https://modelcontextprotocol.io)
- [Python MCP SDK](https://py.sdk.modelcontextprotocol.io)
- [Claude Desktop Setup](https://support.anthropic.com/en/articles/8784710-claude-desktop)
- [Obsidian API](https://docs.obsidian.md/)

## License

MIT - Use freely! If you make improvements, consider submitting a pull request 

## Contributing

Found a bug or have an idea? Open an [issue](https://github.com/your-user/obsidian-mcp/issues) or submit a [pull request](https://github.com/your-user/obsidian-mcp/pulls)!

---

**Created by Pauline Oliveira**

Questions? Open an issue on GitHub or reach out!
