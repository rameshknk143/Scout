# scoutd — the always-on half of ScoutVeda

Everything that runs on the Oracle scraping VM. This directory is the source of
truth: the box is built *from* here, not the other way round.

The goal is narrow and worth stating plainly, because every decision below
follows from it: **run for six months without anyone looking at it, and if that
becomes untrue, say so by email.** Not "run well". Not "run fast". Keep running,
and be honest when it stops.

---

## 1. The constraints this is built against

These were measured on 13–14 Aug 2026, not assumed. Nearly every design choice
here is downstream of one of them.

| Constraint | Reality | What it forces |
|---|---|---|
| VM shape | Oracle always-free x86 micro: **2 vCPU, 956 MB RAM**, 45 GB disk, 4 GB swap | No resident daemons. No container runtime. Memory ceilings on everything. |
| The VM cannot speak | No mail transport, and by standing rule **no production `DATABASE_URL`** | It reports to the API over the key it already holds; the API owns delivery. |
| amazon.in blocking | Blocks this datacenter IP roughly **a third of all passes**, and a wide gap does not buy immunity: a 12 h gap has both succeeded and failed. Time of day looks like it matters more than gap. | Twice a day, no more, and never on demand. The yield is a fact to be measured, not a knob to be turned. |
| GitHub Actions | Private repo → **2,000 min/month**, billed **per job rounded up to the whole minute**. Already ~77% consumed | Recurring work lives on the VM. Actions does only what must come from outside. |
| Render free tier | Sleeps after ~15 min idle; **750 instance-hours/month** | Keep-warm runs in a window, not around the clock. The API cannot run its own schedules. |
| Supabase free tier | 500 MB | Operational history has a retention window. |
| Budget | **₹0** | Everything above is a free tier, and staying inside each one is a design input. |

---

## 2. Architecture

```
                          ┌─────────────────────────────────────┐
   GitHub Actions         │  Oracle VM  (the only always-on box)│
   4x/day, from outside   │                                     │
   ──────────────────►    │  systemd timers ─► scoutd.run <task>│
   monitor.py             │        │                            │
     • 11 product checks  │        ├── scrape    2x/day  ───────┼──► amazon.in
     • dead-man's switch  │        ├── push      hourly         │
            │             │        ├── keepwarm  10 min (window)│
            │             │        ├── health    15 min ◄───────┼── watchdog + self-healing
            │             │        └── maintain  nightly        │
            │             │             │                       │
            │             │        OnFailure ─► scout-alert@    │
            ▼             └─────────────┼───────────────────────┘
   ┌──────────────────────┐             │  heartbeats + alerts
   │ ScoutVeda API (Render)│◄────────────┘  (X-Scout-Key)
   │  api/ops.py           │
   │   /ops/heartbeat      │──► Postgres: ops_heartbeats, ops_events
   │   /ops/alert          │──► Resend ──► email to Ram
   │   /ops/status         │
   │   /ops/deadman        │
   └──────────────────────┘
```

### Why short-lived jobs instead of a supervisor daemon

The obvious design for "run things forever" is a long-lived supervisor process.
On this box that is the wrong choice. 956 MB of RAM, six months of uptime: a
resident Python process that leaks a few hundred kilobytes a day is a slow death
that is very hard to diagnose, and it raises the question of who supervises the
supervisor.

So every job starts, works, reports, and exits. A process that has exited cannot
leak, cannot wedge, and cannot drift. PID 1 does the scheduling and is the only
thing that must stay alive — which it does regardless.

### The division of labour

systemd is better at several of these jobs than Python is, so scoutd does not
reimplement them:

| systemd owns | Why not in Python |
|---|---|
| `TimeoutStartSec` → SIGKILL | Python cannot reliably interrupt a hung C-level call inside a Playwright subprocess. The kernel can. |
| `MemoryMax` (cgroup kill) | Without it the kernel OOM killer picks the victim, and on a 956 MB box that is as likely to be `sshd`. Being locked out is far worse than a failed scrape. |
| `Persistent=true` catch-up | A cron slot missed while the box is down is lost forever with no record. |
| `OnFailure=` | A SIGKILLed process runs no exception handler. This is the only thing left standing to notice. |

