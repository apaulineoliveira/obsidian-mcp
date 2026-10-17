from core.priorities import LANGUAGE_NAMES, supported_languages


def supported_language_names() -> dict[str, str]:
    return {code: LANGUAGE_NAMES.get(code, code) for code in supported_languages()}
