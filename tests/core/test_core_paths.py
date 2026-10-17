from pathlib import PurePosixPath

import pytest

from core.errors import InvalidPathError
from core.paths import is_note_file, is_visible_dir, normalize_note_path, normalize_path


@pytest.mark.parametrize("path", [
    "../secret.md",
    "notes/../../secret.md",
    "/etc/passwd",
    "C:\\Windows\\win.ini",
    "..\\secret.md",
    "notes/\x00.md",
    ".obsidian/workspace.json",
    "notes/.git/config",
])
def test_normalize_rejects_unsafe_paths(path):
    with pytest.raises(InvalidPathError):
        normalize_path(path)


@pytest.mark.parametrize("path, expected", [
    (None, PurePosixPath()),
    ("", PurePosixPath()),
    (".", PurePosixPath()),
    ("a/../a/note.md", PurePosixPath("a/note.md")),
    ("./a//b\\c.md", PurePosixPath("a/b/c.md")),
])
def test_normalize_resolves_inside_vault(path, expected):
    assert normalize_path(path) == expected


@pytest.mark.parametrize("path", ["", "  ", "data.json", "pasta"])
def test_normalize_note_path_requires_markdown(path):
    with pytest.raises(InvalidPathError):
        normalize_note_path(path)


def test_visibility_rules():
    assert is_visible_dir("Projects")
    assert not is_visible_dir(".obsidian")
    assert not is_visible_dir(".hidden")
    assert is_note_file("Nota.MD")
    assert not is_note_file("image.png")
