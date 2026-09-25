"""
Maxun autonomous runner — trigger every configured Amazon robot, then forward
each robot's new runs into ScoutVeda via maxun_bridge.py.

Designed to run unattended (Windows Task Scheduler, hourly). It:
  1. Ensures the three Maxun services are up (backend :8080, browser :3001/3002,
     frontend :5173).
  2. Triggers every robot in MAXUN_ROBOTS (laptop.env) via the live SDK
     execute endpoint, which returns the scraped rows synchronously.
  3. Forwards each robot's new successful runs to ScoutVeda by invoking
     maxun_bridge.py (which de-dupes via .maxun_bridge_state.json).

Reads config from scraper/laptop.env (loaded at import). Exits 0 when at least
one robot forwarded rows; exits 1 when nothing could run. Prints a compact log.

    python maxun_autonomous.py            # run all robots once
    python maxun_autonomous.py --limit 2  # only the first 2 robots
    python maxun_autonomous.py --no-start # skip the service auto-start
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

SCRAPER_DIR = Path(__file__).resolve().parent

# ---- load laptop.env (do not override vars already in the environment) ----
def _load_env():
    for cand in (SCRAPER_DIR / "laptop.env", SCRAPER_DIR / ".env"):
        if not cand.exists():
            continue
        for line in cand.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
        break
_load_env()

MAXUN_API_URL = os.environ.get("MAXUN_API_URL", "http://127.0.0.1:8080").rstrip("/")
MAXUN_API_KEY = os.environ.get("MAXUN_API_KEY", "")
SCOUT_API_URL = os.environ.get("SCOUT_API_URL", "https://scout-api-3yvy.onrender.com").rstrip("/")
SCOUT_API_KEY = os.environ.get("SCOUT_API_KEY", "")

# ---- overlap lock ------------------------------------------------------------
# The hourly scheduler can fire while a previous pass is still running (or while
# the watchdog / a manual run holds the services). Two passes at once = two
# browser sessions hammering the same robots, which is what surfaced as
# Last Result -1 / stuck "Running" on the Windows task. A lock file with a
# stale-detection window makes overlap impossible: a second run exits 0
# immediately (nothing lost — the first pass owns the work), and a crashed
# pass cannot hold the lock past STALE_AFTER so the next tick self-heals.
LOCK_FILE = SCRAPER_DIR / ".maxun_pass.lock"
STALE_AFTER = 90 * 60  # a healthy pass finishes in ~6 min; 90 min = crashed


def acquire_lock() -> bool:
    import json as _json
    now = time.time()
    try:
        if LOCK_FILE.exists():
            age = now - LOCK_FILE.stat().st_mtime
            if age < STALE_AFTER:
                log("Pass already running (lock %ds old) — skipping this tick." % int(age))
                return False
            log("Stale lock (%dm old) — clearing and taking over." % int(age // 60))
    except OSError:
        pass
    try:
        LOCK_FILE.write_text(_json.dumps({
            "pid": os.getpid(), "started": datetime.now(timezone.utc).isoformat(),
        }))
        return True
    except OSError as e:
        log("Could not write lock: %s" % e)
        return True  # proceed anyway; dedupe in the bridge still guards


def release_lock():
    try:
        LOCK_FILE.unlink()
    except OSError:
        pass

# MAXUN_ROBOTS format: "ID1=Category1;ID2=Category2;..."
def parse_robots():
    raw = os.environ.get("MAXUN_ROBOTS", "")
    out = []
    for part in raw.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        rid, cat = part.split("=", 1)
        out.append((rid.strip(), cat.strip()))
    if not out:
        single = os.environ.get("MAXUN_ROBOT_ID", "")
        if single:
            out.append((single, os.environ.get("SCOUT_CATEGORY", "Beauty & Personal Care")))
    return out


def log(msg):
    print("[%s] %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg), flush=True)


def services_healthy():
    """Return True when backend + browser are reachable."""
    try:
        backend = requests.get(MAXUN_API_URL, timeout=5)
    except Exception:
        backend = None
    try:
        browser = requests.get("http://127.0.0.1:3002/health", timeout=5)
    except Exception:
        browser = None
    return backend is not None and browser is not None


def ensure_services():
    log("Checking Maxun services...")
    if services_healthy():
        log("  backend :8080 OK, browser :3002 OK")
        return True
    log("  a service is down — starting the stack...")
    mgr = SCRAPER_DIR / "maxun_service_manager.py"
    if mgr.exists():
        subprocess.run([sys.executable, str(mgr), "start"],
                       capture_output=True, text=True, timeout=60)
        time.sleep(5)
    return services_healthy()


def trigger_robot(robot_id):
    """Trigger a robot; returns runId or None. The SDK execute call returns the
    scraped rows synchronously (~8s), so the run is essentially complete here."""
    headers = {"x-api-key": MAXUN_API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(
            "%s/api/sdk/robots/%s/execute" % (MAXUN_API_URL, robot_id),
            headers=headers, json={}, timeout=60)
    except Exception as e:
        log("  execute failed: %s" % type(e).__name__)
        return None
    if resp.status_code == 200:
        d = resp.json().get("data", {})
        return d.get("runId")
    log("  execute HTTP %s: %s" % (resp.status_code, resp.text[:120]))
    return None


def wait_for_run(robot_id, run_id, timeout=90):
    """The execute call returns the rows immediately, but the run's data persists
    asynchronously into the listing the bridge reads. Poll until this run shows
    status=success so the bridge's detail fetch finds its rows."""
    headers = {"x-api-key": MAXUN_API_KEY}
    start = time.time()
    while time.time() - start < timeout:
        try:
            listing = requests.get(
                "%s/api/robots/%s/runs" % (MAXUN_API_URL, robot_id),
                headers=headers, timeout=15).json()
        except Exception:
            time.sleep(4)
            continue
        items = listing.get("runs", {}).get("items", [])
        target = next((it for it in items if it.get("runId") == run_id), None)
        if target and str(target.get("status", "")).lower() in ("success", "completed"):
            return True
        time.sleep(4)
    return False


