
"""
Example: How to Add Custom Languages to Obsidian MCP Server

This script shows how to extend the multilingual support
without modifying the core code.

You can:
1. Add entirely new languages (Japanese, Chinese, Russian, etc)
2. Extend existing languages with more keywords
3. Test your custom language additions

Run this before starting the MCP server to load your custom languages!
"""

from src.i18n import add_language, normalize_priority, print_supported_keywords



def add_japanese():
    """Adiciona suporte para Japonês"""
    print("\n🇯🇵 Adding Japanese (日本語)...\n")
    
    try:
        add_language('high', 'ja', ['高', '高優先度', '緊急', '重大', 'こうゆうせんど'])
        add_language('medium', 'ja', ['中', '中優先度', '通常', '中程度'])
        add_language('low', 'ja', ['低', '低優先度', '次要', '小'])
        add_language('blocked', 'ja', ['ブロック済み', '保留中', 'ブロック', '停止'])
        print("✅ Japanese added successfully!\n")
    except Exception as e:
        print(f"❌ Error adding Japanese: {e}\n")



def add_chinese_simplified():
    """Adiciona suporte para Chinês Simplificado"""
    print("\n🇨🇳 Adding Chinese Simplified (简体中文)...\n")
    
    try:
        add_language('high', 'zh', ['高', '高优先级', '紧急', '严重', '危急'])
        add_language('medium', 'zh', ['中', '中优先级', '正常', '中等'])
        add_language('low', 'zh', ['低', '低优先级', '次要', '轻微'])
        add_language('blocked', 'zh', ['阻止', '被阻止', '待定', '暂停'])
        print("✅ Chinese (Simplified) added successfully!\n")
    except Exception as e:
        print(f"❌ Error adding Chinese: {e}\n")



def add_russian():
    """Adiciona suporte para Russo"""
    print("\n🇷🇺 Adding Russian (Русский)...\n")
    
    try:
        add_language('high', 'ru', ['высокий', 'высокий приоритет', 'срочно', 'критический'])
        add_language('medium', 'ru', ['средний', 'средний приоритет', 'обычный', 'нормально'])
        add_language('low', 'ru', ['низкий', 'низкий приоритет', 'вторичный', 'малый'])
        add_language('blocked', 'ru', ['заблокирован', 'блокировка', 'отложено', 'ожидание'])
        print("✅ Russian added successfully!\n")
    except Exception as e:
        print(f"❌ Error adding Russian: {e}\n")



def add_greek():
    """Adiciona suporte para Grego"""
    print("\n🇬🇷 Adding Greek (Ελληνικά)...\n")
    
    try:
        add_language('high', 'el', ['υψηλή', 'υψηλή προτεραιότητα', 'επείγον', 'κρίσιμο'])
        add_language('medium', 'el', ['μεσαία', 'μεσαία προτεραιότητα', 'κανονικό', 'μέσο'])
        add_language('low', 'el', ['χαμηλή', 'χαμηλή προτεραιότητα', 'δευτερεύον', 'μικρό'])
        add_language('blocked', 'el', ['μπλοκαρισμένο', 'φραγμένο', 'σε αναμονή', 'σταματημένο'])
        print("✅ Greek added successfully!\n")
    except Exception as e:
        print(f"❌ Error adding Greek: {e}\n")



def add_korean():
    """Adiciona suporte para Coreano"""
    print("\n🇰🇷 Adding Korean (한국어)...\n")
    
    try:
        add_language('high', 'ko', ['높음', '높은 우선순위', '긴급', '중요'])
        add_language('medium', 'ko', ['중간', '중간 우선순위', '일반', '보통'])
        add_language('low', 'ko', ['낮음', '낮은 우선순위', '부차적', '작은'])
        add_language('blocked', 'ko', ['차단됨', '막힘', '대기 중', '정지'])
        print("✅ Korean added successfully!\n")
    except Exception as e:
        print(f"❌ Error adding Korean: {e}\n")


