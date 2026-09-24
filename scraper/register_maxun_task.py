"""Register the Windows scheduled tasks that keep Maxun running by itself.

Two tasks:
  1. "ScoutVeda Maxun Watchdog"      — every 15 min + at boot: repair any down service
  2. "ScoutVeda Maxun Hourly Scrape" — every hour + at boot: run all 15 robots

The watchdog is the safety net: if a service dies between hourly passes it is
restarted within 15 min. The boot-start triggers cover a laptop reboot.

Run once:
    python register_maxun_task.py

Both tasks run as the current (interactive) user with no stored password.
To make them survive a *logoff* (not just a lock) you'd need to create them
"whether user is logged on or not", which requires storing the password —
that is a one-time step I cannot do for you; the interactive form keeps them
alive through lock/sleep/reboot, which is what matters for a personal laptop.

Remove later:
    schtasks /Delete /TN "ScoutVeda Maxun Watchdog" /F
    schtasks /Delete /TN "ScoutVeda Maxun Hourly Scrape" /F
"""
import subprocess
import sys
from pathlib import Path

SCRAPER_DIR = Path(__file__).resolve().parent

WATCHDOG_TASK = "ScoutVeda Maxun Watchdog"
SCRAPE_TASK = "ScoutVeda Maxun Hourly Scrape"

WATCHDOG = SCRAPER_DIR / "maxun_watchdog.py"
AUTONOMOUS = SCRAPER_DIR / "maxun_autonomous.py"

PYTHON = sys.executable
if "venv" not in str(PYTHON).lower():
    candidate = r"C:\Users\rames\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
    if Path(candidate).exists():
        PYTHON = candidate


def create_task(name, trigger_args, script):
    cmd = [
        "schtasks", "/Create",
        "/TN", name,
        "/TR", '"%s" "%s"' % (PYTHON, script),
        "/RL", "LIMITED",
        "/F",
    ] + trigger_args
    print("Creating:", name)
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout.strip() or r.stderr.strip()
    print(" ", out)
    ok = r.returncode == 0
    if ok:
        q = subprocess.run(["schtasks", "/Query", "/TN", name], capture_output=True, text=True)
        for line in (q.stdout + q.stderr).splitlines():
            if any(k in line for k in ("TaskName", "Next Run", "Status")):
                print("  ", line.strip())
    else:
        print("  could not register automatically. Manual one-liner:")
        print('  schtasks /Create %s /TN "%s" /TR "\\"%s\\" \\"%s\\"" /RL LIMITED /F'
              % (" ".join(trigger_args), name, PYTHON, script))
    return ok


def main():
    if not (WATCHDOG.exists() and AUTONOMOUS.exists()):
        print("missing watchdog or autonomous script in", SCRAPER_DIR)
        return 1

    # Watchdog: every 15 minutes + fire at startup.
    ok1 = create_task(WATCHDOG_TASK,
                      ["/SC", "MINUTE", "/MO", "15"],
                      WATCHDOG)
    # Also start the services at boot so the 15-min tick is a repair, not the
    # sole starter. ONSTART re-uses the watchdog (it starts any service that's
    # down, so it is exactly a boot-time "make sure everything is up").
    create_task("ScoutVeda Maxun Boot Start",
                ["/SC", "ONSTART"],
                WATCHDOG)
    ok2 = create_task(SCRAPE_TASK,
                      ["/SC", "HOURLY"],
                      AUTONOMOUS)

    print("\nSummary: watchdog=%s hourly=%s" % ("OK" if ok1 else "FAIL", "OK" if ok2 else "FAIL"))
    print("\nSelf-heal chain: watchdog (15 min) -> manager starts any dead service;")
    print("hourly scrape -> runs all robots. Boot task -> services up after reboot.")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())
