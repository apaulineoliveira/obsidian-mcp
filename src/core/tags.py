import re
from typing import Any, Iterable, Iterator


INLINE_TAG_PATTERN = re.compile(r"(?<![\w#/&])#([\w/-]+)")
INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")
CODE_FENCE_PATTERN = re.compile(r"^\s*(```|~~~)")


def inline_tags(text: str) -> list[str]:
    tags = []
    for line in _lines_outside_code_blocks(text):
        line_without_code = INLINE_CODE_PATTERN.sub("", line)
        for raw_tag in INLINE_TAG_PATTERN.findall(line_without_code):
            tag = raw_tag.strip("/")
            if _is_valid_tag(tag):
                tags.append(tag)
    return tags


def remove_inline_tags(text: str) -> str:
    return INLINE_TAG_PATTERN.sub("", text)


def parse_tag_field(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        candidates = re.split(r"[,\s]+", value)
    elif isinstance(value, (list, tuple, set)):
        candidates = [str(item) for item in value if item is not None]
    else:
        candidates = [str(value)]

    tags = (candidate.strip().lstrip("#") for candidate in candidates)
    return [tag for tag in tags if tag]


def frontmatter_tags(metadata: dict) -> list[str]:
    return parse_tag_field(metadata.get("tags")) + parse_tag_field(metadata.get("tag"))


def note_tags(metadata: dict, body: str) -> list[str]:
    return unique_lowercase(frontmatter_tags(metadata) + inline_tags(body))


def unique_lowercase(tags: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(tag.lower() for tag in tags))


def tag_matches(tag: str, wanted: str) -> bool:
    tag = tag.lower()
    wanted = wanted.lower().lstrip("#").rstrip("/")
    return tag == wanted or tag.startswith(wanted + "/")


def has_all_tags(tags: list[str], wanted_tags: list[str]) -> bool:
    return all(any(tag_matches(tag, wanted) for tag in tags) for wanted in wanted_tags)


def count_notes_per_tag(tags_per_note: Iterable[list[str]]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for tags in tags_per_note:
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def _lines_outside_code_blocks(text: str) -> Iterator[str]:
    inside_code_block = False
    for line in text.splitlines():
        if CODE_FENCE_PATTERN.match(line):
            inside_code_block = not inside_code_block
        elif not inside_code_block:
            yield line


def _is_valid_tag(tag: str) -> bool:
    return bool(tag) and not tag.replace("/", "").isdigit()
