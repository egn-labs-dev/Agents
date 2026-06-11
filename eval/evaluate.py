import os
import json
import csv
import time
import asyncio
import httpx

API_URL = "https://fastapi-agent-1053060999264.europe-west3.run.app/agent/run"
RESULTS_FILE = "eval/results.csv"

async def run_evaluation():
    print("🔬 Запуск системи оцінки якості ШІ-Агента (Human-in-the-loop)...")
    
    if not os.path.exists("eval/queries.json"):
        print("❌ Файл eval/queries.json не знайдено.")
        return

    with open("eval/queries.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    # Ініціалізуємо CSV файл, якщо його не існує
    file_exists = os.path.exists(RESULTS_FILE)
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Timestamp", "ID", "Category", "Query", "Agent_Response", "Latency_Sec", "Score"])

    async with httpx.AsyncClient() as client:
        for case in test_cases:
            print(f"\n[Тест {case['id']}] Категорія: {case['category']}")
            print(f"📥 Запит: {case['query']}")
            
            start_time = time.time()
            try:
                # Запит до нашого хмарного Cloud Run мікросервісу
                response = await client.post(API_URL, json={"instruction": case["query"]}, timeout=15.0)
                latency = round(time.time() - start_time, 2)
                
                if response.status_code == 200:
                    agent_reply = response.json().get("agent_response", "")
                else:
                    agent_reply = f"Помилка API: {response.status_code} - {response.text}"
            except Exception as e:
                latency = round(time.time() - start_time, 2)
                agent_reply = f"Помилка з'єднання: {str(e)}"

            print(f"🤖 Відповідь Агента:\n{agent_reply}")
            print(f"⏱️ Latency: {latency} сек")

            # Інтерактивна оцінка
            while True:
                score_input = input("⭐ Поставте оцінку якості (1-5) або 's' для пропуску: ").strip()
                if score_input.lower() == 's':
                    score = "Skipped"
                    break
                try:
                    score = int(score_input)
                    if 1 <= score <= 5:
                        break
                    print("❌ Оцінка має бути від 1 до 5.")
                except ValueError:
                    print("❌ Введіть число або 's'.")

            # Записуємо результат в CSV
            with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    case["id"],
                    case["category"],
                    case["query"],
                    agent_reply.replace("\n", " "),
                    latency,
                    score
                ])
            print(f"✅ Результат зафіксовано в {RESULTS_FILE}")

    print("\n🏁 Оцінювання завершено!")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
