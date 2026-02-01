@echo off
REM Windows wrapper for commit-msg hook
cd /d "%~dp0"
cd ..
py .githooks/commit-msg.py %*
