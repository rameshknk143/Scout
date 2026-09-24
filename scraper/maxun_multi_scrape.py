"""
Maxun Multi-Category Scraper for ScoutVeda

Runs multiple robots sequentially across Amazon categories to maximize output.
Each robot scrapes ~30 products per category. With 15 categories × hourly runs,
this can produce ~450 rows/day from residential IPs.
"""
import argparse
import json
import os
import sys
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

# Configuration
MAXUN_URL = os.environ.get("MAXUN_API_URL", "http://127.0.0.1:8080")
API_KEY = os.environ.get("MAXUN_API_KEY", "")
SCOUT_API_URL = os.environ.get("SCOUT_API_URL", "https://scout-api-3yvy.onrender.com")
SCOUT_API_KEY = os.environ.get("SCOUT_API_KEY", "")

# Category mapping: (ScoutVeda category, Amazon bestseller slug)
CATEGORIES = [
    ("Electronics Accessories", "electronics-accessories"),
    ("Home & Kitchen", "home-kitchen"),
    ("Beauty & Personal Care", "beauty"),
    ("Health & Personal Care", "hpc"),
    ("Grocery & Gourmet Foods", "grocery-gourmet-food"),
    ("Shoes & Handbags", "shoes-handbags"),
    ("Pet Supplies", "pet-supplies"),
    ("Toys & Games", "toys-games"),
    ("Baby Products", "baby-products"),
    ("Watches & Gifting", "watches-jewelry"),
    ("Clothing & Accessories", "clothing-fashion"),
    ("Sports & Fitness", "sports-outdoors"),
    ("Garden & Outdoors", "garden-outdoors"),
    ("Computers & Accessories", "computers-accessories"),
    ("Books", "books"),
]

