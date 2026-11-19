@echo off
echo ========================================================
echo  RECODA --- Autonomous Data Quality ^& Repair Engine
echo ========================================================
echo.
echo Starting FastAPI server at http://127.0.0.1:8000
echo.
cd /d "%~dp0\backend"
set PYTHONPATH=%cd%
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
