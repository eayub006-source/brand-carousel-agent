#!/usr/bin/env pwsh
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $dir

Write-Host "Starting Brand Post Agent..." -ForegroundColor Green
Write-Host ""

& "c:\Users\DELL PRECision 7550\Documents\.venv\Scripts\python.exe" app.py
