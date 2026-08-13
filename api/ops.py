"""Operational telemetry and alerting for the unattended scraping platform.

This exists because of one requirement: the system has to keep running for six
months while nobody is watching it. Everything else in this file follows from
that, and from two constraints measured on 14 Aug 2026 rather than assumed:

  * The Oracle VM is the always-on component (x86 micro shape, 2 vCPU, 956 MB).
    It can supervise itself, but it cannot tell Ram anything -- it has no mail
    transport and, by standing rule, no production DATABASE_URL.
  * GitHub Actions is a *metered* resource here. The repo is private, and the
    workflows already consume ~1,540 of the 2,000 free minutes a month. So it
    cannot be the thing that polls anything frequently.

Hence: the VM pushes heartbeats and alerts here over the API key it already
holds, this service owns the mail transport and the history, and a cheap
twice-daily workflow reads /ops/status as an outside observer. If the VM dies,
the heartbeat goes stale and the outside observer notices -- which is the one
failure a self-monitoring box can never report on its own.

ALERT STORM PROTECTION is not a nicety here. An unattended system that mails on
every failed tick will send hundreds of messages during a single outage, and the
practical result is that Ram stops reading them -- so the one that matters gets
missed. Repeat alerts for the same (component, event) are suppressed for
ALERT_COOLDOWN_HOURS, and recoveries are always delivered, so a resolved
incident closes itself out in the inbox instead of leaving a scare hanging.
"""
import datetime
import json
import os

import requests
from psycopg2.extras import Json, RealDictCursor

import auth
import db

# How long the same (component, event) stays quiet after it has been reported
# once. Six hours is chosen so a fault that starts overnight is reported once
# when it happens and once more the next morning, rather than 90 times.
ALERT_COOLDOWN_HOURS = float(os.environ.get("ALERT_COOLDOWN_HOURS", "6"))

# Events older than this are pruned by /ops/prune so the table cannot grow
# without bound on a 500 MB free-tier database.
EVENT_RETENTION_DAYS = int(os.environ.get("EVENT_RETENTION_DAYS", "90"))

SEVERITIES = ("info", "warn", "error", "resolved")

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30), "IST")


def _ist(value):
    """Render any timestamp in IST. Every human-facing time in this project is."""
    if value is None:
        return "never"
    if isinstance(value, str):
        try:
            value = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    return value.astimezone(IST).strftime("%d %b %H:%M IST")


def _alert_recipient(conn):
    """Where operational mail goes.

    ALERT_EMAIL wins if set. Otherwise the oldest user account, which on this
    deployment is the owner -- chosen so alerting works the moment this ships,
    with no extra environment variable to remember to set on Render. Returning
    None is not an error: it means mail is not configured, and the caller
    records the event anyway rather than losing it.
    """
    configured = os.environ.get("ALERT_EMAIL", "").strip()
    if configured:
        return configured
    with conn.cursor() as cur:
        cur.execute("SELECT email FROM users ORDER BY id LIMIT 1")
        row = cur.fetchone()
    return row[0] if row else None


