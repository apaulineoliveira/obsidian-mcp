from typing import Any, Optional, Protocol


class NoteRepository(Protocol):
    def list_notes(self, folder: Optional[str] = None) -> list[str]: ...

    def read(self, note_path: str) -> str: ...

    def write(self, note_path: str, content: str) -> None: ...


class FrontmatterCodec(Protocol):
    def load(self, yaml_text: str) -> Any: ...

    def update(
        self,
        yaml_text: str,
        set_values: dict[str, Any],
        remove_keys: list[str],
    ) -> str: ...
