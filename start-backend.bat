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

echo [1/2] Activating virtual environment...
call venv\Scripts\activate.bat

echo [2/2] Starting backend server...
echo.
echo Backend starting on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo.

uvicorn main:app --reload
