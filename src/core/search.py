import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .errors import SearchError


MAX_PATTERN_LENGTH = 500
MAX_SNIPPET_LENGTH = 240
MAX_RESULTS_LIMIT = 200
MAX_MATCHES_LIMIT = 100


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

    def validate(self) -> "SearchQuery":
        if not self.query and not self.tags and not self.frontmatter:
            raise SearchError("Informe 'query', 'tags' e/ou 'frontmatter'")
        return self

    @property
    def result_limit(self) -> int:
        return clamp(self.max_results, 1, MAX_RESULTS_LIMIT)

    @property
    def match_limit(self) -> int:
        return clamp(self.max_matches_per_note, 1, MAX_MATCHES_LIMIT)

    def pattern(self) -> Optional[re.Pattern]:
        if not self.query:
            return None
        return compile_query(self.query, self.regex, self.case_sensitive)


@dataclass(frozen=True)
class SearchResult:
    results: list[NoteMatch]
    total: int

    @property
    def truncated(self) -> bool:
        return self.total > len(self.results)


def clamp(value: int, low: int, high: int) -> int:
    return min(max(value, low), high)


def compile_query(query: str, regex: bool = False, case_sensitive: bool = False) -> re.Pattern:
    if len(query) > MAX_PATTERN_LENGTH:
        raise SearchError(f"Consulta muito longa (máx. {MAX_PATTERN_LENGTH} caracteres)")

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        return re.compile(query if regex else re.escape(query), flags)
    except re.error as e:
        raise SearchError(f"Regex inválida: {e}") from e


def find_matches(content: str, pattern: re.Pattern, limit: int) -> tuple[list[LineMatch], int]:
    matches = []
    total = 0

    for i, line in enumerate(content.splitlines()):
        match = pattern.search(line)
        if not match:
            continue
        total += 1
        if len(matches) < limit:
            matches.append(LineMatch(i, snippet(line, match.start(), match.end())))

    return matches, total


def snippet(line: str, start: int, end: int) -> str:
    if len(line) <= MAX_SNIPPET_LENGTH:
        return line.strip()

    padding = max(0, (MAX_SNIPPET_LENGTH - (end - start)) // 2)
    left = max(0, start - padding)
    right = min(len(line), left + MAX_SNIPPET_LENGTH)
    left = max(0, right - MAX_SNIPPET_LENGTH)
    return ("…" if left else "") + line[left:right].strip() + ("…" if right < len(line) else "")


def matches_frontmatter(metadata: dict, filters: Optional[dict[str, Any]]) -> bool:
    for key, expected in (filters or {}).items():
        if key not in metadata:
            return False

        actual = metadata[key]
        actual_values = actual if isinstance(actual, (list, tuple, set)) else [actual]
        expected_values = expected if isinstance(expected, (list, tuple, set)) else [expected]

        actual_norm = {_normalize_value(v) for v in actual_values}
        if not all(_normalize_value(v) in actual_norm for v in expected_values):
            return False

    return True


def rank(matches: list[NoteMatch], limit: int) -> SearchResult:
    ordered = sorted(matches, key=lambda m: (-m.match_count, m.file))
    return SearchResult(results=ordered[:limit], total=len(ordered))


def _normalize_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value).strip().lower()
