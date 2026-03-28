@echo off
echo.
echo  ============================================================
echo   Pull Microsoft Phi model for Ollama
echo  ============================================================
echo.
echo  Choose a Phi variant:
echo.
echo   [1] phi      - Fastest, smallest  (~1.6 GB)  RECOMMENDED
echo   [2] phi3     - Smarter, balanced  (~2.3 GB)
echo   [3] phi3.5   - Best quality       (~2.2 GB)
echo.
set /p choice="Enter choice (1/2/3) or press Enter for phi: "

if "%choice%"=="2" (
    echo  Pulling phi3...
    ollama pull phi3
    echo.
    echo  Update OLLAMA_MODEL=phi3 in backend\.env
) else if "%choice%"=="3" (
    echo  Pulling phi3.5...
    ollama pull phi3.5
    echo.
    echo  Update OLLAMA_MODEL=phi3.5 in backend\.env
) else (
    echo  Pulling phi (default)...
    ollama pull phi
)

echo.
echo  Done! Run setup.bat if you haven't already, then run_backend.bat
echo.
pause
