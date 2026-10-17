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

from dotenv import load_dotenv
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
from vault import Vault, VaultPathError

# Variáveis do config do cliente MCP têm prioridade sobre o .env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

vault = Vault(os.getenv("OBSIDIAN_VAULT_PATH", "~/Obsidian"))

mcp = MCPServer("obsidian-mcp")

CHECKBOX_RE = re.compile(r'^(\s*[-*+]\s+\[)([ xX])(\])')


def error_response(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)

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

    try:
        notes = list(vault.iter_notes(folder))
    except VaultPathError as e:
        return error_response(str(e))

    for md_file in notes:
        relative_path = vault.relative(md_file)
        
        try:
            content = vault.read_text(md_file)
            
            
            file_metadata, body_content = extract_frontmatter(content)
            
           
            frontmatter_tags = file_metadata.get('tags', [])
            if isinstance(frontmatter_tags, str):
                frontmatter_tags = [frontmatter_tags]
            
           
            frontmatter_priority_raw = file_metadata.get('prioridade') or file_metadata.get('priority')
            frontmatter_priority = normalize_priority(frontmatter_priority_raw, language=language)
            
            lines = body_content.split('\n')
            
            for i, line in enumerate(lines):
                checkbox = CHECKBOX_RE.match(line)
                if checkbox:
                    is_completed = checkbox.group(2).lower() == "x"
                    
                    
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
    try:
        full_path = vault.resolve_note(note_path)
    except VaultPathError as e:
        return error_response(str(e))

    return vault.read_text(full_path)


@mcp.tool()
def update_todo(note_path: str, line_number: int, completed: bool) -> str:
    """
    Marca um to-do como completo ou incompleto em uma nota.
    
    Parâmetros:
    - note_path: Caminho da nota (ex: "Projects/oloroke.md")
    - line_number: Número da linha (0-indexed)
    - completed: True para marcar como [x], False para [ ]
    """
    try:
        full_path = vault.resolve_note(note_path)
    except VaultPathError as e:
        return error_response(str(e))

    lines = vault.read_text(full_path).splitlines(keepends=True)

    if not 0 <= line_number < len(lines):
        return error_response("Linha não existe")

    if not CHECKBOX_RE.match(lines[line_number]):
        return error_response(f"A linha {line_number} não é um to-do (- [ ] / - [x])")

    mark = "x" if completed else " "
    lines[line_number] = CHECKBOX_RE.sub(rf"\g<1>{mark}\g<3>", lines[line_number], count=1)

    vault.write_text(full_path, "".join(lines))

    return json.dumps({
        "success": True,
        "message": f"Tarefa marcada como {'completa' if completed else 'incompleta'}"
    }, ensure_ascii=False)


@mcp.tool()
def list_projects() -> str:
    """Lista todos os projetos encontrados nas notas (via frontmatter)"""
    projects = set()

    try:
        notes = list(vault.iter_notes())
    except VaultPathError as e:
        return error_response(str(e))

    for md_file in notes:
        try:
            content = vault.read_text(md_file)
            
            metadata, _ = extract_frontmatter(content)
            project = metadata.get('projeto') or metadata.get('project')
            
            if project:
                projects.add(str(project))
        except (OSError, UnicodeDecodeError):
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
