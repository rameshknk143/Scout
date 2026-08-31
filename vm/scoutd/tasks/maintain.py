"""The nightly janitor: back up the data, then clean up after everything.

Long-term stability on a small box is not an architecture problem, it is a
housekeeping problem. Nothing here is clever; all of it is the set of things
that, left undone, quietly kill an unattended Linux box over six months:

  logs        Five append-only logs with no rotation. tunnel-watch.log alone
              adds ~11 kB a day forever. None of them is dangerous this month,
              and together they are unbounded, which is the only property that
              matters over six months.
  /tmp        Playwright leaves profile directories behind when a browser is
              killed rather than closed -- which is exactly what happens on a
              timeout or an OOM kill, so the mess accumulates fastest at
              precisely the times the box can least afford it.
  journal     systemd's journal is capped by default, but at 10% of a 45 GB
              disk. That is 4.5 GB of logs on a box with 956 MB of RAM.
  SQLite      Deleted pages are never returned to the OS without a VACUUM, and
              an unchecked database can carry corruption for months before
              anything reads the damaged page.
  ops_events  Bounded by retention on the API side, but the API sleeps on the
              free tier and cannot run its own cleanup, so it is triggered
              from here -- the VM is the only always-on component.

BACKUP FIRST, ALWAYS. Every destructive step in this file runs after the
backup, so the worst case of a bug here is a wasted night, not lost history.
"""
import gzip
import os
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path

from .. import config, ops

# Logs the old cron scripts write, which nothing rotates. Trimmed to the last
# N lines rather than deleted: recent history is what diagnoses a problem, and
# the whole file is never needed.
LEGACY_LOGS = {
    "scout/data/cron.log": 3000,
    "scout/data/scrape.log": 4000,
    "scout/data/push.log": 2000,
    "scout/data/discover.log": 500,
    "tunnel-watch.log": 1000,
    "keep-warm.log": 2000,
    "arm-retry.log": 1000,
}

BACKUP_KEEP = 14            # two weeks of nightly snapshots
JOURNAL_MAX = "200M"
TMP_AGE_HOURS = 24


def _trim_logs():
    """Cap each legacy log at its last N lines. Returns bytes reclaimed.

    Writes a new file and renames it over the old one, so a process appending
    to the log keeps working; truncating in place would leave a writer's file
    offset past the new end and produce a file padded with null bytes.
    """
    reclaimed = 0
    for relative, keep in LEGACY_LOGS.items():
        path = config.HOME / relative
        try:
            before = path.stat().st_size
        except OSError:
            continue
        try:
            with path.open("r", errors="replace") as handle:
                lines = handle.readlines()
            if len(lines) <= keep:
                continue
            temp = path.with_suffix(path.suffix + ".trim")
            temp.write_text("".join(lines[-keep:]))
            os.replace(temp, path)
            reclaimed += before - path.stat().st_size
        except OSError as exc:
            ops._local_note(f"could not trim {path}: {exc}")
    return reclaimed


def _backup_db():
    """Consistent online snapshot of scout.db, gzipped, dated.

    sqlite3's backup API rather than a file copy: a copy taken while a scrape
    is mid-write produces a torn database that looks fine until it is needed.
    This is cheap here (the file is well under a megabyte) and it is the only
    copy of the local price history that exists off the live file.
    """
    if not config.DB_PATH.exists():
        return None
    config.ensure_dirs()
    target = config.BACKUP_DIR / f"scout-{time.strftime('%Y%m%d')}.db.gz"
    staging = config.BACKUP_DIR / "staging.db"
    try:
        source = sqlite3.connect(str(config.DB_PATH))
        dest = sqlite3.connect(str(staging))
        with dest:
            source.backup(dest)
        dest.close()
        source.close()
        with open(staging, "rb") as raw, gzip.open(target, "wb", compresslevel=6) as out:
            shutil.copyfileobj(raw, out)
        return target
    except (sqlite3.Error, OSError) as exc:
        ops._local_note(f"backup failed: {exc}")
        return None
    finally:
        try:
            staging.unlink()
        except OSError:
            pass


