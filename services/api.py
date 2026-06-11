import os
import time
import re
import httpx
import shutil
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, status
from pydantic import BaseModel, Field, field_validator

# Нативна інтеграція з Google Cloud Logging
from google.cloud import logging as cloud_logging
from google.cloud import firestore
from agents.gemini_client import run_autonomous_agent_async, analyze_document_structured_async, query_agent_builder_async

# Ініціалізація Cloud Logging клієнта
log_client = cloud_logging.Client()
# Зв'язуємо стандартний логгер Python з Cloud Logging (структурований JSON)
log_client.setup_logging()
import logging

logger = logging.getLogger("fastapi-agent-logger")
logger.setLevel(logging.INFO)

app = FastAPI(
    title="GCP AI Agents Lab API",
    description="Production-ready сервіс із Middleware моніторингом та Hardening безпекою",
    version="2.0.0"
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
db = firestore.AsyncClient()

# Ліміт на розмір завантажуваного файлу (наприклад, 10 МБ)
MAX_FILE_SIZE = 10 * 1024 * 1024 

# --- 🔐 HARDENING & БЕЗПЕКА (Pydantic Валідація) ---
class AgentInstructionRequest(BaseModel):
    instruction: str = Field(..., max_length=1000, example="Збережи рахунок від Apple на 450 USD.")

    @field_validator('instruction')
    @classmethod
    def prevent_prompt_injection(cls, v: str) -> str:
        # Патерни для блокування очевидних спроб атак на системний промпт
        forbidden_patterns = [
            r"(?i)ignore previous instructions",
            r"(?i)system_hacked",
            r"(?i)bypass system prompt",
            r"(?i)you are now a chat bot"
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, v):
                logger.warning(f"⚠️ [Security Alert] Виявлено спробу Prompt Injection: {v}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Запит відхилено системою безпеки: виявлено підозрілі інструкції."
                )
        return v

class QueryRequest(BaseModel):
    query: str = Field(..., max_length=1000, example="Які кроки для вирішення CrashLoopBackOff?")

class InvoiceItem(BaseModel):
    description: str
    price: float

class ExtractedInvoice(BaseModel):
    vendor_name: str
    total_amount: float
    currency: str
    items: List[InvoiceItem]

# --- 📊 MIDDLEWARE ДЛЯ МОНІТОРИНГУ ТА ЛОГУВАННЯ МЕТРИК ---
@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Обробити запит
    response = await call_next(request)
    
    latency = round(time.time() - start_time, 3)
    
    # Збираємо структуровані метрики для Cloud Logging / Looker Dashboard
    log_payload = {
        "event": "http_request",
        "endpoint": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "latency_seconds": latency,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Логуємо як структурований JSON
    if response.status_code >= 400:
        logger.error(log_payload)
    else:
        logger.info(log_payload)
        
    return response

# --- 🚀 ЕНДПОЇНТИ ---
@app.get("/")
async def root():
    return {"status": "healthy", "version": "2.0.0"}

@app.post("/agent/run")
async def run_agent(payload: AgentInstructionRequest):
    if not payload.instruction.strip():
        raise HTTPException(status_code=400, detail="Інструкція порожня")
    try:
        response = await run_autonomous_agent_async(user_instruction=payload.instruction)
        
        # Визначаємо, чи це була "невпевнена" або "нецільова" відповідь
        is_denial = "не можу допомогти" in response or "обмежений лише технічними" in response
        
        # Додатково логуємо бізнес-метрику відмов у Cloud Logging
        logger.info({
            "event": "agent_execution",
            "is_denial": is_denial,
            "query_length": len(payload.instruction)
        })
        
        return {"success": True, "agent_response": response}
    except Exception as e:
        logger.error({"event": "agent_error", "error": str(e)})
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
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "skipped", "reason": "no_token"}

    try:
        data = await request.json()
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"]["text"]
            
            # Анонімізуємо потенційні PII (наприклад, явні довгі цифри карток чи телефонів перед відправкою в логгер)
            sanitized_text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD REDACTED]', user_text)
            logger.info({"event": "telegram_message_received", "chat_id": chat_id, "text": sanitized_text})
            
            # Валідація довжини повідомлення з Telegram (Hardening)
            if len(user_text) > 1000:
                agent_response = "Запит занадто довгий (ліміт 1000 символів)."
            else:
                try:
                    # Проганяємо через логіку нашого інжекшн-фільтра вручну для телеграму
                    AgentInstructionRequest(instruction=user_text)
                    agent_response = await run_autonomous_agent_async(user_instruction=user_text)
                except HTTPException as he:
                    agent_response = he.detail
                except Exception:
                    agent_response = "Вибачте, виникла внутрішня помилка обробки безпеки."
            
            telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            async with httpx.AsyncClient() as client:
                await client.post(telegram_api_url, json={"chat_id": chat_id, "text": agent_response}, timeout=10.0)
                
        return {"status": "ok"}
    except Exception as e:
        logger.error({"event": "telegram_webhook_error", "error": str(e)})
        return {"status": "error"}

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
