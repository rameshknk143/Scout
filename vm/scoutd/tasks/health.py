"""The watchdog. Runs every 15 minutes, fixes what it can, reports the rest.

This is the task that makes "leave it alone for six months" a defensible claim
rather than a hope. Every other job reports on itself when it runs; this one
reports on the things that fail *between* runs, and on the failure mode that no
self-reporting job can ever catch -- not running at all.

Two rules shape it:

CHEAP AND FAILURE-PROOF. It runs 96 times a day for six months, roughly 17,000
executions. Anything it does has to cost close to nothing and must not be able
to break the system it is watching. So it reads counters and kills only
processes it can positively identify.

FIX FIRST, THEN REPORT. A watchdog that only complains still needs a person.
Where the remedy is unambiguous -- an orphaned browser holding 200 MB on a
956 MB box, logs eating a disk -- it acts, and reports what it did. Where the
remedy involves judgement, it reports and leaves it alone.

CONSECUTIVE-FAILURE THRESHOLDS matter as much as the checks. Almost everything
here is transient at least occasionally: Render restarts a free dyno, amazon.in
refuses one request, a timer fires a minute late. Alerting on a single sample
produces false alarms, and false alarms at 3am are how monitoring gets muted --
after which the platform is unmonitored while looking monitored. So a condition
must persist across several consecutive checks before it becomes an email.
"""
import calendar
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from .. import config, ops

DISK_WARN_PCT = 85
DISK_CRITICAL_PCT = 92
MEM_AVAILABLE_WARN_MB = 80

# 26h, not 24: the scrape runs twice a day, so anything under ~13h is normal
# and 26 means two consecutive passes produced nothing.
DATA_STALE_HOURS = 26

# A browser still alive this long after its scrape finished is orphaned. The
# longest legitimate run is about 20 minutes.
ORPHAN_BROWSER_MINUTES = 45

# How many consecutive 15-minute checks a condition must hold before it alerts.
# 3 = 45 minutes, which is past every transient this system actually produces.
CONSECUTIVE = 3

STATE_FILE = "health_state.json"


def _state():
    try:
        return json.loads((config.STATE_DIR / STATE_FILE).read_text())
    except (OSError, ValueError):
        return {}


def _save_state(state):
    try:
        (config.STATE_DIR / STATE_FILE).write_text(json.dumps(state, indent=2))
    except OSError as exc:
        ops._local_note(f"could not save health state: {exc}")


class Report:
    """Collects findings, and only escalates ones that have persisted.

    `problem()` registers a condition seen right now. It becomes an alert only
    once it has been seen on CONSECUTIVE checks in a row; a check that passes
    clears the counter, and clearing a counter that had escalated sends the
    recovery.
    """

    def __init__(self, state):
        self.state = state
        self.counters = state.get("counters", {})
        self.alerted = set(state.get("alerted", []))
        self.problems, self.actions, self.facts = [], [], {}
        self.seen = set()

    def fact(self, key, value):
        self.facts[key] = value

    def action(self, text):
        self.actions.append(text)

    def problem(self, event, message, severity="warn"):
        self.seen.add(event)
        count = self.counters.get(event, 0) + 1
        self.counters[event] = count
        if count >= CONSECUTIVE and event not in self.alerted:
            ops.alert("health", severity, event,
                      f"{message} (seen on {count} consecutive checks)",
                      detail=dict(self.facts))
            self.alerted.add(event)
        self.problems.append(f"{event}: {message}")

    def finish(self, all_events):
        """Clear counters for everything that is healthy now, closing incidents."""
        for event in all_events:
            if event in self.seen:
                continue
            self.counters.pop(event, None)
            if event in self.alerted:
                ops.alert("health", "resolved", event,
                          f"{event} has cleared on its own.")
                self.alerted.discard(event)
        self.state["counters"] = self.counters
        self.state["alerted"] = sorted(self.alerted)
        return self.state


# --- individual checks -------------------------------------------------------

def _check_disk(report):
    usage = shutil.disk_usage("/")
    pct = round(usage.used * 100.0 / usage.total)
    free_gb = round(usage.free / 1e9, 1)
    report.fact("disk_pct", pct)
    report.fact("disk_free_gb", free_gb)
    if pct >= DISK_CRITICAL_PCT:
        report.problem("disk-critical",
                       f"root filesystem {pct}% full, only {free_gb} GB free",
                       severity="error")
    elif pct >= DISK_WARN_PCT:
        report.problem("disk-low", f"root filesystem {pct}% full, {free_gb} GB free")


def _check_memory(report):
    """Available memory, not free memory.

    'free' on this box reads about 93 MB and always will, because Linux uses
    the rest for page cache. MemAvailable is the number that predicts whether
    the next allocation triggers the OOM killer, and on a 956 MB box running
    Chromium that distinction is the difference between a false alarm every
    fifteen minutes and a real signal.
    """
    values = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, _, rest = line.partition(":")
            values[key] = int(rest.split()[0]) // 1024      # kB -> MB
    except (OSError, ValueError, IndexError):
        return
    available = values.get("MemAvailable", 0)
    swap_used = values.get("SwapTotal", 0) - values.get("SwapFree", 0)
    report.fact("mem_available_mb", available)
    report.fact("swap_used_mb", swap_used)
    if available < MEM_AVAILABLE_WARN_MB:
        report.problem("memory-low",
                       f"only {available} MB available, {swap_used} MB of swap in use")


