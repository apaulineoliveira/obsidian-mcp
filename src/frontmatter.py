import datetime
import io
from typing import Any, Optional

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError


DELIMITER = "---"

_safe_yaml = YAML(typ="safe")

_rt_yaml = YAML()
_rt_yaml.preserve_quotes = True
_rt_yaml.width = 4096
_rt_yaml.indent(mapping=2, sequence=4, offset=2)


class FrontmatterError(ValueError):
    pass


def split_frontmatter(content: str) -> tuple[Optional[str], str, int]:
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n").rstrip() != DELIMITER:
        return None, content, 0

    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n").rstrip() == DELIMITER:
            return "".join(lines[1:i]), "".join(lines[i + 1:]), i + 1

    return None, content, 0


def parse_frontmatter(content: str) -> tuple[dict, str, int]:
    yaml_text, body, offset = split_frontmatter(content)
    if yaml_text is None:
        return {}, body, 0

    try:
        data = _safe_yaml.load(yaml_text)
    except YAMLError as e:
        raise FrontmatterError(f"YAML inválido no frontmatter: {e}") from e

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise FrontmatterError("O frontmatter precisa ser um mapeamento chave: valor")

    return data, body, offset


def extract_frontmatter(content: str) -> tuple[dict, str, int]:
    try:
        return parse_frontmatter(content)
    except FrontmatterError:
        _, body, offset = split_frontmatter(content)
        return {}, body, offset


def update_frontmatter(
    content: str,
    set_values: Optional[dict[str, Any]] = None,
    remove_keys: Optional[list[str]] = None,
) -> str:
    yaml_text, body, _ = split_frontmatter(content)
    newline = "\r\n" if content.split("\n", 1)[0].endswith("\r") else "\n"

    if yaml_text is None:
        data = CommentedMap()
    else:
        try:
            data = _rt_yaml.load(yaml_text)
        except YAMLError as e:
            raise FrontmatterError(f"YAML inválido no frontmatter: {e}") from e
        if data is None:
            data = CommentedMap()
        if not isinstance(data, dict):
            raise FrontmatterError("O frontmatter precisa ser um mapeamento chave: valor")

    for key in remove_keys or []:
        data.pop(key, None)
    for key, value in (set_values or {}).items():
        data[key] = value

    if not data:
        return body

    buffer = io.StringIO()
    _rt_yaml.dump(data, buffer)
    dumped = buffer.getvalue()
    if newline != "\n":
        dumped = dumped.replace("\r\n", "\n").replace("\n", newline)

    return f"{DELIMITER}{newline}{dumped}{DELIMITER}{newline}{body}"


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value
