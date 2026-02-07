@echo off

echo.
echo ================================================
echo  Seed Test Data (Docker)
echo ================================================
echo.

echo Seeding database with test data...
docker-compose exec backend python seed_test_data.py

echo.
echo Test data seeded successfully!
echo.

pause
