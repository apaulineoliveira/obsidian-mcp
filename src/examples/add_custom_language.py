import sys

from src.core.priorities import (
    PRIORITY_BY_EMOJI,
    PRIORITY_KEYWORDS,
    add_priority_keywords,
    normalize_priority,
)


EXTRA_LANGUAGES = {
    "ja": {
        "high": ["高", "高優先度", "緊急", "重大"],
        "medium": ["中", "中優先度", "通常", "中程度"],
        "low": ["低", "低優先度", "次要", "小"],
        "blocked": ["ブロック済み", "保留中", "ブロック", "停止"],
    },
    "zh": {
        "high": ["高", "高优先级", "紧急", "严重", "危急"],
        "medium": ["中", "中优先级", "正常", "中等"],
        "low": ["低", "低优先级", "次要", "轻微"],
        "blocked": ["阻止", "被阻止", "待定", "暂停"],
    },
    "ru": {
        "high": ["высокий", "высокий приоритет", "срочно", "критический"],
        "medium": ["средний", "средний приоритет", "обычный", "нормально"],
        "low": ["низкий", "низкий приоритет", "вторичный", "малый"],
        "blocked": ["заблокирован", "блокировка", "отложено", "ожидание"],
    },
    "el": {
        "high": ["υψηλή", "υψηλή προτεραιότητα", "επείγον", "κρίσιμο"],
        "medium": ["μεσαία", "μεσαία προτεραιότητα", "κανονικό", "μέσο"],
        "low": ["χαμηλή", "χαμηλή προτεραιότητα", "δευτερεύον", "μικρό"],
        "blocked": ["μπλοκαρισμένο", "φραγμένο", "σε αναμονή", "σταματημένο"],
    },
    "ko": {
        "high": ["높음", "높은 우선순위", "긴급", "중요"],
        "medium": ["중간", "중간 우선순위", "일반", "보통"],
        "low": ["낮음", "낮은 우선순위", "부차적", "작은"],
        "blocked": ["차단됨", "막힘", "대기 중", "정지"],
    },
}

SAMPLE_KEYWORDS = [
    ("高", "ja", "high"),
    ("中", "ja", "medium"),
    ("紧急", "zh", "high"),
    ("срочно", "ru", "high"),
    ("низкий", "ru", "low"),
    ("κανονικό", "el", "medium"),
    ("긴급", "ko", "high"),
]

USAGE = """
Uso: python -m src.examples.add_custom_language <comando>

  --add <código>   Registra um idioma de exemplo (ja, zh, ru, el, ko) e confere as palavras
  --add-all        Registra todos os idiomas de exemplo
  --list           Mostra as palavras de prioridade conhecidas

Este script só demonstra o mecanismo: o registro vale para este processo.
Para o servidor MCP reconhecer um idioma novo, adicione as palavras em
PRIORITY_KEYWORDS, no arquivo src/core/priorities.py.
"""


def register_language(code: str) -> None:
    for priority, keywords in EXTRA_LANGUAGES[code].items():
        add_priority_keywords(priority, code, keywords)


def check_sample_keywords(codes: list[str]) -> bool:
    all_correct = True
    for keyword, code, expected in SAMPLE_KEYWORDS:
        if code not in codes:
            continue
        result = normalize_priority(keyword, language=code)
        status = "✅" if result == expected else "❌"
        all_correct = all_correct and result == expected
        print(f"{status} {code}: '{keyword}' → {result} (esperado: {expected})")
    return all_correct


def print_known_keywords() -> None:
    for priority, keywords_by_language in PRIORITY_KEYWORDS.items():
        print(f"\n{priority.upper()}")
        for code, keywords in sorted(keywords_by_language.items()):
            print(f"  {code:3} → {', '.join(keywords)}")

    print("\nEMOJI")
    for emoji, priority in PRIORITY_BY_EMOJI.items():
        print(f"  {emoji} → {priority}")


def main(arguments: list[str]) -> int:
    if not arguments:
        print(USAGE)
        return 0

    command = arguments[0]
    if command == "--list":
        print_known_keywords()
        return 0

    if command == "--add-all":
        codes = list(EXTRA_LANGUAGES)
    elif command == "--add" and len(arguments) > 1 and arguments[1] in EXTRA_LANGUAGES:
        codes = [arguments[1]]
    else:
        print(USAGE)
        return 1

    for code in codes:
        register_language(code)
    return 0 if check_sample_keywords(codes) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
