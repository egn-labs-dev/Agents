# Архітектура та джерела даних ШІ-Агента (Тиждень 3)

## 1. Структура даних

### А. Неструктуровані дані (RAG)
- **Джерело:** Google Cloud Storage (`gs://n8n-automations-k8s-runbook`) -> Vertex AI Agent Builder Data Store (`k8s-runbook-store`).
- **Формат:** Текстові ранбуки (`.txt`, `.pdf`) для DevOps-інструкцій.

### Б. Структуровані дані (Транзакційні)
- **Джерело:** Google Cloud Firestore (NoSQL).
- **Колекція:** `invoices`
- **Схема документа (Firestore JSON):**
  ```json
  {
    "vendor": "String",
    "amount": "Number (Float)",
    "currency": "String",
    "processed_at": "Timestamp"
  }
  ```

## 2. Управління доступом (IAM)

- **Локальне середовище:** Доступ через `gcloud auth application-default login` (права твого користувача).
- **Production (Cloud Run):** Застосунок використовує Compute Engine default service account або кастомний сервісний акаунт, який повинен мати наступні ролі:
  - `roles/datastore.user` (для читання/запису у Firestore).
  - `roles/discoveryengine.viewer` (для запитів до Agent Builder).

## 3. Ризики безпеки та витоку даних (PII, Секрети)

- **Витік PII (Personally Identifiable Information):** У рахунках можуть міститися персональні дані (ПІБ, адреси). **Мітигація:** Температура моделі зафіксована на 0.1, дані записуються строго у внутрішню базу Firestore без логування тіла інвойсу у відкритий Cloud Logging.
- **Галюцинації API-ключів:** Заборонено завантажувати у Cloud Storage файли конфігурацій, що містять паролі чи токени до кластерів.
