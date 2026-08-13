"""Run the watchlist scrape and judge whether the result was actually usable.

The scraper itself is unchanged and stays where it is. What this adds is a
verdict: scrape.py exits 0 whether it captured 15 of 15 targets or 2 of 15,
because from its point of view a blocked request is a handled condition, not a
crash. Under the old cron wrapper that meant a pass which collected almost
nothing looked identical to a good one, and the only way to tell them apart was
to read cron.log over SSH -- which is a person doing a computer's job.

So the verdict comes from the database rather than from the exit code or from
parsing stdout: count the distinct ASINs that actually landed as ok=1 rows
during this run's window. That is the number that decides whether price history
is being built, and it cannot be faked by a scraper that fails politely.
"""
import os
import sqlite3
import subprocess
import time

from .. import config


def _targets():
    """How many ASINs the run was supposed to cover."""
    path = config.SCOUT_DIR / "targets.txt"
    try:
        lines = [ln.strip() for ln in path.read_text().splitlines()]
    except OSError:
        return 0
    return len([ln for ln in lines if ln and not ln.startswith("#")])


def _landed_since(started_epoch):
    """Distinct ASINs successfully captured since the run began."""
    if not config.DB_PATH.exists():
        return 0, 0
    started_utc = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(started_epoch - 60))
    conn = sqlite3.connect(str(config.DB_PATH))
    try:
        ok = conn.execute(
            "SELECT COUNT(DISTINCT asin) FROM price_history "
            "WHERE ok = 1 AND scraped_at >= ?", (started_utc,)).fetchone()[0]
        attempted = conn.execute(
            "SELECT COUNT(DISTINCT asin) FROM price_history "
            "WHERE scraped_at >= ?", (started_utc,)).fetchone()[0]
        return ok, attempted
    except sqlite3.Error:
        return 0, 0
    finally:
        conn.close()


def run(args):
    started = time.time()
    want = _targets()
    env = dict(os.environ)
    env.setdefault("SCOUT_API_KEY", config.api_key() or "")

    proc = subprocess.run(
        [config.PYTHON, "scrape.py", *args],
        cwd=str(config.SCOUT_DIR), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = (proc.stdout or "").strip()
    if output:
        print(output)

    # The scraper skips its own run when the last attempt was too recent. That
    # is the MIN_GAP_HOURS guard doing its job, not a failure -- amazon.in
    # rate-limits this datacenter IP on the gap since the last request, so a
    # skipped run is what protects the next real one.
    if "skipping:" in output:
        return {"ok": True, "skipped": True,
                "message": "skipped by the minimum-gap guard (working as intended)"}

    got, attempted = _landed_since(started)

    if proc.returncode == 2:
        return {"ok": True, "severity": "warn", "event": "tunnel-down",
                "landed": got, "targets": want,
                "message": "scrape skipped: the phone tunnel is down. This is "
                           "expected -- the tunnel is optional and the VM's own "
                           "IP works when runs are spaced far enough apart."}

    if proc.returncode != 0:
        return {"ok": False, "event": "scrape-crashed", "rc": proc.returncode,
                "landed": got, "targets": want,
                "message": f"scrape.py exited {proc.returncode}. "
                           f"{got} of {want} targets landed. "
                           f"Last output: {output.splitlines()[-1] if output else '(none)'}"}

    # Half the list is the line. Below it the pass is not producing usable price
    # history. warn, not error: the cause is almost always amazon.in refusing
    # the datacenter IP, which recovers on its own by the next run, and paging
    # about a condition that self-heals in twelve hours trains people to ignore
    # the alerts that matter.
    if want and got < want / 2:
        return {"ok": False, "severity": "warn", "event": "low-scrape-yield",
                "landed": got, "attempted": attempted, "targets": want,
                "message": f"only {got} of {want} targets landed. amazon.in is "
                           "likely refusing this VM's datacenter IP; it usually "
                           "clears by the next run."}

    return {"ok": True, "landed": got, "attempted": attempted, "targets": want,
            "message": f"{got} of {want} targets landed"}