STATE_FILE = Path(__file__).parent / ".maxun_multi_state.json"


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except:
        return {"last_runs": {}, "failed_robots": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_robots(api_key):
    """Get list of all robots from Maxun."""
    headers = {"x-api-key": api_key}
    resp = requests.get(f"{MAXUN_URL}/api/robots", headers=headers, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        return data.get('robots', []) or data.get('data', [])
    return []


def run_robot(robot_id, robot_name):
    """Trigger a robot run and return the run ID."""
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    
    log(f"  Triggering {robot_name} ({robot_id})...")
    resp = requests.post(
        f"{MAXUN_URL}/api/robots/{robot_id}/runs",
        headers=headers,
        json={},
        timeout=30
    )
    
    if resp.status_code in (200, 201):
        run_id = resp.json().get('run', {}).get('runId')
        log(f"    Run started: {run_id}")
        return run_id
    else:
        log(f"    Failed: {resp.status_code} - {resp.text[:100]}")
        return None


def wait_for_run(robot_id, run_id, timeout=180):
    """Wait for a run to complete."""
    headers = {"x-api-key": API_KEY}
    start = time.time()
    
    while time.time() - start < timeout:
        resp = requests.get(
            f"{MAXUN_URL}/api/robots/{robot_id}/runs/{run_id}",
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            status = resp.json().get('run', {}).get('status', '')
            if status in ('success', 'completed'):
                return True, resp.json().get('run', {}).get('data', {})
            elif status in ('failed', 'error'):
                return False, None
        
        time.sleep(5)
    
    return False, None


def forward_to_scoutveda(run_data, category):
    """Forward scraped data to ScoutVeda."""
    if not SCOUT_API_KEY:
        log("    Warning: SCOUT_API_KEY not set, skipping forward")
        return False
    
    # Extract items from run data
    items = []
    for bucket in ("listData", "textData", "crawlData"):
        blob = run_data.get(bucket)
        if isinstance(blob, list):
            for row in blob:
                if isinstance(row, dict) and 'asin' in row:
                    items.append({
                        "asin": str(row.get('asin', '')).strip().upper(),
                        "title": row.get('title'),
                        "price": row.get('price'),
                        "rating": row.get('rating'),
                        "review_count": row.get('review_count'),
                        "rank": row.get('rank'),
                        "image_url": row.get('image_url'),
                    })
    
    if not items:
        log("    No valid items to forward")
        return False
    
    # Post to ScoutVeda
    resp = requests.post(
        f"{SCOUT_API_URL}/ingest/maxun",
        headers={"X-Scout-Key": SCOUT_API_KEY, "Content-Type": "application/json"},
        json={"items": items, "category": category},
        timeout=60
    )
    
    if resp.status_code == 200:
        log(f"    Forwarded {len(items)} items to ScoutVeda")
        return True
    else:
        log(f"    Forward failed: {resp.status_code}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Maxun robots for all categories")
    parser.add_argument("--categories", nargs="+", help="Specific categories to run")
    parser.add_argument("--limit", type=int, default=5, help="Max robots to run per pass")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()
    
    if not API_KEY:
        print("ERROR: MAXUN_API_KEY not set")
        sys.exit(1)
    
    log("=" * 60)
    log("MAXUN MULTI-CATEGORY SCRAPER")
    log("=" * 60)
    
    # Get available robots
    robots = get_robots(API_KEY)
    log(f"Found {len(robots)} robots in Maxun")
    
    if not robots:
        log("No robots found! Create robots in Maxun UI first:")
        log("  1. Open http://localhost:5173")
        log("  2. Click 'New Robot'")
        log("  3. Record a scraper for each Amazon category")
        log("  4. Save and note the Robot ID")
        sys.exit(1)
    
    # Build robot map
    robot_map = {}
    for r in robots:
        rid = r.get('id') or r.get('robotId')
        name = r.get('name') or r.get('title', 'Unnamed')
        robot_map[rid] = name
    
    log(f"\nAvailable robots:")
    for rid, name in list(robot_map.items())[:10]:
        log(f"  • {name}: {rid}")
    
    # Determine which robots to run
    state = load_state()
    now = datetime.now(timezone.utc)
    
    robots_to_run = []
    for rid, rname in robot_map.items():
        # Check if we've run this robot recently (last 55 minutes)
        last_run = state.get("last_runs", {}).get(rid)
        if last_run:
            last_dt = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
            elapsed = (now - last_dt).total_seconds() / 3600
            if elapsed < 1:  # Less than 1 hour since last run
                log(f"  Skipping {rname} (ran {elapsed:.1f}h ago)")
                continue
        
        robots_to_run.append((rid, rname))
        
        if len(robots_to_run) >= args.limit:
            break
    
    if not robots_to_run:
        log("\nAll robots ran recently. Waiting for cooldown...")
        return
    
    log(f"\nRunning {len(robots_to_run)} robots...")
    
    stats = {
        "started": now.isoformat(),
        "total": len(robots_to_run),
        "success": 0,
        "failed": 0,
        "items_forwarded": 0,
    }
    
    for robot_id, robot_name in robots_to_run:
        log(f"\n--- {robot_name} ---")
        
        # Run the robot
        run_id = run_robot(robot_id, robot_name)
        if not run_id:
            stats["failed"] += 1
            continue
        
        # Wait for completion
        success, run_data = wait_for_run(robot_id, run_id)
        if not success:
            log(f"  Run failed or timed out")
            stats["failed"] += 1
            state.setdefault("failed_robots", []).append(robot_id)
            save_state(state)
            continue
        
        # Determine category from robot name
        category = robot_name.split()[0] if robot_name else "Unknown"
        
        # Forward to ScoutVeda
        if forward_to_scoutveda(run_data, category):
            stats["success"] += 1
            # Count items
            for bucket in ("listData", "textData"):
                if isinstance(run_data.get(bucket), list):
                    stats["items_forwarded"] += len(run_data[bucket])
        
        # Update state
        state["last_runs"][robot_id] = now.isoformat()
        save_state(state)
        
        # Delay between robots (be polite to Amazon)
        log(f"  Waiting 10s before next robot...")
        time.sleep(10)
    
    log("\n" + "=" * 60)
    log(f"RESULTS: {stats['success']}/{stats['total']} successful")
    log(f"Items forwarded: {stats['items_forwarded']}")
    log("=" * 60)
    
    # Calculate projected daily output
    if stats['success'] > 0:
        projected_daily = stats['items_forwarded'] * 24 // max(len(robots_to_run), 1)
        log(f"\nProjected daily output: ~{projected_daily} rows")
    
    return 0 if stats['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
