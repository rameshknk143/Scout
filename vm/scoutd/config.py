"""Paths, secrets and constants for everything that runs on the scraping VM.

One module so that no task hardcodes a path, and so the whole layout can be
pointed somewhere else (a rebuilt VM, a test box) by environment alone.

Stdlib only, deliberately. scoutd is the layer that reports when the rest of
the system is broken, so it must not be able to break for the same reasons --
a pip resolution failure or a half-upgraded virtualenv has to leave the
reporting path working.
"""
import datetime
import os
from pathlib import Path

HOME = Path(os.environ.get("SCOUTD_HOME", "/home/ubuntu"))

# The existing scraper. scoutd supervises it, it does not replace it: the
# scraping logic is proven and the value here is in how it gets run.
SCOUT_DIR = Path(os.environ.get("SCOUT_DIR", HOME / "scout"))
DATA_DIR = Path(os.environ.get("SCOUT_DATA", SCOUT_DIR / "data"))
DB_PATH = DATA_DIR / "scout.db"

# scoutd's own state: locks, run records, backups. Kept apart from the
# scraper's data so that "what did the platform do" and "what did it collect"
# are never tangled together.
STATE_DIR = Path(os.environ.get("SCOUTD_STATE", HOME / "scoutd-state"))
LOG_DIR = STATE_DIR / "logs"
BACKUP_DIR = STATE_DIR / "backups"

PYTHON = os.environ.get("SCOUT_PYTHON", str(HOME / "ocienv" / "bin" / "python"))

API_BASE = os.environ.get("SCOUT_API_URL",
                          "https://scout-api-3yvy.onrender.com").rstrip("/")

# The VM's own public IP, for the tunnel checks: a request that comes back
# through the tunnel reporting this address means traffic is looping home
# instead of exiting via the phone.
VM_PUBLIC_IP = os.environ.get("SCOUT_VM_PUBLIC_IP", "140.245.239.162")

# Every human-facing time in this project is IST. The VM runs UTC, so anything
# written for a person to read is converted at the edge rather than leaving Ram
# to add 5:30 in his head at the exact moment something is broken.
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30), "IST")

COMPONENT_PREFIX = "vm"


def api_key():
    """The ScoutVeda API key, or None.

    Read from the file at call time rather than captured at import, so rotating
    the key is a file write and a restart of nothing. SCOUT_API_KEY in the
    environment wins, which is what the systemd EnvironmentFile supplies.

    .strip() is load-bearing and has bitten this project before: a key stored
    with a trailing newline makes urllib raise "Invalid header value", which
    presents as the API rejecting everything rather than as a local typo.
    """
    from_env = os.environ.get("SCOUT_API_KEY", "").strip()
    if from_env:
        return from_env
    for candidate in (SCOUT_DIR / ".scout_api_key", HOME / ".config" / "scoutd" / "api_key"):
        try:
            value = candidate.read_text().strip()
            if value:
                return value
        except OSError:
            continue
    return None


def now_ist():
    return datetime.datetime.now(IST)


def stamp():
    """Timestamp for log lines: IST, since a human reads these."""
    return now_ist().strftime("%Y-%m-%d %H:%M:%S IST")


def ensure_dirs():
    for path in (STATE_DIR, LOG_DIR, BACKUP_DIR):
        path.mkdir(parents=True, exist_ok=True)
