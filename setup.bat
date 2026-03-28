@echo off
setlocal enabledelayedexpansion

echo.
echo  ============================================================
echo   CyberSec Copilot (Phi Edition) - Windows Setup Script
echo  ============================================================
echo.

:: ── Check Python ────────────────────────────────────────────────────────────
echo [1/5] Checking Python version...
python --version 2>nul
if errorlevel 1 (
    echo  ERROR: Python not found. Download from https://python.org
    pause & exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Found Python %PYVER%

:: ── Check Node.js ────────────────────────────────────────────────────────────
echo.
echo [2/5] Checking Node.js...
node --version 2>nul
if errorlevel 1 (
    echo  ERROR: Node.js not found. Download from https://nodejs.org
    pause & exit /b 1
)
echo  Found Node: 
node --version

:: ── Check Ollama ─────────────────────────────────────────────────────────────
echo.
echo [3/5] Checking Ollama...
ollama --version 2>nul
if errorlevel 1 (
    echo  WARNING: Ollama CLI not in PATH. Make sure Ollama desktop app is open.
) else (
    echo  Ollama found: 
    ollama --version
)

:: ── Backend setup ────────────────────────────────────────────────────────────
echo.
echo [4/5] Setting up Backend...
cd backend

if not exist ".venv" (
    echo  Creating virtual environment with Python 3.13...
    python -m venv .venv
)

echo  Installing Python packages (phi-compatible)...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
echo  Backend packages installed.

if not exist ".env" (
    copy .env.example .env >nul
    echo  Created .env - using phi model by default.
)

cd ..

:: ── Frontend setup ───────────────────────────────────────────────────────────
echo.
echo [5/5] Setting up Frontend...
cd frontend

if not exist ".env.local" (
    copy .env.local.example .env.local >nul
    echo  Created .env.local
)

npm install
echo  Frontend packages installed.
cd ..

:: ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   Setup Complete!  (Phi Edition)
echo  ============================================================
echo.
echo   BEFORE FIRST RUN - pull the phi model (only once):
echo     pull_model.bat     (~1.6 GB download)
echo.
echo   THEN START THE APP:
echo     Terminal 1:  run_backend.bat
echo     Terminal 2:  run_frontend.bat
echo.
echo   OPEN BROWSER:
echo     App:      http://localhost:3000
echo     API docs: http://localhost:8000/docs
echo.
echo   PHI MODEL OPTIONS (edit backend\.env to change):
echo     phi        - original, fastest  (~1.6 GB)
echo     phi3       - smarter, balanced  (~2.3 GB)
echo     phi3.5     - best quality       (~2.2 GB)
echo     phi3-mini  - smallest           (~2.2 GB)
echo.
pause
