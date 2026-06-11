import sys
import os
import asyncio
from agents.gemini_client import run_autonomous_agent_async

async def main():
    print("🤖 Запуск автономного ШІ-Агента (CLI Mode)...")
    
    instruction = (
        "Я щойно отримав рахунок від компанії 'Google Cloud Ukraine' на суму 15000 UAH. "
        "Будь ласка, збережи цей рахунок в базу даних, а потім надішли сповіщення в канал 'finance' "
        "про те, що новий інвойс успішно зафіксовано."
    )
    
    print("\n📝 Інструкція для агента:")
    print(f"\"{instruction}\"\n")
    
    print("📡 Передача управління асинхронному агенту...")
    try:
        agent_response = await run_autonomous_agent_async(user_instruction=instruction)
        
        print("\n== Фінальна відповідь агента ==")
        print(agent_response)
        print("===============================\n")
        
        if os.path.exists("mock_database.json"):
            print("📦 Перевірка mock_database.json: Файл успішно оновлено.")
        else:
            print("❌ Помилка: Інструмент запису в БД не був викликаний.")
            
    except Exception as e:
        print(f"❌ Критична помилка під час роботи агента: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Запускаємо асинхронний контекст для CLI
    asyncio.run(main())