def heartbeat(component, status="ok", detail=None):
    """Record that `component` is alive. Upsert: one row per component, forever.

    Deliberately not an append-only log. A heartbeat every five minutes from
    every component would be ~100k rows a year of data whose only interesting
    value is the newest one. Anything worth keeping history for goes to
    ops_events instead.
    """
    with db.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO ops_heartbeats (component, last_seen, status, detail)
                   VALUES (%s, now(), %s, %s)
                   ON CONFLICT (component) DO UPDATE
                     SET last_seen = now(), status = EXCLUDED.status,
                         detail = EXCLUDED.detail""",
                (component, status, Json(detail or {})),
            )
    return {"ok": True, "component": component}


def _recently_alerted(cur, component, event):
    """True if this exact fault was already mailed inside the cooldown."""
    cur.execute(
        """SELECT 1 FROM ops_events
           WHERE component = %s AND event = %s AND notified_at IS NOT NULL
             AND notified_at > now() - (%s || ' hours')::interval
           LIMIT 1""",
        (component, event, str(ALERT_COOLDOWN_HOURS)),
    )
    return cur.fetchone() is not None


def record(component, severity, event, message="", detail=None):
    """Store an operational event and mail it if it is worth waking up for.

    Returns what actually happened, including whether mail was suppressed, so
    the caller can log the truth rather than assuming delivery.
    """
    severity = severity if severity in SEVERITIES else "info"
    with db.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO ops_events (component, severity, event, message, detail)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (component, severity, event, message, Json(detail or {})),
            )
            event_id = cur.fetchone()[0]

            # info never mails. resolved always mails, but only if the matching
            # fault was actually reported -- otherwise a recovery for something
            # nobody was told about is just noise.
            should_mail = severity in ("warn", "error")
            if severity == "resolved":
                cur.execute(
                    """SELECT 1 FROM ops_events
                       WHERE component = %s AND event = %s AND severity IN ('warn','error')
                         AND notified_at IS NOT NULL
                         AND created_at > now() - interval '7 days' LIMIT 1""",
                    (component, event),
                )
                should_mail = cur.fetchone() is not None
            elif should_mail and _recently_alerted(cur, component, event):
                should_mail = False

            recipient = _alert_recipient(conn) if should_mail else None

    outcome = {"id": event_id, "severity": severity, "mailed": False,
               "suppressed": bool(severity in ("warn", "error") and not should_mail),
               "recipient": None}

    if should_mail and recipient:
        sent = _send(recipient, component, severity, event, message, detail)
        outcome["mailed"] = sent
        outcome["recipient"] = auth.mask_email(recipient)
        if sent:
            with db.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE ops_events SET notified_at = now() WHERE id = %s",
                                (event_id,))
    return outcome


def _send(to_email, component, severity, event, message, detail):
    """Deliver one operational email. Resend first, SMTP second, both optional.

    Mirrors the transport auth.send_otp_email already proved works in this
    deployment rather than introducing a second mail path with its own failure
    modes. Returns a plain bool -- the caller records delivery, and an
    unrecorded failure would be worse than a noisy one.
    """
    icon = {"error": "DOWN", "warn": "WARN", "resolved": "RECOVERED"}.get(severity, "INFO")
    subject = f"[ScoutVeda {icon}] {component}: {event}"
    when = _ist(datetime.datetime.now(datetime.timezone.utc))
    body = (
        f"<div style=\"font-family:ui-sans-serif,system-ui;max-width:560px\">"
        f"<h2 style=\"margin:0 0 4px\">{component} &mdash; {event}</h2>"
        f"<p style=\"color:#6b7488;margin:0 0 16px;font-size:13px\">{when}</p>"
        f"<p style=\"font-size:15px;line-height:1.5\">{message or '(no detail)'}</p>"
    )
    if detail:
        pretty = json.dumps(detail, indent=2, default=str)
        body += (f"<pre style=\"background:#0b0f1a;color:#c9d1d9;padding:12px;"
                 f"border-radius:8px;font-size:12px;overflow:auto\">{pretty}</pre>")
    body += ("<p style=\"color:#6b7488;font-size:12px\">Sent by the ScoutVeda ops "
             "watchdog. Repeats of the same fault are suppressed for "
             f"{ALERT_COOLDOWN_HOURS:g}h.</p></div>")

    if auth.RESEND_API_KEY:
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {auth.RESEND_API_KEY}",
                         "Content-Type": "application/json"},
                json={"from": auth.EMAIL_FROM, "to": [to_email],
                      "subject": subject, "html": body},
                timeout=15,
            )
            return 200 <= resp.status_code < 300
        except requests.RequestException as exc:
            print(f"[ops] Resend delivery failed: {exc}")
            return False
    if auth.SMTP_HOST:
        try:
            import re
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            port = int(auth.SMTP_PORT) if auth.SMTP_PORT else (
                465 if auth.SMTP_SECURE == "ssl" else 587)
            msg = MIMEMultipart("alternative")
            msg["Subject"], msg["From"], msg["To"] = subject, auth.EMAIL_FROM, to_email
            msg.attach(MIMEText(body, "html"))
            match = re.search(r"<([^>]+)>", auth.EMAIL_FROM)
            sender = match.group(1) if match else auth.EMAIL_FROM
            smtp_cls = smtplib.SMTP_SSL if auth.SMTP_SECURE == "ssl" else smtplib.SMTP
            with smtp_cls(auth.SMTP_HOST, port, timeout=15) as server:
                if auth.SMTP_SECURE == "tls":
                    server.starttls()
                if auth.SMTP_USER and auth.SMTP_PASSWORD:
                    server.login(auth.SMTP_USER, auth.SMTP_PASSWORD)
                server.sendmail(sender, [to_email], msg.as_string())
            return True
        except Exception as exc:                     # noqa: BLE001 - never crash the caller
            print(f"[ops] SMTP delivery failed: {exc}")
            return False
    print(f"[ops:MOCK] {subject} -> {to_email}")
    return False


def status():
    """Everything an outside observer needs to judge the platform, in one call.

    Shaped for the twice-daily dead-man's-switch workflow, which must decide
    pass/fail without a database connection and without a second request.
    `stale` is computed here, in SQL against now(), so the verdict does not
    depend on the caller's clock being right.
    """
    with db.get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT component, status, last_seen, detail,
                          round(EXTRACT(EPOCH FROM (now() - last_seen))/60.0)::int AS age_minutes
                   FROM ops_heartbeats ORDER BY component""")
            beats = [dict(r) for r in cur.fetchall()]
            cur.execute(
                """SELECT component, severity, event, message, created_at, notified_at
                   FROM ops_events
                   WHERE created_at > now() - interval '48 hours'
                     AND severity IN ('warn','error','resolved')
                   ORDER BY created_at DESC LIMIT 25""")
            events = [dict(r) for r in cur.fetchall()]

    for beat in beats:
        beat["last_seen_ist"] = _ist(beat["last_seen"])
        beat["last_seen"] = beat["last_seen"].isoformat() if beat["last_seen"] else None
    for evt in events:
        evt["created_at_ist"] = _ist(evt["created_at"])
        evt["created_at"] = evt["created_at"].isoformat() if evt["created_at"] else None
        evt["notified_at"] = evt["notified_at"].isoformat() if evt["notified_at"] else None

    return {"heartbeats": beats, "recent_events": events,
            "generated_at_ist": _ist(datetime.datetime.now(datetime.timezone.utc))}


