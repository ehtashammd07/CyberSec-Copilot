@echo off
echo.
echo  Starting CyberSec Copilot Backend...
echo  API:  http://localhost:8000
echo  Docs: http://localhost:8000/docs
echo.
echo  Press Ctrl+C to stop.
echo.

cd backend
call .venv\Scripts\activate.bat
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