def _check_orphan_browsers(report):
    """Kill Chromium processes left behind by a crashed or killed scrape.

    This is the leak that actually kills a small box over months. Playwright
    launches a browser per run; if the run is SIGKILLed -- by a timeout, by the
    OOM killer, by a reboot at the wrong moment -- the browser can survive its
    parent and sit there holding a couple of hundred megabytes. Two or three of
    those and there is no room left to run a scrape at all, and the symptom is
    "scraping mysteriously stopped working", weeks later and far from the cause.

    Safe because of the age test: no legitimate browser from this system lives
    past ORPHAN_BROWSER_MINUTES, and nothing else on this VM runs a browser.
    """
    try:
        out = subprocess.run(
            ["ps", "-eo", "pid,etimes,comm,args", "--no-headers"],
            stdout=subprocess.PIPE, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return
    killed = []
    for line in out.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        pid, etimes, _comm, args = parts
        if "chrome" not in args and "chromium" not in args and "headless_shell" not in args:
            continue
        try:
            age_minutes = int(etimes) / 60.0
        except ValueError:
            continue
        if age_minutes < ORPHAN_BROWSER_MINUTES:
            continue
        try:
            os.kill(int(pid), 15)
            killed.append(int(pid))
        except (OSError, ValueError):
            continue
    if killed:
        time.sleep(3)
        for pid in killed:
            try:
                os.kill(pid, 9)          # only if SIGTERM was ignored
            except OSError:
                pass
        report.action(f"killed {len(killed)} orphaned browser process(es): {killed}")
        report.fact("orphan_browsers_killed", len(killed))


def _check_data_freshness(report):
    """Has anything been collected recently?

    The scrape task reports on its own runs, but only when it runs. If the
    timer itself stops -- a bad unit file, a failed boot, a systemd state that
    got lost -- nothing else in the system notices, because the absence of a
    report is not an event. This check turns that absence into one.
    """
    if not config.DB_PATH.exists():
        report.problem("db-missing", f"{config.DB_PATH} does not exist",
                       severity="error")
        return
    conn = sqlite3.connect(str(config.DB_PATH))
    try:
        newest = conn.execute(
            "SELECT MAX(scraped_at) FROM price_history WHERE ok = 1").fetchone()[0]
        rows = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
    except sqlite3.Error as exc:
        report.problem("db-unreadable", f"cannot read price_history: {exc}",
                       severity="error")
        return
    finally:
        conn.close()

    report.fact("db_rows", rows)
    if not newest:
        report.problem("no-data", "price_history has no successful rows at all",
                       severity="error")
        return
    # scraped_at is written in UTC, so parse it as UTC. timegm rather than
    # mktime: mktime assumes local time, which happens to be UTC on this VM
    # today and would silently skew by hours on any box where it is not.
    try:
        newest_epoch = calendar.timegm(time.strptime(newest[:19], "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return
    age_hours = (time.time() - newest_epoch) / 3600.0
    report.fact("data_age_hours", round(age_hours, 1))
    if age_hours > DATA_STALE_HOURS:
        report.problem("data-stale",
                       f"newest successful scrape is {age_hours:.0f}h old -- "
                       "two consecutive passes have produced nothing",
                       severity="error")


def _check_tunnel(report):
    """Phone tunnel state -- the residential-IP route that scrapes fall back on.

    Three signals, cheapest first:
      1. Listener: is 127.0.0.1:1080 up at all (the ssh -R forward from the phone)?
      2. Data flow: can a request actually THROUGH the tunnel fetch a page --
         the half-tunnel failure mode of 1 Sep 2026, where the SOCKS handshake
         succeeded but every byte died in the app, evaded the listener check
         for hours. Data flow is the only truth.
      3. Trend: last 12 watch-log samples, so the page can show a flapping
         tunnel rather than a single boolean.

    The data-flow probe costs one small request every 15 minutes and only runs
    when the listener is up; when it is down there is nothing to probe.
    """
    try:
        out = subprocess.run(
            ["ss", "-tln"], stdout=subprocess.PIPE, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return
    listener_up = "127.0.0.1:1080" in out
    report.fact("tunnel_listener", "up" if listener_up else "down")

    exit_ip = None
    if listener_up:
        # One request through the phone, to a service whose only job is to
        # echo the caller's IP. 15s cap: the wedge showed up as requests that
        # connect then hang forever, and the watchdog must not hang with them.
        # curl rather than urllib: stdlib has no SOCKS support without PySocks,
        # and curl --socks5-hostname is the exact probe already proven live on
        # this box (it is what diagnosed the 1 Sep wedge).
        try:
            proc = subprocess.run(
                ["curl", "-s", "-m", "15", "--socks5-hostname", "127.0.0.1:1080",
                 "https://api.ipify.org"],
                stdout=subprocess.PIPE, text=True, timeout=25)
            exit_ip = (proc.stdout or "").strip()[:45]
        except (OSError, subprocess.SubprocessError):
            exit_ip = ""
        if exit_ip and exit_ip == config.VM_PUBLIC_IP:
            report.fact("tunnel_exit_ip", exit_ip)
            report.fact("tunnel_flow", "loop")
            report.problem("tunnel-exit-loop",
                           f"exit IP {exit_ip} through the tunnel is the VM's own "
                           f"public IP -- traffic is looping, not exiting via the phone")
            return
        if exit_ip:
            report.fact("tunnel_exit_ip", exit_ip)
            report.fact("tunnel_flow", "ok")
        else:
            # Listener accepted but no bytes came back -- exactly the 1 Sep
            # half-tunnel wedge. Named distinctly so the recovery email and
            # the health page can say "restart the phone-side proxy", not
            # "check your internet".
            report.fact("tunnel_exit_ip", None)
            report.fact("tunnel_flow", "dead")
            report.problem("tunnel-wedged",
                           "tunnel listener up but no data flows through it -- "
                           "the phone-side proxy is wedged (the 1 Sep 2026 "
                           "failure mode); restart the app or reboot the phone")
            return
    else:
        report.fact("tunnel_flow", "n/a")
        report.fact("tunnel_exit_ip", None)

    # Trend: the last 12 five-minute samples from the watch log. The page can
    # then show "up 12/12" vs "flapping" instead of a single boolean.
    try:
        log_path = Path.home() / "tunnel-watch.log"
        tail = log_path.read_text().splitlines()[-12:]
        ups = sum(1 for ln in tail if ln.endswith(" up"))
        report.fact("tunnel_uptime_samples", f"{ups}/12")
    except OSError:
        pass

    if not listener_up:
        report.fact("tunnel_flow", "n/a")


def _check_api(report):
    try:
        request = urllib.request.Request(f"{config.API_BASE}/health",
                                         headers={"User-Agent": "scoutd-health"})
        with urllib.request.urlopen(request, timeout=90) as response:
            if response.status == 200:
                report.fact("api", "ok")
                return
            report.problem("api-unhealthy", f"/health returned {response.status}")
    except (urllib.error.URLError, socket.timeout, OSError) as exc:
        report.problem("api-unreachable",
                       f"cannot reach {config.API_BASE}: {type(exc).__name__}")


def _check_timers(report):
    """Are the scoutd timers still scheduled?

    Guards against the case where a unit is disabled, masked or fails to load
    after an upgrade. systemd will not tell anyone; the jobs simply stop.
    """
    try:
        out = subprocess.run(
            ["systemctl", "list-timers", "--all", "--no-pager", "--no-legend"],
            stdout=subprocess.PIPE, text=True, timeout=25).stdout
    except (OSError, subprocess.SubprocessError):
        return
    active = {line.split()[-1] for line in out.splitlines() if line.strip()}
    expected = {"scout-scrape.service", "scout-push.service",
                "scout-keepwarm.service", "scout-maintain.service",
                "scout-health.service"}
    missing = sorted(expected - active)
    report.fact("timers_active", len(expected) - len(missing))
    if missing:
        report.problem("timers-missing",
                       f"timers not scheduled: {', '.join(missing)}",
                       severity="error")


def _check_reboot_pending(report):
    """A pending kernel update that never gets applied is a growing liability.

    unattended-upgrades installs security fixes but will not reboot unless it
    is told to, so a kernel or libc fix sits inactive indefinitely. The deploy
    configures an automatic reboot window; this check catches the case where
    that stops working, and it also flags the second-order risk -- the longer a
    reboot is deferred, the less anyone knows whether this box still boots
    cleanly, and the worse a time it will pick to find out.
    """
    marker = Path("/var/run/reboot-required")
    if not marker.exists():
        return
    age_days = (time.time() - marker.stat().st_mtime) / 86400.0
    report.fact("reboot_pending_days", round(age_days, 1))
    if age_days > 8:
        report.problem("reboot-overdue",
                       f"a reboot has been required for {age_days:.0f} days; "
                       "the automatic reboot window is not firing")


def run(args):
    config.ensure_dirs()
    state = _state()
    report = Report(state)

    _check_disk(report)
    _check_memory(report)
    _check_orphan_browsers(report)
    _check_data_freshness(report)
    _check_tunnel(report)
    _check_api(report)
    _check_timers(report)
    _check_reboot_pending(report)

    all_events = ["disk-critical", "disk-low", "memory-low", "db-missing",
                  "db-unreadable", "no-data", "data-stale", "api-unhealthy",
                  "api-unreachable", "timers-missing", "reboot-overdue",
                  "tunnel-wedged", "tunnel-exit-loop"]
    _save_state(report.finish(all_events))

    for text in report.actions:
        print(f"[{config.stamp()}] healed: {text}")

    if report.problems:
        return {"ok": True, "message": "; ".join(report.problems)[:400],
                "healed": report.actions, **report.facts}
    return {"ok": True, "message": "all clear",
            "healed": report.actions, **report.facts}
