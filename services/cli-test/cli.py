import os
import sys
import argparse
import asyncio
from google.cloud import discoveryengine_v1 as discoveryengine

async def query_agent_async(project_id: str, location: str, data_store_id: str, user_query: str):
    """
    Надсилає пошуковий/діалоговий запит до Vertex AI Agent Builder (Data Store / Search API).
    Використовує Application Default Credentials (ADC).
    """
    # Ініціалізуємо асинхронного клієнта
    client = discoveryengine.SearchServiceAsyncClient()

    # Формуємо повне ім'я сервісного сервісу (Serving Config)
    # За замовчуванням для пошуку використовується 'default_serving_config'
    serving_config = f"projects/{project_id}/locations/{location}/dataStores/{data_store_id}/servingConfigs/default_serving_config"

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=user_query,
        page_size=3 # Отримуємо топ-3 релевантних відповіді
    )

    try:
        print(f"📡 Надсилання запиту до хмарного Агента...")
        response = await client.search(request)
        
        print("\n== 🤖 Відповідь Хмарного Агента ==")
        
        # Перевіряємо, чи є згенерована саммарі-відповідь (LLM summary)
        if response.summary and response.summary.summary_text:
            print(response.summary.summary_text)
        else:
            # Якщо увімкнено суто пошуковий режим — виводимо знайдені фрагменти
            print("Саммарі не згенеровано. Знайдені релевантні фрагменти з Runbook:")
            for result in response.results:
                document_data = result.document.derived_struct_data
                if "snippets" in document_data:
                    for snippet in document_data["snippets"]:
                        print(f"- {snippet.get('snippet')}")
        print("==================================\n")

    except Exception as e:
        print(f"❌ Помилка під час звернення до Agent Builder API: {e}")
        print("Перевірте, чи правильно вказано Data Store ID та чи пройдено 'gcloud auth application-default login'")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="GCP AI Agent Lab CLI Test Tool")
    parser.add_argument("--query", type=str, required=True, help="Запитання для ШІ-агента")
    
    # Автоматично підтягуємо ID проєкту з gcloud, якщо він не переданий
    default_project = os.getenv("GCP_PROJECT_ID", "n8n-automations-497913")
    parser.add_argument("--project", type=str, default=default_project, help="GCP Project ID")
    parser.add_argument("--location", type=str, default="global", help="GCP Location (global / europe-west3)")
    
    # Цей ID ти отримаєш після створення Data Store в консолі
    parser.add_argument("--datastore", type=str, required=True, help="ID вашого Data Store в Agent Builder")

    args = parser.parse_args()

    # Запускаємо асинхронний цикл
    asyncio.run(query_agent_async(
        project_id=args.project,
        location=args.location,
        data_store_id=args.datastore,
        user_query=args.query
    ))

if __name__ == "__main__":
    main()
