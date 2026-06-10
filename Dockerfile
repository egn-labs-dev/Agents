# Використовуємо легкий та стабільний образ Python
FROM python:3.11-slim

# Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Забороняємо Python писати файли .pyc на диск і буферизувати stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Встановлюємо системні залежності (якщо знадобляться для компіляції пакетів)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо лише файл залежностей для ефективного кешування шарів Docker
COPY requirements.txt .

# Оновлюємо pip та встановлюємо пакети
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копіюємо всю структуру нашого проєкту в контейнер
COPY . .

# Cloud Run передає порт через змінну середовища $PORT (за замовчуванням 8080)
EXPOSE 8080

# Запускаємо uvicorn, прив'язуючись до хосту 0.0.0.0 та порту Cloud Run
CMD ["sh", "-c", "python -m uvicorn services.api:app --host 0.0.0.0 --port ${PORT}"]
