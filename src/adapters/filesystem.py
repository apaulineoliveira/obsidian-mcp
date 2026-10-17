import os
import tempfile
from pathlib import Path
from typing import Optional

from core.errors import (
    InvalidPathError,
    NoteNotFoundError,
    NoteReadError,
    VaultNotFoundError,
)
from core.paths import is_ignored, is_note_file, is_visible_dir, normalize_note_path, normalize_path


class FileSystemVault:
    def __init__(self, root: str | os.PathLike):
        self.root = Path(root).expanduser().resolve()

    def list_notes(self, folder: Optional[str] = None) -> list[str]:
        start = self._resolve(folder)
        if not start.is_dir():
            raise InvalidPathError(f"Não é uma pasta: {folder}")

        notes = []
        for dirpath, dirnames, filenames in os.walk(start, followlinks=False):
            dirnames[:] = sorted(d for d in dirnames if is_visible_dir(d))
            for name in sorted(filenames):
                path = Path(dirpath) / name
                if is_note_file(name) and self._is_inside(path.resolve()) and path.is_file():
                    notes.append(path.relative_to(self.root).as_posix())
        return notes

    def read(self, note_path: str) -> str:
        path = self._resolve_note(note_path)
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                return f.read()
        except (OSError, UnicodeDecodeError) as e:
            raise NoteReadError(f"Não foi possível ler a nota {note_path}: {e}") from e

    def write(self, note_path: str, content: str) -> None:
        path = self._resolve_note(note_path)

        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            os.chmod(tmp, path.stat().st_mode & 0o777)
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def _resolve(self, relative: Optional[str], must_exist: bool = True) -> Path:
        if not self.root.is_dir():
            raise VaultNotFoundError(
                f"Vault não encontrado: {self.root}. Verifique OBSIDIAN_VAULT_PATH."
            )

        candidate = (self.root / normalize_path(relative)).resolve()
        if not self._is_inside(candidate):
            raise InvalidPathError(f"Caminho fora do vault: {relative}")
        if must_exist and not candidate.exists():
            raise InvalidPathError(f"Caminho não encontrado: {relative}")
        return candidate

    def _resolve_note(self, note_path: str) -> Path:
        normalize_note_path(note_path)
        path = self._resolve(note_path, must_exist=False)
        if not path.is_file():
            raise NoteNotFoundError(f"Nota não encontrada: {note_path}")
        return path

    def _is_inside(self, path: Path) -> bool:
        return path.is_relative_to(self.root) and not is_ignored(path.relative_to(self.root).parts)