def forward_robot(robot_id, category, run_id):
    """Invoke the bridge for one robot, pinning the exact run we just triggered so
    we extract the rows the execute call already produced."""
    if not wait_for_run(robot_id, run_id):
        log("  %s -> %s: run did not reach success in time; will catch it next pass"
            % (category, robot_id[:8]))
        return 0
    env = dict(os.environ)
    env["SCOUT_API_KEY"] = SCOUT_API_KEY
    env["MAXUN_API_KEY"] = MAXUN_API_KEY
    cmd = [sys.executable, str(SCRAPER_DIR / "maxun_bridge.py"),
           "--robot-id", robot_id, "--run-id", run_id, "--category", category]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
    m = re.search(r'"inserted"\s*:\s*(\d+)', r.stdout)
    inserted = int(m.group(1)) if m else 0
    if inserted:
        log("  %s -> %s: forwarded (inserted=%d)" % (category, robot_id[:8], inserted))
    else:
        log("  %s -> %s: no new rows (bridge: %s)"
            % (category, robot_id[:8], (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "n/a")))
    return inserted


def main():
    ap = argparse.ArgumentParser(description="Run all configured Maxun robots and forward results.")
    ap.add_argument("--limit", type=int, default=0, help="max robots to run this pass (0 = all)")
    ap.add_argument("--no-start", action="store_true", help="skip the service auto-start")
    ap.add_argument("--force", action="store_true",
                   help="take the lock even if a fresh one exists (manual override)")
    args = ap.parse_args()

    if not args.force and not acquire_lock():
        # A pass already owns the work for this tick. Exiting 0 keeps the
        # scheduler quiet; the running pass will deliver the rows.
        log("SKIP: another pass is running. Next tick will pick up anything new.")
        return 0
    try:
        robots = parse_robots()
        if args.limit:
            robots = robots[:args.limit]
        if not robots:
            log("No robots configured. Set MAXUN_ROBOTS in laptop.env. Nothing to do.")
            return 1

        if not MAXUN_API_KEY:
            log("MAXUN_API_KEY missing in laptop.env. Cannot proceed.")
            return 1

        if not args.no_start:
            if not ensure_services():
                log("Services still down after auto-start. Aborting this pass.")
                return 1

        log("Running %d robot(s)..." % len(robots))
        total_inserted = 0
        ok_robots = 0
        for rid, cat in robots:
            log("--- %s ---" % cat)
            run_id = trigger_robot(rid)
            if not run_id:
                log("  trigger failed; skipping forward")
                time.sleep(5)
                continue
            time.sleep(3)  # let the run fully land in Maxun's store
            total_inserted += forward_robot(rid, cat, run_id)
            ok_robots += 1
            time.sleep(10)  # be polite to Amazon between robots

        log("=" * 52)
        log("PASS DONE: %d/%d robots, %d rows forwarded to ScoutVeda"
            % (ok_robots, len(robots), total_inserted))
        log("=" * 52)
        return 0 if total_inserted > 0 else 1
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())
