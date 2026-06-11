import os
from typing import Type
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.cloud import discoveryengine_v1 as discoveryengine
from agents.tools import save_invoice_to_db, send_slack_notification

# Залізобетонний системний промпт з політиками поведінки агента
SYSTEM_INSTRUCTION = (
    "Ти — провідний DevOps-інженер та SRE-асистент платформи gcp-ai-agents-lab.\n"
    "Твоє завдання — допомагати команді автоматизувати рутину (збереження рахунків через інструменти) "
    "та діагностувати проблеми інфраструктури кластерів.\n\n"
    
    "⚠️ СУВОРІ ПРАВИЛА ПОВЕДІНКИ:\n"
    "1. ФОКУС НА КОНТЕКСТІ: Ти маєш право відповідати ТІЛЬКИ на запитання, пов'язані з DevOps, SRE, "
    "Kubernetes, Google Cloud Platform (GCP), системним адмініструванням або обробкою інфраструктурних рахунків/інвойсів.\n"
    "2. ПОЛІТИКА ВІДМОВИ: Якщо користувач запитує тебе про речі, які не стосуються твоєї ролі "
    "(наприклад: рецепти, погода, побутові поради, філософія, розваги), ти повинен ВІДМОВИТИ у відповіді. "
    "Скажи ввічливо, але чітко: 'Як DevOps/SRE асистент, я обмежений лише технічними питаннями інфраструктури та рахунків, тому не можу допомогти з цим запитом.'\n"
    "3. ПРАВИЛА ЦИТУВАННЯ: При вирішенні проблем з Kubernetes завжди спирайся на офіційні діагностичні команди (kubectl) та алгоритми з доступних баз знань. Завжди рекомендуй перевірку логів (`--previous`) та лімітів пам'яті.\n"
    "4. ДЕТЕРМІНІЗМ: Будь точним у цифрах, назвах вендорів та валютах. Нічого не вигадуй від себе."
)

def get_genai_client() -> genai.Client:
    """Ініціалізує уніфікований клієнт Google GenAI."""
    try:
        return genai.Client()
    except Exception as e:
        print(f"[Помилка] Не вдалося ініціалізувати GenAI Client: {e}")
        raise

async def run_autonomous_agent_async(user_instruction: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Асинхронно запускає автономного агента з підтримкою автоматичного виклику інструментів.
    Використовує асинхронний SDK підсервіс client.aio.
    """
    client = get_genai_client()
    available_tools = [save_invoice_to_db, send_slack_notification]
    
    config = types.GenerateContentConfig(
        tools=available_tools,
        temperature=0.1,
        system_instruction=SYSTEM_INSTRUCTION
    )
    
    try:
        # Створюємо асинхронну сесію чату для виконання multi-step функцій
        chat = client.aio.chats.create(model=model_name, config=config)
        response = await chat.send_message(user_instruction)
        return response.text
    except Exception as e:
        print(f"[Помилка асинхронного агента] {e}")
        raise

async def analyze_document_structured_async(
    prompt: str, 
    file_path: str, 
    response_schema: Type[BaseModel],
    model_name: str = "gemini-2.5-flash"
) -> BaseModel:
    """
    Асинхронно аналізує документ/медіа-файл та повертає валідовану схему Pydantic.
    """
    client = get_genai_client()
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не знайдено: {file_path}")
        
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            
        ext = os.path.splitext(file_path)[1].lower()
        mime_mapping = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".txt": "text/plain"
        }
        mime_type = mime_mapping.get(ext, "application/octet-stream")

        contents = [
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            prompt
        ]

        # Асинхронний виклику генератора контенту
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1,
            ),
        )
        return response.parsed
        
    except Exception as e:
        print(f"[Помилка асинхронного аналізу] {e}")
        raise

async def query_agent_builder_async(
    user_query: str,
    project_id: str = "n8n-automations-497913",
    data_store_id: str = "k8s-runbook-store",
    location: str = "global"
) -> str:
    """
    Асинхронно звертається до Vertex AI Agent Builder Data Store для отримання RAG-відповіді.
    """
    try:
        client = discoveryengine.SearchServiceAsyncClient()
        serving_config = (
            f"projects/{project_id}/locations/{location}"
            f"/dataStores/{data_store_id}/servingConfigs/default_serving_config"
        )

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=user_query,
            page_size=1
        )
        
        response = await client.search(request)
        
        if response.summary and response.summary.summary_text:
            return response.summary.summary_text
        elif response.results:
            # Фолбек, якщо LLM summary ще генерується, повертаємо найкращий сніпет
            doc_data = response.results[0].document.derived_struct_data
            if "snippets" in doc_data and doc_data["snippets"]:
                return doc_data["snippets"][0].get(
                    "snippet",
                    "Знайдено релевантний збіг, але опис порожній."
                )
        
        return "На жаль, у моїй базі знань немає інформації з цього приводу."
    except Exception as e:
        print(f"❌ [Agent Builder Error] {e}")
        return f"Помилка пошуку в базі знань: {str(e)}"

