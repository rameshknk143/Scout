@echo off
REM ============================================================
REM  ONE-TIME ADMIN CLICK — registers the boot-start Maxun task
REM  (the ONSTART trigger needs admin rights; this is the only
REM  manual step in the whole pipeline).
REM
REM  HOW: press Windows key, type "cmd", right-click "Command
REM  Prompt" -> "Run as administrator", then paste:
REM      D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\scout-cloud\fix-boot-start.bat
REM  ...or just run this file from an elevated cmd.
REM  It is safe to run more than once (re-creates idempotently).
REM ============================================================

set PYTHON="C:\Users\rames\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
set SCRIPT="D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\scout-cloud\scraper\maxun_watchdog.py"

echo Registering "ScoutVeda Maxun Boot Start" (fires when Windows turns on)...
schtasks /Create /SC ONSTART /TN "ScoutVeda Maxun Boot Start" /TR %PYTHON% %SCRIPT% /RL LIMITED /F
if %errorlevel%==0 (
    echo.
    echo OK — boot-start task registered. Services will now come up automatically
    echo after every reboot; the 15-min watchdog covers the rest of the day.
    schtasks /Query /TN "ScoutVeda Maxun Boot Start" /FO LIST | findstr /i "TaskName Next Run Status"
) else (
    echo FAILED — still not running as admin. Check the prompt is admin and retry.
)
echo.
pause
