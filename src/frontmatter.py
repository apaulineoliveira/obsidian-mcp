"""
Leitura e escrita de YAML frontmatter em notas Markdown.

A escrita usa o modo round-trip do ruamel.yaml: comentários, ordem das
chaves e estilo de listas existentes são mantidos, e o corpo da nota é
preservado byte a byte.
"""

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
    """Raised when the frontmatter exists but is not a valid YAML mapping"""


def split_frontmatter(content: str) -> tuple[Optional[str], str, int]:
    """
    Separa o bloco de frontmatter do corpo da nota.

    Retorna (yaml_text ou None, corpo, linhas_ocupadas_pelo_bloco).
    O bloco só é reconhecido se a primeira linha for exatamente '---'.
    """
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n").rstrip() != DELIMITER:
        return None, content, 0

    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n").rstrip() == DELIMITER:
            return "".join(lines[1:i]), "".join(lines[i + 1:]), i + 1

    return None, content, 0


def parse_frontmatter(content: str) -> tuple[dict, str, int]:
    """
    Retorna (metadata, corpo, linhas_ocupadas_pelo_bloco).

    Lança FrontmatterError se o YAML for inválido ou não for um mapeamento.
    """
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
    """Versão tolerante de parse_frontmatter: YAML inválido vira {}"""
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
    """
    Aplica alterações ao frontmatter e devolve o novo conteúdo da nota.

    - set_values: chaves a criar ou sobrescrever (chaves novas vão para o fim)
    - remove_keys: chaves a remover (ausentes são ignoradas)

    Se o frontmatter ficar vazio, o bloco é removido.
    """
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
    """Converte valores do YAML (datas, mapas ordenados) em tipos JSON"""
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value
