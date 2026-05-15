@echo off
cd /d "%~dp0"
echo Starting Brand Post Agent...
echo.
"..\..\..\.venv\Scripts\python.exe" app.py
pause
