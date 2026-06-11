import os
import shutil
import httpx
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from agents.gemini_client import run_autonomous_agent_async, analyze_document_structured_async, query_agent_builder_async

app = FastAPI(
    title="GCP AI Agents Lab API",
    description="Повністю асинхронний мікросервіс для керування ШІ-агентами (Hardened Version)",
    version="1.3.0"
)

# Токен бота, який ми пропишемо в конфігурації Cloud Run
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ліміт на розмір завантажуваного файлу (наприклад, 10 МБ)
MAX_FILE_SIZE = 10 * 1024 * 1024 

class AgentInstructionRequest(BaseModel):
    instruction: str = Field(..., example="Збережи рахунок від Apple на 450 USD.")

class QueryRequest(BaseModel):
    query: str = Field(..., example="Які кроки для вирішення CrashLoopBackOff?")

class InvoiceItem(BaseModel):
    description: str
    price: float

class ExtractedInvoice(BaseModel):
    vendor_name: str
    total_amount: float
    currency: str
    items: List[InvoiceItem]

@app.get("/")
async def root():
    return {"status": "healthy", "workspace": "gcp-ai-agents-lab", "async_mode": True}

@app.post("/agent/run")
async def run_agent(payload: AgentInstructionRequest):
    if not payload.instruction.strip():
        raise HTTPException(status_code=400, detail="Інструкція порожня")
    try:
        response = await run_autonomous_agent_async(user_instruction=payload.instruction)
        return {"success": True, "agent_response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка сервера агента: {str(e)}")

@app.post("/query")
async def query_knowledge_base(payload: QueryRequest):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Запит порожній")
    
    # Викликаємо RAG-пошук через Agent Builder
    answer = await query_agent_builder_async(user_query=payload.query)
    return {"success": True, "response": answer}

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    Ендпоїнт для отримання вебхуків від Telegram.
    Мапує повідомлення користувача на нашого автономного ШІ-агента.
    """
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ [Telegram Webhook] Запит отримано, але TELEGRAM_BOT_TOKEN не задано в середовищі.")
        return {"status": "skipped", "reason": "no_token"}

    try:
        data = await request.json()
        
        # Перевіряємо наявність тексту у повідомленні
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"]["text"]
            
            print(f"📥 [Telegram] Отримано запит від Chat ID {chat_id}: '{user_text}'")
            
            # 🔥 Передаємо команду нашому асинхронному ШІ-агенту
            agent_response = await run_autonomous_agent_async(user_instruction=user_text)
            
            # Відправляємо відповідь назад користувачу в Telegram
            telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            async with httpx.AsyncClient() as client:
                await client.post(telegram_api_url, json={
                    "chat_id": chat_id,
                    "text": agent_response
                }, timeout=10.0)
                
            print(f"📤 [Telegram] Відповідь успішно відправлена в чат {chat_id}")
            
        return {"status": "ok"}
    except Exception as e:
        print(f"❌ [Telegram Webhook Error] {e}")
        # Завжди повертаємо 200 OK для Telegram, щоб він не спамив ретраями при багах у коді
        return {"status": "error", "details": str(e)}

@app.post("/analyst/invoice")
async def analyze_invoice(
    file: UploadFile = File(...), 
    prompt: str = Form("Витягни структуровані дані")
):
    # 📝 [ЗАХИСТ #1] Перевірка розміру файлу (Проблема #6)
    # Зчитуємо заголовок або перші байти для валідації розміру без повного завантаження в пам'ять
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0) # Повертаємо покажчик на початок
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Файл занадто великий. Максимум 10 МБ.")

    # 🔒 [ЗАХИСТ #2] Санітизація імені файлу від Path Traversal (Проблема #7)
    # Витягуємо тільки чисте ім'я файлу, відсікаючи шляхи типу ../../etc/passwd
    safe_filename = os.path.basename(file.filename)
    if not safe_filename:
         raise HTTPException(status_code=400, detail="Некоректне ім'я файлу")

    upload_dir = "tmp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        extracted_data = await analyze_document_structured_async(
            prompt=prompt,
            file_path=file_path,
            response_schema=ExtractedInvoice
        )
        return {"success": True, "data": extracted_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка обробки: {str(e)}")
    finally:
        # Безпечне видалення у будь-якому випадку
        if os.path.exists(file_path):
            os.remove(file_path)
