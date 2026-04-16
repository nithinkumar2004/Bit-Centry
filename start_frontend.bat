@echo off
echo ======================================
echo   BidSentry Frontend Setup
echo ======================================
echo.

cd /d "%~dp0\frontend"

echo [1/2] Installing Node dependencies...
call npm install

echo.
echo [2/2] Starting Vite dev server...
echo.
echo   Dashboard: http://localhost:5173
echo.

call npm run dev
