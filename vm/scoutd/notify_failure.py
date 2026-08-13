"""Report a systemd unit failure, with enough context to act on it.

    python3 -m scoutd.notify_failure scout-scrape.service

Run from scout-alert@.service via OnFailure=. Everything it reports is pulled
from systemd rather than from the job, because the job is dead -- and the cases
that reach here are exactly the ones where it died without a chance to speak:
killed at its timeout, killed for exceeding its memory cap, or killed by the
OOM killer.

The distinction between those matters enough to be worth extracting. "Job
failed" is not actionable; "job was killed after 45 minutes at its timeout" and
"job was killed for exceeding a 700 MB memory cap" point at different fixes,
and neither is guessable from the other.
"""
import subprocess
import sys

from . import config, ops


def _property(unit, name):
    try:
        out = subprocess.run(["systemctl", "show", unit, "-p", name, "--value"],
                             stdout=subprocess.PIPE, text=True, timeout=20).stdout
        return out.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _journal_tail(unit, lines=25):
    try:
        return subprocess.run(
            ["journalctl", "-u", unit, "-n", str(lines), "--no-pager", "-o", "cat"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def explain(result, status, code):
    """Turn systemd's vocabulary into a sentence that says what to do next."""
    if result == "success":
        # OnFailure cannot fire for a unit that succeeded, so reaching here
        # means somebody started this handler by hand -- almost always to check
        # that alerting still works. Say so, rather than sending an alarming
        # email about a healthy job.
        return ("this handler was run manually; the unit is not actually "
                "failing. Treat this as a test of the alert path.")
    if result == "timeout":
        return ("the job hit its timeout and was killed. Something inside it "
                "hung -- most often a page load with no response. The next "
                "scheduled run is unaffected.")
    if result == "oom-kill" or code == "9":
        return ("the job was killed for using too much memory. On a 956 MB box "
                "this is usually a browser that failed to close. The watchdog "
                "reaps orphaned browsers every 15 minutes.")
    if result == "exit-code":
        return f"the job exited with status {status}."
    if result == "signal":
        return f"the job was killed by signal {status}."
    return f"systemd reported result={result!r}, status={status!r}."


def main(argv):
    unit = argv[1] if len(argv) > 1 else "unknown.service"
    # OnFailure passes %N, which is the unit name without its type suffix, so
    # the instance reads scout-alert@scout-scrape rather than the doubled-up
    # scout-alert@scout-scrape.service.service that %n produces. Accept either,
    # because the difference is invisible until systemctl is asked about the
    # wrong name and cheerfully reports the wrong unit's state.
    if not unit.endswith(".service"):
        unit += ".service"
    task = unit.replace("scout-", "").replace(".service", "")

    result = _property(unit, "Result")
    status = _property(unit, "ExecMainStatus")
    code = _property(unit, "ExecMainCode")
    tail = _journal_tail(unit)

    message = f"{unit} failed: {explain(result, status, code)}"
    print(f"[{config.stamp()}] {message}")

    # A stable event key per unit, so a unit failing on every run for a week
    # produces a first email and then silence rather than 300 of them.
    #
    # "info" for a manual invocation: recorded so the test is visible in the
    # event history, but not mailed. An alerting test that itself pages people
    # is a good way to get alerting switched off.
    severity = "info" if result == "success" else "error"
    ops.alert(task, severity, f"{task}-unit-failed", message, detail={
        "unit": unit, "result": result, "exit_status": status,
        "journal": tail[-1500:] if tail else "(no journal output)"})
    if severity != "info":
        # Mark the component unhealthy too, so /ops/status shows it as failing
        # even to someone who never opens the email.
        ops.heartbeat(task, status="error", detail={"summary": message[:300]})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
