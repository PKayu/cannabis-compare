@echo off
REM Cannabis Aggregator - Complete Dependencies Installation
REM Installs ALL required packages for both backend and frontend

echo.
echo ================================================
echo  Cannabis Aggregator - Install Dependencies
echo ================================================
echo.

REM Check if running from scripts folder
if exist "..\backend" (
    cd ..
)

REM ============================================
REM BACKEND DEPENDENCIES
REM ============================================

echo [1/8] Setting up Python virtual environment...
if not exist "backend\venv" (
    echo Creating virtual environment...
    cd backend
    python -m venv venv
    cd ..
)

echo [2/8] Activating virtual environment...
call backend\venv\Scripts\activate.bat

echo [3/8] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [4/8] Installing core FastAPI and web server...
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install python-multipart==0.0.6

echo.
echo [5/8] Installing database packages (Python 3.13 compatible)...
pip install sqlalchemy==2.0.36
pip install psycopg2-binary==2.9.11
pip install alembic==1.13.1

echo.
echo [6/8] Installing Pydantic and validation...
pip install pydantic==2.5.3
pip install pydantic-settings==2.1.0
pip install email-validator

echo.
echo [7/8] Installing authentication packages...
pip install python-jose[cryptography]
pip install passlib[bcrypt]
pip install supabase==2.0.0

echo.
echo Installing web scraping and utilities...
pip install requests==2.31.0
pip install beautifulsoup4==4.12.2
pip install lxml
pip install aiohttp==3.9.1
pip install rapidfuzz
pip install python-dotenv==1.0.0

echo.
echo Installing scheduler and testing tools...
pip install apscheduler==3.10.4
pip install pytest==7.4.3
pip install pytest-asyncio==0.21.1

REM ============================================
REM FRONTEND DEPENDENCIES
REM ============================================

echo.
echo [8/8] Installing frontend dependencies...
if exist "frontend\package.json" (
    cd frontend
    call npm install
    cd ..
    echo Frontend dependencies installed.
) else (
    echo WARNING: frontend/package.json not found. Skipping frontend install.
)

REM ============================================
REM VERIFICATION
REM ============================================

echo.
echo ================================================
echo  Verifying Installation
echo ================================================
echo.

call backend\venv\Scripts\activate.bat
python -c "import fastapi, uvicorn, sqlalchemy, psycopg2, pydantic, jose, passlib, supabase, requests, bs4, aiohttp, rapidfuzz, dotenv, alembic, apscheduler; print('Backend: All required modules imported successfully!')" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo  Installation Complete!
    echo ================================================
    echo.
    echo To start development:
    echo   scripts\start-dev.bat     - Start both servers
    echo   scripts\start-backend.bat - Start backend only
    echo   scripts\start-frontend.bat - Start frontend only
    echo.
) else (
    echo.
    echo ================================================
    echo  WARNING: Some modules failed to import
    echo ================================================
    echo.
    echo Please check the error messages above.
)

pause
