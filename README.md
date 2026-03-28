# CyberSec Copilot — Phi Edition

AI-powered cybersecurity assistant running on Microsoft Phi via Ollama.
No Docker. No cloud. Runs locally on Windows with Python 3.13.

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
