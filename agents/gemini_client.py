import os
from typing import Type
from pydantic import BaseModel
from google import genai
from google.genai import types

def get_genai_client() -> genai.Client:
    """
    Ініціалізує клієнта Google GenAI за допомогою ADC.
    """
    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "n8n-automations-497913")
        return genai.Client(vertexai=True, project=project_id, location="us-central1")
    except Exception as e:
        print(f"[Помилка] Не вдалося ініціалізувати GenAI Client: {e}")
        raise

def generate_response(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Базовий текстовий запит.
    """
    client = get_genai_client()
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"[Помилка] Помилка генерації у {model_name}: {e}")
        raise

def analyze_document_structured(
    prompt: str, 
    file_path: str, 
    response_schema: Type[BaseModel],
    model_name: str = "gemini-2.5-flash"
) -> BaseModel:
    """
    Приймає шлях до файлу (зображення/документ), аналізує його згідно з промптом
    і повертає валідований об'єкт Pydantic (Structured JSON).
    """
    client = get_genai_client()
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не знайдено за шляхом: {file_path}")
        
    try:
        # Читаємо файл у бінарному режимі
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            
        # Визначаємо базовий mime_type за розширенням
        ext = os.path.splitext(file_path)[1].lower()
        mime_mapping = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".txt": "text/plain"
        }
        mime_type = mime_mapping.get(ext, "application/octet-stream")

        # Формуємо контент для нового SDK (текст + медіа-парт)
        contents = [
            types.Part.from_bytes(
                data=file_bytes,
                mime_type=mime_type,
            ),
            prompt
        ]

        # Запит із вимогою структурованого виведення
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1, # Низька температура для точнішого парсингу фактів
            ),
        )
        
        # Новий SDK вміє автоматично повертати розпарсений pydantic-об'єкт через .parsed
        return response.parsed
        
    except Exception as e:
        print(f"[Помилка] Не вдалося проаналізувати документ: {e}")
        raise

from agents.tools import save_invoice_to_db, send_slack_notification

def run_autonomous_agent(user_instruction: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Запускає агента, який має доступ до інструментів (Function Calling).
    Він може самостійно вирішувати, які функції викликати для виконання інструкції.
    """
    client = get_genai_client()
    
    # Реєструємо список доступних функцій для моделі
    available_tools = [save_invoice_to_db, send_slack_notification]
    
    try:
        # Для автоматичного виконання функцій на боці SDK використовується client.chats
        # або конфіг enable_automatic_function_calling
        config = types.GenerateContentConfig(
            tools=available_tools,
            temperature=0.2,
            system_instruction=(
                "Ти автономний ШІ-агент лабораторії GCP. Твоя мета — допомагати користувачу "
                "автоматизувати рутину за допомогою доступних інструментів. "
                "Якщо користувач просить зберегти дані або надіслати звіт — використовуй відповідні функції."
            )
        )
        
        # Запускаємо сесію чату з підтримкою автоматичного виклику інструментів
        chat = client.chats.create(model=model_name, config=config)
        response = chat.send_message(user_instruction)
        
        return response.text
    except Exception as e:
        print(f"[Помилка агента] Не вдалося виконати сценарій: {e}")
        raise
