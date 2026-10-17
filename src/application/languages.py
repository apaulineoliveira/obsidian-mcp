from core.i18n import LANGUAGE_NAMES, get_supported_languages


def supported_languages() -> dict[str, str]:
    return {code: LANGUAGE_NAMES.get(code, code) for code in get_supported_languages()}
