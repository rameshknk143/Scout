#!/data/data/com.termux/files/usr/bin/bash
# Scout tunnel supervisor v2 — ssh IS the tunnel AND the SOCKS proxy (no Every Proxy)
# Health-tested every 20 min through the real path (VM -> tunnel -> internet -> back).
VM=ubuntu@140.245.239.162
VMIP=140.245.239.162
KEY="$HOME/.ssh/id_ed25519"
PIDFILE="$HOME/.tunnel.pid"
STATUS="$HOME/tunnel-status.txt"
LOG="$HOME/tunnel.log"

log(){ echo "$(date '+%F %T') $*" >> "$LOG"; }
notify(){ command -v termux-notification >/dev/null 2>&1 && termux-notification --title "Scout tunnel DOWN" --content "$1" --priority high 2>/dev/null; }

# single instance (flock if present, else pidfile)
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
  # log rotation at 500 KB
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
