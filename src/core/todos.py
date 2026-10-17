import re
from dataclasses import asdict, dataclass
from typing import Optional

from .errors import TodoError
from .i18n import EMOJI_PRIORITY, extract_priority_emoji, normalize_priority
from .tags import extract_inline_tags, frontmatter_tags, has_all_tags, strip_inline_tags, unique_tags


CHECKBOX_RE = re.compile(r"^(\s*[-*+]\s+\[)([ xX])(\])")
PRIORITY_EMOJI_RE = re.compile("|".join(map(re.escape, EMOJI_PRIORITY)))


@dataclass(frozen=True)
class Todo:
    file: str
    line: int
    completed: bool
    text: str
    raw_text: str
    tags: list[str]
    priority: Optional[str]
    project: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TodoFilter:
    tag: Optional[str] = None
    priority: Optional[str] = None
    completed: Optional[bool] = None

    def accepts(self, todo: Todo) -> bool:
        if self.completed is not None and todo.completed != self.completed:
            return False
        if self.tag and not has_all_tags(todo.tags, [self.tag]):
            return False
        if self.priority and todo.priority != self.priority:
            return False
        return True


def project_of(metadata: dict) -> Optional[str]:
    project = metadata.get("projeto") or metadata.get("project")
    return str(project) if project is not None else None


def priority_of(metadata: dict, language: str) -> Optional[str]:
    raw = metadata.get("prioridade") or metadata.get("priority")
    return normalize_priority(str(raw) if raw is not None else None, language=language)


def parse_todos(
    file: str,
    metadata: dict,
    body: str,
    line_offset: int,
    language: str = "en",
) -> list[Todo]:
    base_tags = frontmatter_tags(metadata)
    base_priority = priority_of(metadata, language)
    project = project_of(metadata)
    todos = []

    for i, line in enumerate(body.split("\n")):
        checkbox = CHECKBOX_RE.match(line)
        if not checkbox:
            continue

        clean_text = PRIORITY_EMOJI_RE.sub("", line.strip()).strip()
        clean_text = strip_inline_tags(clean_text).strip()

        todos.append(Todo(
            file=file,
            line=line_offset + i,
            completed=checkbox.group(2).lower() == "x",
            text=clean_text,
            raw_text=line.strip(),
            tags=unique_tags(base_tags + extract_inline_tags(line)),
            priority=extract_priority_emoji(line) or base_priority,
            project=project,
        ))

    return todos


def set_checkbox(content: str, line_number: int, completed: bool) -> str:
    lines = content.splitlines(keepends=True)

    if not 0 <= line_number < len(lines):
        raise TodoError("Linha não existe")

    if not CHECKBOX_RE.match(lines[line_number]):
        raise TodoError(f"A linha {line_number} não é um to-do (- [ ] / - [x])")

    mark = "x" if completed else " "
    lines[line_number] = CHECKBOX_RE.sub(rf"\g<1>{mark}\g<3>", lines[line_number], count=1)
    return "".join(lines)
