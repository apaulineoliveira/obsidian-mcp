import datetime
import functools
import json
from dataclasses import asdict
from typing import Any, Callable, Optional

from mcp.server.mcpserver import MCPServer

from application import Services
from application.languages import supported_language_names
from core.errors import DomainError
from core.paths import safe_note_path
from core.priorities import DEFAULT_LANGUAGE
from core.search import SearchQuery
from core.todos import TodoFilter


SERVER_NAME = "obsidian-mcp"

TOOL_NAMES = (
    "get_todos",
    "get_note_content",
    "create_note",
    "update_todo",
    "get_frontmatter",
    "update_frontmatter",
    "search_notes",
    "list_tags",
    "list_projects",
    "get_supported_languages",
)


def to_json(data: Any, indent: Optional[int] = 2) -> str:
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


def error_response(message: str) -> str:
    return to_json({"error": message}, indent=None)


def json_compatible(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_compatible(item) for item in value]
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


def display_path(note_path: str) -> str:
    return safe_note_path(note_path).as_posix()


def returns_errors_as_json(tool: Callable[..., str]) -> Callable[..., str]:
    @functools.wraps(tool)
    def run_tool(*args, **kwargs) -> str:
        try:
            return tool(*args, **kwargs)
        except DomainError as error:
            return error_response(str(error))
    return run_tool


class VaultTools:
    def __init__(self, services: Services):
        self.services = services

    @returns_errors_as_json
    def get_todos(
        self,
        folder: Optional[str] = None,
        tag: Optional[str] = None,
        priority: Optional[str] = None,
        completed: Optional[bool] = None,
        language: Optional[str] = DEFAULT_LANGUAGE
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
        todos = self.services.todos.list_todos(
            folder,
            TodoFilter(tag=tag, priority=priority, completed=completed),
            language or DEFAULT_LANGUAGE,
        )
        return to_json({
            "todos": [todo.to_dict() for todo in todos],
            "count": len(todos),
            "filters": {
                "folder": folder,
                "tag": tag,
                "priority": priority,
                "completed": completed,
                "language": language
            }
        })

    @returns_errors_as_json
    def get_note_content(self, note_path: str) -> str:
        """Lê o conteúdo completo de uma nota do Obsidian"""
        return self.services.notes.get_content(note_path)

    @returns_errors_as_json
    def create_note(self, note_path: str, content: str) -> str:
        """
        Cria uma nota nova no vault. Nunca sobrescreve uma nota existente.

        Parâmetros:
        - note_path: Caminho da nota relativo ao vault (ex: "Artigos/rascunho.md").
          Pastas que não existem são criadas.
        - content: Conteúdo Markdown da nota (pode incluir frontmatter YAML)
        """
        self.services.notes.create_note(note_path, content)
        return to_json({"success": True, "file": display_path(note_path)}, indent=None)

    @returns_errors_as_json
    def update_todo(self, note_path: str, line_number: int, completed: bool) -> str:
        """
        Marca um to-do como completo ou incompleto em uma nota.

        Parâmetros:
        - note_path: Caminho da nota (ex: "Projects/oloroke.md")
        - line_number: Número da linha (0-indexed)
        - completed: True para marcar como [x], False para [ ]
        """
        self.services.todos.set_completed(note_path, line_number, completed)
        return to_json({
            "success": True,
            "message": f"Tarefa marcada como {'completa' if completed else 'incompleta'}"
        }, indent=None)

    @returns_errors_as_json
    def get_frontmatter(self, note_path: str) -> str:
        """
        Lê os metadados YAML (frontmatter) de uma nota.

        Parâmetros:
        - note_path: Caminho da nota relativo ao vault (ex: "Projects/oloroke.md")
        """
        metadata = self.services.notes.get_frontmatter(note_path)
        return to_json({"file": display_path(note_path), "frontmatter": json_compatible(metadata)})

    @returns_errors_as_json
    def update_frontmatter(
        self,
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
        metadata = self.services.notes.update_frontmatter(note_path, set_values, remove_keys)
        return to_json({
            "success": True,
            "file": display_path(note_path),
            "frontmatter": json_compatible(metadata)
        })

    @returns_errors_as_json
    def search_notes(
        self,
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
        result = self.services.search.search(SearchQuery(
            query=query,
            regex=regex,
            case_sensitive=case_sensitive,
            tags=tags,
            frontmatter=frontmatter,
            folder=folder,
            max_results=max_results,
            max_matches_per_note=max_matches_per_note,
        ))
        return to_json({
            "results": [asdict(note) for note in result.notes],
            "count": len(result.notes),
            "total_notes_matched": result.total_notes_matched,
            "truncated": result.truncated,
            "filters": {
                "query": query,
                "regex": regex,
                "case_sensitive": case_sensitive,
                "tags": tags,
                "frontmatter": frontmatter,
                "folder": folder
            }
        })

    @returns_errors_as_json
    def list_tags(self, folder: Optional[str] = None) -> str:
        """
        Lista todas as tags do vault (inline e frontmatter) com o número de
        notas em que aparecem, da mais usada para a menos usada.

        Parâmetros:
        - folder: Restringe a uma pasta (ex: "Projects")
        """
        tags = self.services.notes.list_tags(folder)
        return to_json({
            "tags": [{"tag": tag, "notes": count} for tag, count in tags],
            "count": len(tags)
        })

    @returns_errors_as_json
    def list_projects(self) -> str:
        """Lista todos os projetos encontrados nas notas (via frontmatter)"""
        projects = self.services.notes.list_projects()
        return to_json({"projects": projects, "count": len(projects)})

    @returns_errors_as_json
    def get_supported_languages(self) -> str:
        """
        Lista todos os idiomas suportados para filtros de prioridade.

        Retorna:
            JSON com lista de códigos de idioma
        """
        names_by_code = supported_language_names()
        return to_json({
            "languages": list(names_by_code),
            "count": len(names_by_code),
            "details": names_by_code
        })


def create_server(services: Services) -> MCPServer:
    server = MCPServer(SERVER_NAME)
    tools = VaultTools(services)
    for name in TOOL_NAMES:
        server.tool()(getattr(tools, name))
    return server
