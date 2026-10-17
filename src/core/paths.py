from pathlib import PurePosixPath, PureWindowsPath
from typing import Iterable, Optional

from .errors import InvalidPathError


INTERNAL_FOLDERS = frozenset({".obsidian", ".trash", ".git"})

NOTE_EXTENSION = ".md"


def safe_relative_path(raw_path: Optional[str]) -> PurePosixPath:
    if _points_to_vault_root(raw_path):
        return PurePosixPath()

    _reject_unsafe_characters(raw_path)
    _reject_absolute_path(raw_path)
    parts = _resolve_dot_segments(raw_path)

    if is_inside_internal_folder(parts):
        raise InvalidPathError(f"Acesso negado a pasta interna: {raw_path}")

    return PurePosixPath(*parts)


def safe_note_path(raw_path: Optional[str]) -> PurePosixPath:
    if not raw_path or not raw_path.strip():
        raise InvalidPathError("Informe o caminho da nota")

    path = safe_relative_path(raw_path)
    if path.suffix.lower() != NOTE_EXTENSION:
        raise InvalidPathError(f"Apenas notas {NOTE_EXTENSION} são permitidas: {raw_path}")
    return path


def is_inside_internal_folder(parts: Iterable[str]) -> bool:
    return any(part in INTERNAL_FOLDERS for part in parts)


def should_scan_folder(folder_name: str) -> bool:
    return not folder_name.startswith(".")


def is_note_filename(filename: str) -> bool:
    return filename.lower().endswith(NOTE_EXTENSION)


def _points_to_vault_root(raw_path: Optional[str]) -> bool:
    return raw_path is None or raw_path.strip() in ("", ".")


def _reject_unsafe_characters(raw_path: str) -> None:
    if "\x00" in raw_path:
        raise InvalidPathError("Caminho contém caractere inválido")


def _reject_absolute_path(raw_path: str) -> None:
    if PurePosixPath(raw_path).anchor or PureWindowsPath(raw_path).anchor:
        raise InvalidPathError(f"Use um caminho relativo ao vault, não absoluto: {raw_path}")


def _resolve_dot_segments(raw_path: str) -> list[str]:
    parts: list[str] = []
    for segment in raw_path.replace("\\", "/").split("/"):
        if segment in ("", "."):
            continue
        if segment != "..":
            parts.append(segment)
        elif parts:
            parts.pop()
        else:
            raise InvalidPathError(f"Caminho fora do vault: {raw_path}")
    return parts
