@echo off
echo ======================================
echo   BidSentry Backend Setup
echo ======================================
echo.

cd /d "%~dp0\backend"

echo [1/2] Installing Python dependencies...
pip install -r requirements.txt

echo.
echo [2/2] Starting FastAPI server...
echo.
echo   API Docs: http://localhost:8000/docs
echo   Health:   http://localhost:8000/api/health
echo.

cd /d "%~dp0"
python -m uvicorn backend.main:app --reload --port 8000
