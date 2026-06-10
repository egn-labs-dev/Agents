import os
from typing import Type
from pydantic import BaseModel
from google import genai
from google.genai import types
from agents.tools import save_invoice_to_db, send_slack_notification

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
        temperature=0.2,
        system_instruction=(
            "Ти автономний ШІ-агент лабораторії GCP. Твоя мета — допомагати користувачу "
            "автоматизувати рутину за допомогою доступних інструментів. "
            "Якщо користувач просить зберегти дані або надіслати звіт — використовуй відповідні функції."
        )
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
