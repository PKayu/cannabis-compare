@echo off
REM Fix Backend - Upgrade SQLAlchemy for Python 3.13 compatibility

echo.
echo ================================================
echo  Fixing Backend for Python 3.13
echo ================================================
echo.

cd backend

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Upgrading SQLAlchemy to compatible version...
pip install --upgrade sqlalchemy==2.0.36

echo.
echo Verifying installation...
python -c "from main import app; print('✓ Backend imports successfully!')" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo  Fix Complete! Backend is ready.
    echo ================================================
    echo.
    echo Starting backend server...
    echo.
    uvicorn main:app --reload
) else (
    echo.
    echo ERROR: Backend still has issues.
    echo Please check the error message above.
    pause
)
