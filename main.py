import sys
import os
from agents.gemini_client import run_autonomous_agent

def main():
    print("🤖 Запуск автономного ШІ-Агента (Function Calling)...")
    
    # Сценарій: Користувач дає комплексну інструкцію людською мовою
    instruction = (
        "Я щойно отримав рахунок від компанії 'Google Cloud Ukraine' на суму 15000 UAH. "
        "Будь ласка, збережи цей рахунок в базу даних, а потім надішли сповіщення в канал 'finance' "
        "про те, що новий інвойс успішно зафіксовано."
    )
    
    print("\n📝 Інструкція для агента:")
    print(f"\"{instruction}\"\n")
    
    print("📡 Передача управління агенту...")
    try:
        agent_response = run_autonomous_agent(user_instruction=instruction)
        
        print("== Фінальна відповідь агента ==")
        print(agent_response)
        print("===============================\n")
        
        # Перевіримо, чи дійсно створився файл бази даних в результаті роботи моделі
        if os.path.exists("mock_database.json"):
            print("📦 Перевірка mock_database.json: Файл існує! Модель успішно виконала функцію.")
            with open("mock_database.json", "r", encoding="utf-8") as f:
                print(f"Зміст БД:\n{f.read()}")
        else:
            print("❌ Помилка: Інструмент запису в БД не був викликаний.")
            
    except Exception as e:
        print(f"❌ Критична помилка під час роботи агента: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
