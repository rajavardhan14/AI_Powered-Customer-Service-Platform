@echo off
TITLE AI-Powered Customer Service & Business Analytics Platform
echo ==========================================================
echo Starting AI Customer Service & Business Analytics Platform
echo ==========================================================

REM Locate Python
set "PYTHON_EXE=python"
where %PYTHON_EXE% >nul 2>nul
if %ERRORLEVEL% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    )
)

echo Using Python: %PYTHON_EXE%
set "PYTHONPATH=%~dp0backend"

echo [1/2] Checking Machine Learning Models...
"%PYTHON_EXE%" -m app.ml.train

echo [2/2] Starting FastAPI Backend & Dashboard UI on http://localhost:8000 ...
"%PYTHON_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
