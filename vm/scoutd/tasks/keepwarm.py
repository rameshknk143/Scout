"""Keep the Render free-tier API awake during the hours people use it.

Render sleeps a free service after ~15 minutes idle and the next visitor waits
about 42 seconds. GitHub Actions was meant to do this ping, but its scheduler
is best-effort: measured on 2 Aug 2026, the API was still cold after only ~25
minutes idle, so the gaps were stretching past 15. Cron on this box was exact;
a systemd timer is exact too, and costs nothing, since the VM is up anyway.

The window is deliberate, not laziness. Render's free tier allows 750 instance
hours a month; pinging around the clock keeps the service awake for ~730 of
them, which leaves no margin at all. The 02:00-19:59 UTC window (07:30-01:29
IST) covers every waking hour in India and uses roughly 547 hours.

This task never fails loudly. A cold API is a slow page load, not lost data,
and an alert for it at three in the morning would be a false emergency.
"""
import json
import socket
import urllib.error
import urllib.request

from .. import config

TIMEOUT = 120       # generous: a cold start is the case being paid for here


def run(args):
    url = f"{config.API_BASE}/health"
    request = urllib.request.Request(url, headers={"User-Agent": "scoutd-keepwarm"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            status = response.status
            body = json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        status, body = exc.code, None
    except (urllib.error.URLError, socket.timeout, ValueError, OSError) as exc:
        # Reported as a warning, and only after the health task has seen it
        # several times in a row -- see tasks/health.py. One failed ping is
        # almost always Render restarting a free dyno.
        return {"ok": True, "reachable": False, "status": 0,
                "message": f"API unreachable ({type(exc).__name__}); "
                           "not alerting on a single miss"}

    if status != 200 or body != {"ok": True}:
        return {"ok": True, "reachable": False, "status": status,
                "message": f"/health returned {status} {body!r}"}
    return {"ok": True, "reachable": True, "status": 200, "message": "warm"}
