@echo off
REM Windows wrapper for pre-commit hook
cd /d "%~dp0"
cd ..
py .githooks/pre-commit.py %*