def _prune_backups():
    backups = sorted(config.BACKUP_DIR.glob("scout-*.db.gz"))
    removed = 0
    for old in backups[:-BACKUP_KEEP] if len(backups) > BACKUP_KEEP else []:
        try:
            old.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def _check_and_vacuum():
    """Integrity check, then reclaim free pages. Returns (status, bytes freed).

    quick_check rather than integrity_check: it catches the corruption that
    actually happens (torn pages, bad indexes) in a fraction of the time, and
    this runs unattended every night rather than as a forensic tool.
    """
    if not config.DB_PATH.exists():
        return "missing", 0
    before = config.DB_PATH.stat().st_size
    conn = sqlite3.connect(str(config.DB_PATH), timeout=30)
    try:
        result = conn.execute("PRAGMA quick_check").fetchone()[0]
        if result != "ok":
            # Do not vacuum a damaged database -- rewriting it can turn a
            # recoverable problem into an unrecoverable one. Report and stop.
            ops.alert("maintain", "error", "db-corrupt",
                      f"sqlite quick_check on scout.db returned: {result}. "
                      "Left untouched; restore from the nightly backup in "
                      f"{config.BACKUP_DIR}.",
                      detail={"quick_check": str(result)[:400]})
            return result, 0
        conn.execute("VACUUM")
        conn.execute("PRAGMA optimize")
    except sqlite3.Error as exc:
        return f"error: {exc}", 0
    finally:
        conn.close()
    return "ok", max(before - config.DB_PATH.stat().st_size, 0)


def _clean_tmp():
    """Remove Playwright leftovers older than a day. Returns bytes reclaimed."""
    reclaimed, cutoff = 0, time.time() - TMP_AGE_HOURS * 3600
    patterns = ("playwright*", ".org.chromium.*", "chrome_*", "puppeteer_*")
    for pattern in patterns:
        for path in Path("/tmp").glob(pattern):
            try:
                if path.stat().st_mtime > cutoff:
                    continue
                size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) \
                    if path.is_dir() else path.stat().st_size
                shutil.rmtree(path, ignore_errors=True) if path.is_dir() else path.unlink()
                reclaimed += size
            except OSError:
                continue
    return reclaimed


def _vacuum_journal():
    try:
        subprocess.run(["journalctl", f"--vacuum-size={JOURNAL_MAX}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=120, check=False)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def run(args):
    started = time.time()
    backup = _backup_db()
    pruned = _prune_backups()
    integrity, vacuumed = _check_and_vacuum()
    log_bytes = _trim_logs()
    tmp_bytes = _clean_tmp()
    _vacuum_journal()

    remote = ops.prune() or {}
    usage = shutil.disk_usage("/")

    reclaimed_mb = round((log_bytes + tmp_bytes + vacuumed) / 1e6, 1)
    ok = integrity in ("ok", "missing") and backup is not None
    message = (f"backup {'ok' if backup else 'FAILED'}, integrity {integrity}, "
               f"{reclaimed_mb} MB reclaimed, {remote.get('deleted', 0)} ops events "
               f"pruned, disk {round(usage.used * 100.0 / usage.total)}% full")

    result = {
        "ok": ok,
        "message": message,
        "backup": backup.name if backup else None,
        "backups_pruned": pruned,
        "integrity": integrity,
        "reclaimed_mb": reclaimed_mb,
        "ops_events_pruned": remote.get("deleted", 0),
        "disk_pct": round(usage.used * 100.0 / usage.total),
        "seconds": round(time.time() - started, 1),
    }

    # Failure labels belong on failures only. This dict is merged into the
    # heartbeat's detail verbatim, so labelling a successful night
    # "maintenance-failed / warn" made every /ops/status reader (and the
    # 31 Aug audit) believe maintenance was broken while it was fine.
    # The event name is "vm-maintain-failed", not the old "maintenance-failed":
    # run.py raises recovery mail under f"{task_name}-failed", and record()
    # only delivers a recovery when a notified fault with the SAME event name
    # exists -- the old mismatch meant a real failure's recovery would have
    # been silently swallowed.
    if not ok:
        result["event"] = "vm-maintain-failed"
        result["severity"] = "warn"
    return result
