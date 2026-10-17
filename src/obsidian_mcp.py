import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

from i18n import (
    normalize_priority,
    extract_priority_emoji,
    get_supported_languages
)
from frontmatter import (
    FrontmatterError,
    extract_frontmatter,
    parse_frontmatter,
    to_jsonable,
    update_frontmatter as apply_frontmatter_update,
)
from search import (
    INLINE_TAG_RE,
    SearchError,
    compile_query,
    extract_inline_tags,
    find_matches,
    has_all_tags,
    matches_frontmatter,
    normalize_tags,
    note_tags,
    unique_tags,
)
from vault import Vault, VaultPathError

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

vault = Vault(os.getenv("OBSIDIAN_VAULT_PATH", "~/Obsidian"))

mcp = MCPServer("obsidian-mcp")

CHECKBOX_RE = re.compile(r'^(\s*[-*+]\s+\[)([ xX])(\])')


def error_response(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)


def matches_filter(todo: dict, tag: Optional[str], priority: Optional[str]) -> bool:
    if tag:
        if not has_all_tags(todo.get('tags', []), [tag]):
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
    - tag: Filtrar por tag (ex: "urgente", "backend"; "projeto" inclui "projeto/x")
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

            file_metadata, body_content, line_offset = extract_frontmatter(content)


            frontmatter_tags = (
                normalize_tags(file_metadata.get('tags')) + normalize_tags(file_metadata.get('tag'))
            )

            frontmatter_priority_raw = file_metadata.get('prioridade') or file_metadata.get('priority')
            frontmatter_priority = normalize_priority(
                str(frontmatter_priority_raw) if frontmatter_priority_raw is not None else None,
                language=language
            )

            lines = body_content.split('\n')

            for i, line in enumerate(lines):
                checkbox = CHECKBOX_RE.match(line)
                if checkbox:
                    is_completed = checkbox.group(2).lower() == "x"

                    if completed is not None and is_completed != completed:
                        continue

                    inline_tags = extract_inline_tags(line)
                    inline_priority = extract_priority_emoji(line)

                    all_tags = unique_tags(frontmatter_tags + inline_tags)


                    final_priority = inline_priority or frontmatter_priority

                    clean_text = line.strip()
                    clean_text = re.sub(r'🔴|🟡|🟢|⚫', '', clean_text).strip()
                    clean_text = INLINE_TAG_RE.sub('', clean_text).strip()

                    todo = {
                        "file": str(relative_path),
                        "line": line_offset + i,
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
def get_frontmatter(note_path: str) -> str:
    """
    Lê os metadados YAML (frontmatter) de uma nota.

    Parâmetros:
    - note_path: Caminho da nota relativo ao vault (ex: "Projects/oloroke.md")
    """
    try:
        full_path = vault.resolve_note(note_path)
        metadata, _, _ = parse_frontmatter(vault.read_text(full_path))
    except (VaultPathError, FrontmatterError) as e:
        return error_response(str(e))

    return json.dumps({
        "file": vault.relative(full_path),
        "frontmatter": to_jsonable(metadata)
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def update_frontmatter(
    note_path: str,
    set_values: Optional[dict[str, Any]] = None,
    remove_keys: Optional[list[str]] = None
) -> str:
    """
    Cria, altera ou remove chaves do frontmatter YAML de uma nota,
    preservando comentários, ordem das chaves e o corpo da nota.

    Parâmetros:
    - note_path: Caminho da nota relativo ao vault (ex: "Projects/oloroke.md")
    - set_values: Chaves a criar/sobrescrever (ex: {"status": "done", "tags": ["a", "b"]})
    - remove_keys: Chaves a remover (ex: ["draft"])

    Se a nota não tiver frontmatter, um bloco é criado no topo.
    """
    if not set_values and not remove_keys:
        return error_response("Informe 'set_values' e/ou 'remove_keys'")

    try:
        full_path = vault.resolve_note(note_path)
        content = vault.read_text(full_path)
        new_content = apply_frontmatter_update(content, set_values, remove_keys)
        metadata, _, _ = parse_frontmatter(new_content)
    except (VaultPathError, FrontmatterError) as e:
        return error_response(str(e))

    if new_content != content:
        vault.write_text(full_path, new_content)

    return json.dumps({
        "success": True,
        "file": vault.relative(full_path),
        "frontmatter": to_jsonable(metadata)
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def search_notes(
    query: Optional[str] = None,
    regex: bool = False,
    case_sensitive: bool = False,
    tags: Optional[list[str]] = None,
    frontmatter: Optional[dict[str, Any]] = None,
    folder: Optional[str] = None,
    max_results: int = 50,
    max_matches_per_note: int = 20
) -> str:
    """
    Busca notas por texto, regex, tags e/ou campos do frontmatter.
    Os filtros são combinados (AND). Informe pelo menos um deles.

    Parâmetros:
    - query: Texto a procurar no conteúdo (ou regex, se regex=True)
    - regex: Interpreta query como expressão regular Python
    - case_sensitive: Diferencia maiúsculas/minúsculas (padrão: não)
    - tags: Nota deve ter todas as tags (inline ou frontmatter). "projeto" inclui "projeto/x"
    - frontmatter: Campos que devem casar (ex: {"status": "draft", "tags": "api"})
    - folder: Restringe a busca a uma pasta (ex: "Projects")
    - max_results: Máximo de notas retornadas (1-200)
    - max_matches_per_note: Máximo de trechos por nota (1-100)

    As notas são ordenadas pela quantidade de linhas que casam com a query.
    Os números de linha (0-indexed) valem para o arquivo inteiro.
    """
    if not query and not tags and not frontmatter:
        return error_response("Informe 'query', 'tags' e/ou 'frontmatter'")

    max_results = min(max(max_results, 1), 200)
    max_matches_per_note = min(max(max_matches_per_note, 1), 100)

    try:
        pattern = compile_query(query, regex, case_sensitive) if query else None
        notes = list(vault.iter_notes(folder))
    except (SearchError, VaultPathError) as e:
        return error_response(str(e))

    results = []
    for md_file in notes:
        try:
            content = vault.read_text(md_file)
        except (OSError, UnicodeDecodeError):
            continue

        metadata, body, _ = extract_frontmatter(content)
        if not matches_frontmatter(metadata, frontmatter):
            continue

        file_tags = note_tags(metadata, body)
        if tags and not has_all_tags(file_tags, tags):
            continue

        matches, match_count = [], 0
        if pattern:
            matches, match_count = find_matches(content, pattern, max_matches_per_note)
            if not match_count:
                continue

        results.append({
            "file": vault.relative(md_file),
            "tags": file_tags,
            "match_count": match_count,
            "matches": matches
        })

    results.sort(key=lambda r: (-r["match_count"], r["file"]))

    return json.dumps({
        "results": results[:max_results],
        "count": min(len(results), max_results),
        "total_notes_matched": len(results),
        "truncated": len(results) > max_results,
        "filters": {
            "query": query,
            "regex": regex,
            "case_sensitive": case_sensitive,
            "tags": tags,
            "frontmatter": frontmatter,
            "folder": folder
        }
    }, indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def list_tags(folder: Optional[str] = None) -> str:
    """
    Lista todas as tags do vault (inline e frontmatter) com o número de
    notas em que aparecem, da mais usada para a menos usada.

    Parâmetros:
    - folder: Restringe a uma pasta (ex: "Projects")
    """
    try:
        notes = list(vault.iter_notes(folder))
    except VaultPathError as e:
        return error_response(str(e))

    counts: dict[str, int] = {}
    for md_file in notes:
        try:
            metadata, body, _ = extract_frontmatter(vault.read_text(md_file))
        except (OSError, UnicodeDecodeError):
            continue
        for tag in note_tags(metadata, body):
            counts[tag] = counts.get(tag, 0) + 1

    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    return json.dumps({
        "tags": [{"tag": tag, "notes": count} for tag, count in ordered],
        "count": len(ordered)
    }, indent=2, ensure_ascii=False)


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

            metadata, _, _ = extract_frontmatter(content)
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
