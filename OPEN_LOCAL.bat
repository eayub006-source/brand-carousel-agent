@echo off
echo Starting Brand Carousel Agent...
echo.
echo Waiting for server to start...
timeout /t 3 /nobreak
echo.
echo Opening browser to http://127.0.0.1:8000
start http://127.0.0.1:8000
