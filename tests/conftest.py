import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import obsidian_mcp  # noqa: E402
from vault import Vault  # noqa: E402


@pytest.fixture
def vault_dir(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    return root


@pytest.fixture
def server(vault_dir, monkeypatch):
    """Módulo do servidor apontando para um vault temporário"""
    monkeypatch.setattr(obsidian_mcp, "vault", Vault(vault_dir))
    return obsidian_mcp


def write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
