@echo off
REM Fix Backend - Install missing dependencies and start server

echo.
echo ================================================
echo  Fixing Backend Dependencies
echo ================================================
echo.

cd backend

echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [2/4] Upgrading SQLAlchemy for Python 3.13 compatibility...
pip install --upgrade sqlalchemy==2.0.36

echo [3/4] Installing rapidfuzz (prebuilt wheel)...
pip install rapidfuzz

echo [4/4] Installing missing dependencies...
pip install pytest pytest-asyncio aiohttp
pip install email-validator
pip install pydantic[email]

echo.
echo ================================================
echo  Verifying Installation
echo ================================================
echo.

python -c "import fastapi, uvicorn, sqlalchemy, rapidfuzz; print('✓ All core modules imported successfully!')" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo  Backend is Ready!
    echo ================================================
    echo.
    echo Starting backend server on http://localhost:8000
    echo API Docs will be available at http://localhost:8000/docs
    echo.
    echo Press Ctrl+C to stop the server.
    echo.

    REM Start the server
    uvicorn main:app --reload
) else (
    echo.
    echo ================================================
    echo  ERROR: Some modules failed to import
    echo ================================================
    echo.
    echo Please check the error messages above.
    echo You may need to install dependencies manually:
    echo   pip install fastapi uvicorn sqlalchemy rapidfuzz
    echo.
    pause
)
