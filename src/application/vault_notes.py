from dataclasses import dataclass
from typing import Iterator, Optional

from core.errors import NoteReadError
from core.frontmatter import Frontmatter
from core.ports import NoteRepository


@dataclass(frozen=True)
class VaultNote:
    path: str
    content: str
    metadata: dict
    body: str
    body_start_line: int


def read_vault_notes(
    repository: NoteRepository,
    frontmatter: Frontmatter,
    folder: Optional[str] = None,
) -> Iterator[VaultNote]:
    for path in repository.list_notes(folder):
        try:
            content = repository.read(path)
        except NoteReadError:
            continue

        parsed = frontmatter.parse_ignoring_invalid_yaml(content)
        yield VaultNote(path, content, parsed.metadata, parsed.body, parsed.body_start_line)
