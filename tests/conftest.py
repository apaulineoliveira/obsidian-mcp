import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.filesystem import FileSystemVault
from adapters.mcp_server import VaultTools
from adapters.yaml_codec import RuamelFrontmatterCodec
from application import build_services


@pytest.fixture
def vault_dir(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    return root


@pytest.fixture
def write(vault_dir):
    def _write(relative: str, content: str, root: Path = vault_dir) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
    return _write


@pytest.fixture
def tools(vault_dir):
    return VaultTools(build_services(FileSystemVault(vault_dir), RuamelFrontmatterCodec()))
