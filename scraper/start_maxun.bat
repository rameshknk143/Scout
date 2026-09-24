@echo off
REM ScoutVeda Maxun Auto-Start Script
REM This script starts all required Maxun services

echo ========================================
echo ScoutVeda Maxun Auto-Start
echo ========================================
echo.

set MAXUN_DIR=D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun
set BROWSER_DIR=%MAXUN_DIR%\browser

REM Check if backend is running
netstat -ano | findstr ":8080.*LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Backend API already running on port 8080
) else (
    echo Starting Backend API...
    start /d "%MAXUN_DIR%" cmd /c "npm run server"
    timeout /t 5 /nobreak >nul
)

REM Check if browser service is running
netstat -ano | findstr ":3002.*LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Browser Health service running on port 3002
) else (
    echo Starting Browser Service...
    start /d "%BROWSER_DIR%" cmd /c "node dist/server.js"
    timeout /t 3 /nobreak >nul
)

REM Check if frontend is running
netstat -ano | findstr ":5173.*LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Frontend UI running on port 5173
) else (
    echo Starting Frontend UI...
    start /d "%MAXUN_DIR%" cmd /c "npm run dev:frontend"
    timeout /t 5 /nobreak >nul
)

echo.
echo ========================================
echo Maxun Services Startup Complete
echo ========================================
echo.
echo Access the Maxun UI at: http://localhost:5173
echo Login: scoutveda@maxun.local / ScoutMaxun2026!
echo.
echo To get your API key:
echo 1. Click your profile picture (top right)
echo 2. Select "API Keys"
echo 3. Copy the generated key
echo.
echo Then update scraper/laptop.env with:
echo   MAXUN_API_KEY=your_key_here
echo.
pause