def test_custom_languages():
    """Test all custom languages with examples"""
    
    print("\n" + "="*60)
    print("🧪 TESTING CUSTOM LANGUAGES")
    print("="*60 + "\n")
    
  
    test_cases = [
        ("高", "ja", "high"),
        ("中", "ja", "medium"),
        ("低", "ja", "low"),
        
        
        ("高", "zh", "high"),
        ("中", "zh", "medium"),
        ("紧急", "zh", "high"),
        
        
        ("срочно", "ru", "high"),
        ("обычный", "ru", "medium"),
        ("низкий", "ru", "low"),
        
        
        ("επείγον", "el", "high"),
        ("κανονικό", "el", "medium"),
        
        
        ("긴급", "ko", "high"),
        ("중간", "ko", "medium"),
    ]
    
    passed = 0
    failed = 0
    
    for input_str, lang, expected in test_cases:
        result = normalize_priority(input_str, language=lang)
        is_correct = result == expected
        
        if is_correct:
            status = "✅"
            passed += 1
        else:
            status = "❌"
            failed += 1
        
        lang_emoji = "🇯🇵" if lang == "ja" else \
                    "🇨🇳" if lang == "zh" else \
                    "🇷🇺" if lang == "ru" else \
                    "🇬🇷" if lang == "el" else \
                    "🇰🇷" if lang == "ko" else "🌐"
        
        print(
            f"{status} {lang_emoji} {lang.upper():3} | "
            f"normalize_priority('{input_str}', '{lang}') "
            f"→ '{result}' (expected: '{expected}')"
        )
    
    print(f"\n📊 Results: {passed} passed, {failed} failed\n")


def show_usage():
    """Show usage instructions"""
    
    print("\n" + "="*60)
    print("📖 HOW TO ADD YOUR OWN LANGUAGES")
    print("="*60 + "\n")
    
    print("""
1. OPTION A: Run this file to add pre-defined languages:
   
   python3 add_custom_language.py --add-all
   
   or individually:
   
   python3 add_custom_language.py --add-japanese
   python3 add_custom_language.py --add-chinese
   python3 add_custom_language.py --add-russian

2. OPTION B: Import in your own script:
   
   from add_custom_language import add_japanese
   add_japanese()
   
3. OPTION C: Manually add your own language:
   
   from src.i18n import add_language
   
   add_language('high', 'your-lang-code', ['keyword1', 'keyword2', ...])
   add_language('medium', 'your-lang-code', ['...'])
   add_language('low', 'your-lang-code', ['...'])
   add_language('blocked', 'your-lang-code', ['...'])

4. Test your language:
   
   from src.i18n import normalize_priority
   
   result = normalize_priority('your-keyword', language='your-lang-code')
   print(result)  # Should print 'high', 'medium', 'low', or 'blocked'

5. Use in Obsidian:
   
   ---
   prioridade: your-keyword
   ---
   
   - [ ] 🔴 Your task

6. Call from Claude:
   
   "Show me high priority tasks in Spanish"
   → get_todos(priority='high', language='es')
    """)


if __name__ == "__main__":
    import sys
    
   
    if len(sys.argv) == 1:
        show_usage()
    
  
    args = sys.argv[1:]
    
    if '--add-all' in args:
        add_japanese()
        add_chinese_simplified()
        add_russian()
        add_greek()
        add_korean()
        test_custom_languages()
        print_supported_keywords()
    
    elif '--add-japanese' in args or '--add-ja' in args:
        add_japanese()
        test_custom_languages()
    
    elif '--add-chinese' in args or '--add-zh' in args:
        add_chinese_simplified()
        test_custom_languages()
    
    elif '--add-russian' in args or '--add-ru' in args:
        add_russian()
        test_custom_languages()
    
    elif '--add-greek' in args or '--add-el' in args:
        add_greek()
        test_custom_languages()
    
    elif '--add-korean' in args or '--add-ko' in args:
        add_korean()
        test_custom_languages()
    
    elif '--test' in args:
        test_custom_languages()
    
    elif '--list' in args or '--show' in args:
        print_supported_keywords()
    
    else:
        print(f"❌ Unknown argument: {args[0]}")
        show_usage()
