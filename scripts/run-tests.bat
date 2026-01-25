@echo off
REM Cannabis Aggregator - Run All Tests
REM Runs both backend (pytest) and frontend (jest) tests

echo.
echo ================================================
echo  Cannabis Aggregator - Test Runner
echo ================================================
echo.

REM Check if running from scripts folder
if exist "..\backend" (
    cd ..
)

set BACKEND_PASSED=0
set FRONTEND_PASSED=0

REM ============================================
REM BACKEND TESTS
REM ============================================

echo.
echo ================================================
echo  Running Backend Tests (pytest)
echo ================================================
echo.

if exist "backend\venv" (
    call backend\venv\Scripts\activate.bat
    cd backend
    pytest -v
    if %ERRORLEVEL% EQU 0 (
        set BACKEND_PASSED=1
        echo.
        echo Backend tests PASSED
    ) else (
        echo.
        echo Backend tests FAILED
    )
    cd ..
) else (
    echo WARNING: Backend venv not found. Skipping backend tests.
    echo Run scripts\install-deps.bat first.
)

REM ============================================
REM FRONTEND TESTS
REM ============================================

echo.
echo ================================================
echo  Running Frontend Tests (jest)
echo ================================================
echo.

if exist "frontend\node_modules" (
    cd frontend
    call npm test -- --watchAll=false
    if %ERRORLEVEL% EQU 0 (
        set FRONTEND_PASSED=1
        echo.
        echo Frontend tests PASSED
    ) else (
        echo.
        echo Frontend tests FAILED
    )
    cd ..
) else (
    echo WARNING: Frontend node_modules not found. Skipping frontend tests.
    echo Run scripts\install-deps.bat first.
)

REM ============================================
REM E2E TESTS (Optional)
REM ============================================

echo.
echo ================================================
echo  E2E Tests
echo ================================================
echo.
echo To run E2E tests with Playwright:
echo   cd frontend
echo   npx playwright test
echo.

REM ============================================
REM SUMMARY
REM ============================================

echo.
echo ================================================
echo  Test Summary
echo ================================================
echo.

if %BACKEND_PASSED%==1 (
    echo Backend:  PASSED
) else (
    echo Backend:  FAILED or SKIPPED
)

if %FRONTEND_PASSED%==1 (
    echo Frontend: PASSED
) else (
    echo Frontend: FAILED or SKIPPED
)

echo.
pause
