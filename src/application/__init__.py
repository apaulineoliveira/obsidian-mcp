from dataclasses import dataclass

from core.frontmatter import Frontmatter
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
    frontmatter = Frontmatter(codec)
    return Services(
        notes=NoteService(repository, frontmatter),
        todos=TodoService(repository, frontmatter),
        search=SearchService(repository, frontmatter),
    )
