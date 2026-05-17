#!/usr/bin/env pwsh
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $dir

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Brand Carousel Agent - Local Server" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ Starting server..." -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Open your browser to:" -ForegroundColor Yellow
Write-Host "   http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

python app.py
