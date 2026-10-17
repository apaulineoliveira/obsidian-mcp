from pathlib import PurePosixPath

import pytest

from core.errors import InvalidPathError
from core.paths import is_note_filename, safe_note_path, safe_relative_path, should_scan_folder


@pytest.mark.parametrize("raw_path", [
    "../secret.md",
    "notes/../../secret.md",
    "/etc/passwd",
    "C:\\Windows\\win.ini",
    "..\\secret.md",
    "notes/\x00.md",
    ".obsidian/workspace.json",
    "notes/.git/config",
])
def test_rejects_unsafe_paths(raw_path):
    with pytest.raises(InvalidPathError):
        safe_relative_path(raw_path)


@pytest.mark.parametrize("raw_path, expected", [
    (None, PurePosixPath()),
    ("", PurePosixPath()),
    (".", PurePosixPath()),
    ("a/../a/note.md", PurePosixPath("a/note.md")),
    ("./a//b\\c.md", PurePosixPath("a/b/c.md")),
])
def test_resolves_paths_that_stay_inside_the_vault(raw_path, expected):
    assert safe_relative_path(raw_path) == expected


@pytest.mark.parametrize("raw_path", ["", "  ", "data.json", "pasta"])
def test_note_path_must_be_markdown(raw_path):
    with pytest.raises(InvalidPathError):
        safe_note_path(raw_path)


def test_folder_and_file_rules():
    assert should_scan_folder("Projects")
    assert not should_scan_folder(".obsidian")
    assert not should_scan_folder(".hidden")
    assert is_note_filename("Nota.MD")
    assert not is_note_filename("image.png")
