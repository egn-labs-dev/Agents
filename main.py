import sys
import os
from pydantic import BaseModel, Field
from typing import List
from agents.gemini_client import analyze_document_structured

# 1. Описуємо структуру, яку хочемо отримати від ШІ
class InvoiceItem(BaseModel):
    description: str = Field(description="Назва товару або послуги")
    price: float = Field(description="Ціна за одиницю або загальна вартість позиції")

class ExtractedInvoice(BaseModel):
    vendor_name: str = Field(description="Назва компанії або особи, яка виставила рахунок")
    total_amount: float = Field(description="Загальна сума до сплати")
    currency: str = Field(description="Валюта (наприклад: UAH, USD, EUR)")
    items: List[InvoiceItem] = Field(description="Список знайдених позицій у рахунку")

def main():
    print("🤖 Запуск аналітичного модуля GCP Agent Lab...")
    
    # Створимо тимчасовий тестовий текстовий "документ", ніби це збережений лог рахунку
    test_file = "sample_invoice.txt"
    invoice_content = (
        "РАХУНОК НА ОПЛАТУ №42 від 10 червня 2026 р.\n"
        "Постачальник: ТОВ 'Хмара Технолоджіз'\n"
        "Покупець: ФОП Іванов\n"
        "-----------------------------------------\n"
        "1. Послуги хостингу Vertex AI Cloud - 1200.00 UAH\n"
        "2. Консультація по архітектурі ШІ - 2500.00 UAH\n"
        "-----------------------------------------\n"
        "РАЗОМ ДО СПЛАТИ: 3700.00 UAH\n"
        "ПДВ: 0%\n"
    )
    
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(invoice_content)
        
    print(f"📄 Створено тестовий документ: {test_file}")
    
    prompt = "Витягни структуровані дані з цього рахунку. Обов'язково знайди всіх вендорів та позиції."
    
    print("📡 Надсилання документа на аналіз в Gemini (Structured Output)...")
    try:
        # Викликаємо нашу нову функцію
        extracted_data: ExtractedInvoice = analyze_document_structured(
            prompt=prompt,
            file_path=test_file,
            response_schema=ExtractedInvoice
        )
        
        print("\n✅ Дані успішно валідовані Pydantic!")
        print(f"Вендор: {extracted_data.vendor_name}")
        print(f"Загальна сума: {extracted_data.total_amount} {extracted_data.currency}")
        print("Позиції в чеку:")
        for item in extracted_data.items:
            print(f"  - {item.description}: {item.price}")
            
        # Прибираємо за собою тимчасовий файл
        os.remove(test_file)
        
    except Exception as e:
        print(f"❌ Помилка під час тестування аналітики: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        sys.exit(1)

if __name__ == "__main__":
    main()
