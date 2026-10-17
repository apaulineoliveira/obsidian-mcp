import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import obsidian_mcp
from vault import Vault


@pytest.fixture
def vault_dir(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    return root


@pytest.fixture
def server(vault_dir, monkeypatch):
    monkeypatch.setattr(obsidian_mcp, "vault", Vault(vault_dir))
    return obsidian_mcp


def write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
