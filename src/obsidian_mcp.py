import json
import os
from pathlib import Path
from typing import Optional
from mcp.server.mcpserver import MCPServer

vault_path = Path(os.getenv("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/Obsidian")))

mcp = MCPServer("obsidian-mcp")

@mcp.tool()
def get_todos(folder: Optional[str] = None) -> str:
    
    todos = []
    search_path = vault_path / folder if folder else vault_path

    if not search_path.exists():
        return json.dumps({"error": "Caminho não encontrado"}, ensure_ascii=False)

    for md_file in search_path.rglob("*.md"):
        relative_path = md_file.relative_to(vault_path)
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if "- [ ]" in line or "- [x]" in line:
                    todos.append({
                        "file": str(relative_path),
                        "line": i,
                        "completed": "[x]" in line,
                        "text": line.strip(),
                    })
        except Exception:
            pass

    return json.dumps({"todos": todos, "count": len(todos)}, indent=2, ensure_ascii=False)

@mcp.tool()
def get_note_content(note_path: str) -> str:
    
    full_path = vault_path / note_path
    if not full_path.exists():
        return json.dumps({"error": f"Nota não encontrada: {note_path}"}, ensure_ascii=False)
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()

@mcp.tool()
def update_todo(note_path: str, line_number: int, completed: bool) -> str:
   
    full_path = vault_path / note_path
    if not full_path.exists():
        return json.dumps({"error": f"Nota não encontrada: {note_path}"}, ensure_ascii=False)

    with open(full_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if line_number >= len(lines):
        return json.dumps({"error": "Linha não existe"}, ensure_ascii=False)

    checkbox = "[x]" if completed else "[ ]"
    lines[line_number] = lines[line_number].replace("[ ]", checkbox).replace("[x]", checkbox)

    with open(full_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return json.dumps({"success": True}, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()
