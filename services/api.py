import os
import shutil
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from agents.gemini_client import run_autonomous_agent_async, analyze_document_structured_async

app = FastAPI(
    title="GCP AI Agents Lab API",
    description="Повністю асинхронний мікросервіс для керування ШІ-агентами (Hardened Version)",
    version="1.2.0"
)

# Ліміт на розмір завантажуваного файлу (наприклад, 10 МБ)
MAX_FILE_SIZE = 10 * 1024 * 1024 

class AgentInstructionRequest(BaseModel):
    instruction: str = Field(..., example="Збережи рахунок від Apple на 450 USD.")

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
