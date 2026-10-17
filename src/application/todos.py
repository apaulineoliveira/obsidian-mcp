from typing import Optional

from core.frontmatter import Frontmatter
from core.ports import NoteRepository
from core.priorities import DEFAULT_LANGUAGE
from core.todos import Todo, TodoFilter, note_defaults, parse_todos, set_todo_completed

from .vault_notes import read_vault_notes


class TodoService:
    def __init__(self, repository: NoteRepository, frontmatter: Frontmatter):
        self.repository = repository
        self.frontmatter = frontmatter

    def list_todos(
        self,
        folder: Optional[str] = None,
        todo_filter: Optional[TodoFilter] = None,
        language: str = DEFAULT_LANGUAGE,
    ) -> list[Todo]:
        todo_filter = todo_filter or TodoFilter()
        todos = []
        for note in read_vault_notes(self.repository, self.frontmatter, folder):
            defaults = note_defaults(note.metadata, language)
            note_todos = parse_todos(note.path, note.body, note.body_start_line, defaults)
            todos.extend(todo for todo in note_todos if todo_filter.matches(todo))
        return todos

    def set_completed(self, note_path: str, line_number: int, completed: bool) -> None:
        content = self.repository.read(note_path)
        self.repository.write(note_path, set_todo_completed(content, line_number, completed))
