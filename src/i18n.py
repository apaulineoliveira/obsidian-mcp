from typing import Optional


LANGUAGES = {
    'priority': {
        'high': {
            'pt': ['alta', 'urgente', 'alto', 'crítico'],
            'en': ['high', 'urgent'],
            'es': ['alta', 'urgente', 'alto', 'crítico'],
            'fr': ['haut', 'urgent', 'élevé', 'critique'],
            'de': ['hoch', 'dringend', 'kritisch'],
            'it': ['alto', 'urgente', 'critico'],
        },
        'medium': {
            'pt': ['média', 'normal', 'médio', 'moderada'],
            'en': ['medium', 'normal'],
            'es': ['media', 'normal', 'medio', 'moderada'],
            'fr': ['moyen', 'normal', 'modéré'],
            'de': ['mittel', 'normal', 'moderat'],
            'it': ['medio', 'normale', 'moderato'],
        },
        'low': {
            'pt': ['baixa', 'baixo', 'mínima'],
            'en': ['low', 'minor'],
            'es': ['baja', 'bajo', 'mínima'],
            'fr': ['bas', 'faible', 'mineur'],
            'de': ['niedrig', 'gering', 'klein'],
            'it': ['basso', 'minore', 'piccolo'],
        },
        'blocked': {
            'pt': ['bloqueado', 'bloqueada', 'impedido'],
            'en': ['blocked', 'blocked', 'pending'],
            'es': ['bloqueado', 'bloqueada', 'impedido'],
            'fr': ['bloqué', 'bloquée', 'en attente'],
            'de': ['blockiert', 'gehemmt', 'ausstehend'],
            'it': ['bloccato', 'bloccata', 'in sospeso'],
        }
    }
}


EMOJI_PRIORITY = {
    '🔴': 'high',
    '🟡': 'medium',
    '🟢': 'low',
    '⚫': 'blocked'
}


def extract_priority_emoji(text: str) -> Optional[str]:
    for emoji, priority in EMOJI_PRIORITY.items():
        if emoji in text:
            return priority
    return None


def get_supported_languages() -> list[str]:
    if not LANGUAGES['priority']:
        return []
    return list(LANGUAGES['priority']['high'].keys())


def normalize_priority(
    priority_str: Optional[str],
    language: str = 'en'
) -> Optional[str]:
    if not priority_str:
        return None

    priority_str = priority_str.lower().strip()

    if priority_str in EMOJI_PRIORITY:
        return EMOJI_PRIORITY[priority_str]

    for priority_level, translations in LANGUAGES['priority'].items():
        if language in translations:
            if priority_str in translations[language]:
                return priority_level

        if 'en' in translations and priority_str in translations['en']:
            return priority_level

    return priority_str


def add_language(
    priority_level: str,
    language_code: str,
    keywords: list[str]
) -> bool:
    if priority_level not in LANGUAGES['priority']:
        raise ValueError(
            f"❌ Invalid priority level '{priority_level}'. "
            f"Must be one of: {list(LANGUAGES['priority'].keys())}"
        )

    LANGUAGES['priority'][priority_level][language_code] = [kw.lower() for kw in keywords]
    print(f"✅ Added language '{language_code}' for priority '{priority_level}'")
    return True


def get_priority_translations(priority_level: str) -> dict[str, list[str]]:
    if priority_level not in LANGUAGES['priority']:
        raise ValueError(
            f"Invalid priority level '{priority_level}'. "
            f"Must be one of: {list(LANGUAGES['priority'].keys())}"
        )

    return LANGUAGES['priority'][priority_level]


def print_supported_keywords():
    print("\n" + "="*60)
    print("📚 SUPPORTED KEYWORDS BY LANGUAGE AND PRIORITY")
    print("="*60 + "\n")

    for priority_level, translations in LANGUAGES['priority'].items():
        print(f"🎯 {priority_level.upper()}")
        print("-" * 40)
        for language, keywords in sorted(translations.items()):
            langs_map = {
                'pt': '🇧🇷',
                'en': '🇺🇸',
                'es': '🇪🇸',
                'fr': '🇫🇷',
                'de': '🇩🇪',
                'it': '🇮🇹',
            }
            emoji = langs_map.get(language, '🌐')
            print(f"   {emoji} {language.upper():5} → {', '.join(keywords)}")
        print()

    print("🎨 EMOJI MAPPING")
    print("-" * 40)
    for emoji, priority in sorted(EMOJI_PRIORITY.items()):
        print(f"   {emoji} → {priority}")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print_supported_keywords()

    print("🧪 TEST EXAMPLES\n")

    test_cases = [
        ('alta', 'pt', 'high'),
        ('haut', 'fr', 'high'),
        ('medio', 'es', 'medium'),
        ('🔴', 'en', 'high'),
        ('bloqueado', 'pt', 'blocked'),
        ('low', 'en', 'low'),
    ]

    for input_str, lang, expected in test_cases:
        result = normalize_priority(input_str, language=lang)
        status = "✅" if result == expected else "❌"
        print(f"{status} normalize_priority('{input_str}', '{lang}') → '{result}' (expected: '{expected}')")
