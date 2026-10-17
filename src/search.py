import re
from typing import Any, Iterable, Optional


MAX_PATTERN_LENGTH = 500
MAX_SNIPPET_LENGTH = 240

INLINE_TAG_RE = re.compile(r"(?<![\w#/&])#([\w/-]+)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


class SearchError(ValueError):
    pass


def extract_inline_tags(text: str) -> list[str]:
    tags = []
    in_fence = False

    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for tag in INLINE_TAG_RE.findall(INLINE_CODE_RE.sub("", line)):
            tag = tag.strip("/")
            if tag and not tag.replace("/", "").isdigit():
                tags.append(tag)

    return tags


def normalize_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = re.split(r"[,\s]+", value)
    elif isinstance(value, (list, tuple, set)):
        items = [str(v) for v in value if v is not None]
    else:
        items = [str(value)]

    return [item.strip().lstrip("#") for item in items if item.strip().lstrip("#")]


def unique_tags(tags: Iterable[str]) -> list[str]:
    seen = {}
    for tag in tags:
        seen.setdefault(tag.lower(), None)
    return list(seen)


def note_tags(metadata: dict, body: str) -> list[str]:
    frontmatter_tags = normalize_tags(metadata.get("tags")) + normalize_tags(metadata.get("tag"))
    return unique_tags(frontmatter_tags + extract_inline_tags(body))


def tag_matches(wanted: str, tag: str) -> bool:
    wanted = wanted.lower().lstrip("#").rstrip("/")
    tag = tag.lower()
    return tag == wanted or tag.startswith(wanted + "/")


def has_all_tags(tags: list[str], wanted: list[str]) -> bool:
    return all(any(tag_matches(w, t) for t in tags) for w in wanted)


def compile_query(query: str, regex: bool = False, case_sensitive: bool = False) -> re.Pattern:
    if len(query) > MAX_PATTERN_LENGTH:
        raise SearchError(f"Consulta muito longa (máx. {MAX_PATTERN_LENGTH} caracteres)")

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        return re.compile(query if regex else re.escape(query), flags)
    except re.error as e:
        raise SearchError(f"Regex inválida: {e}") from e


def find_matches(content: str, pattern: re.Pattern, limit: int) -> tuple[list[dict], int]:
    matches = []
    total = 0

    for i, line in enumerate(content.splitlines()):
        match = pattern.search(line)
        if not match:
            continue
        total += 1
        if len(matches) < limit:
            matches.append({"line": i, "text": snippet(line, match.start(), match.end())})

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


def _normalize_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value).strip().lower()
