"""
Maxun Service Manager - Keeps all Maxun services running
Usage: python maxun_service_manager.py [start|stop|status]
"""
import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
import socket
import requests

MAXUN_DIR = Path(r"D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun")
BROWSER_DIR = MAXUN_DIR / "browser"
STATE_FILE = Path(__file__).parent / ".maxun_services.state"

# Service configurations
SERVICES = {
    "backend": {
        "name": "Backend API",
        "cmd": ["node", "server/dist/server/src/server.js"],
        "cwd": MAXUN_DIR,
        "port": 8080,
        "health_check": "http://127.0.0.1:8080",
    },
    "frontend": {
        "name": "Frontend UI",
        "cmd": ["node", "node_modules/vite/bin/vite.js", "--host"],
        "cwd": MAXUN_DIR,
        "port": 5173,
        "health_check": "http://127.0.0.1:5173",
    },
    "browser": {
        "name": "Browser Service",
        "cmd": ["node", "dist/server.js"],
        "cwd": BROWSER_DIR,
        "port": 3002,
        "health_check": "http://127.0.0.1:3002/health",
    },
}

_processes = {}


def log(msg, level="INFO"):
    print(f"[{level}] {msg}", flush=True)


def is_port_open(port, host="127.0.0.1"):
    """Check if a port is listening."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except:
        return False


def load_state():
    """Load process IDs from state file."""
    try:
        if STATE_FILE.exists():
            return eval(STATE_FILE.read_text())
    except:
        pass
    return {}


def save_state(state):
    """Save process IDs to state file."""
    try:
        STATE_FILE.write_text(str(state))
    except:
        pass


def start_service(name):
    """Start a single service."""
    if name not in SERVICES:
        log(f"Unknown service: {name}", "ERROR")
        return False

    svc = SERVICES[name]
    
    # Check if already running
    if is_port_open(svc["port"]):
        log(f"{svc['name']} is already running on port {svc['port']}")
        return True

    log(f"Starting {svc['name']}...")
    try:
        proc = subprocess.Popen(
            svc["cmd"],
            cwd=str(svc["cwd"]),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
        _processes[name] = proc
        state = load_state()
        state[name] = proc.pid
        save_state(state)
        log(f"{svc['name']} started (PID {proc.pid})")
        return True
    except Exception as e:
        log(f"Failed to start {svc['name']}: {e}", "ERROR")
        return False


def stop_service(name):
    """Stop a single service."""
    if name not in SERVICES:
        return

    if name in _processes:
        proc = _processes[name]
        try:
            if os.name == 'nt':
                proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                proc.terminate()
            proc.wait(timeout=5)
            log(f"{SERVICES[name]['name']} stopped")
        except:
            try:
                proc.kill()
                log(f"{SERVICES[name]['name']} killed")
            except:
                pass
        del _processes[name]

    # Also kill by PID if in state file
    state = load_state()
    if name in state:
        pid = state[name]
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
        except:
            pass
        del state[name]
        save_state(state)


def show_status():
    """Show status of all services."""
    print("\n" + "="*60)
    print("MAXUN SERVICE STATUS")
    print("="*60 + "\n")
    
    for name, svc in SERVICES.items():
        is_running = is_port_open(svc["port"])
        status = "✓ RUNNING" if is_running else "✗ DOWN"
        print(f"{status:12} {svc['name']:20} (Port {svc['port']})")
        
        # Try health check
        if is_running and svc["health_check"]:
            try:
                r = requests.get(svc["health_check"], timeout=3)
                if r.status_code == 200:
                    if '/health' in svc["health_check"]:
                        data = r.json()
                        print(f"           Health: {data.get('status', 'unknown')}")
                    else:
                        print(f"           HTTP: {r.status_code}")
            except:
                pass
        print()


def start_all():
    """Start all services."""
    log("Starting all Maxun services...")
    
    for name in SERVICES:
        start_service(name)
        time.sleep(2)  # Give each service time to bind port
    
    show_status()
    
    log("\nAccess Maxun UI at: http://localhost:5173")
    log("Login: scoutveda@maxun.local / ScoutMaxun2026!")
    log("\nTo run scraper:")
    log("  cd scraper && python maxun_multi_scrape.py --limit 5")


def stop_all():
    """Stop all services."""
    log("Stopping all Maxun services...")
    
    for name in list(SERVICES.keys()):
        stop_service(name)
    
    log("All services stopped.")


def main():
    parser = argparse.ArgumentParser(description="Maxun Service Manager")
    parser.add_argument("command", choices=["start", "stop", "status"], help="Command to run")
    args = parser.parse_args()

    if args.command == "start":
        start_all()
    elif args.command == "stop":
        stop_all()
    elif args.command == "status":
        show_status()


if __name__ == "__main__":
    main()
