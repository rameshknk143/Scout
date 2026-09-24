@echo off
REM ScoutVeda Maxun Scraper Launcher
REM Usage: run_maxun.bat [API_KEY]

echo ========================================
echo ScoutVeda Maxun Scraper Launcher
echo ========================================
echo.

REM Check if backend is running
netstat -an | findstr ":8080" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Maxun backend not running on port 8080
    echo Start it with: cd maxun && npm run server
    echo.
    pause
    exit /b 1
)
echo [OK] Maxun backend is running on port 8080

REM Start browser service if not already running
netstat -an | findstr ":3001" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Starting browser service on port 3001...
    start /d "D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun\browser" node dist/server.js
    timeout /t 5 /nobreak >nul
    echo [OK] Browser service started
) else (
    echo [OK] Browser service already running on port 3001
)

REM Check for API key argument or environment variable
if "%~1"=="" (
    set /p MAXUN_API_KEY="Enter your Maxun API key (get from http://localhost:5173 → Settings → API Keys): "
) else (
    set MAXUN_API_KEY=%~1
)

if "%MAXUN_API_KEY%"=="" (
    echo ERROR: MAXUN_API_KEY is required!
    echo Get your API key from:
    echo   1. Open http://localhost:5173 in browser
    echo   2. Login with scoutveda@maxun.local
    echo   3. Go to Settings → API Keys
    echo   4. Copy the key
    echo.
    pause
    exit /b 1
)
echo [OK] API key configured

REM Run the scraper
echo.
echo Running Maxun scraper...
set "MAXUN_API_KEY=%MAXUN_API_KEY%"
cd "D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\scout-cloud\scraper"
python maxun_multi_scrape.py --limit 5

echo.
echo ========================================
echo Done!
echo ========================================
pause