| scoutd owns | |
|---|---|
| Locking + **stale-lock recovery** | See §6. This was a real silent-failure mode. |
| Run history, pass/fail transitions | So a recovery can be recognised and the incident closed. |
| Verdicts on ambiguous outcomes | A scrape that captures 2 of 15 exits 0 exactly like one that captures 15. |
| Reporting | Turning a run into something an absent person can read. |

---

## 3. Folder structure

```
vm/
  deploy.sh                 idempotent installer; run with sudo on the VM
  scoutd/
    config.py               paths, secrets, IST helpers. No task hardcodes a path.
    ops.py                  the VM's voice: heartbeat() and alert(). Fails soft.
    run.py                  the supervision envelope. Every job goes through it.
    notify_failure.py       runs from OnFailure=; reports deaths the job cannot
    tasks/
      scrape.py             runs the scraper, then judges the result from the DB
      push.py               ships rows to the API, watches the backlog
      keepwarm.py           keeps Render awake inside its hour budget
      health.py             the watchdog: checks, self-heals, escalates
      maintain.py           nightly backup then housekeeping
  systemd/                  five service+timer pairs, scout-alert@, scout-selftest
```

On the VM:

```
/home/ubuntu/scoutd/            the code above
/home/ubuntu/scoutd-state/      locks, runs.jsonl, health_state.json
/home/ubuntu/scoutd-state/backups/   14 nightly gzipped scout.db snapshots
/home/ubuntu/.config/scoutd/env      SCOUT_API_KEY, 0600, never committed
/home/ubuntu/scout/             the scraper itself — unchanged, supervised
```

`scoutd` is **stdlib only**, on purpose. It is the layer that reports when the
rest of the system is broken, so a pip resolution failure or a half-upgraded
virtualenv must still leave the reporting path working. Only the scraper itself
uses `~/ocienv` (Playwright).

---

## 4. Schedule

All times UTC; IST in brackets. The VM runs UTC, everything a human reads is IST.

| Unit | When | Timeout | MemoryMax | Catch-up |
|---|---|---|---|---|
| `scout-scrape` | 06:20, 15:20 (11:50, 20:50 IST) ±15 min jitter | 45 min | 850 M | yes |
| `scout-push` | hourly at :35 | 15 min | 250 M | yes |
| `scout-keepwarm` | every 10 min, 02:00–19:59 (07:30–01:29 IST) | 5 min | 120 M | no |
| `scout-health` | every 15 min, and 2 min after boot | 8 min | 200 M | yes |
| `scout-maintain` | 01:10 (06:40 IST) | 30 min | 350 M | yes |
| unattended-upgrades reboot | 02:00 (07:30 IST) when required | — | — | — |
| `monitor.yml` (GitHub) | 03, 08, 13, 18 | — | — | — |

The jitter on the scrape is not cosmetic: requests arriving at exactly 06:20:00
every day are a pattern, and a pattern is a fingerprint.

**Do not add a third daily scrape.** Every extra request from this IP raises the
odds that the two scheduled passes get refused, and the scheduled passes are the
only ones that matter. An ad-hoc run has already cost a scheduled pass its whole
sweep once. `scrape.py` enforces `MIN_GAP_HOURS = 8` for exactly this reason;
`--force` exists but spends the budget the next pass needs.

---

## 5. How a failure reaches Ram

Three independent paths, because each covers a case the others cannot.

1. **The job reports itself.** `scoutd/run.py` sends a heartbeat and, on
   failure, an alert. Covers everything the job can see.
