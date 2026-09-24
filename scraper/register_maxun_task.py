"""Register a Windows scheduled task that runs the Maxun autonomous pass every hour.

This makes Maxun contribution fully autonomous:
  - Every hour, Windows Task Scheduler fires maxun_autonomous.py
  - That script auto-starts the Maxun services if they're down
  - Triggers all 15 configured robots, forwards each new run to ScoutVeda

Run once:
    python register_maxun_task.py

Remove later:
    schtasks /Delete /TN "ScoutVeda Maxun Hourly Scrape" /F
"""
import subprocess
import sys
from pathlib import Path

TASK_NAME = "ScoutVeda Maxun Hourly Scrape"
SCRAPER_DIR = Path(__file__).resolve().parent
SCRIPT = SCRAPER_DIR / "maxun_autonomous.py"

# Use the desktop venv python (same one the user runs the pipeline with).
PYTHON = sys.executable
if "venv" not in str(PYTHON).lower():
    candidate = r"C:\Users\rames\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
    if Path(candidate).exists():
        PYTHON = candidate


def main():
    if not SCRIPT.exists():
        print("maxun_autonomous.py not found next to this script:", SCRIPT)
        return 1

    cmd = [
        "schtasks", "/Create",
        "/SC", "HOURLY",
        "/TN", TASK_NAME,
        "/TR", f'"{PYTHON}" "{SCRIPT}"',
        "/RL", "LIMITED",
        "/F",
    ]
    print("Registering hourly task:", TASK_NAME)
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("\nCould not auto-register (may need admin rights). Manual one-liner:")
        print('schtasks /Create /SC HOURLY /TN "%s" /TR "\"%s\" \"%s\"" /RL LIMITED /F'
              % (TASK_NAME, PYTHON, SCRIPT))
        return 1

    # confirm it's registered
    check = subprocess.run(["schtasks", "/Query", "/TN", TASK_NAME],
                           capture_output=True, text=True)
    print("\nTask registered and visible to Windows:")
    print(check.stdout.strip())
    print("\nIt will now fire every hour, auto-starting the Maxun services and")
    print("running all robots. Per-pass results land in scraper/.maxun_lastpass.log")
    return 0


if __name__ == "__main__":
    sys.exit(main())
