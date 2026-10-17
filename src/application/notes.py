from typing import Any, Optional

from core.errors import FrontmatterError
from core.frontmatter import FrontmatterParser
from core.ports import NoteRepository
from core.tags import count_tags, note_tags
from core.todos import project_of

from .documents import load_documents


class NoteService:
    def __init__(self, repository: NoteRepository, parser: FrontmatterParser):
        self.repository = repository
        self.parser = parser

    def get_content(self, note_path: str) -> str:
        return self.repository.read(note_path)

    def get_frontmatter(self, note_path: str) -> dict:
        return self.parser.parse(self.repository.read(note_path)).metadata

    def update_frontmatter(
        self,
        note_path: str,
        set_values: Optional[dict[str, Any]] = None,
        remove_keys: Optional[list[str]] = None,
    ) -> dict:
        if not set_values and not remove_keys:
            raise FrontmatterError("Informe 'set_values' e/ou 'remove_keys'")

        content = self.repository.read(note_path)
        new_content = self.parser.update(content, set_values, remove_keys)
        metadata = self.parser.parse(new_content).metadata

        if new_content != content:
            self.repository.write(note_path, new_content)
        return metadata

    def list_tags(self, folder: Optional[str] = None) -> list[tuple[str, int]]:
        documents = load_documents(self.repository, self.parser, folder)
        return count_tags(note_tags(doc.metadata, doc.body) for doc in documents)

    def list_projects(self) -> list[str]:
        projects = {project_of(doc.metadata) for doc in load_documents(self.repository, self.parser)}
        return sorted(p for p in projects if p)
