import os
import tempfile
from pathlib import Path
from typing import Iterator, Optional

from core.errors import InvalidPathError, NoteNotFoundError, NoteReadError, VaultNotFoundError
from core.paths import (
    is_inside_internal_folder,
    is_note_filename,
    safe_note_path,
    safe_relative_path,
    should_scan_folder,
)


class FileSystemVault:
    def __init__(self, root: str | os.PathLike):
        self.root = Path(root).expanduser().resolve()

    def list_notes(self, folder: Optional[str] = None) -> list[str]:
        folder_path = self._existing_folder(folder)
        return [self._relative(path) for path in self._walk_notes(folder_path)]

    def read(self, note_path: str) -> str:
        path = self._existing_note(note_path)
        try:
            with open(path, "r", encoding="utf-8", newline="") as file:
                return file.read()
        except (OSError, UnicodeDecodeError) as error:
            raise NoteReadError(f"Não foi possível ler a nota {note_path}: {error}") from error

    def write(self, note_path: str, content: str) -> None:
        write_atomically(self._existing_note(note_path), content)

    def _existing_folder(self, folder: Optional[str]) -> Path:
        path = self._absolute_path(folder)
        if not path.is_dir():
            raise InvalidPathError(f"Pasta não encontrada: {folder}")
        return path

    def _existing_note(self, note_path: str) -> Path:
        safe_note_path(note_path)
        path = self._absolute_path(note_path)
        if not path.is_file():
            raise NoteNotFoundError(f"Nota não encontrada: {note_path}")
        return path

    def _absolute_path(self, relative_path: Optional[str]) -> Path:
        self._ensure_vault_exists()
        path = (self.root / safe_relative_path(relative_path)).resolve()
        if not self._is_safe(path):
            raise InvalidPathError(f"Caminho fora do vault: {relative_path}")
        return path

    def _walk_notes(self, folder_path: Path) -> Iterator[Path]:
        for current_folder, subfolders, filenames in os.walk(folder_path):
            subfolders[:] = sorted(name for name in subfolders if should_scan_folder(name))
            for filename in sorted(filenames):
                path = Path(current_folder) / filename
                if is_note_filename(filename) and self._is_safe(path.resolve()) and path.is_file():
                    yield path

    def _ensure_vault_exists(self) -> None:
        if not self.root.is_dir():
            raise VaultNotFoundError(f"Vault não encontrado: {self.root}. Verifique OBSIDIAN_VAULT_PATH.")

    def _is_safe(self, resolved_path: Path) -> bool:
        if not resolved_path.is_relative_to(self.root):
            return False
        return not is_inside_internal_folder(resolved_path.relative_to(self.root).parts)

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()


def write_atomically(path: Path, content: str) -> None:
    file_descriptor, temp_path = tempfile.mkstemp(dir=path.parent, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as file:
            file.write(content)
        os.chmod(temp_path, path.stat().st_mode & 0o777)
        os.replace(temp_path, path)
    except BaseException:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