# How long a component may go quiet before it is presumed dead. The watchdog on
# the VM beats every 15 minutes, so 90 covers a slow run, a reboot, and a missed
# tick without crying wolf.
DEADMAN_MINUTES = int(os.environ.get("DEADMAN_MINUTES", "90"))

# Components that only run occasionally are exempt from the staleness rule --
# the nightly maintenance job is *supposed* to be silent for 23 hours.
DEADMAN_EXEMPT = {"vm-maintain", "vm-scrape", "vm-push", "deploy-check"}


def deadman():
    """Detect a VM that has gone silent, and say so. The one check it cannot do.

    Every other failure in this system is reported by the component that
    suffered it. This is the exception: a VM that is powered off, kernel
    panicked, or cut off from the network sends nothing at all, and silence is
    indistinguishable from health unless somebody is specifically looking for
    it. That "somebody" has to live outside the VM, which is why this runs here
    and is called from GitHub Actions rather than from the box itself.

    Deliberately a POST with a side effect rather than a field on /ops/status:
    a GET that silently emails people is a surprise, and this needs to be an
    explicit act by a caller whose job is to check.
    """
    with db.get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT component,
                          round(EXTRACT(EPOCH FROM (now() - last_seen))/60.0)::int AS age
                   FROM ops_heartbeats ORDER BY component""")
            beats = [dict(r) for r in cur.fetchall()]

    watched = [b for b in beats if b["component"] not in DEADMAN_EXEMPT]
    stale = [b for b in watched if b["age"] > DEADMAN_MINUTES]

    if not watched:
        # Nothing has ever reported. Either this is a fresh deployment or the
        # VM has never once succeeded -- both worth saying out loud rather than
        # returning a cheerful "no stale components found".
        return {"ok": False, "reason": "no components have ever reported",
                "checked": 0, "stale": []}

    names = ", ".join(f"{b['component']} ({b['age']}m)" for b in stale)
    if stale:
        record("deadman", "error", "vm-silent",
               f"No heartbeat from {names} for over {DEADMAN_MINUTES} minutes. "
               "The scraping VM is presumed down: check that the Oracle instance "
               "is running, then that the scout-health timer is active.",
               {"stale": stale, "threshold_minutes": DEADMAN_MINUTES})
    else:
        # Closes the incident when the box comes back, without anyone acting.
        record("deadman", "resolved", "vm-silent",
               "All components are reporting again.",
               {"checked": len(watched)})

    return {"ok": not stale, "checked": len(watched),
            "threshold_minutes": DEADMAN_MINUTES,
            "stale": [b["component"] for b in stale],
            "components": {b["component"]: b["age"] for b in watched}}


def prune():
    """Delete operational history past the retention window.

    Called from the VM's nightly maintenance rather than on a schedule here,
    because the API sleeps on Render's free tier and cannot be relied on to run
    anything by itself.
    """
    with db.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM ops_events WHERE created_at < now() - (%s || ' days')::interval",
                (str(EVENT_RETENTION_DAYS),))
            return {"deleted": cur.rowcount, "retention_days": EVENT_RETENTION_DAYS}
