"""Ship new scrape rows to ScoutVeda, and notice when they stop arriving.

Runs hourly rather than only after a scrape. It is a no-op when there is
nothing new, so the cost is one cheap check -- and in exchange a missed tick, a
Render cold start, or a failed push all self-heal on the next hour instead of
waiting twelve hours for the next scrape.

The addition over the old push.sh is backlog awareness. push_to_scoutveda.py
moves a marker file forward only after a successful send, which makes it safe
to re-run, but it also means a persistently failing push looks like a quiet
no-op from outside: rows pile up in SQLite, the API keeps serving yesterday's
data, and nothing says so. Here the gap between the newest local row and the
marker is measured every hour, so a stuck pipe is visible while it is still
one hour of data rather than one month.
"""
import os
import sqlite3
import subprocess

from .. import config

# One scrape produces ~15 rows, so an hour of backlog is at most ~30. This
# tolerates a full day of failed pushes before shouting, which is enough to
# ride out a Render outage without waking anyone, and far short of the point
# where catching up becomes a problem.
BACKLOG_ALERT = 400


def _backlog():
    """(unpushed_rows, newest_local_id) -- how far behind the marker is."""
    marker_path = config.DATA_DIR / ".pushed_id"
    try:
        marker = int(marker_path.read_text().strip())
    except (OSError, ValueError):
        marker = 0
    if not config.DB_PATH.exists():
        return 0, 0
    conn = sqlite3.connect(str(config.DB_PATH))
    try:
        pending = conn.execute(
            "SELECT COUNT(*) FROM price_history WHERE id > ? AND ok = 1",
            (marker,)).fetchone()[0]
        newest = conn.execute("SELECT COALESCE(MAX(id), 0) FROM price_history").fetchone()[0]
        return pending, newest
    except sqlite3.Error:
        return 0, 0
    finally:
        conn.close()


def run(args):
    before, _ = _backlog()
    env = dict(os.environ)
    key = config.api_key()
    if not key:
        return {"ok": False, "event": "no-api-key",
                "message": "SCOUT_API_KEY is not set and no key file was found, "
                           "so nothing can be pushed."}
    env["SCOUT_API_KEY"] = key

    proc = subprocess.run(
        [config.PYTHON, "push_to_scoutveda.py", *args],
        cwd=str(config.SCOUT_DIR), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = (proc.stdout or "").strip()
    if output:
        print(output)

    after, newest = _backlog()

    if proc.returncode != 0:
        severity = "error" if before >= BACKLOG_ALERT else "warn"
        return {"ok": False, "severity": severity, "event": "push-failed",
                "rc": proc.returncode, "backlog": before,
                "message": f"push failed (rc={proc.returncode}) with {before} "
                           f"row(s) waiting. {output.splitlines()[-1] if output else ''}"}

    if after >= BACKLOG_ALERT:
        # Exited zero but the backlog did not clear. Worth its own event: it
        # means the push is succeeding at the transport level while the data
        # is not actually moving, which no exit code will ever tell you.
        return {"ok": False, "severity": "warn", "event": "push-backlog",
                "backlog": after, "newest_id": newest,
                "message": f"push reported success but {after} rows are still "
                           "unsent. The marker is not advancing."}

    moved = max(before - after, 0)
    return {"ok": True, "pushed": moved, "backlog": after, "newest_id": newest,
            "message": f"{moved} row(s) pushed, {after} pending"}
