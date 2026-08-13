"""The VM's voice: heartbeats and alerts to the ScoutVeda API.

The scraping VM cannot tell anyone anything on its own. It has no mail
transport, and by standing rule it never gets the production DATABASE_URL. So
it reports over the API key it already holds, and the API owns delivery and
history (api/ops.py).

Two channels, and the difference matters:

  heartbeat()  "I ran, here is what happened." Cheap, frequent, overwritten.
               Silence is the signal -- a heartbeat that stops updating is how
               a dead VM gets noticed, because a dead VM cannot send an alert
               about being dead.
  alert()      "Something is wrong and a person should know." Rate-limited at
               the API by (component, event), so a fault that repeats every
               15 minutes for a week does not produce 672 emails.

Everything here fails soft. A monitoring call that raises would take down the
task it was reporting on, which inverts the whole point: the worst outcome of
the API being unreachable must be that Ram is not told, never that collection
stops. Unreported failures are instead written to the local run log, which the
next successful heartbeat carries along.
"""
import json
import socket
import urllib.error
import urllib.request

from . import config

TIMEOUT = 45          # Render free tier cold-starts; this is not a hot path.
RETRIES = 3


def _post(path, payload):
    """POST JSON, retrying briefly. Returns parsed body or None. Never raises.

    Retries exist for one specific reason: the API sleeps after 15 minutes idle
    on the free tier, and the first request after that wakes it and can time
    out. Giving up on the first failure would drop precisely the heartbeats
    sent during quiet periods -- which are the ones that prove the VM is alive
    when nothing else is happening.
    """
    key = config.api_key()
    if not key:
        return None
    body = json.dumps(payload).encode()
    request = urllib.request.Request(
        f"{config.API_BASE}{path}", data=body, method="POST",
        headers={"X-Scout-Key": key, "Content-Type": "application/json",
                 "User-Agent": "scoutd/1.0"})
    last = None
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.loads(response.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            # 4xx will not fix itself by trying again -- a bad key stays bad.
            detail = exc.read().decode(errors="replace")[:200]
            last = f"HTTP {exc.code}: {detail}"
            if exc.code < 500:
                break
        except (urllib.error.URLError, socket.timeout, ValueError, OSError) as exc:
            last = f"{type(exc).__name__}: {exc}"
    if last:
        _local_note(f"ops {path} failed after {RETRIES} tries: {last}")
    return None


def _local_note(message):
    """Last-resort record when the API cannot be reached.

    Goes to stderr, which systemd captures into the journal, so the evidence
    survives even when the network path out is the thing that is broken.
    """
    import sys
    print(f"[{config.stamp()}] scoutd/ops: {message}", file=sys.stderr)


def component(name):
    """Namespaced component id, so API-side and VM-side names cannot collide."""
    return f"{config.COMPONENT_PREFIX}-{name}"


def heartbeat(name, status="ok", detail=None):
    """Record that a component ran. Returns True if the API confirmed it.

    `detail` is an explicit dict rather than **kwargs on purpose. Tasks return
    free-form dicts that legitimately contain keys like "status", "event" and
    "message", and splatting those into a signature that also has parameters by
    those names raises TypeError -- inside the reporting path, which is the one
    piece of this system that must never be the thing that breaks.
    """
    return _post("/ops/heartbeat", {
        "component": component(name), "status": status, "detail": detail or {},
    }) is not None


def alert(name, severity, event, message="", detail=None):
    """Report a fault (or a recovery) worth a person's attention.

    severity: "warn" | "error" | "resolved" | "info"

    Use a stable `event` string -- it is the dedupe key. "scrape-failed" is
    right; "scrape failed at 03:21:44" would defeat suppression entirely and
    mail every occurrence, which is how alerting stops being read.
    """
    result = _post("/ops/alert", {
        "component": component(name), "severity": severity, "event": event,
        "message": message, "detail": detail or {},
    })
    if result is None:
        _local_note(f"UNDELIVERED {severity} {name}/{event}: {message}")
    return result


def prune():
    """Ask the API to drop operational history past its retention window.

    Called from here rather than scheduled on the API because the free tier
    sleeps and cannot be relied on to run anything by itself. The VM is the
    only always-on component, so it owns every recurring job in the system.
    """
    return _post("/ops/prune", {})
