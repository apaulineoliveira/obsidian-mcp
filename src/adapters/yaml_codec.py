import io
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError

from core.errors import FrontmatterError


class RuamelFrontmatterCodec:
    def __init__(self):
        self._safe = YAML(typ="safe")
        self._round_trip = YAML()
        self._round_trip.preserve_quotes = True
        self._round_trip.width = 4096
        self._round_trip.indent(mapping=2, sequence=4, offset=2)

    def load(self, yaml_text: str) -> Any:
        try:
            return self._safe.load(yaml_text)
        except YAMLError as e:
            raise FrontmatterError(f"YAML inválido no frontmatter: {e}") from e

    def update(self, yaml_text: str, set_values: dict[str, Any], remove_keys: list[str]) -> str:
        try:
            data = self._round_trip.load(yaml_text) if yaml_text.strip() else None
        except YAMLError as e:
            raise FrontmatterError(f"YAML inválido no frontmatter: {e}") from e

        if data is None:
            data = CommentedMap()
        if not isinstance(data, dict):
            raise FrontmatterError("O frontmatter precisa ser um mapeamento chave: valor")

        for key in remove_keys:
            data.pop(key, None)
        for key, value in set_values.items():
            data[key] = value

        if not data:
            return ""

        buffer = io.StringIO()
        self._round_trip.dump(data, buffer)
        return buffer.getvalue()
