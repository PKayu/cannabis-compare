@echo off
REM Cannabis Aggregator - Backend Server Startup Script

echo.
echo ================================================
echo  Cannabis Aggregator - Backend Server
echo ================================================
echo.

cd backend

REM Check if venv exists
if not exist "venv" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [1/2] Checking virtual environment...
REM Use explicit Python path to avoid using wrong venv (root .venv vs backend\venv)
venv\Scripts\python.exe -c "import sys; print('Python:', sys.executable)"

echo [2/2] Starting backend server...
echo.
echo Backend starting on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Use explicit Python path to ensure correct venv is used
venv\Scripts\python.exe -m uvicorn main:app --reload --log-level info
