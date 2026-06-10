import json
import os
from datetime import datetime

def save_invoice_to_db(vendor_name: str, total_amount: float, currency: str) -> str:
    """
    Зберігає дані про отриманий інвойс (рахунок) у локальну базу даних.

    Args:
        vendor_name: Назва компанії або постачальника, який виставив рахунок.
        total_amount: Загальна сума до сплати (число з плаваючою крапкою).
        currency: Трьохлітерний код валюти (наприклад: UAH, USD, EUR).
    """
    db_file = "mock_database.json"
    data = []
    
    if os.path.exists(db_file):
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
            
    record = {
        "vendor": vendor_name,
        "amount": total_amount,
        "currency": currency,
        "processed_at": datetime.now().isoformat()
    }
    data.append(record)
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    return f"Успішно збережено в БД рахунок від {vendor_name} на суму {total_amount} {currency}."

def send_slack_notification(channel: str, text: str) -> str:
    """
    Надсилає текстове сповіщення або звіт у вказаний робочий чат-канал (Slack/Telegram).

    Args:
        channel: Назва каналу без символу решітки (наприклад: 'finance', 'general').
        text: Повний текст повідомлення для надсилання.
    """
    print(f"\n📢 [СИСТЕМА] Надсилання сповіщення в #{channel}: {text}\n")
    return f"Сповіщення успішно надіслано в канал #{channel}."
