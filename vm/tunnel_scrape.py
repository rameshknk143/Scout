#!/usr/bin/env python3
"""
Tunnel-aware scrape wrapper for the VM.

When the phone tunnel is up (SOCKS5 at 127.0.0.1:1080), this script
sets up proxy environment variables so the underlying scraper routes
through the residential IP instead of the blocked datacenter IP.

Usage:
    python3 tunnel_scrape.py [--force-direct] [--test-tunnel]

If --test-tunnel is passed, it prints the exit IP through the tunnel
without running the actual scrape.
"""
import os
import subprocess
import sys
import urllib.request
import urllib.error
import json
import argparse

TUNNEL_SOCKS = "socks5h://127.0.0.1:1080"
VM_PUBLIC_IP = "140.245.239.162"
IPIFY_URL = "https://api.ipify.org?format=json"


def check_tunnel():
    """Check if tunnel is up by testing SOCKS proxy via curl."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-m", "15", "--socks5-hostname", "127.0.0.1:1080", IPIFY_URL],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("ip", ""), True
    except Exception:
        pass
    return "", False


def check_direct_ip():
    """Check what IP we appear as without proxy."""
    try:
        req = urllib.request.Request(IPIFY_URL)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode()).get("ip", "")
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Tunnel-aware VM scraper wrapper")
    parser.add_argument("--force-direct", action="store_true",
                        help="Skip tunnel even if available")
    parser.add_argument("--test-tunnel", action="store_true",
                        help="Just test tunnel, don't run scrape")
    args = parser.parse_args()

    if args.test_tunnel:
        ip, up = check_tunnel()
        print(json.dumps({"tunnel_up": up, "exit_ip": ip, "vm_ip": VM_PUBLIC_IP}))
        return 0

    # Check tunnel status
    tunnel_ip, tunnel_up = check_tunnel()

    if args.force_direct or not tunnel_up:
        print("[tunnel-scrape] Using direct route (tunnel down or forced)")
        # Run scraper with no proxy
        env = os.environ.copy()
        env.pop("HTTPS_PROXY", None)
        env.pop("http_proxy", None)
        env.pop("all_proxy", None)
        cmd = [sys.executable, "-m", "scoutd.run", "scrape"]
    else:
        print(f"[tunnel-scrape] Tunnel UP! Routing through residential IP: {tunnel_ip}")
        # Set proxy env vars for the scraper
        env = os.environ.copy()
        env["HTTPS_PROXY"] = TUNNEL_SOCKS
        env["http_proxy"] = TUNNEL_SOCKS
        env["all_proxy"] = TUNNEL_SOCKS
        # Also set for Python's urllib/requests
        env["SCOUT_USE_TUNNEL"] = "1"
        cmd = [sys.executable, "-m", "scoutd.run", "scrape"]

    # Run the actual scrape
    result = subprocess.run(cmd, env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    sys.exit(main())
