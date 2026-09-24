"""
Maxun watchdog — restart any Maxun service that is down.

Designed to be fired by Windows Task Scheduler every 15 minutes AND at
boot/logon (see register_maxun_task.py). Idempotent: already-running services
are skipped, only dead ones are (re)started. Appends one timestamped line per
fire to .maxun_watchdog.log so "was it watching?" has a paper trail.

    python maxun_watchdog.py            # check + repair + log
    python maxun_watchdog.py --check    # status only, no log
"""
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SCRAPER_DIR = Path(__file__).resolve().parent
MANAGER = SCRAPER_DIR / "maxun_service_manager.py"
LOG_FILE = SCRAPER_DIR / ".maxun_watchdog.log"


def main():
    ap = argparse.ArgumentParser(description="Maxun watchdog")
    ap.add_argument("--check", action="store_true", help="report status only, do not start services")
    args = ap.parse_args()

    import socket

    def up(port):
        s = socket.socket(); s.settimeout(3)
        ok = s.connect_ex(("127.0.0.1", port)) == 0
        s.close()
        return ok

    def critical():
        # backend + browser are load-bearing; frontend is cosmetic-only.
        return up(8080) and up(3002)

    def state():
        return ("backend=%s browser=%s frontend=%s" % (
            "UP" if up(8080) else "DOWN",
            "UP" if up(3002) else "DOWN",
            "UP" if up(5173) else "DOWN"))

    was_down = not critical()
    before = state()

    if args.check:
        print(before)
        return 0 if critical() else 1

    if not MANAGER.exists():
        print("maxun_service_manager.py missing:", MANAGER)
        return 1

    # The manager is idempotent: it starts only what is down.
    subprocess.run([sys.executable, str(MANAGER), "start"],
                   capture_output=True, text=True, timeout=90)

    after = state()
    ok = critical()
    status = "OK" if not was_down else ("REPAIRED" if ok else "STILL-DOWN")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s | before: %s | after: %s" % (now, status, before, after)
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > 200_000:
            LOG_FILE.write_text("\n".join(LOG_FILE.read_text().splitlines()[-500:]) + "\n")
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
