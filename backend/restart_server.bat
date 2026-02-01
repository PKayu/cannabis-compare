@echo off
REM Restart Backend Server with Clean Slate
REM This script kills all Python processes and starts a fresh server

echo ========================================
echo Killing all Python processes...
echo ========================================
taskkill /F /IM python.exe /T 2>nul

echo.
echo Waiting for ports to be released...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Checking if port 8000 is free...
echo ========================================
netstat -an | findstr ":8000"
if errorlevel 1 (
    echo Port 8000 is FREE - ready to start
) else (
    echo WARNING: Port 8000 is still in use!
    echo Please check Task Manager and manually end python.exe processes
    pause
    exit /b 1
)

echo.
echo ========================================
echo Starting backend server...
echo ========================================
cd /d "%~dp0"
venv\Scripts\python.exe -m uvicorn main:app --port 8000

pause
