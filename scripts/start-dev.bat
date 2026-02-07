@echo off
REM Cannabis Aggregator - Development Startup Script
REM This script starts both the backend (FastAPI) and frontend (Next.js) servers

setlocal enabledelayedexpansion

echo.
echo ================================================
echo  Cannabis Aggregator - Development Environment
echo ================================================
echo.

REM Check if backend dependencies are installed
if not exist "backend\venv" (
    echo [1/4] Creating Python virtual environment...
    cd backend
    python -m venv venv
    cd ..
    echo.
)

REM Activate venv and install/verify dependencies
echo [2/4] Setting up backend dependencies...
call backend\venv\Scripts\activate.bat
pip install -r backend\requirements.txt > nul 2>&1
echo Backend ready.
echo.

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo [3/4] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
    echo.
) else (
    echo [3/4] Frontend dependencies already installed.
    echo.
)

REM Start both servers
echo [4/4] Launching servers...
echo.
echo Starting backend on http://localhost:8000
echo Starting frontend on http://localhost:3000
echo.
echo Press Ctrl+C to stop all servers.
echo.

REM Open API docs in browser
timeout /t 2 /nobreak
start http://localhost:8000/docs

REM Create two new windows for backend and frontend
start "Cannabis Backend" cmd /k "cd backend && venv\Scripts\activate.bat && python run_server.py"
start "Cannabis Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are starting in separate windows.
echo Frontend: http://localhost:3000
echo Backend API Docs: http://localhost:8000/docs
echo.
