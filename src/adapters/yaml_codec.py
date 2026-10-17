import io
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError

from core.errors import FrontmatterError


class RuamelYamlCodec:
    def __init__(self):
        self._reader = YAML(typ="safe")
        self._editor = YAML()
        self._editor.preserve_quotes = True
        self._editor.width = 4096
        self._editor.indent(mapping=2, sequence=4, offset=2)

    def load(self, yaml_text: str) -> Any:
        try:
            return self._reader.load(yaml_text)
        except YAMLError as error:
            raise FrontmatterError(f"YAML inválido no frontmatter: {error}") from error

    def update(self, yaml_text: str, set_values: dict[str, Any], remove_keys: list[str]) -> str:
        metadata = self._load_editable(yaml_text)
        for key in remove_keys:
            metadata.pop(key, None)
        metadata.update(set_values)
        return self._dump(metadata) if metadata else ""

    def _load_editable(self, yaml_text: str) -> CommentedMap:
        try:
            metadata = self._editor.load(yaml_text) if yaml_text.strip() else None
        except YAMLError as error:
            raise FrontmatterError(f"YAML inválido no frontmatter: {error}") from error
        return metadata if metadata is not None else CommentedMap()

    def _dump(self, metadata: CommentedMap) -> str:
        buffer = io.StringIO()
        self._editor.dump(metadata, buffer)
        return buffer.getvalue()
