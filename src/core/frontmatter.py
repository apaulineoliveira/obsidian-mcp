from dataclasses import dataclass
from typing import Any, Optional

from .errors import FrontmatterError
from .ports import FrontmatterCodec


DELIMITER = "---"


@dataclass(frozen=True)
class SplitNote:
    yaml_text: Optional[str]
    body: str
    body_start_line: int


@dataclass(frozen=True)
class ParsedNote:
    metadata: dict
    body: str
    body_start_line: int


def split_frontmatter(content: str) -> SplitNote:
    lines = content.splitlines(keepends=True)
    if not lines or not _is_delimiter(lines[0]):
        return SplitNote(None, content, 0)

    for index in range(1, len(lines)):
        if _is_delimiter(lines[index]):
            yaml_text = "".join(lines[1:index])
            body = "".join(lines[index + 1:])
            return SplitNote(yaml_text, body, index + 1)

    return SplitNote(None, content, 0)


def join_frontmatter(yaml_text: str, body: str, newline: str) -> str:
    if not yaml_text.strip():
        return body

    yaml_text = _use_newline(yaml_text, newline)
    if not yaml_text.endswith(newline):
        yaml_text += newline
    return f"{DELIMITER}{newline}{yaml_text}{DELIMITER}{newline}{body}"


def newline_style(content: str) -> str:
    first_line = content.split("\n", 1)[0]
    return "\r\n" if first_line.endswith("\r") else "\n"


class Frontmatter:
    def __init__(self, codec: FrontmatterCodec):
        self.codec = codec

    def parse(self, content: str) -> ParsedNote:
        split = split_frontmatter(content)
        metadata = self._load_metadata(split.yaml_text)
        return ParsedNote(metadata, split.body, split.body_start_line)

    def parse_ignoring_invalid_yaml(self, content: str) -> ParsedNote:
        try:
            return self.parse(content)
        except FrontmatterError:
            split = split_frontmatter(content)
            return ParsedNote({}, split.body, split.body_start_line)

    def update(
        self,
        content: str,
        set_values: Optional[dict[str, Any]] = None,
        remove_keys: Optional[list[str]] = None,
    ) -> str:
        split = split_frontmatter(content)
        self._load_metadata(split.yaml_text)
        new_yaml = self.codec.update(split.yaml_text or "", set_values or {}, remove_keys or [])
        return join_frontmatter(new_yaml, split.body, newline_style(content))

    def _load_metadata(self, yaml_text: Optional[str]) -> dict:
        if yaml_text is None:
            return {}

        metadata = self.codec.load(yaml_text)
        if metadata is None:
            return {}
        if not isinstance(metadata, dict):
            raise FrontmatterError("O frontmatter precisa ser um mapeamento chave: valor")
        return metadata


def _is_delimiter(line: str) -> bool:
    return line.rstrip() == DELIMITER


def _use_newline(text: str, newline: str) -> str:
    return text.replace("\r\n", "\n").replace("\n", newline)
