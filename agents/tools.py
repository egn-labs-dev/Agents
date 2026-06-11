import os
from datetime import datetime
from google.cloud import firestore

# Ініціалізуємо асинхронного клієнта Firestore
# Він автоматично підхопить Project ID з середовища (локально через ADC, в Cloud Run - нативно)
db = firestore.AsyncClient()

async def save_invoice_to_db(vendor_name: str, total_amount: float, currency: str) -> str:
    """
    Асинхронно зберігає дані про отриманий інвойс (рахунок) у хмарну базу даних Firestore.

    Args:
        vendor_name: Назва компанії або постачальника, який виставив рахунок.
        total_amount: Загальна сума до сплати (число з плаваючою крапкою).
        currency: Трьохлітерний код валюти (наприклад: UAH, USD, EUR).
    """
    try:
        # Створюємо лінк на документ у колекції "invoices" з автогенерацією ID
        doc_ref = db.collection("invoices").document()
        
        # Формуємо структуру для Firestore
        invoice_data = {
            "vendor": vendor_name,
            "amount": float(total_amount),
            "currency": currency,
            "processed_at": datetime.utcnow() # Використовуємо UTC таймаут для Firestore
        }
        
        # Записуємо документ у хмару через await
        await doc_ref.set(invoice_data)
        
        print(f"✅ [Firestore] Записано новий інвойс ID: {doc_ref.id}")
        return f"Успішно збережено в хмарну БД Firestore рахунок від {vendor_name} на суму {total_amount} {currency}."
        
    except Exception as e:
        print(f"❌ [Помилка Firestore] Не вдалося записати дані: {e}")
        return f"Помилка запису в базу даних: {str(e)}"

def send_slack_notification(channel: str, text: str) -> str:
    """
    Надсилає текстове сповіщення або звіт у вказаний робочий чат-канал (Slack/Telegram).

    Args:
        channel: Назва каналу без символу решітки (наприклад: 'finance', 'general').
        text: Повний текст повідомлення для надсилання.
    """
    # На Днях 19-21 ми замінимо це на реальний httpx запит до вебхука Slack, поки залишаємо лог
    print(f"\n📢 [СИСТЕМА] Надсилання сповіщення в #{channel}: {text}\n")
    return f"Сповіщення успішно надіслано в канал #{channel}."
