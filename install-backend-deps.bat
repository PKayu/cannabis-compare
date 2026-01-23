@echo off
REM Install Backend Dependencies - Minimal Version
REM This installs only the essential packages to get the server running

echo.
echo ================================================
echo  Installing Backend Dependencies
echo ================================================
echo.

cd backend

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip first
echo [2/3] Upgrading pip...
python -m pip install --upgrade pip

REM Install essential packages (avoiding problematic ones)
echo [3/3] Installing dependencies...
echo.
echo Installing core packages...
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install sqlalchemy==2.0.23
pip install psycopg2-binary==2.9.11
pip install python-dotenv==1.0.0
pip install requests==2.31.0
pip install beautifulsoup4==4.12.2
pip install lxml
pip install alembic==1.13.1

echo.
echo Installing Pydantic with prebuilt wheels...
pip install pydantic==2.5.3
pip install pydantic-settings==2.1.0

echo.
echo Installing auth dependencies...
pip install "python-jose[cryptography]"
pip install "passlib[bcrypt]"

echo.
echo Installing Supabase client...
pip install supabase==2.0.0

echo.
echo ================================================
echo  Installation Complete!
echo ================================================
echo.
echo You can now start the backend with:
echo   cd backend
echo   venv\Scripts\activate
echo   uvicorn main:app --reload
echo.
pause
