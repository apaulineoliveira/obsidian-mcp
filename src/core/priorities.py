from typing import Optional


DEFAULT_LANGUAGE = "en"

PRIORITY_KEYWORDS = {
    "high": {
        "pt": ["alta", "urgente", "alto", "crítico"],
        "en": ["high", "urgent"],
        "es": ["alta", "urgente", "alto", "crítico"],
        "fr": ["haut", "urgent", "élevé", "critique"],
        "de": ["hoch", "dringend", "kritisch"],
        "it": ["alto", "urgente", "critico"],
    },
    "medium": {
        "pt": ["média", "normal", "médio", "moderada"],
        "en": ["medium", "normal"],
        "es": ["media", "normal", "medio", "moderada"],
        "fr": ["moyen", "normal", "modéré"],
        "de": ["mittel", "normal", "moderat"],
        "it": ["medio", "normale", "moderato"],
    },
    "low": {
        "pt": ["baixa", "baixo", "mínima"],
        "en": ["low", "minor"],
        "es": ["baja", "bajo", "mínima"],
        "fr": ["bas", "faible", "mineur"],
        "de": ["niedrig", "gering", "klein"],
        "it": ["basso", "minore", "piccolo"],
    },
    "blocked": {
        "pt": ["bloqueado", "bloqueada", "impedido"],
        "en": ["blocked", "pending"],
        "es": ["bloqueado", "bloqueada", "impedido"],
        "fr": ["bloqué", "bloquée", "en attente"],
        "de": ["blockiert", "gehemmt", "ausstehend"],
        "it": ["bloccato", "bloccata", "in sospeso"],
    },
}

PRIORITY_BY_EMOJI = {
    "🔴": "high",
    "🟡": "medium",
    "🟢": "low",
    "⚫": "blocked",
}

LANGUAGE_NAMES = {
    "pt": "Português (Portuguese)",
    "en": "English (English)",
    "es": "Español (Spanish)",
    "fr": "Français (French)",
    "de": "Deutsch (German)",
    "it": "Italiano (Italian)",
}


def supported_languages() -> list[str]:
    languages = []
    for keywords_by_language in PRIORITY_KEYWORDS.values():
        languages.extend(lang for lang in keywords_by_language if lang not in languages)
    return languages


def priority_from_emoji(text: str) -> Optional[str]:
    for emoji, priority in PRIORITY_BY_EMOJI.items():
        if emoji in text:
            return priority
    return None


def normalize_priority(value: Optional[str], language: str = DEFAULT_LANGUAGE) -> Optional[str]:
    if not value:
        return None

    keyword = value.strip().lower()
    if keyword in PRIORITY_BY_EMOJI:
        return PRIORITY_BY_EMOJI[keyword]

    for priority, keywords_by_language in PRIORITY_KEYWORDS.items():
        accepted = keywords_by_language.get(language, []) + keywords_by_language.get(DEFAULT_LANGUAGE, [])
        if keyword in accepted:
            return priority

    return keyword


def add_priority_keywords(priority: str, language: str, keywords: list[str]) -> None:
    if priority not in PRIORITY_KEYWORDS:
        raise ValueError(f"Prioridade inválida '{priority}'. Use uma de: {list(PRIORITY_KEYWORDS)}")
    PRIORITY_KEYWORDS[priority][language] = [keyword.lower() for keyword in keywords]
