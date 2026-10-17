from pathlib import PurePosixPath, PureWindowsPath
from typing import Iterable, Optional

from .errors import InvalidPathError


IGNORED_DIRS = frozenset({".obsidian", ".trash", ".git"})

NOTE_SUFFIX = ".md"


def normalize_path(relative: Optional[str]) -> PurePosixPath:
    if relative is None or relative.strip() in ("", "."):
        return PurePosixPath()

    if "\x00" in relative:
        raise InvalidPathError("Caminho contém caractere inválido")

    if PurePosixPath(relative).anchor or PureWindowsPath(relative).anchor:
        raise InvalidPathError(f"Use um caminho relativo ao vault, não absoluto: {relative}")

    parts: list[str] = []
    for part in relative.replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise InvalidPathError(f"Caminho fora do vault: {relative}")
            parts.pop()
        else:
            parts.append(part)

    if is_ignored(parts):
        raise InvalidPathError(f"Acesso negado a pasta interna: {relative}")

    return PurePosixPath(*parts)


def normalize_note_path(relative: Optional[str]) -> PurePosixPath:
    if not relative or not relative.strip():
        raise InvalidPathError("Informe o caminho da nota")

    path = normalize_path(relative)
    if path.suffix.lower() != NOTE_SUFFIX:
        raise InvalidPathError(f"Apenas notas {NOTE_SUFFIX} são permitidas: {relative}")
    return path


def is_ignored(parts: Iterable[str]) -> bool:
    return any(part in IGNORED_DIRS for part in parts)


def is_visible_dir(name: str) -> bool:
    return name not in IGNORED_DIRS and not name.startswith(".")


def is_note_file(name: str) -> bool:
    return name.lower().endswith(NOTE_SUFFIX)