2. **systemd reports the job.** `OnFailure=scout-alert@%N.service` fires when a
   job is killed at its timeout or for exceeding its memory cap — the two most
   likely silent deaths, and neither runs an exception handler.
3. **The outside observer reports the VM.** `POST /ops/deadman`, called from the
   monitor workflow. Everything else reports its own failures; a machine that is
   off reports nothing, and nothing looks exactly like a healthy quiet night.

   It watches **`vm-health` only**, and that is deliberate. A dead-man's switch
   wants one beacon that is reliable around the clock, not several whose silence
   has innocent explanations — every other component has a schedule with gaps
   longer than the 90-minute threshold, including keep-warm, which is meant to
   be quiet for six hours a night. Add a component to `DEADMAN_EXEMPT` in
   `api/ops.py` unless it genuinely runs at least hourly, forever.

### Alert-storm suppression is load-bearing

A system that mails on every failed tick sends hundreds of emails in one outage,
and the practical result is that the alerts stop being read — so the one that
matters is missed. Therefore:

- Repeats of the same `(component, event)` are suppressed for **6 h**
  (`ALERT_COOLDOWN_HOURS`).
- The watchdog escalates only after a condition holds for **3 consecutive
  checks** (45 min), because almost everything here is occasionally transient.
- **Recoveries always deliver.** An incident that fixes itself closes itself out
  in the inbox, so coming back after a week away does not require logging in to
  tell a resolved blip from an ongoing outage.
- `info` is recorded but never mailed.

### Reading the state without logging in

```bash
curl -s -H "X-Scout-Key: $KEY" https://scout-api-3yvy.onrender.com/ops/status
```

Heartbeats with ages, plus 48 h of real events. `age_minutes` is computed in SQL
against `now()`, so the verdict does not depend on the caller's clock.

---

## 6. Self-healing: what it fixes without being asked

| Condition | Action |
|---|---|
| Lock held > 3 h | Presumed wedged. Alert, kill the holder (only after confirming the PID is still a scoutd process — PIDs get recycled), proceed. |
| Orphaned Chromium > 45 min | SIGTERM then SIGKILL. Playwright browsers can outlive a SIGKILLed parent holding ~200 MB; two or three and there is no room to scrape at all. |
| Logs growing unbounded | Nightly trim to the last N lines, via write-and-rename so appending writers keep working. |
| `/tmp` litter | Private `/tmp` for the scrape (destroyed on exit), plus a nightly sweep of anything older than 24 h. |
| Journal growth | Capped at 200 M in `journald.conf`, enforced continuously by journald rather than by a nightly job that might itself be broken. |
| SQLite bloat | Nightly `quick_check`, then `VACUUM`. **A failed integrity check does not vacuum** — rewriting a damaged database can turn a recoverable problem into an unrecoverable one. |
| `ops_events` growth | 90-day retention, triggered from the VM because the API sleeps. |
| Security updates | unattended-upgrades, security origins only, automatic reboot at 02:00 UTC. |

The stale-lock case deserves its own note, because it was a real hole. The old
cron wrappers used `flock -n || exit 0`. A job wedged holding the lock therefore
suppressed **every future run, forever**, while `cron.log` filled with cheerful
"skipped, previous run still going" lines. That failure looks healthy from
outside, which makes it exactly the kind this platform exists to eliminate.

---

## 7. Deploying

```bash
# from the repo root, on the laptop
scp -i <key> -r vm/scoutd vm/systemd vm/deploy.sh ubuntu@<vm>:/tmp/scoutd-deploy/
ssh -i <key> ubuntu@<vm> 'sudo bash /tmp/scoutd-deploy/deploy.sh'
```

Idempotent. It installs the code, creates `~/.config/scoutd/env` from the
existing key file if absent (and never overwrites it), installs and enables the
units, caps the journal, configures unattended reboots, and removes the three
cron entries it replaces — backing the crontab up first.

`arm-retry` and `tunnel-watch` are deliberately **left on cron**. They are
independent and self-limiting, and rewriting something that works earns nothing
but a chance to break it.

### Verifying a deployment

```bash
systemctl list-timers 'scout-*'
sudo systemctl start scout-health.service
journalctl -u scout-health -n 30 --no-pager
```

### Testing that alerting still works

Monitoring that has never been fired is a guess.

```bash
sudo systemctl start scout-selftest.service     # installed, not enabled
journalctl -u 'scout-alert@*' -n 20 --no-pager
```

---

## 8. Backup and restore

Nightly, `scout.db` is snapshotted with SQLite's online backup API (not a file
copy — a copy taken mid-write produces a torn database that looks fine until it
is needed), gzipped to `~/scoutd-state/backups/`, 14 kept.

```bash
# restore
sudo systemctl stop scout-scrape.service scout-push.service
gunzip -c ~/scoutd-state/backups/scout-YYYYMMDD.db.gz > /tmp/restore.db
sqlite3 /tmp/restore.db "PRAGMA quick_check;"      # verify BEFORE overwriting
cp ~/scout/data/scout.db ~/scout/data/scout.db.before-restore
mv /tmp/restore.db ~/scout/data/scout.db
```

**What is and is not protected.** These backups are local to the VM, so they
cover corruption and bad writes, not loss of the instance. That is acceptable
because `scout.db` is not the system of record: every successful row is pushed
to Postgres, which is where the durable history lives. The local file is a
staging buffer and a re-push source.

After restoring, `~/scout/data/.pushed_id` may point past the restored rows. Set
it to the highest id already in Postgres, or run
`push_to_scoutveda.py --all` — ingest upserts, so re-sending is safe.

---

## 9. Troubleshooting

| Symptom | First thing to check |
|---|---|
| `[ScoutVeda DOWN] deadman: vm-silent` | The VM is presumed off. Oracle console first, then `systemctl list-timers 'scout-*'`. |
| `low-scrape-yield` | Almost always amazon.in refusing the datacenter IP. Usually clears by the next run. Confirm the twelve-hour gap has not been shortened by a manual `--force`. |
| `stale-lock` | A job wedged. It has already been killed and the run proceeded; look at `journalctl -u scout-<task>` around the time in the alert for *why*. |
| `push-backlog` | The push exits 0 but the marker is not advancing. Check `~/scout/data/.pushed_id` against `SELECT MAX(id) FROM price_history`. |
| `data-stale` | Two consecutive passes produced nothing. Check the scrape unit ran at all before assuming Amazon is blocking. |
| `<task>-unit-failed` | Killed by systemd. The email says which: timeout or memory. |
| `reboot-overdue` | The automatic reboot window is not firing. `journalctl -u unattended-upgrades`. |
| Everything silent, no alerts at all | The reporting path itself. `journalctl -u scout-health | grep 'scoutd/ops'` — undeliverable alerts are logged locally. |

```bash
tail -5 ~/scoutd-state/runs.jsonl          # what ran, how long, peak memory
cat ~/scoutd-state/health_state.json       # what the watchdog is currently escalating
systemctl list-timers 'scout-*'            # what is scheduled
journalctl -u scout-scrape -n 50 --no-pager
```

---

## 10. Scaling, and where the real ceilings are

Adding a job is one file and one unit pair: write `tasks/<name>.py` exposing
`run(args) -> dict`, copy a service+timer pair, deploy. The envelope gives it
locking, timeouts, memory limits, reporting and recovery detection for free.

The honest limits, in the order they will actually bite:

1. **The IP, not the CPU.** More targets or more frequent passes means more
   requests from one datacenter IP, and that is what gets blocked. This box is
   nowhere near CPU- or RAM-bound at 15 targets twice a day. Scaling collection
   means more *addresses*, not more threads — residential proxies (not free) or
   the phone tunnel (free, but depends on a phone). Adding concurrency to the
   existing IP would reduce yield, not increase it.
