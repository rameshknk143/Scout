"""
Laptop half of the hybrid.

The VM handles the 24/7 half: scout-scraper on cron, pushed to ScoutVeda hourly
by scout/push.sh. It is deliberately lightweight - 956 MB of RAM cannot run a
browser, so it only does HTTP fetches of a fixed watchlist.

The laptop is the only place with enough memory for Maxun and a real browser, so
it does the work the VM physically cannot: visual robots over bestseller lists.
But it is only on about an hour a day at unpredictable times, so this script is
built to make an arbitrary short window productive and to lose nothing when the
window closes.

What it does, in order:

  1. Health-check Maxun - and actually repair the known silent failure. The
     browser service's /health reports a CACHED wsEndpoint string, so it says
     "healthy" even when its Chromium has died and port 3001 is unbound. This
     probes the port itself and restarts the service if it is really down.
  2. Trigger a robot run, but at most once every TRIGGER_EVERY_HOURS, so a
     laptop that goes on and off five times in a day does not scrape Amazon
     five times.
  3. Forward every run that has not been forwarded yet - including runs from
     previous sessions. This is the "no loss" part and is cheap, so it happens
     on every invocation regardless of whether a new run was triggered.

    python laptop_mode.py                # full pass
    python laptop_mode.py --forward-only # skip scraping, just catch up
    python laptop_mode.py --force-run    # ignore the trigger throttle
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
STATE = HERE / ".laptop_mode_state.json"

# 127.0.0.1 deliberately - see the note in maxun_bridge.py. localhost resolves
# to ::1 first on Windows, which lets any IPv6 listener shadow Maxun.
MAXUN_API_URL = os.environ.get("MAXUN_API_URL", "http://127.0.0.1:8080").rstrip("/")
MAXUN_API_KEY = os.environ.get("MAXUN_API_KEY")
MAXUN_ROBOT_ID = os.environ.get("MAXUN_ROBOT_ID")
BROWSER_DIR = Path(os.environ.get(
    "MAXUN_BROWSER_DIR",
    r"D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research"
    r"\self-hosted-stack\maxun\browser"))

TRIGGER_EVERY_HOURS = float(os.environ.get("TRIGGER_EVERY_HOURS", "12"))
CATEGORY = os.environ.get("SCOUT_CATEGORY", "Grocery & Gourmet")
LIST_TYPE = os.environ.get("SCOUT_LIST_TYPE", "bestsellers")


def log(msg):
    print("%s  %s" % (datetime.now().strftime("%H:%M:%S"), msg), flush=True)


def port_open(port, host="127.0.0.1", timeout=3):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(st):
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")


def repair_browser_service():
    """Restart the Maxun browser service so port 3001 rebinds.

    Playwright's launchServer ties the WS listener to a spawned Chromium. When
    that Chromium dies the port goes with it while the Node process - and its
    health endpoint - survive, so nothing reports the failure.
    """
    log("port 3001 is down - restarting the browser service")
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-NetTCPConnection -LocalPort 3002 -State Listen -ErrorAction SilentlyContinue "
         "| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"],
        capture_output=True,
    )
    time.sleep(2)
    subprocess.Popen(
        ["node", "dist/server.js"],
        cwd=str(BROWSER_DIR),
        stdout=open(BROWSER_DIR / "browser-service.log", "ab"),
        stderr=open(BROWSER_DIR / "browser-service.err.log", "ab"),
        creationflags=0x00000008 | 0x00000200,  # detached, no window
    )
    for _ in range(30):
        if port_open(3001):
            log("browser service is back, 3001 bound")
            return True
        time.sleep(1)
    log("browser service did NOT come back on 3001")
    return False


def health_check():
    """Return True when Maxun can actually run a robot."""
    checks = {
        "postgres 5432": port_open(5432),
        "backend 8080": port_open(8080),
        "browser ws 3001": port_open(3001),
        "browser health 3002": port_open(3002),
        "minio 9000": port_open(9000),
    }
    for name, ok in checks.items():
        log("  %-20s %s" % (name, "up" if ok else "DOWN"))

    if not checks["browser ws 3001"] and checks["browser health 3002"]:
        # The exact silent-failure signature: health port alive, WS port dead.
        if not repair_browser_service():
            return False
        checks["browser ws 3001"] = True

    essential = ["postgres 5432", "backend 8080", "browser ws 3001"]
    missing = [k for k in essential if not checks[k]]
    if missing:
        log("cannot run: %s still down. Start Maxun first." % ", ".join(missing))
        return False
    return True


def trigger_run():
    log("triggering a Maxun robot run (this blocks until it finishes)")
    req = urllib.request.Request(
        "%s/api/robots/%s/runs" % (MAXUN_API_URL, MAXUN_ROBOT_ID),
        data=b"{}",
        headers={"x-api-key": MAXUN_API_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            body = json.loads(resp.read().decode())
        run = body.get("run") or {}
        log("run %s finished with status=%s" % (run.get("runId"), run.get("status")))
        return True
    except urllib.error.HTTPError as e:
        log("trigger failed HTTP %s: %s" % (e.code, e.read().decode(errors="replace")[:200]))
    except Exception as e:
        log("trigger failed: %s" % e)
    return False


def forward():
    """Hand off to the bridge, which already tracks what it has forwarded."""
    log("forwarding any unforwarded runs")
    r = subprocess.run(
        [sys.executable, str(HERE / "maxun_bridge.py"),
         "--category", CATEGORY, "--list-type", LIST_TYPE],
        cwd=str(HERE), capture_output=True, text=True,
    )
    for line in (r.stdout or "").splitlines():
        log("  " + line)
    if r.returncode != 0:
        for line in (r.stderr or "").splitlines()[-5:]:
            log("  ! " + line)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forward-only", action="store_true",
                    help="do not scrape; just push anything outstanding")
    ap.add_argument("--force-run", action="store_true",
                    help="trigger a run even if one happened recently")
    args = ap.parse_args()

    if not (MAXUN_API_KEY and MAXUN_ROBOT_ID):
        sys.exit("MAXUN_API_KEY and MAXUN_ROBOT_ID must be set.")

    log("laptop mode starting")
    st = load_state()

    if not health_check():
        # Still worth trying to forward: earlier runs may be sitting unsent and
        # forwarding needs nothing from Maxun's browser.
        log("health check failed - attempting forward-only catch-up anyway")
        forward()
        return

    if args.forward_only:
        log("--forward-only: skipping the scrape")
    else:
        last = st.get("last_trigger_utc")
        due = True
        if last and not args.force_run:
            try:
                elapsed = datetime.now(timezone.utc) - datetime.fromisoformat(last)
                due = elapsed >= timedelta(hours=TRIGGER_EVERY_HOURS)
                if not due:
                    log("last run was %s ago; throttle is %sh, skipping the scrape"
                        % (str(elapsed).split(".")[0], TRIGGER_EVERY_HOURS))
            except Exception:
                due = True
        if due:
            if trigger_run():
                st["last_trigger_utc"] = datetime.now(timezone.utc).isoformat()
                save_state(st)

    forward()
    st["last_pass_utc"] = datetime.now(timezone.utc).isoformat()
    save_state(st)
    log("laptop mode done")


if __name__ == "__main__":
    main()
