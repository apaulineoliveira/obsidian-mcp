"""
Safe access to the Obsidian vault.

Every path received from a client goes through Vault.resolve(), which
guarantees the final (symlink-resolved) path stays inside the vault root.
This blocks path traversal (`../../etc/passwd`), absolute paths and
symlinks that point outside the vault.
"""

import os
import tempfile
from pathlib import Path, PurePath
from typing import Iterator, Optional


# Folders never read or written: Obsidian config, trash and VCS metadata
IGNORED_DIRS = {".obsidian", ".trash", ".git"}

NOTE_SUFFIX = ".md"


class VaultPathError(ValueError):
    """Raised when a path is invalid or escapes the vault"""


class Vault:
    def __init__(self, root: str | os.PathLike):
        self.root = Path(root).expanduser().resolve()

    def ensure_exists(self) -> None:
        if not self.root.is_dir():
            raise VaultPathError(
                f"Vault não encontrado: {self.root}. Verifique OBSIDIAN_VAULT_PATH."
            )

    def resolve(self, relative: Optional[str] = None, must_exist: bool = True) -> Path:
        """
        Converte um caminho relativo ao vault em um caminho absoluto seguro.

        Rejeita caminhos absolutos, caracteres nulos, pastas ignoradas e
        qualquer caminho que, após resolver '..' e symlinks, saia do vault.
        """
        self.ensure_exists()

        if relative is None or relative.strip() in ("", "."):
            return self.root

        if "\x00" in relative:
            raise VaultPathError("Caminho contém caractere inválido")

        pure = PurePath(relative)
        if pure.anchor:
            raise VaultPathError(
                f"Use um caminho relativo ao vault, não absoluto: {relative}"
            )

        candidate = (self.root / pure).resolve()
        if not candidate.is_relative_to(self.root):
            raise VaultPathError(f"Caminho fora do vault: {relative}")

        if self._is_ignored(candidate):
            raise VaultPathError(f"Acesso negado a pasta interna: {relative}")

        if must_exist and not candidate.exists():
            raise VaultPathError(f"Caminho não encontrado: {relative}")

        return candidate

    def resolve_note(self, relative: str, must_exist: bool = True) -> Path:
        """Como resolve(), mas exige um arquivo Markdown (.md)"""
        if not relative or not relative.strip():
            raise VaultPathError("Informe o caminho da nota")

        path = self.resolve(relative, must_exist=must_exist)
        if path.suffix.lower() != NOTE_SUFFIX:
            raise VaultPathError(f"Apenas notas {NOTE_SUFFIX} são permitidas: {relative}")
        if must_exist and not path.is_file():
            raise VaultPathError(f"Nota não encontrada: {relative}")
        return path

    def resolve_folder(self, relative: Optional[str]) -> Path:
        path = self.resolve(relative)
        if not path.is_dir():
            raise VaultPathError(f"Não é uma pasta: {relative}")
        return path

    def relative(self, path: Path) -> str:
        """Caminho relativo ao vault, sempre com '/' (estável entre SOs)"""
        return path.relative_to(self.root).as_posix()

    def iter_notes(self, folder: Optional[str] = None) -> Iterator[Path]:
        """
        Percorre as notas .md de uma pasta do vault, em ordem estável.

        Não segue symlinks de pastas e ignora arquivos cujo destino real
        esteja fora do vault.
        """
        start = self.resolve_folder(folder)

        for dirpath, dirnames, filenames in os.walk(start, followlinks=False):
            dirnames[:] = sorted(
                d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")
            )
            for name in sorted(filenames):
                if not name.lower().endswith(NOTE_SUFFIX):
                    continue
                real = (Path(dirpath) / name).resolve()
                if real.is_relative_to(self.root) and real.is_file():
                    yield Path(dirpath) / name

    @staticmethod
    def read_text(path: Path) -> str:
        # newline="" preserva \r\n, para que reescritas não alterem o arquivo
        with open(path, "r", encoding="utf-8", newline="") as f:
            return f.read()

    def write_text(self, path: Path, content: str) -> None:
        """
        Escrita atômica: grava em arquivo temporário na mesma pasta e troca
        com os.replace, evitando notas corrompidas pela metade.
        """
        real = path.resolve()
        if not real.is_relative_to(self.root) or self._is_ignored(real):
            raise VaultPathError(f"Escrita fora do vault bloqueada: {path}")

        fd, tmp = tempfile.mkstemp(dir=real.parent, prefix=".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            if real.exists():
                os.chmod(tmp, real.stat().st_mode & 0o777)
            os.replace(tmp, real)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def _is_ignored(self, path: Path) -> bool:
        parts = path.relative_to(self.root).parts
        return any(part in IGNORED_DIRS for part in parts)
