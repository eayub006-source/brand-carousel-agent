@echo off
cd /d "%~dp0"
title Brand Carousel Agent - Local Server
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  Brand Carousel Agent                                      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ✓ Starting server...
echo.
echo Open your browser to: http://127.0.0.1:8000
echo.
python app.py
pause
