import os
from pathlib import Path

from dotenv import load_dotenv

from adapters.filesystem import FileSystemVault
from adapters.mcp_server import create_server
from adapters.yaml_codec import RuamelYamlCodec
from application import build_services


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
DEFAULT_VAULT_PATH = "~/Obsidian"


def main() -> None:
    load_dotenv(ENV_FILE)
    vault = FileSystemVault(os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH))
    services = build_services(vault, RuamelYamlCodec())
    create_server(services).run()


if __name__ == "__main__":
    main()
