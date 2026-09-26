"""
Obsidian MCP Server with Advanced Filtering and Multilingual Support

Features:
- Tags inline (#urgente, #backend)
- Priority with emoji (🔴🟡🟢)
- YAML frontmatter metadata
- Multilingual support (PT, EN, ES, FR, DE, IT)
"""

import json
import os
import re
from pathlib import Path
from typing import Optional
from mcp.server.mcpserver import MCPServer

try:
    import yaml
except ImportError:
    yaml = None


from i18n import (
    normalize_priority, 
    extract_priority_emoji,
    get_supported_languages
)

vault_path = Path(os.getenv("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/Obsidian")))

mcp = MCPServer("obsidian-mcp")

def extract_tags(text: str) -> list[str]:
    """Extrai tags de uma linha: #urgente #backend -> ['urgente', 'backend']"""
    return re.findall(r'#(\w+)', text)


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """
    Extrai YAML frontmatter do topo do arquivo.
    Retorna (metadata_dict, content_sem_frontmatter)
    
    Exemplo:
    ---
    projeto: oloroke
    prioridade: alta
    tags: [urgente, backend]
    ---
    
    Resto do conteúdo...
    """
    if not content.startswith('---'):
        return {}, content
    
    try:
        lines = content.split('\n')
        end_idx = None
        
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                end_idx = i
                break
        
        if end_idx is None:
            return {}, content
        
        frontmatter_text = '\n'.join(lines[1:end_idx])
        body_text = '\n'.join(lines[end_idx + 1:])
        
        if yaml:
            metadata = yaml.safe_load(frontmatter_text) or {}
        else:
            metadata = {}
        
        return metadata, body_text
    
    except Exception:
        return {}, content


def matches_filter(todo: dict, tag: Optional[str], priority: Optional[str]) -> bool:
    """Verifica se um to-do passa nos filtros"""
    
   
    if tag:
        todo_tags = todo.get('tags', [])
        if tag.lower() not in [t.lower() for t in todo_tags]:
            return False
    
    
    if priority:
        todo_priority = todo.get('priority')
        if todo_priority != priority:
            return False
    
    return True



@mcp.tool()
def get_todos(
    folder: Optional[str] = None,
    tag: Optional[str] = None,
    priority: Optional[str] = None,
    completed: Optional[bool] = None,
    language: Optional[str] = 'en'
) -> str:
    """
    Extrai todos os to-dos com filtros avançados e suporte multilíngue.
    
    Parâmetros:
    - folder: Pasta específica (ex: "Projects/oloroke")
    - tag: Filtrar por tag (ex: "urgente", "backend")
    - priority: Filtrar por prioridade ("high", "medium", "low", "blocked")
    - completed: True/False para tarefas completas/incompletas
    - language: Idioma para interpretação ('pt', 'en', 'es', 'fr', 'de', 'it')
    
    Suporta 3 formas de metadata:
    1. Tags inline: - [ ] Tarefa #urgente #backend
    2. Emoji: - [ ] 🔴 Tarefa urgente
    3. YAML frontmatter com prioridade em qualquer idioma
    """
    todos = []
    search_path = vault_path / folder if folder else vault_path

    if not search_path.exists():
        return json.dumps(
            {"error": f"Caminho não encontrado: {search_path}"}, 
            ensure_ascii=False
        )

    for md_file in search_path.rglob("*.md"):
        relative_path = md_file.relative_to(vault_path)
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            
            file_metadata, body_content = extract_frontmatter(content)
            
           
            frontmatter_tags = file_metadata.get('tags', [])
            if isinstance(frontmatter_tags, str):
                frontmatter_tags = [frontmatter_tags]
            
           
            frontmatter_priority_raw = file_metadata.get('prioridade') or file_metadata.get('priority')
            frontmatter_priority = normalize_priority(frontmatter_priority_raw, language=language)
            
            lines = body_content.split('\n')
            
            for i, line in enumerate(lines):
                if "- [ ]" in line or "- [x]" in line:
                    is_completed = "[x]" in line
                    
                    
                    if completed is not None and is_completed != completed:
                        continue
                    
                   
                    inline_tags = extract_tags(line)
                    inline_priority = extract_priority_emoji(line)
                    
                    
                    all_tags = list(set(frontmatter_tags + inline_tags))
                    
                   
                    final_priority = inline_priority or frontmatter_priority
                    
                    
                    clean_text = line.strip()
                    clean_text = re.sub(r'🔴|🟡|🟢|⚫', '', clean_text).strip()
                    clean_text = re.sub(r'#\w+', '', clean_text).strip()
                    
                    todo = {
                        "file": str(relative_path),
                        "line": i,
                        "completed": is_completed,
                        "text": clean_text,
                        "raw_text": line.strip(),
                        "tags": all_tags,
                        "priority": final_priority,
                        "project": file_metadata.get('projeto') or file_metadata.get('project')
                    }
                    
                    
                    if matches_filter(todo, tag, priority):
                        todos.append(todo)
        
        except Exception as e:
            
            pass

    return json.dumps({
        "todos": todos,
        "count": len(todos),
        "filters": {
            "folder": folder,
            "tag": tag,
            "priority": priority,
            "completed": completed,
            "language": language
        }
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def get_note_content(note_path: str) -> str:
    """Lê o conteúdo completo de uma nota do Obsidian"""
    full_path = vault_path / note_path
    if not full_path.exists():
        return json.dumps(
            {"error": f"Nota não encontrada: {note_path}"}, 
            ensure_ascii=False
        )
    
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()


@mcp.tool()
def update_todo(note_path: str, line_number: int, completed: bool) -> str:
    """
    Marca um to-do como completo ou incompleto em uma nota.
    
    Parâmetros:
    - note_path: Caminho da nota (ex: "Projects/oloroke.md")
    - line_number: Número da linha (0-indexed)
    - completed: True para marcar como [x], False para [ ]
    """
    full_path = vault_path / note_path
    if not full_path.exists():
        return json.dumps(
            {"error": f"Nota não encontrada: {note_path}"}, 
            ensure_ascii=False
        )

    with open(full_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if line_number >= len(lines):
        return json.dumps(
            {"error": "Linha não existe"}, 
            ensure_ascii=False
        )

    checkbox = "[x]" if completed else "[ ]"
    lines[line_number] = lines[line_number].replace("[ ]", checkbox).replace("[x]", checkbox)

    with open(full_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return json.dumps({
        "success": True,
        "message": f"Tarefa marcada como {'completa' if completed else 'incompleta'}"
    }, ensure_ascii=False)


@mcp.tool()
def list_projects() -> str:
    """Lista todos os projetos encontrados nas notas (via frontmatter)"""
    projects = set()
    
    for md_file in vault_path.rglob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata, _ = extract_frontmatter(content)
            project = metadata.get('projeto') or metadata.get('project')
            
            if project:
                projects.add(project)
        except:
            pass
    
    return json.dumps({
        "projects": sorted(list(projects)),
        "count": len(projects)
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def get_supported_languages() -> str:
    """
    Lista todos os idiomas suportados para filtros de prioridade.
    
    Retorna:
        JSON com lista de códigos de idioma
    """
    from i18n import get_supported_languages as get_langs
    
    langs = get_langs()
    lang_names = {
        'pt': 'Português (Portuguese)',
        'en': 'English (English)',
        'es': 'Español (Spanish)',
        'fr': 'Français (French)',
        'de': 'Deutsch (German)',
        'it': 'Italiano (Italian)',
    }
    
    return json.dumps({
        "languages": langs,
        "count": len(langs),
        "details": {code: lang_names.get(code, code) for code in langs}
    }, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
