# Enterprise AI Shield: DevOps & SRE Assistant 🛡️🤖

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg?style=for-the-badge)](https://github.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge)](https://www.python.org/)
[![GCP](https://img.shields.io/badge/GCP-Cloud_Run-4285F4.svg?style=for-the-badge&logo=google-cloud)](https://cloud.google.com/)

**DevOps AI Assistant with Zero-Trust Infrastructure Protection and Vertex AI RAG integration.**

This project serves as the infrastructure and security backbone for the Enterprise AI Shield ecosystem. It provides an autonomous AI SRE (Site Reliability Engineer) that operates directly within Telegram, monitoring cloud resources, diagnosing database/vault issues, and securely executing DevOps runbooks.

---

## 🏗 Architecture & Security

Our DevOps AI Assistant is designed to be the "SRE Angel" for enterprise logistics applications (like the Zero Trust Dispatch platform). It boasts an advanced infrastructure-specific security pipeline:

```mermaid
graph TD
    classDef client fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff
    classDef secure fill:#0f172a,stroke:#3b82f6,stroke-width:2px,color:#fff,stroke-dasharray: 5 5
    classDef backend fill:#1e293b,stroke:#475569,stroke-width:2px,color:#fff
    classDef ai fill:#7c3aed,stroke:#6d28d9,stroke-width:2px,color:#fff

    Eng["DevOps Engineer<br/>(Telegram)"]:::client
    Webhooks["Cloud Webhooks<br/>(Alerts)"]:::client

    subgraph "Zero Trust DevOps Perimeter"
        API["FastAPI Entry Point"]:::backend
        Pydantic["Pydantic Injection Shield<br/>(Blocks Malicious Prompts)"]:::secure
        InfraScrub["InfraScrubber<br/>(Masks JWT, Passwords, API Keys)"]:::secure
        CloudLog["Cloud Logging Middleware<br/>(Immutable Audit)"]:::backend

        API --> Pydantic
        Webhooks --> API
        Pydantic --> InfraScrub
        InfraScrub --> CloudLog
    end

    Gemini["Google Gemini AI"]:::ai
    Vertex["Vertex AI RAG<br/>(Runbook Store)"]:::ai

    CloudLog --> Gemini
    Gemini <--> Vertex
    Gemini -- "Secure Execution" --> API
```

---

## 🌟 Core Components

| Component | Description |
| --- | --- |
| 🛡️ **Pydantic Injection Shield** | Validates incoming commands at the FastAPI router level, blocking jailbreaks, roleplay attacks, or system prompt overrides in <1ms. |
| 🔒 **InfraScrubber** | A specialized Data Scrubber that parses raw logs and connection strings, masking DB passwords, JWT Bearer tokens, and API Keys before sending context to the LLM. |
| 🧠 **Vertex AI Agent Builder (RAG)** | Empowers the AI to consult your company's proprietary Kubernetes runbooks or ADR regulations to provide hallucination-free incident resolution. |
| 📝 **Immutable Cloud Audit** | Every request is routed through a Cloud Logging Middleware that streams structured JSON events to GCP, ensuring compliance with ISO 27001. |
| 🤖 **Multi-Step Tool Calling** | The agent can autonomously execute predefined Python functions (e.g., Slack notifications, DB queries) in a controlled loop. |

---

## 🚀 Deployment

This project is optimized for **Google Cloud Run**.

### 1. Environment Setup
Create a `.env` file in the project root:
```env
TELEGRAM_BOT_TOKEN=your_token
GCP_PROJECT_ID=your_gcp_project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### 2. Local Run
```bash
python -m uvicorn services.api:app --reload --host 0.0.0.0 --port 8080
```

### 3. Deploy to Cloud Run
```bash
gcloud run deploy devops-ai-assistant \
  --source . \
  --region europe-west4 \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN="your_token"
```

---

<div align="center">
  <i>Enterprise AI Shield — DevOps and SRE Automation without compromising Security.</i>
</div>
