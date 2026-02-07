@echo off

echo.
echo ================================================
echo  Database Initialization (Docker)
echo ================================================
echo.

echo Starting PostgreSQL container only...
docker-compose up -d postgres

echo Waiting for database to be ready...
timeout /t 5 /nobreak >nul

echo Running Alembic migrations...
docker-compose exec backend alembic upgrade head

echo.
echo Database initialized successfully!
echo.
echo To seed test data, run: scripts\docker-seed-data.bat
echo.

pause
