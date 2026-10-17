import os
from pathlib import Path

import pytest

from adapters.filesystem import FileSystemVault
from core.errors import InvalidPathError, NoteNotFoundError, NoteReadError, VaultNotFoundError


def put(root: Path, relative: str, content: str = "") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def fs(vault_dir):
    return FileSystemVault(vault_dir)


def test_read_and_write_notes(fs, vault_dir):
    put(vault_dir, "a/n.md", "x")
    assert fs.read("a/../a/n.md") == "x"
    fs.write("a/n.md", "a\r\nb\r\n")
    assert (vault_dir / "a/n.md").read_bytes() == b"a\r\nb\r\n"
    assert [p.name for p in (vault_dir / "a").iterdir()] == ["n.md"]


@pytest.mark.parametrize("path", ["../secret.md", "/etc/passwd", ".obsidian/x.md"])
def test_rejects_unsafe_paths(fs, vault_dir, path):
    put(vault_dir.parent, "secret.md", "segredo")
    with pytest.raises(InvalidPathError):
        fs.read(path)
    with pytest.raises(InvalidPathError):
        fs.write(path, "x")
    assert (vault_dir.parent / "secret.md").read_text() == "segredo"


def test_rejects_symlinks_escaping_vault(fs, vault_dir, tmp_path):
    outside = put(tmp_path, "outside/secret.md", "segredo")
    os.symlink(outside, vault_dir / "link.md")
    os.symlink(outside.parent, vault_dir / "linkdir")
    os.symlink(vault_dir / ".obsidian", vault_dir / "cfg", target_is_directory=True)
    put(vault_dir, ".obsidian/c.md")

    for path in ("link.md", "linkdir/secret.md", "cfg/c.md"):
        with pytest.raises(InvalidPathError):
            fs.read(path)


def test_missing_note_and_vault(fs, vault_dir, tmp_path):
    put(vault_dir, "pasta.md/n.md")
    with pytest.raises(NoteNotFoundError):
        fs.read("nao_existe.md")
    with pytest.raises(NoteNotFoundError):
        fs.read("pasta.md")
    with pytest.raises(VaultNotFoundError, match="OBSIDIAN_VAULT_PATH"):
        FileSystemVault(tmp_path / "nope").list_notes()


def test_unreadable_note_raises_domain_error(fs, vault_dir):
    (vault_dir / "bin.md").write_bytes(b"\xff\xfe\x00")
    with pytest.raises(NoteReadError):
        fs.read("bin.md")


def test_list_notes_skips_ignored_and_escaping_files(fs, vault_dir, tmp_path):
    put(vault_dir, "a.md")
    put(vault_dir, "sub/b.md")
    put(vault_dir, ".obsidian/c.md")
    put(vault_dir, ".trash/d.md")
    put(vault_dir, "image.png")
    outside = put(tmp_path, "outside/e.md")
    os.symlink(outside, vault_dir / "e.md")
    os.symlink(outside.parent, vault_dir / "outside_dir")

    assert fs.list_notes() == ["a.md", "sub/b.md"]
    assert fs.list_notes("sub") == ["sub/b.md"]
    with pytest.raises(InvalidPathError):
        fs.list_notes("a.md")
    with pytest.raises(InvalidPathError):
        fs.list_notes("..")
