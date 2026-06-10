import os
from google import genai
from google.genai import types

def get_genai_client() -> genai.Client:
    """
    Ініціалізує клієнта Google GenAI.
    Автоматично використовує Application Default Credentials (ADC),
    налаштовані через gcloud CLI.
    """
    try:
        # Новий уніфікований клієнт для Gemini (2026) з підтримкою Vertex AI
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "n8n-automations-497913")
        client = genai.Client(vertexai=True, project=project_id, location="us-central1")
        return client
    except Exception as e:
        print(f"[Помилка] Не вдалося ініціалізувати GenAI Client. Перевірте ADC: {e}")
        raise

def generate_response(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Відправляє базовий запит до моделі Gemini.
    """
    client = get_genai_client()
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"[Помилка] Помилка під час генерації вмісту через {model_name}: {e}")
        raise
