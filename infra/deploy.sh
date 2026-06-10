#!/bin/bash

# 1. Вказуємо регіон для деплою
export REGION="europe-west3"
export REPO_NAME="ai-agents-repository"

# 2. Створюємо репозиторій в Artifact Registry
echo "Створюємо репозиторій..."
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Репозиторій для ШІ-агентів лабораторії"

# Отримуємо ID поточного проєкту
export PROJECT_ID=$(gcloud config get-value project)

# Запускаємо хмарну збірку. Образ отримає тег 'latest'
echo "Запускаємо хмарну збірку..."
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/fastapi-agent:latest .

# Деплой на Cloud Run
echo "Деплоїмо на Cloud Run..."
gcloud run deploy fastapi-agent \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/fastapi-agent:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated
