# Phone Tunnel — Production Setup v2 (2026-09-01)

**Goal:** Scout VM scrapes through your phone's IP. Set up once, runs forever, self-heals.

## Architecture v2 (simpler than v1)

```
┌─────────────────────────┐          ┌──────────────────────────────┐
│ YOUR PHONE (Termux)     │          │ ORACLE VM                    │
│                         │          │                              │
│ tunnel.sh (supervisor)  │  ssh -R  │ sshd :22                     │
│  └─ ssh -N -R 1080  ────┼──────────┼► 127.0.0.1:1080 (SOCKS)      │
│     (ssh IS the proxy)  │          │  └─ scraper uses socks5h://  │
│                         │          │     127.0.0.1:1080 (unchanged)│
└─────────────────────────┘          └──────────────────────────────┘
```

- **v1** used two apps: Termux (tunnel) + Every Proxy (SOCKS). Every Proxy wedged on
  2026-09-01 (granted connections, returned zero bytes) — needed a phone reboot.
- **v2** removes Every Proxy entirely. `ssh -R 127.0.0.1:1080` (dynamic, no destination)
  makes ssh itself the SOCKS5 proxy on the VM. One process = one thing to heal.
  Proxy failure = tunnel failure = auto-restart. Every Proxy can stay installed but OFF.

## What auto-recovers from what

| Interruption | What happens | Your action |
|---|---|---|
| WiFi ↔ Mobile data switch | ssh drops → supervisor reconnects ≤35 s | none |
| Internet outage (minutes/hours) | loop keeps retrying every 30 s | none |
| Termux process killed by Android | supervisor loop restarts ssh | none |
| Termux swiped from recents | foreground wake-lock usually keeps it alive; if OEM kills it | none until next reboot or next time you open Termux (bashrc auto-starts it silently) |
| Phone rebooted | **Termux:Boot starts everything** ~1 min after boot | none |
| Full-path failure detected (every 20 min test) | ssh restarted automatically; after 3 fails (1 h) → phone notification | read notification; reboot phone only if it persists |
| Every Proxy-style wedge | impossible — no separate proxy app exists in v2 | — |

## The one supervisor script: `~/tunnel.sh`

- Single-instance lock (boot + manual open can't create duplicates)
- ssh with keepalives (30 s), reconnect loop every 30 s, `ExitOnForwardFailure`
- **Health test every ~20 min:** real request VM → tunnel → internet; logs the exit IP
- Status file `~/tunnel-status.txt` (`cat` it any time)
- Log `~/tunnel.log` with auto-rotation at 500 KB
- Phone notification only on real trouble (no silent failures, no spam)

## Startup chain (why it always comes back)

1. **Phone boots** → Termux:Boot runs `~/.termux/boot/10-scout-tunnel.sh` → supervisor starts.
2. **Termux opened (any time)** → `.bashrc` guard starts supervisor if not already running.
3. **Supervisor dies** → next boot or next Termux open restarts it. (Termux has no true
   daemon-init; boot+open coverage is the maximum Android allows without root.)

## Android settings checklist (one time)

- [x] Termux → Battery → **Unrestricted**
- [ ] **Termux:Boot** app installed (F-Droid, same signature) and **opened once**
- [ ] **Termux:API** app installed (F-Droid) — enables failure notifications
- [ ] Termux notifications **allowed** (Android Settings → Apps → Termux → Notifications)
- [ ] Xiaomi/Realme/Oppo/Vivo only: Security app → **Autostart → allow Termux**
- [ ] Android 12+ only: phantom process killer is a known risk for long-running child
      processes. Steady state here is ~2 processes (well under its radar). If kills are
      ever observed: `adb shell device_config put activity_manager max_phantom_processes 2147483647`

## Known honest limitations (Android, not fixable from Termux)

1. **Force-close** (Settings → Force stop) kills Termux dead. Recovery: automatic at next
   reboot or next Termux open. Don't force-stop Termux.
2. **Some OEMs** kill background apps despite wake-locks (Aggressive battery management).
   Battery=Unrestricted + Autostart covers the common ones; if the tunnel dies nightly on
   the same schedule, that's the OEM — tell me and we add the adb whitelist step.
3. **Extended Doze** on very long idle can delay reconnects by minutes. Acceptable: the VM
   side falls back automatically and `tunnel-watch.log` records the gap.

## VM side (unchanged, already verified 2026-09-01)

- `tunnel-watch.sh` samples 1080 every 5 min → `~/tunnel-watch.log` (up/down)
- `common.py` routes scrapes via `socks5h://127.0.0.1:1080` when UP, falls back when DOWN
- Exit-IP proof 2026-09-01 14:05 IST: `103.160.27.14` (carrier) · amazon.in → HTTP 200, 400 KB

## Verification protocol after any change

1. `cat ~/tunnel-status.txt` on the phone → STATE=UP with a carrier exit IP
2. From VM: `curl --socks5-hostname 127.0.0.1:1080 https://api.ipify.org` → not 140.245.239.162
3. From VM: amazon.in product page through tunnel → HTTP 200, ~400 KB (block page ≈ 3.8 KB)
4. Reboot test: reboot phone, touch nothing, VM listener must reappear ≤3 min

## Appendix — v2 install block (paste into Termux, 2026-09-01)

Replaces v1 (kills old loop + Every Proxy dependency), installs supervisor, autostart on
Termux open (bashrc) + on boot (Termux:Boot). One paste, one Enter:

```bash
pkill -f tunnel.sh; pkill -f "ssh.*140.245.239.162"; sleep 2
cat > ~/tunnel.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Scout tunnel supervisor v2 — ssh IS the tunnel AND the SOCKS proxy (no Every Proxy)
VM=ubuntu@140.245.239.162
VMIP=140.245.239.162
KEY="$HOME/.ssh/id_ed25519"
PIDFILE="$HOME/.tunnel.pid"
STATUS="$HOME/tunnel-status.txt"
LOG="$HOME/tunnel.log"
log(){ echo "$(date '+%F %T') $*" >> "$LOG"; }
notify(){ command -v termux-notification >/dev/null 2>&1 && termux-notification --title "Scout tunnel DOWN" --content "$1" --priority high 2>/dev/null; }
if command -v flock >/dev/null 2>&1; then
  exec 9>"$HOME/.tunnel.lock"; flock -n 9 || exit 0
else
  [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null && exit 0
fi
echo $$ > "$PIDFILE"
termux-wake-lock 2>/dev/null
alive(){ pgrep -f "ssh .*$VMIP" >/dev/null 2>&1; }
start_ssh(){
  nohup ssh -i "$KEY" -N -R 127.0.0.1:1080 \
    -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
    -o StrictHostKeyChecking=accept-new -o BatchMode=yes \
    "$VM" >> "$LOG" 2>&1 &
  sleep 5
}
health(){
  IP=$(ssh -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 "$VM" \
    "curl -s -m 25 --socks5-hostname 127.0.0.1:1080 https://api.ipify.org" 2>/dev/null)
  [ -n "$IP" ] && [ "$IP" != "$VMIP" ]
}
FAILS=0; LAST=0
log "supervisor v2 started pid $$"
while true; do
  [ -f "$LOG" ] && [ "$(wc -c < "$LOG")" -gt 500000 ] && tail -c 200000 "$LOG" > "$LOG.t" && mv "$LOG.t" "$LOG"
  if ! alive; then start_ssh; fi
  NOW=$(date +%s)
  if [ $((NOW - LAST)) -ge 1200 ]; then
    LAST=$NOW
    if health; then
      FAILS=0
      echo "STATE=UP exit_ip=$IP checked=$(date '+%F %T')" > "$STATUS"
      log "health OK exit=$IP"
    else
      FAILS=$((FAILS+1))
      echo "STATE=DEGRADED fails=$FAILS checked=$(date '+%F %T')" > "$STATUS"
      log "health FAIL #$FAILS - restarting ssh"
      pkill -f "ssh .*$VMIP" 2>/dev/null
      start_ssh
      [ "$FAILS" -eq 3 ] && notify "3 failed checks in 1h. If this repeats, reboot the phone."
    fi
  fi
  sleep 30
done
EOF
chmod +x ~/tunnel.sh
grep -q "tunnel.sh" ~/.bashrc 2>/dev/null || echo 'pgrep -f "bash.*tunnel.sh" >/dev/null 2>&1 || nohup bash ~/tunnel.sh >/dev/null 2>&1 &' >> ~/.bashrc
mkdir -p ~/.termux/boot
printf '#!/data/data/com.termux/files/usr/bin/bash\ntermux-wake-lock\npgrep -f "bash.*tunnel.sh" >/dev/null 2>&1 || nohup bash ~/tunnel.sh >/dev/null 2>&1 &\n' > ~/.termux/boot/10-scout-tunnel.sh
chmod +x ~/.termux/boot/10-scout-tunnel.sh
nohup bash ~/tunnel.sh >/dev/null 2>&1 &
echo "=== INSTALLED v2 — tell Hermes 'installed' ==="
```

Then (one time): install **Termux:Boot** and **Termux:API** from F-Droid (same developer,
Termux must stay installed), open each once. Termux:API enables failure notifications;
Termux:Boot enables start-on-reboot. Every Proxy app: leave installed but toggle OFF.
