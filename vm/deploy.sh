#!/usr/bin/env bash
# Install or update scoutd on the scraping VM. Idempotent: safe to re-run.
#
#   scp -r vm ubuntu@<vm>:/tmp/scoutd-deploy && sudo bash /tmp/scoutd-deploy/deploy.sh
#
# Why a script rather than a list of commands in a document: this box has to be
# rebuildable. Everything that has ever been done to it by hand is invisible the
# moment it is gone, and a VM that only exists as accumulated undocumented
# tinkering is a single point of failure with no recovery path. Anything below
# can be re-run on a blank Ubuntu box to get back to a working platform.
set -euo pipefail

USER_NAME="${SCOUTD_USER:-ubuntu}"
HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME_DIR/scoutd"
CONF_DIR="$HOME_DIR/.config/scoutd"
UNITS=(scout-scrape scout-push scout-keepwarm scout-health scout-maintain)

if [ "$(id -u)" -ne 0 ]; then
  echo "This needs root (systemd units, journald and apt config). Re-run with sudo." >&2
  exit 1
fi

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# --- 1. code ----------------------------------------------------------------
say "Installing scoutd to $DEST"
install -d -o "$USER_NAME" -g "$USER_NAME" -m 755 "$DEST"
rm -rf "$DEST/scoutd"
cp -r "$SRC/scoutd" "$DEST/scoutd"
# Stale .pyc from a previous version shadows a module that was deleted, which
# produces a failure that survives a fix and makes no sense from the outside.
find "$DEST" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
chown -R "$USER_NAME:$USER_NAME" "$DEST"

install -d -o "$USER_NAME" -g "$USER_NAME" -m 755 "$HOME_DIR/scoutd-state"
install -d -o "$USER_NAME" -g "$USER_NAME" -m 755 "$HOME_DIR/scoutd-state/logs"
install -d -o "$USER_NAME" -g "$USER_NAME" -m 755 "$HOME_DIR/scoutd-state/backups"

# --- 2. secrets -------------------------------------------------------------
# 0600 and owned by the service user. The API key is the only credential on this
# box, and the standing rule is that the production DATABASE_URL never lands
# here -- the key can only reach authenticated endpoints, so a compromise of
# this VM cannot become a compromise of the database.
say "Configuring secrets in $CONF_DIR/env"
install -d -o "$USER_NAME" -g "$USER_NAME" -m 700 "$CONF_DIR"
if [ ! -f "$CONF_DIR/env" ]; then
  KEY=""
  [ -f "$HOME_DIR/scout/.scout_api_key" ] && KEY="$(tr -d '\r\n' < "$HOME_DIR/scout/.scout_api_key")"
  cat > "$CONF_DIR/env" <<EOF
# scoutd environment. Read by every unit via EnvironmentFile=.
# Never commit this file. Rotate by editing it -- nothing caches the value.
SCOUT_API_KEY=$KEY
SCOUT_API_URL=https://scout-api-3yvy.onrender.com
EOF
  echo "  created from the existing .scout_api_key"
else
  echo "  already present, left alone"
fi
chown "$USER_NAME:$USER_NAME" "$CONF_DIR/env"
chmod 600 "$CONF_DIR/env"

# --- 3. systemd -------------------------------------------------------------
say "Installing systemd units"
install -m 644 "$SRC"/systemd/*.service "$SRC"/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload
for unit in "${UNITS[@]}"; do
  systemctl enable --now "$unit.timer" >/dev/null
  echo "  enabled $unit.timer"
done

# --- 4. journal cap ---------------------------------------------------------
# systemd's default is 10% of the filesystem: 4.5 GB of logs on a box with
# 956 MB of RAM. Capping it in journald.conf means the limit is enforced
# continuously by journald itself, rather than depending on a nightly job that
# might be the thing that is broken.
say "Capping the systemd journal at 200M"
install -d -m 755 /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/scoutd.conf <<'EOF'
[Journal]
SystemMaxUse=200M
SystemMaxFileSize=20M
MaxRetentionSec=60day
EOF
systemctl restart systemd-journald

# --- 5. unattended security updates, including the reboot -------------------
# unattended-upgrades was already installing security fixes, but nothing ever
# rebooted, so a kernel and libc update sat unapplied from 1 Aug onward. Over
# six months that is both a growing security gap and a growing risk in itself:
# every deferred reboot makes it less certain the box still boots cleanly, and
# guarantees it finds out at a moment nobody chose.
say "Enabling automatic security updates with a reboot window"
cat > /etc/apt/apt.conf.d/52scoutd-unattended <<'EOF'
// 02:00 UTC = 07:30 IST. Between the 15:20 and 03:20 scrapes, with 80 minutes
// of margin before the next one, and clear of the 01:10 maintenance window.
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";
EOF

# --- 6. retire the cron jobs scoutd now owns --------------------------------
# Only the three that have systemd equivalents. arm-retry and tunnel-watch are
# left exactly as they are: they are independent, self-limiting, and rewriting
# something that works earns nothing but a chance to break it.
say "Migrating cron jobs to systemd timers"
CRON_BAK="$HOME_DIR/crontab.bak.$(date -u +%Y%m%d%H%M%S)"
if crontab -u "$USER_NAME" -l > "$CRON_BAK" 2>/dev/null; then
  chown "$USER_NAME:$USER_NAME" "$CRON_BAK"
  echo "  backed up current crontab to $CRON_BAK"
  grep -v -e 'scout/run\.sh' -e 'scout/push\.sh' -e 'keep-warm\.sh' "$CRON_BAK" \
    | crontab -u "$USER_NAME" -
  echo "  remaining cron entries:"
  crontab -u "$USER_NAME" -l | sed 's/^/    /'
fi

# --- 7. report --------------------------------------------------------------
say "Installed. Next runs:"
systemctl list-timers 'scout-*' --no-pager
echo
echo "Verify a task by hand:  sudo systemctl start scout-health.service && journalctl -u scout-health -n 30 --no-pager"
