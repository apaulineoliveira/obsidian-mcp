from dataclasses import dataclass
from typing import Iterator, Optional

from core.errors import NoteReadError
from core.frontmatter import FrontmatterParser
from core.ports import NoteRepository


@dataclass(frozen=True)
class Document:
    path: str
    content: str
    metadata: dict
    body: str
    line_offset: int


def load_documents(
    repository: NoteRepository,
    parser: FrontmatterParser,
    folder: Optional[str] = None,
) -> Iterator[Document]:
    for path in repository.list_notes(folder):
        try:
            content = repository.read(path)
        except NoteReadError:
            continue
        note = parser.parse_lenient(content)
        yield Document(path, content, note.metadata, note.body, note.line_offset)
