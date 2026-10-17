from dataclasses import dataclass

from core.frontmatter import FrontmatterParser
from core.ports import FrontmatterCodec, NoteRepository

from .notes import NoteService
from .search import SearchService
from .todos import TodoService


@dataclass(frozen=True)
class Services:
    notes: NoteService
    todos: TodoService
    search: SearchService


def build_services(repository: NoteRepository, codec: FrontmatterCodec) -> Services:
    parser = FrontmatterParser(codec)
    return Services(
        notes=NoteService(repository, parser),
        todos=TodoService(repository, parser),
        search=SearchService(repository, parser),
    )
