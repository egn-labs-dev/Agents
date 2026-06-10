# Нотатки по Vertex AI Agent Builder (Тиждень 2)

## Що дає Agent Builder станом на 2026 рік:
1. **Out-of-the-box RAG (Data Stores):** Можливість підключити Cloud Storage, BigQuery або веб-сайти. Платформа сама чанкує, ембеддить та індексує документи.
2. **Multi-turn Conversations:** Вбудоване керування сесіями та контекстом діалогу.
3. **Enterprise Security:** Інтеграція з IAM, шифрування даних та ізоляція в межах проєкту GCP.

## Опції конфігурації Агента:
- **Goal / Playbook:** Опис мети агента та кроків (System Instructions).
- **Tools:** Розширення можливостей через OpenAPI (Extensions) або Function Calling (як ми робили на Тижні 1).
- **Data Stores:** Прив'язка баз знань для пошуку відповідей.
