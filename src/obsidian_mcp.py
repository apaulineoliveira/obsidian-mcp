import os
from pathlib import Path

from dotenv import load_dotenv

from adapters.filesystem import FileSystemVault
from adapters.mcp_server import create_server
from adapters.yaml_codec import RuamelFrontmatterCodec
from application import build_services


def main() -> None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    vault = FileSystemVault(os.getenv("OBSIDIAN_VAULT_PATH", "~/Obsidian"))
    create_server(build_services(vault, RuamelFrontmatterCodec())).run()


if __name__ == "__main__":
    main()
