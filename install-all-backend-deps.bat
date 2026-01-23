@echo off
REM Complete Backend Dependencies Installation
REM Installs ALL required packages for the Cannabis Aggregator backend

echo.
echo ================================================
echo  Installing ALL Backend Dependencies
echo ================================================
echo.

cd backend

echo [1/8] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [2/8] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [3/8] Installing core FastAPI and web server...
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install python-multipart==0.0.6

echo.
echo [4/8] Installing database packages (Python 3.13 compatible)...
pip install sqlalchemy==2.0.36
pip install psycopg2-binary==2.9.11
pip install alembic==1.13.1

echo.
echo [5/8] Installing Pydantic with email validation...
pip install pydantic==2.5.3
pip install pydantic-settings==2.1.0
pip install email-validator

echo.
echo [6/8] Installing authentication packages...
pip install python-jose[cryptography]
pip install passlib[bcrypt]
pip install supabase==2.0.0

echo.
echo [7/8] Installing web scraping and utilities...
pip install requests==2.31.0
pip install beautifulsoup4==4.12.2
pip install lxml
pip install aiohttp==3.9.1
pip install rapidfuzz
pip install python-dotenv==1.0.0

echo.
echo [8/8] Installing scheduler and testing tools...
pip install apscheduler==3.10.4
pip install pytest==7.4.3
pip install pytest-asyncio==0.21.1

echo.
echo ================================================
echo  Verifying Installation
echo ================================================
echo.

python -c "import fastapi, uvicorn, sqlalchemy, psycopg2, pydantic, jose, passlib, supabase, requests, bs4, aiohttp, rapidfuzz, dotenv, alembic, apscheduler; print('✓ All required modules imported successfully!')" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo  Installation Complete!
    echo ================================================
    echo.
    echo Testing backend startup...
    python -c "from main import app; print('✓ Backend app loaded successfully!')" 2>&1

    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ================================================
        echo  Backend is Ready to Start!
        echo ================================================
        echo.
        echo Starting backend server...
        echo.
        uvicorn main:app --reload
    ) else (
        echo.
        echo WARNING: Backend app has import errors.
        echo Please check the error above.
        pause
    )
) else (
    echo.
    echo ================================================
    echo  ERROR: Some modules failed to import
    echo ================================================
    echo.
    echo Please check the error messages above.
    pause
)
