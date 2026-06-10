from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List
import shutil
import os
from agents.gemini_client import run_autonomous_agent_async, analyze_document_structured_async

app = FastAPI(
    title="GCP AI Agents Lab API",
    description="Повністю асинхронний мікросервіс для керування ШІ-агентами (Vertex AI 2026 Best Practices)",
    version="1.1.0"
)

class AgentInstructionRequest(BaseModel):
    instruction: str = Field(..., example="Збережи рахунок від Apple на 450 USD в базу та маякни у finance.")

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
        # Викликаємо асинхронну версію агента через await
        response = await run_autonomous_agent_async(user_instruction=payload.instruction)
        return {"success": True, "agent_response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка сервера агента: {str(e)}")

@app.post("/analyst/invoice")
async def analyze_invoice(file: UploadFile = File(...), prompt: str = Form("Витягни структуровані дані")):
    upload_dir = "tmp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Викликаємо асинхронний аналізатор через await
        extracted_data = await analyze_document_structured_async(
            prompt=prompt,
            file_path=file_path,
            response_schema=ExtractedInvoice
        )
        return {"success": True, "data": extracted_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка обробки: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
