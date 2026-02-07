@echo off

echo.
echo ================================================
echo  Docker Cleanup
echo ================================================
echo.

echo Stopping containers...
docker-compose down

echo.
echo To remove all data (including database), run:
echo   docker-compose down -v
echo.

pause
