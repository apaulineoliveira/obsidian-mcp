import json
import os

import pytest

from conftest import write
from vault import Vault, VaultPathError


@pytest.fixture
def vault(vault_dir):
    return Vault(vault_dir)


@pytest.mark.parametrize("path", [
    "../secret.md",
    "notes/../../secret.md",
    "/etc/passwd",
    "notes/\x00.md",
    ".obsidian/workspace.json",
    "notes/.git/config",
])
def test_resolve_rejects_unsafe_paths(vault, vault_dir, path):
    write(vault_dir.parent, "secret.md", "segredo")
    with pytest.raises(VaultPathError):
        vault.resolve(path, must_exist=False)


def test_resolve_allows_dotdot_that_stays_inside(vault, vault_dir):
    write(vault_dir, "a/note.md", "x")
    assert vault.resolve("a/../a/note.md") == vault_dir.resolve() / "a" / "note.md"


def test_resolve_rejects_symlink_escaping_vault(vault, vault_dir, tmp_path):
    outside = write(tmp_path, "outside/secret.md", "segredo")
    os.symlink(outside, vault_dir / "link.md")
    os.symlink(outside.parent, vault_dir / "linkdir")

    with pytest.raises(VaultPathError):
        vault.resolve_note("link.md")
    with pytest.raises(VaultPathError):
        vault.resolve_note("linkdir/secret.md")


def test_resolve_note_requires_markdown(vault, vault_dir):
    write(vault_dir, "data.json", "{}")
    with pytest.raises(VaultPathError):
        vault.resolve_note("data.json")


def test_missing_vault_is_reported(tmp_path):
    with pytest.raises(VaultPathError, match="OBSIDIAN_VAULT_PATH"):
        Vault(tmp_path / "nope").resolve()


def test_iter_notes_skips_ignored_and_escaping_files(vault, vault_dir, tmp_path):
    write(vault_dir, "a.md", "")
    write(vault_dir, "sub/b.md", "")
    write(vault_dir, ".obsidian/c.md", "")
    write(vault_dir, ".trash/d.md", "")
    write(vault_dir, "image.png", "")
    outside = write(tmp_path, "outside/e.md", "")
    os.symlink(outside, vault_dir / "e.md")
    os.symlink(outside.parent, vault_dir / "outside_dir")

    found = [vault.relative(p) for p in vault.iter_notes()]
    assert found == ["a.md", "sub/b.md"]


def test_write_text_is_atomic_and_preserves_crlf(vault, vault_dir):
    path = write(vault_dir, "n.md", "")
    vault.write_text(path, "a\r\nb\r\n")
    assert path.read_bytes() == b"a\r\nb\r\n"
    assert [p.name for p in vault_dir.iterdir()] == ["n.md"]


def test_tools_reject_traversal(server, vault_dir):
    write(vault_dir.parent, "secret.md", "- [ ] segredo")

    for result in (
        server.get_note_content("../secret.md"),
        server.update_todo("../secret.md", 0, True),
        server.get_todos(folder=".."),
    ):
        assert "error" in json.loads(result)

    assert (vault_dir.parent / "secret.md").read_text() == "- [ ] segredo"


def test_update_todo_only_touches_checkbox_lines(server, vault_dir):
    path = write(vault_dir, "n.md", "Texto com [ ] solto\n  * [ ] tarefa [ ] fim\n")

    assert "error" in json.loads(server.update_todo("n.md", 0, True))
    assert json.loads(server.update_todo("n.md", 1, True))["success"]
    assert path.read_text() == "Texto com [ ] solto\n  * [x] tarefa [ ] fim\n"
