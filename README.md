# CyberSec Copilot — Phi Edition

AI-powered cybersecurity assistant running on Microsoft Phi via Ollama.
No Docker. No cloud. Runs locally on Windows with Python 3.13.



https://github.com/user-attachments/assets/53a54f70-c993-45db-a489-f76e0144be1b
<img width="1919" height="875" alt="Screenshot 2026-03-25 152821" src="https://github.com/user-attachments/assets/e1c6c132-643a-416e-a280-bede03f91588" />
<img width="1919" height="876" alt="Screenshot 2026-03-25 152842" src="https://github.com/user-attachments/assets/2dbd8478-be91-4674-875b-33fb64159772" />

## What Is This?

CyberSec Copilot is a local AI assistant built specifically for cybersecurity tasks. You can:

- **Chat** with it about vulnerabilities, CVEs, attack techniques, and defences
- **Analyze** log files and source code to detect threats automatically
- Switch between **Attacker**, **Defender**, and **Explain** perspectives
- Get structured results with severity ratings, OWASP categories, and mitigation steps

It uses a **RAG (Retrieval-Augmented Generation)** pipeline backed by a built-in OWASP and CVE knowledge base, so answers are grounded in real security knowledge — not just the model's training data.

## Why Phi?

| Model  | Size   | Speed  | Quality |
|--------|--------|--------|---------|
| phi    | 1.6 GB | Fast   | Good    |
| phi3   | 2.3 GB | Medium | Better  |
| phi3.5 | 2.2 GB | Medium | Best    |
| llama3 | 4.7 GB | Slow   | Best    |

Phi is ideal for local use — small download, fast responses, low RAM usage.

---

## Prerequisites

| Tool | Download |
|------|----------|
| Python 3.13 | https://python.org/downloads — tick "Add to PATH" |
| Node.js 20+ | https://nodejs.org (LTS) |
| Ollama | Already installed |

---

## Quick Start

1. Double-click pull_model.bat  — downloads Phi (~1.6 GB, once only)
2. Double-click setup.bat       — installs all dependencies
3. Double-click run_backend.bat — starts API on port 8000
4. Double-click run_frontend.bat (new window) — starts UI on port 3000
5. Open http://localhost:3000

---

## Phi Model Variants

Edit backend\.env and change OLLAMA_MODEL:

    OLLAMA_MODEL=phi        # default — fastest
    OLLAMA_MODEL=phi3       # better reasoning
    OLLAMA_MODEL=phi3.5     # best quality, still small
    OLLAMA_MODEL=phi3-mini  # smallest footprint

Then re-run: ollama pull phi3  (or whichever you chose)

---

## Project Structure

    cybersec-copilot/
    ├── pull_model.bat      <- Step 1: download phi
    ├── setup.bat           <- Step 2: install dependencies
    ├── run_backend.bat     <- Step 3a: start API
    ├── run_frontend.bat    <- Step 3b: start UI
    │
    ├── backend/
    │   ├── .env.example    <- config (phi settings pre-configured)
    │   ├── requirements.txt
    │   └── app/
    │       ├── main.py
    │       ├── routes/chat.py
    │       ├── routes/analyze.py
    │       ├── services/llm_service.py   <- phi-tuned (temp=0.2, stop tokens)
    │       ├── services/rag_service.py
    │       ├── services/embedding.py
    │       ├── services/analyzer.py
    │       ├── core/config.py
    │       ├── models/schemas.py
    │       └── utils/prompt_builder.py   <- phi instruction format
    │
    ├── frontend/
    │   └── src/app/page.tsx
    │
    └── dataset/
        └── cybersec_kb.json

---

## API

POST /api/v1/chat
    { "message": "What is SQL injection?", "mode": "explain" }
    modes: explain | attacker | defender

POST /api/v1/analyze
    { "content": "paste logs or code here", "type": "auto" }
    types: auto | log | code

GET /health

---

## Phi-Specific Optimisations

llm_service.py:
  - temperature: 0.2       (phi is more accurate at low temp)
  - num_predict: 1024      (phi is concise, 1024 tokens is enough)
  - repeat_penalty: 1.1    (prevents phi from looping)
  - stop tokens: <|end|>, <|user|>  (phi's native stop tokens)

prompt_builder.py:
  - Uses phi's native <|system|> / <|user|> / <|assistant|> format
  - Shorter prompts (phi has smaller context window than llama3)
  - Content snippets limited to 1000 chars for analysis prompts

---

## Troubleshooting

"Cannot connect to Ollama"
  -> Make sure Ollama desktop app is open (system tray icon)

Phi gives incomplete JSON
  -> This can happen. The analyzer falls back to heuristic results automatically.
  -> Upgrade to phi3 or phi3.5 for better JSON output.

Slow first response
  -> Phi loads the model into memory on first use. Second query is faster.

Port in use
  -> netstat -ano | findstr :8000
  -> taskkill /PID <number> /F


# 🚀 CyberSec Copilot (Phi) — Windows Setup Guide

## ✅ Step 1 — Verify Installation

Open Command Prompt (CMD) and run:

```bash
python --version
node --version
ollama --version
```

---

## 📂 Step 2 — Clone Repository

```bash
git clone https://github.com/ehtashammd07/CyberSec-Copilot.git
cd cybersec-copilot-phi
```

---

## 🤖 Step 3 — Pull Phi Model

```bash
ollama pull phi
```

Test the model:

```bash
ollama run phi
```

---

## ⚙️ Step 4 — Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🔐 Step 5 — Configure Environment

Create a `.env` file inside the `backend/` directory:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi
```

---

## ▶️ Step 6 — Run Backend

```bash
uvicorn app.main:app --reload
```

Backend will run at:

* API Base: http://127.0.0.1:8000
* API Docs: http://127.0.0.1:8000/docs

---

## 🌐 Step 7 — Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at:

* http://localhost:3000

---

## 🔁 Running the Project (Next Time)

You only need to run:

### 🖥️ Terminal 1 (Backend)

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

### 🌐 Terminal 2 (Frontend)

```bash
cd frontend
npm run dev
```

---

## 🧠 Tech Stack

* **LLM**: Phi (via Ollama)
* **Backend**: FastAPI (Python)
* **Frontend**: Next.js + React
* **AI Integration**: Local LLM (Ollama)

---

## 📌 Notes

* Ensure **Ollama is running** before starting the backend.
* First run may take time due to model loading.
* Compatible with **Windows environment**.

---

## 📄 License

MIT License

