# Scout Dev Suite — Local Startup Runner
# Runs Next.js and FastAPI together locally pointing to Supabase database.

$ErrorActionPreference = "Stop"

# 1. Read parent/root .env variables
$envPath = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envPath)) {
    Write-Host "❌ Error: Root .env file not found at $envPath" -ForegroundColor Red
    exit 1
}

Write-Host "Reading database credentials from .env..." -ForegroundColor Gray
Get-Content $envPath | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } | ForEach-Object {
    $parts = $_.Split('=', 2)
    $key = $parts[0].Trim()
    $val = $parts[1].Trim()
    [System.Environment]::SetEnvironmentVariable($key, $val, "Process")
}

# 2. Configure local routing
$env:API_URL = "http://localhost:8000"

Write-Host "🚀 Spawning FastAPI Local Backend (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\api'; `$env:DATABASE_URL='$env:DATABASE_URL'; `$env:API_KEY='$env:API_KEY'; python -m uvicorn main:app --reload --port 8000"

Write-Host "🚀 Starting Next.js Dev Server (Port 3000) pointing to Localhost..." -ForegroundColor Cyan
cd "$PSScriptRoot\web"
npm run dev
