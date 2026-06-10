import sys
from agents.gemini_client import generate_response

def main():
    print("🤖 Запуск GCP AI Agents Lab...")
    
    # Тестовий промпт для перевірки зв'язку з Vertex AI
    test_prompt = (
        "Привіт! Ти працюєш у складі локальної лабораторії ШІ-агентів на базі GCP. "
        "Дай коротку відповідь з трьох слів, що підтверджує твою готовність до автоматизації."
    )
    
    print(f"📡 Надсилання тестового запиту до Gemini...")
    try:
        # Використовуємо швидку та ефективну модель за замовчуванням
        result = generate_response(prompt=test_prompt, model_name="gemini-2.5-flash")
        print("\n== Відповідь моделі ==")
        print(result)
        print("======================\n")
        print("✅ Тест успішний! Зв'язок з Vertex AI встановлено.")
    except Exception:
        print("❌ Тест провалено. Перевірте логи помилок вище.")
        sys.exit(1)

if __name__ == "__main__":
    main()
