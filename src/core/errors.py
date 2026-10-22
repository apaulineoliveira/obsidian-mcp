class DomainError(ValueError):
    pass


class VaultNotFoundError(DomainError):
    pass


class InvalidPathError(DomainError):
    pass


class NoteNotFoundError(DomainError):
    pass


class NoteAlreadyExistsError(DomainError):
    pass


class NoteReadError(DomainError):
    pass


class NoteWriteError(DomainError):
    pass


class FrontmatterError(DomainError):
    pass


class SearchError(DomainError):
    pass


class TodoError(DomainError):
    pass
