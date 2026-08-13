"""The supervision envelope. Every scheduled job on the VM runs through here.

    python3 -m scoutd.run <task> [args...]

WHY AN ENVELOPE RATHER THAN A DAEMON
------------------------------------
The obvious design for "run things forever" is a long-lived supervisor process.
On this box that is the wrong choice. It has 956 MB of RAM and has to stay up
for six months unattended; a resident Python process that leaks a few hundred
kilobytes a day is a slow, hard-to-diagnose death, and it introduces the
question of who supervises the supervisor.

So: every job is a short-lived process that starts, works, reports, and exits.
A process that has exited cannot leak, cannot wedge, and cannot drift. systemd
timers do the scheduling, and PID 1 is the only thing that has to stay alive --
which it does regardless.

WHAT THIS LAYER OWNS, AND WHAT IT DELIBERATELY DOES NOT
-------------------------------------------------------
systemd already does several of these jobs better than Python can, so this
does not duplicate them:

  timeouts        systemd TimeoutStartSec SIGKILLs a wedged job. Python cannot
                  reliably time out a hung C-level call in a Playwright
                  subprocess; the kernel can.
  memory ceiling  MemoryMax kills the cgroup, not whatever the OOM killer feels
                  like picking -- on a 956 MB box that would otherwise be sshd.
  failure alerts  scout-alert@.service fires OnFailure. It catches the cases
                  this file cannot possibly catch, because a SIGKILLed process
                  runs no exception handler.
  catch-up        Persistent=true on the timers reruns a job whose slot was
                  missed while the VM was down.

What this file owns is everything systemd has no opinion about: mutual
exclusion, stale-lock recovery, run history, and the success/failure/recovery
reporting that turns a run into something an absent person can read.
"""
import errno
import fcntl
import importlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

from . import config, ops

# A lock older than this is not a running job, it is a corpse. The longest real
# job is the scrape at roughly 20 minutes; three hours is far past anything
# legitimate and still short enough that a wedged job self-clears before the
# next day's run rather than blocking collection indefinitely.
STALE_LOCK_HOURS = 3

# Kept small on purpose. This is a breadcrumb trail for diagnosing a bad week,
# not an archive -- the durable history lives in Postgres via ops_events.
RUN_LOG_KEEP = 400


def _run_log_path():
    return config.STATE_DIR / "runs.jsonl"


def _outcome_path():
    return config.STATE_DIR / "last_outcome.json"


def _load_outcomes():
    try:
        return json.loads(_outcome_path().read_text())
    except (OSError, ValueError):
        return {}


def _save_outcome(task, ok):
    """Remember pass/fail per task so a recovery can be recognised.

    Without this, a fault that fixes itself leaves an alarming email as the
    last word and no closing one. Someone coming back from a week away then
    cannot tell a resolved blip from an ongoing outage without logging in --
    which is exactly the manual check this platform exists to remove.
    """
    outcomes = _load_outcomes()
    previous = outcomes.get(task, {}).get("ok")
    outcomes[task] = {"ok": ok, "at": config.stamp()}
    try:
        _outcome_path().write_text(json.dumps(outcomes, indent=2))
    except OSError as exc:
        ops._local_note(f"could not save outcome for {task}: {exc}")
    return previous


def _append_run(record):
    path = _run_log_path()
    try:
        with path.open("a") as handle:
            handle.write(json.dumps(record) + "\n")
        # Trim in place rather than relying on logrotate, so the cap holds even
        # if logrotate is misconfigured or the file is renamed out from under it.
        lines = path.read_text().splitlines()
        if len(lines) > RUN_LOG_KEEP * 2:
            path.write_text("\n".join(lines[-RUN_LOG_KEEP:]) + "\n")
    except OSError as exc:
        ops._local_note(f"could not write run log: {exc}")


