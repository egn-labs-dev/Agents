# Інструкція з розгортання: DevOps AI Assistant (З нуля до Production)

Цей посібник описує процес розгортання асинхронного ШІ-мікросервісу в екосистемі Google Cloud Platform (GCP).

## 🗺️ Архітектурна схема продукту
1. **Шар доступу:** Telegram Bot API / REST API (FastAPI фреймворк)
2. **Обчислення:** Google Cloud Run (Stateless Docker-контейнер, Python 3.11-slim)
3. **Мозок (AI Engine):** Google GenAI SDK (Gemini 2.5 Flash) + Vertex AI Agent Builder (RAG)
4. **Пам'ять (State):** Google Cloud Firestore (Native NoSQL)
5. **Аудит:** GCP Cloud Logging (Структуровані JSON метрики через Middleware)

---

## 🛠️ Покрокове розгортання інфраструктури

### 1. Підготовка локального середовища
```bash
git clone <url-твого-репозиторію>
cd gcp-ai-agents-lab
python -m venv .venv
source .venv/bin/activate  # Для Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Ініціалізація Google Cloud CLI
Переконайтеся, що ви автентифіковані та вибрали правильний проєкт:

```bash
gcloud auth login
gcloud config set project n8n-automations-497913
```
Активація необхідних API в хмарі Google:

```bash
gcloud services enable datastore.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

### 3. Налаштування Сховища Пам'яті (Firestore)
Створіть базу даних Firestore у Native режимі:

```bash
gcloud alpha firestore databases create --database="(default)" --location=europe-west3 --type=firestore-native
```

### 4. Хмарна збірка та Деплой на Cloud Run
Запустіть конвеєр Cloud Build для компіляції Docker-образу та його автоматичного розгортання на Cloud Run:

```bash
# Створення репозиторію артефактів (якщо не створено)
gcloud artifacts repositories create ai-agents-repository --repository-format=docker --location=europe-west3

# Хмарна збірка
gcloud builds submit --tag europe-west3-docker.pkg.dev/n8n-automations-497913/ai-agents-repository/fastapi-agent:latest .

# Деплой сервісу у хмару
gcloud run deploy fastapi-agent \
    --image europe-west3-docker.pkg.dev/n8n-automations-497913/ai-agents-repository/fastapi-agent:latest \
    --region europe-west3 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars="TELEGRAM_BOT_TOKEN=твоє_значення,GOOGLE_API_KEY=твоє_значення"
```

### 🔒 Налаштування безпеки (Hardening)
* **Prompt Injection:** Усі вхідні інструкції валідуються на рівні FastAPI через Pydantic-регулярні вирази (AgentInstructionRequest). Максимальна довжина запиту обмежена до 1000 символів.
* **IAM:** Системний сервісний акаунт `gcp-sa-discoveryengine` повинен мати роль `Storage Object Viewer` на бакет знань для коректної роботи RAG.
