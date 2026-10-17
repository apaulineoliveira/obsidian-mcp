import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .errors import SearchError


MAX_QUERY_LENGTH = 500
MAX_EXCERPT_LENGTH = 240
MAX_RESULTS_LIMIT = 200
MAX_MATCHES_PER_NOTE_LIMIT = 100


@dataclass(frozen=True)
class LineMatch:
    line: int
    text: str


@dataclass(frozen=True)
class NoteMatch:
    file: str
    tags: list[str]
    match_count: int = 0
    matches: list[LineMatch] = field(default_factory=list)


@dataclass(frozen=True)
class SearchQuery:
    query: Optional[str] = None
    regex: bool = False
    case_sensitive: bool = False
    tags: Optional[list[str]] = None
    frontmatter: Optional[dict[str, Any]] = None
    folder: Optional[str] = None
    max_results: int = 50
    max_matches_per_note: int = 20

    def validate(self) -> None:
        if not self.query and not self.tags and not self.frontmatter:
            raise SearchError("Informe 'query', 'tags' e/ou 'frontmatter'")

    @property
    def results_limit(self) -> int:
        return clamp(self.max_results, 1, MAX_RESULTS_LIMIT)

    @property
    def matches_per_note_limit(self) -> int:
        return clamp(self.max_matches_per_note, 1, MAX_MATCHES_PER_NOTE_LIMIT)


@dataclass(frozen=True)
class SearchResult:
    notes: list[NoteMatch]
    total_notes_matched: int

    @property
    def truncated(self) -> bool:
        return self.total_notes_matched > len(self.notes)


def clamp(value: int, minimum: int, maximum: int) -> int:
    return min(max(value, minimum), maximum)


def compile_search_pattern(query: str, regex: bool = False, case_sensitive: bool = False) -> re.Pattern:
    if len(query) > MAX_QUERY_LENGTH:
        raise SearchError(f"Consulta muito longa (máx. {MAX_QUERY_LENGTH} caracteres)")

    flags = 0 if case_sensitive else re.IGNORECASE
    source = query if regex else re.escape(query)
    try:
        return re.compile(source, flags)
    except re.error as error:
        raise SearchError(f"Regex inválida: {error}") from error


def find_matching_lines(content: str, pattern: re.Pattern) -> list[LineMatch]:
    matches = []
    for line_number, line in enumerate(content.splitlines()):
        match = pattern.search(line)
        if match:
            matches.append(LineMatch(line_number, excerpt_around(line, match.start(), match.end())))
    return matches


def excerpt_around(line: str, match_start: int, match_end: int) -> str:
    if len(line) <= MAX_EXCERPT_LENGTH:
        return line.strip()

    context = (MAX_EXCERPT_LENGTH - (match_end - match_start)) // 2
    window_start = max(0, min(match_start - context, len(line) - MAX_EXCERPT_LENGTH))
    window_end = window_start + MAX_EXCERPT_LENGTH

    prefix = "…" if window_start > 0 else ""
    suffix = "…" if window_end < len(line) else ""
    return prefix + line[window_start:window_end].strip() + suffix


def metadata_matches(metadata: dict, filters: Optional[dict[str, Any]]) -> bool:
    for key, expected in (filters or {}).items():
        if key not in metadata:
            return False

        available = {_comparable(value) for value in _as_list(metadata[key])}
        if not all(_comparable(value) in available for value in _as_list(expected)):
            return False

    return True


def rank_by_relevance(notes: list[NoteMatch], limit: int) -> SearchResult:
    ranked = sorted(notes, key=lambda note: (-note.match_count, note.file))
    return SearchResult(notes=ranked[:limit], total_notes_matched=len(ranked))


def _as_list(value: Any) -> list:
    return list(value) if isinstance(value, (list, tuple, set)) else [value]


def _comparable(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value).strip().lower()
