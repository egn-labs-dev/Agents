from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import shutil
import os
from agents.gemini_client import run_autonomous_agent, analyze_document_structured

app = FastAPI(
    title="GCP AI Agents Lab API",
    description="Мікросервіс для керування автономними ШІ-агентами на базі Vertex AI",
    version="1.0.0"
)

# Модель для текстових запитів до агента
class AgentInstructionRequest(BaseModel):
    instruction: str

# Моделі Pydantic для структурованого парсингу (перевикористовуємо логіку)
from pydantic import Field
from typing import List

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
    return {"status": "healthy", "workspace": "gcp-ai-agents-lab"}

@app.post("/agent/run")
async def run_agent(payload: AgentInstructionRequest):
    """
    Ендпоїнт для запуску автономного агента з доступом до інструментів (Function Calling).
    """
    if not payload.instruction.strip():
        raise HTTPException(status_code=400, detail="Інструкція не може бути порожньою")
    
    try:
        response = run_autonomous_agent(user_instruction=payload.instruction)
        return {"success": True, "agent_response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка агента: {str(e)}")

@app.post("/analyst/invoice")
async def analyze_invoice(file: UploadFile = File(...), prompt: str = Form("Витягни структуровані дані")):
    """
    Ендпоїнт для завантаження файлу інвойсу та його моментального структурованого аналізу.
    """
    # Створюємо тимчасову папку для завантажень, якщо її немає
    upload_dir = "tmp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    # Зберігаємо завантажений файл локально
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Викликаємо аналітичний модуль
        extracted_data = analyze_document_structured(
            prompt=prompt,
            file_path=file_path,
            response_schema=ExtractedInvoice
        )
        
        return {"success": True, "data": extracted_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка аналізу документа: {str(e)}")
    finally:
        # Очищаємо тимчасовий файл після обробки
        if os.path.exists(file_path):
            os.remove(file_path)
