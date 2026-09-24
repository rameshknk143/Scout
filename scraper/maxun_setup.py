"""
Maxun Setup Script - Configures Maxun for ScoutVeda scraping

Usage:
    python maxun_setup.py          # Interactive setup
    python maxun_setup.py --quick  # Quick setup with defaults
"""
import argparse
import json
import os
import requests
import sys
from pathlib import Path

MAXUN_URL = "http://127.0.0.1:8080"
CONFIG_FILE = Path(__file__).parent / ".maxun_config.json"


def register_user(email: str, password: str) -> dict:
    """Register a new user and get session token."""
    resp = requests.post(
        f"{MAXUN_URL}/api/auth/register",
        json={"email": email, "password": password},
        timeout=30
    )
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 400:
        # User already exists, try to login
        return login_user(email, password)
    else:
        raise Exception(f"Registration failed: {resp.status_code} {resp.text}")


def login_user(email: str, password: str) -> dict:
    """Login and get session token."""
    resp = requests.post(
        f"{MAXUN_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30
    )
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f"Login failed: {resp.status_code} {resp.text}")


def get_api_key(session) -> str:
    """Generate or retrieve API key."""
    # Try to get existing key
    resp = session.get(f"{MAXUN_URL}/api/auth/api-key", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('api_key'):
            return data['api_key']
    
    # Generate new key
    resp = session.post(f"{MAXUN_URL}/api/auth/generate-api-key", timeout=10)
    if resp.status_code == 200:
        return resp.json().get('api_key')
    else:
        raise Exception(f"Failed to generate API key: {resp.status_code}")


def create_robot(session, api_key: str, name: str, url: str) -> str:
    """Create a new robot and return its ID."""
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    
    # Start recording
    resp = session.post(
        f"{MAXUN_URL}/api/robots",
        headers=headers,
        json={"name": name, "url": url},
        timeout=60
    )
    
    if resp.status_code in (200, 201):
        return resp.json().get('robot', {}).get('id') or resp.json().get('id')
    else:
        print(f"  Warning: Failed to create robot '{name}': {resp.status_code}")
        return None


def get_robots(session, api_key: str) -> list:
    """List all robots."""
    headers = {"x-api-key": api_key}
    resp = session.get(f"{MAXUN_URL}/api/robots", headers=headers, timeout=10)
    if resp.status_code == 200:
        return resp.json().get('robots', []) or resp.json().get('data', [])
    return []


AMAZON_CATEGORIES = [
    ("Electronics Accessories", "electronics"),
    ("Home & Kitchen", "home-kitchen"),
    ("Beauty & Personal Care", "beauty"),
    ("Health & Personal Care", "hpc"),
    ("Grocery & Gourmet Foods", "grocery"),
    ("Shoes & Handbags", "shoes-handbags"),
    ("Pet Supplies", "pet-supplies"),
    ("Toys & Games", "toys-games"),
    ("Baby Products", "baby-products"),
    ("Watches & Gifting", "watches-gifting"),
    ("Clothing & Accessories", "clothing"),
    ("Sports & Fitness", "sports-fitness"),
    ("Garden & Outdoors", "garden-outdoors"),
    ("Computers & Accessories", "computers-accessories"),
    ("Books", "books"),
]


def main():
    parser = argparse.ArgumentParser(description="Setup Maxun for ScoutVeda")
    parser.add_argument("--email", default="scoutveda@maxun.local")
    parser.add_argument("--password", default="ScoutMaxun2026!")
    parser.add_argument("--quick", action="store_true", help="Use defaults without prompts")
    parser.add_argument("--list-robots", action="store_true", help="Just list existing robots")
    args = parser.parse_args()
    
    print("=" * 60)
    print("SCOUTVEDA MAXUN SETUP")
    print("=" * 60)
    
    # Check if backend is running
    try:
        resp = requests.get(MAXUN_URL, timeout=5)
        if resp.status_code != 200:
            print(f"ERROR: Maxun backend not reachable at {MAXUN_URL}")
            print(f"Status: {resp.status_code}")
            print("Please start Maxun first: cd maxun && npm run server")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot connect to Maxun: {e}")
        sys.exit(1)
    
    # List existing robots
    if args.list_robots:
        session = requests.Session()
        # Need to login first
        try:
            user = login_user(args.email, args.password)
            api_key = get_api_key(session)
            robots = get_robots(session, api_key)
            print(f"\nFound {len(robots)} robots:")
            for r in robots:
                rid = r.get('id') or r.get('robotId', 'unknown')
                name = r.get('name') or r.get('title', 'unnamed')
                print(f"  - {rid}: {name}")
        except Exception as e:
            print(f"Error: {e}")
        return
    
    # Register/Login
    print(f"\nAuthenticating as {args.email}...")
    session = requests.Session()
    try:
        user = register_user(args.email, args.password)
        api_key = get_api_key(session)
        print(f"✓ Authenticated. API Key: {api_key[:20]}...")
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)
    
    # Get existing robots
    robots = get_robots(session, api_key)
    existing_ids = {r.get('id') or r.get('robotId') for r in robots}
    print(f"\nExisting robots: {len(robots)}")
    
    # Create robots for categories (skip if already exists)
    print("\nCreating robots for Amazon categories...")
    created = []
    for category, slug in AMAZON_CATEGORIES:
        # Check if we already have a robot for this
        existing = [r for r in robots if category.lower() in str(r).lower()]
        if existing:
            print(f"  ✓ {category}: Already exists")
            continue
        
        robot_url = f"https://www.amazon.in/gp/bestsellers/{slug}/"
        rid = create_robot(session, api_key, category, robot_url)
        if rid:
            created.append((rid, category))
            print(f"  ✓ Created: {category} ({rid})")
        else:
            print(f"  ✗ Failed: {category}")
    
    # Save configuration
    config = {
        "maxun_api_url": MAXUN_URL,
        "maxun_api_key": api_key,
        "robots": created,
        "last_updated": __import__('datetime').datetime.now().isoformat()
    }
    
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    print(f"\nConfiguration saved to {CONFIG_FILE}")
    
    # Print next steps
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print(f"""
1. Record each robot in the Maxun UI:
   Open http://localhost:5173 and record a scrape for each category
   
2. Add to your environment (create or edit scraper/laptop.env):
   MAXUN_API_KEY={api_key}
   MAXUN_ROBOTS='{";".join(f"{rid}={cat}" for rid, cat in created)}
   TRIGGER_EVERY_HOURS=1

3. Run the bridge manually to test:
   cd scraper
   python maxun_bridge.py --category "Home & Kitchen" --limit 3

4. Set up scheduled runs with laptop_mode.py:
   python laptop_mode.py
""")
    
    # Show robots for config
    if created:
        print("\nROBOT IDS FOR CONFIGURATION:")
        print("-" * 40)
        for rid, cat in created:
            print(f'  {rid}={cat}')


if __name__ == "__main__":
    main()
