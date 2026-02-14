@echo off
REM test-on-edit.bat - Smart test runner for afterEdit hook
REM Only runs backend tests when backend files are edited

setlocal enabledelayedexpansion

REM Get the edited file path from first argument
set "EDITED_FILE=%~1"

REM Check if file path contains "backend\"
echo %EDITED_FILE% | findstr /C:"backend\" >nul 2>&1

if %errorlevel% == 0 (
    echo [Hook] Backend file changed: %EDITED_FILE%
    echo [Hook] Running backend tests...

    REM Change to backend directory
    cd /d "%~dp0..\backend"

    REM Run pytest with brief output
    venv\Scripts\python.exe -m pytest tests/ -x -q --tb=short 2>nul

    if !errorlevel! neq 0 (
        echo [Hook] ❌ TESTS FAILED - check output above
        exit /b 1
    ) else (
        echo [Hook] ✓ Tests passed
        exit /b 0
    )
) else (
    REM Non-backend file, skip tests silently
    exit /b 0
)
