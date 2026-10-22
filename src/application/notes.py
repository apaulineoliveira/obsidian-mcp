from typing import Any, Optional

from core.errors import FrontmatterError
from core.frontmatter import Frontmatter
from core.ports import NoteRepository
from core.tags import count_notes_per_tag, note_tags
from core.todos import project_name

from .vault_notes import read_vault_notes


class NoteService:
    def __init__(self, repository: NoteRepository, frontmatter: Frontmatter):
        self.repository = repository
        self.frontmatter = frontmatter

    def get_content(self, note_path: str) -> str:
        return self.repository.read(note_path)

    def create_note(self, note_path: str, content: str) -> None:
        self.repository.create(note_path, content)

    def get_frontmatter(self, note_path: str) -> dict:
        content = self.repository.read(note_path)
        return self.frontmatter.parse(content).metadata

    def update_frontmatter(
        self,
        note_path: str,
        set_values: Optional[dict[str, Any]] = None,
        remove_keys: Optional[list[str]] = None,
    ) -> dict:
        if not set_values and not remove_keys:
            raise FrontmatterError("Informe 'set_values' e/ou 'remove_keys'")

        content = self.repository.read(note_path)
        updated_content = self.frontmatter.update(content, set_values, remove_keys)
        if updated_content != content:
            self.repository.write(note_path, updated_content)

        return self.frontmatter.parse(updated_content).metadata

    def list_tags(self, folder: Optional[str] = None) -> list[tuple[str, int]]:
        notes = read_vault_notes(self.repository, self.frontmatter, folder)
        return count_notes_per_tag(note_tags(note.metadata, note.body) for note in notes)

    def list_projects(self) -> list[str]:
        notes = read_vault_notes(self.repository, self.frontmatter)
        projects = {project_name(note.metadata) for note in notes}
        return sorted(project for project in projects if project)