class Lock:
    """Non-blocking flock with stale detection.

    Two of the same job at once is not merely wasteful here: two scrapes double
    the request rate to amazon.in from one datacenter IP, which is the exact
    pattern that gets the IP blocked. So overlap has to be prevented, not just
    discouraged.

    The stale check is the important half. Plain `flock -n || exit 0` -- which
    is what the old cron wrappers did -- means a job wedged holding the lock
    silently suppresses every future run, forever, while the log fills with
    cheerful "skipped, previous run still going" lines. That failure looks
    healthy from outside and is precisely the kind of silent stop this platform
    is meant to make impossible.
    """

    def __init__(self, task):
        self.path = config.STATE_DIR / f".{task}.lock"
        self.task = task
        self.handle = None
        self.broke_stale = False

    def acquire(self):
        config.ensure_dirs()
        self.handle = self.path.open("a+")
        try:
            fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.ftruncate(self.handle.fileno(), 0)
            self.handle.write(f"{os.getpid()} {config.stamp()}\n")
            self.handle.flush()
            return True
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN):
                raise
        age_hours = (time.time() - self.path.stat().st_mtime) / 3600.0
        if age_hours < STALE_LOCK_HOURS:
            return False
        # Held far too long. Report it -- do not silently steal the lock, or the
        # underlying wedge is never investigated -- then let this run proceed,
        # because a stuck predecessor is not a reason to also skip today.
        self.broke_stale = True
        ops.alert(self.task, "warn", "stale-lock",
                  f"{self.task} lock held for {age_hours:.1f}h, past the "
                  f"{STALE_LOCK_HOURS}h limit. Treating it as a wedged run and "
                  "proceeding; the previous process was killed.",
                  detail={"age_hours": round(age_hours, 1)})
        self._kill_holder()
        try:
            fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False

    def _kill_holder(self):
        """Kill whatever still holds a stale lock, if it is still around.

        Only a process we recorded ourselves, and only after confirming the PID
        still looks like the job we started -- PIDs get recycled, and killing a
        stranger because the number matched would be a far worse bug than the
        wedge being cleaned up.
        """
        try:
            recorded = self.path.read_text().split()
            pid = int(recorded[0])
        except (OSError, ValueError, IndexError):
            return
        try:
            cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace")
        except OSError:
            return          # already gone; nothing to do
        if "scoutd" not in cmdline and "scrape" not in cmdline:
            ops._local_note(f"refusing to kill pid {pid}: not a scoutd process")
            return
        for sig, wait in ((15, 5), (9, 0)):
            try:
                os.kill(pid, sig)
            except OSError:
                return
            if wait:
                time.sleep(wait)
                if not Path(f"/proc/{pid}").exists():
                    return

    def release(self):
        if self.handle:
            try:
                fcntl.flock(self.handle, fcntl.LOCK_UN)
                self.handle.close()
            except OSError:
                pass


def _cgroup_peak_mb():
    """High-water memory for this unit, in MB, or None outside systemd.

    Read after the job's children have exited: memory.peak is the cgroup's
    high-water mark and survives the processes that caused it, so this captures
    the browser's real appetite even though the browser is already gone.

    Recorded on every run so the memory ceilings in the unit files can be set
    from measurement rather than from a guess. Guessing here has a real cost in
    both directions -- too low kills legitimate scrapes, too high lets a runaway
    take the whole 956 MB box down with it -- and neither is a number anyone
    should be inventing when the kernel is already counting it.
    """
    try:
        line = Path("/proc/self/cgroup").read_text().strip().split(":")[-1]
        peak = Path(f"/sys/fs/cgroup{line}/memory.peak")
        return round(int(peak.read_text().strip()) / 1048576)
    except (OSError, ValueError, IndexError):
        return None


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    task_name = argv[1]
    args = argv[2:]
    config.ensure_dirs()

    try:
        module = importlib.import_module(f"scoutd.tasks.{task_name}")
    except ImportError as exc:
        print(f"unknown task {task_name!r}: {exc}", file=sys.stderr)
        return 2

    lock = Lock(task_name)
    if not lock.acquire():
        # A healthy overlap: the previous run is still inside its normal
        # window. Exit 0 -- this is not a failure and must not alert.
        print(f"[{config.stamp()}] {task_name}: already running, skipping")
        return 0

    started = time.time()
    detail, failure = {}, None
    try:
        detail = module.run(args) or {}
        ok = detail.get("ok", True)
    except Exception:                        # noqa: BLE001 - report, never crash
        ok, failure = False, traceback.format_exc()
        detail = {"traceback": failure.splitlines()[-1]}
    finally:
        lock.release()

    elapsed = round(time.time() - started, 1)
    peak_mb = _cgroup_peak_mb()
    record = {"task": task_name, "ok": bool(ok), "seconds": elapsed,
              "peak_mb": peak_mb, "at": config.stamp(),
              **{k: v for k, v in detail.items() if k not in ("message",)}}
    _append_run(record)

    previous_ok = _save_outcome(task_name, bool(ok))
    summary = detail.get("message", "")
    print(f"[{config.stamp()}] {task_name}: {'ok' if ok else 'FAILED'} "
          f"in {elapsed}s  {summary}")

    # The task's own keys are namespaced under "detail" rather than merged, so a
    # task returning {"status": 200} can never collide with the heartbeat's own
    # status field. Reporting has to be impossible to break from a task.
    context = {"seconds": elapsed, "peak_mb": peak_mb, "summary": summary[:300],
               "detail": {k: v for k, v in detail.items() if k != "traceback"}}

    ops.heartbeat(task_name, status="ok" if ok else "error", detail=context)

    if not ok:
        ops.alert(task_name, detail.get("severity", "error"),
                  detail.get("event", f"{task_name}-failed"),
                  summary or "task reported failure", detail=context)
        if failure:
            print(failure, file=sys.stderr)
    elif previous_ok is False:
        # Only on a transition. Sending "recovered" after every success would
        # be noise; sending it once, when the state actually changes, is what
        # closes the incident out in the inbox.
        ops.alert(task_name, "resolved", f"{task_name}-failed",
                  f"{task_name} succeeded again after a failure. {summary}",
                  detail=context)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
