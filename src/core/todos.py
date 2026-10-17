import re
from dataclasses import asdict, dataclass
from typing import Optional

from .errors import TodoError
from .priorities import PRIORITY_BY_EMOJI, normalize_priority, priority_from_emoji
from .tags import frontmatter_tags, has_all_tags, inline_tags, remove_inline_tags, unique_lowercase


CHECKBOX_PATTERN = re.compile(r"^(?P<prefix>\s*[-*+]\s+\[)(?P<mark>[ xX])\]")
PRIORITY_EMOJI_PATTERN = re.compile("|".join(map(re.escape, PRIORITY_BY_EMOJI)))


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

    def matches(self, todo: Todo) -> bool:
        if self.completed is not None and todo.completed != self.completed:
            return False
        if self.tag and not has_all_tags(todo.tags, [self.tag]):
            return False
        if self.priority and todo.priority != self.priority:
            return False
        return True


@dataclass(frozen=True)
class NoteDefaults:
    tags: list[str]
    priority: Optional[str]
    project: Optional[str]


def project_name(metadata: dict) -> Optional[str]:
    project = metadata.get("projeto") or metadata.get("project")
    return str(project) if project is not None else None


def frontmatter_priority(metadata: dict, language: str) -> Optional[str]:
    raw_priority = metadata.get("prioridade") or metadata.get("priority")
    return normalize_priority(str(raw_priority) if raw_priority is not None else None, language)


def note_defaults(metadata: dict, language: str) -> NoteDefaults:
    return NoteDefaults(
        tags=frontmatter_tags(metadata),
        priority=frontmatter_priority(metadata, language),
        project=project_name(metadata),
    )


def parse_todos(note_path: str, body: str, body_start_line: int, defaults: NoteDefaults) -> list[Todo]:
    todos = []
    for index, line in enumerate(body.split("\n")):
        checkbox = CHECKBOX_PATTERN.match(line)
        if checkbox:
            completed = checkbox.group("mark").lower() == "x"
            todos.append(_build_todo(note_path, body_start_line + index, line, completed, defaults))
    return todos


def set_todo_completed(content: str, line_number: int, completed: bool) -> str:
    lines = content.splitlines(keepends=True)
    if not 0 <= line_number < len(lines):
        raise TodoError("Linha não existe")

    checkbox = CHECKBOX_PATTERN.match(lines[line_number])
    if not checkbox:
        raise TodoError(f"A linha {line_number} não é um to-do (- [ ] / - [x])")

    mark = "x" if completed else " "
    line = lines[line_number]
    lines[line_number] = checkbox.group("prefix") + mark + line[checkbox.end() - 1:]
    return "".join(lines)


def _build_todo(note_path: str, line_number: int, line: str, completed: bool, defaults: NoteDefaults) -> Todo:
    return Todo(
        file=note_path,
        line=line_number,
        completed=completed,
        text=_readable_text(line),
        raw_text=line.strip(),
        tags=unique_lowercase(defaults.tags + inline_tags(line)),
        priority=priority_from_emoji(line) or defaults.priority,
        project=defaults.project,
    )


def _readable_text(line: str) -> str:
    without_emoji = PRIORITY_EMOJI_PATTERN.sub("", line.strip()).strip()
    return remove_inline_tags(without_emoji).strip()