2. **956 MB.** One Chromium at a time. Two concurrent scrapes would not fit, and
   the cgroup limits are set so that trying fails loudly instead of taking the
   box down.
3. **Supabase 500 MB.** Fine for years at the current row rate; the retention
   window on `ops_events` exists so operational noise never becomes the thing
   that fills it.
4. **GitHub Actions minutes.** `nightly-collect.yml` alone is ~1,408 min/month
   of a 2,000-minute allowance. If more scheduled work is ever needed, it goes
   on the VM — that collector is the obvious candidate to move.

---

## 11. Deliberately not done

- **No Docker/Kubernetes/Airflow/Celery.** All of them cost more RAM than the
  work does on a 956 MB box. Redis alone would be a meaningful fraction of it.
  systemd is already installed, already supervises, already survives reboots,
  and has no runtime cost.
- **No self-hosted n8n or a third VPS.** Standing decision, and it would not fit.
- **No retry-the-whole-pass logic.** Retrying a blocked scrape sooner makes the
  next one worse; the correct backoff for this failure is to wait for the next
  scheduled slot.
- **No `DATABASE_URL` on the VM.** Standing rule. A compromise of this box
  reaches authenticated API endpoints, not the database.
- **Memory ceilings are measured now, and still loose on purpose.** A real
  scrape pass peaks at **108 MB** against an 850 MB `MemoryMax` -- 8x headroom,
  where the rule of thumb says ~1.5x. Tightening to ~250 MB is safe and is
  outstanding work, not a decision against it.

- **A dead VM takes up to ~9 hours to be noticed.** The in-VM alerting is
  15-minute, but it dies with the box; the outside check runs 4×/day, and the
  gap between the 18:00 and 03:00 UTC runs is the worst case. Closing it means
  spending Actions minutes that are not there (§10). Given that the box has run
  for months without vanishing, and that the failure it covers is rare and not
  urgent at 3am, this was judged the right trade — but it is a choice, not an
  oversight, and it is the first thing to revisit if the VM ever does disappear.

- ~~**The reboot test has not been done.**~~ **Done, and it passed unsupervised.**
  The box rebooted itself in the configured window on 15 Aug 02:00 UTC, moved
  6.8.0-1054-oracle -> 6.8.0-1058-oracle, and brought all five timers back with
  no hand on the wheel. Boot persistence is now proven rather than configured.

- **No Scrapling (evaluated 19 Aug 2026, rejected).** Proposed as a fix for the
  scrape yield. It is not one, for two independent reasons.

  Its anti-bot work is *fingerprint*-based -- TLS spoofing, canvas and WebRTC
  leak prevention, defeating headless detection. That answers "does this client
  look like a bot?". This VM is failing a different question: "do I trust this
  IP?". The evidence is already in our own data -- the laptop's residential IP
  collects 14,940 rows against the same targets that this datacenter IP gets
  refused on. Same code, same targets, different IP, opposite result. Scrapling
  supplies no IPs of its own; it hands you a `ProxyRotator` and an empty list,
  and residential proxies cost money we have decided not to spend.

  Separately, its stealth fetchers cannot physically run here. `StealthyFetcher`
  launches a real patched Firefox (camoufox); one session budgets at ~1 GB
  against this box's 956 MB total. It would OOM before it ever reached amazon.in.

  The one genuinely good part -- adaptive parsing that re-finds an element after
  a site changes its markup -- solves a problem we have never actually had. In
  16 days of history every failure was the IP being refused and not one was a
  parse failure; when a pass gets through it lands 15 of 15 and parses cleanly.
  Rewriting working parse logic to defend against a hypothetical, on a box where
  the real fault is elsewhere, is motion rather than progress.

  If markup breakage ever does appear, the cheap answer is a canary -- alert when
  requests succeed but fields come back empty -- which buys the *detection* that
  matters for an unattended run without a dependency or a rewrite. Revisit only
  if that canary actually fires.
