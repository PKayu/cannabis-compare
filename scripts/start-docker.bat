@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================
echo  Cannabis Aggregator - Docker Environment
echo ================================================
echo.

echo Checking Docker Desktop...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or not installed.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Docker is running.
echo.

REM Check if .env files exist
if not exist "backend\.env" (
    echo Creating backend\.env from .env.example...
    copy backend\.env.example backend\.env >nul
    echo WARNING: Please edit backend\.env with your configuration.
    echo.
)

if not exist "frontend\.env.local" (
    echo Creating frontend\.env.local from .env.example...
    copy frontend\.env.example frontend\.env.local >nul
    echo WARNING: Please edit frontend\.env.local with your configuration.
    echo.
)

echo Starting Docker containers...
echo.

docker-compose up --build

echo.
echo Containers stopped.
pause
