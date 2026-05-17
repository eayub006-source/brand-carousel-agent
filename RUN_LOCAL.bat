@echo off
REM Brand Carousel Agent - Local Launcher
title Brand Carousel Agent
cls

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  Brand Carousel Agent - Starting Local Server             ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo.
    echo Please install Python from https://www.python.org
    pause
    exit /b 1
)

echo ✓ Python found
echo.

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ⚠ Installing dependencies...
    python -m pip install -r requirements.txt
)

echo ✓ Dependencies ready
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  Starting server...                                       ║
echo ║                                                           ║
echo ║  🌐 Open your browser to:                                ║
echo ║     http://127.0.0.1:8000                                ║
echo ║                                                           ║
echo ║  Press Ctrl+C to stop the server                         ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

python app.py
pause
