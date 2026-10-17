import re
from typing import Any, Iterable


INLINE_TAG_RE = re.compile(r"(?<![\w#/&])#([\w/-]+)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


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


def strip_inline_tags(text: str) -> str:
    return INLINE_TAG_RE.sub("", text)


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


def frontmatter_tags(metadata: dict) -> list[str]:
    return normalize_tags(metadata.get("tags")) + normalize_tags(metadata.get("tag"))


def note_tags(metadata: dict, body: str) -> list[str]:
    return unique_tags(frontmatter_tags(metadata) + extract_inline_tags(body))


def tag_matches(wanted: str, tag: str) -> bool:
    wanted = wanted.lower().lstrip("#").rstrip("/")
    tag = tag.lower()
    return tag == wanted or tag.startswith(wanted + "/")


def has_all_tags(tags: list[str], wanted: list[str]) -> bool:
    return all(any(tag_matches(w, t) for t in tags) for w in wanted)


def count_tags(tag_lists: Iterable[list[str]]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for tags in tag_lists:
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))
