@echo off
REM Cannabis Aggregator - Frontend Server Startup Script

echo.
echo ================================================
echo  Cannabis Aggregator - Frontend Server
echo ================================================
echo.

REM Check if running from scripts folder
if exist "..\frontend" (
    cd ..\frontend
) else (
    cd frontend
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo ERROR: Node modules not found!
    echo Please run: npm install
    echo Or use: scripts\install-deps.bat
    pause
    exit /b 1
)

echo [1/1] Starting frontend server...
echo.
echo Frontend starting on http://localhost:3000
echo.
echo Press Ctrl+C to stop the server.
echo.

npm run dev
