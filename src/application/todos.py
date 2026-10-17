from typing import Optional

from core.frontmatter import FrontmatterParser
from core.ports import NoteRepository
from core.todos import Todo, TodoFilter, parse_todos, set_checkbox

from .documents import load_documents


class TodoService:
    def __init__(self, repository: NoteRepository, parser: FrontmatterParser):
        self.repository = repository
        self.parser = parser

    def list_todos(
        self,
        folder: Optional[str] = None,
        todo_filter: TodoFilter = TodoFilter(),
        language: str = "en",
    ) -> list[Todo]:
        todos = []
        for doc in load_documents(self.repository, self.parser, folder):
            for todo in parse_todos(doc.path, doc.metadata, doc.body, doc.line_offset, language):
                if todo_filter.accepts(todo):
                    todos.append(todo)
        return todos

    def set_completed(self, note_path: str, line_number: int, completed: bool) -> None:
        content = self.repository.read(note_path)
        self.repository.write(note_path, set_checkbox(content, line_number, completed))
