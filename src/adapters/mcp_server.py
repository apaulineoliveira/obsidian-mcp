import functools
import json
from dataclasses import asdict
from typing import Any, Callable, Optional

from mcp.server.mcpserver import MCPServer

from application import Services
from application.languages import supported_languages
from core.errors import DomainError
from core.frontmatter import to_jsonable
from core.paths import normalize_note_path
from core.search import SearchQuery
from core.todos import TodoFilter


SERVER_NAME = "obsidian-mcp"

TOOL_NAMES = (
    "get_todos",
    "get_note_content",
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


def handles_domain_errors(method: Callable[..., str]) -> Callable[..., str]:
    @functools.wraps(method)
    def wrapper(*args, **kwargs) -> str:
        try:
            return method(*args, **kwargs)
        except DomainError as e:
            return error_response(str(e))
    return wrapper


class VaultTools:
    def __init__(self, services: Services):
        self.services = services

    @handles_domain_errors
    def get_todos(
        self,
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
        todos = self.services.todos.list_todos(
            folder,
            TodoFilter(tag=tag, priority=priority, completed=completed),
            language or 'en',
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

    @handles_domain_errors
    def get_note_content(self, note_path: str) -> str:
        """Lê o conteúdo completo de uma nota do Obsidian"""
        return self.services.notes.get_content(note_path)

    @handles_domain_errors
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

    @handles_domain_errors
    def get_frontmatter(self, note_path: str) -> str:
        """
        Lê os metadados YAML (frontmatter) de uma nota.

        Parâmetros:
        - note_path: Caminho da nota relativo ao vault (ex: "Projects/oloroke.md")
        """
        metadata = self.services.notes.get_frontmatter(note_path)
        return to_json({"file": normalize_note_path(note_path).as_posix(), "frontmatter": to_jsonable(metadata)})

    @handles_domain_errors
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
            "file": normalize_note_path(note_path).as_posix(),
            "frontmatter": to_jsonable(metadata)
        })

    @handles_domain_errors
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
            "results": [asdict(match) for match in result.results],
            "count": len(result.results),
            "total_notes_matched": result.total,
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

    @handles_domain_errors
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

    @handles_domain_errors
    def list_projects(self) -> str:
        """Lista todos os projetos encontrados nas notas (via frontmatter)"""
        projects = self.services.notes.list_projects()
        return to_json({"projects": projects, "count": len(projects)})

    @handles_domain_errors
    def get_supported_languages(self) -> str:
        """
        Lista todos os idiomas suportados para filtros de prioridade.

        Retorna:
            JSON com lista de códigos de idioma
        """
        languages = supported_languages()
        return to_json({
            "languages": list(languages),
            "count": len(languages),
            "details": languages
        })


def create_server(services: Services) -> MCPServer:
    server = MCPServer(SERVER_NAME)
    tools = VaultTools(services)
    for name in TOOL_NAMES:
        server.tool()(getattr(tools, name))
    return server
