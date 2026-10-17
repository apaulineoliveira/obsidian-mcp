import datetime
from dataclasses import dataclass
from typing import Any, Optional

from .errors import FrontmatterError
from .ports import FrontmatterCodec


DELIMITER = "---"


@dataclass(frozen=True)
class ParsedNote:
    metadata: dict
    body: str
    line_offset: int


def split_frontmatter(content: str) -> tuple[Optional[str], str, int]:
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n").rstrip() != DELIMITER:
        return None, content, 0

    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n").rstrip() == DELIMITER:
            return "".join(lines[1:i]), "".join(lines[i + 1:]), i + 1

    return None, content, 0


def detect_newline(content: str) -> str:
    return "\r\n" if content.split("\n", 1)[0].endswith("\r") else "\n"


def assemble(yaml_text: str, body: str, newline: str) -> str:
    if not yaml_text.strip():
        return body
    if newline != "\n":
        yaml_text = yaml_text.replace("\r\n", "\n").replace("\n", newline)
    if not yaml_text.endswith(newline):
        yaml_text += newline
    return f"{DELIMITER}{newline}{yaml_text}{DELIMITER}{newline}{body}"


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


class FrontmatterParser:
    def __init__(self, codec: FrontmatterCodec):
        self.codec = codec

    def parse(self, content: str) -> ParsedNote:
        yaml_text, body, offset = split_frontmatter(content)
        if yaml_text is None:
            return ParsedNote({}, body, 0)

        data = self.codec.load(yaml_text)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise FrontmatterError("O frontmatter precisa ser um mapeamento chave: valor")

        return ParsedNote(data, body, offset)

    def parse_lenient(self, content: str) -> ParsedNote:
        try:
            return self.parse(content)
        except FrontmatterError:
            _, body, offset = split_frontmatter(content)
            return ParsedNote({}, body, offset)

    def update(
        self,
        content: str,
        set_values: Optional[dict[str, Any]] = None,
        remove_keys: Optional[list[str]] = None,
    ) -> str:
        self.parse(content)
        yaml_text, body, _ = split_frontmatter(content)
        new_yaml = self.codec.update(yaml_text or "", set_values or {}, remove_keys or [])
        return assemble(new_yaml, body, detect_newline(content))
