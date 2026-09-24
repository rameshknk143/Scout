#!/usr/bin/env python3
"""
Start Maxun services in correct order for ScoutVeda.
Run this script when setting up or restarting Maxun.
"""
import subprocess
import time
import requests
from pathlib import Path
import os

MAXUN_DIR = Path(r"D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun")

def run(cmd, check=True):
    print(f"\n{'='*60}")
    print(f"$ {cmd}")
    print('='*60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout[:500])
    if result.stderr:
        print(result.stderr[:500])
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return result

def wait_for(port, timeout=30):
    """Wait for a service to become available on a port."""
    print(f"\nWaiting for service on port {port}...")
    for i in range(timeout):
        try:
            requests.get(f"http://127.0.0.1:{port}", timeout=1)
            print(f"✓ Service ready on port {port}")
            return True
        except:
            time.sleep(1)
    raise TimeoutError(f"Service not ready on port {port} after {timeout}s")

def main():
    print("=== Maxun Startup Sequence ===\n")
    
    # 1. Kill any existing instances
    print("\n[1/6] Stopping existing processes...")
    for proc in ['node', 'chrome.exe', 'minio.exe']:
        subprocess.run(f'taskkill /F /IM {proc} /T 2>nul', shell=True)
    time.sleep(2)
    
    # 2. Start MinIO (S3 storage)
    print("\n[2/6] Starting MinIO (S3 storage)...")
    minio_data = Path(r"C:\Users\rames\minio-data")
    minio_data.mkdir(exist_ok=True)
    minio_bin = Path(r"C:\Users\rames\minio.exe")
    mc_bin = Path(r"C:\Users\rames\mc.exe")
    
    # Download if needed
    if not minio_bin.exists():
        print("  Downloading MinIO...")
        subprocess.run('curl -sL -o {} https://dl.min.io/server/minio/release/windows-amd64/minio.exe'.format(minio_bin), shell=True)
    if not mc_bin.exists():
        print("  Downloading MC...")
        subprocess.run('curl -sL -o {} https://dl.min.io/client/mc/release/windows-amd64/mc.exe'.format(mc_bin), shell=True)
    
    # Start MinIO in background
    env = {**os.environ, 
           'MINIO_ROOT_USER': 'maxun_minio',
           'MINIO_ROOT_PASSWORD': 'LfIEGyNGQuSQ3KwhpsZs9yqe'}
    subprocess.Popen(
        [str(minio_bin), 'server', str(minio_data), '--console-address', ':9001', '--address', ':9000'],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    
    # Verify MinIO
    print("  Setting up MC alias...")
    subprocess.run([str(mc_bin), 'alias', 'set', 'local', 'http://localhost:9000', 'maxun_minio', 'LfIEGyNGQuSQ3KwhpsZs9yqe'], 
                   capture_output=True)
    print("  Creating bucket...")
    subprocess.run([str(mc_bin), 'mb', 'local/maxun-test'], capture_output=True)
    print("✓ MinIO ready")
    
    # 3. Start Maxun Browser service
    print("\n[3/6] Starting Maxun Browser service...")
    browser_dir = MAXUN_DIR / "browser"
    subprocess.Popen(['npm', 'start'], cwd=str(browser_dir), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_for(3001, timeout=15)
    
    # 4. Start Maxun Server (API)
    print("\n[4/6] Starting Maxun Backend API...")
    server_env = {**os.environ,
                  'DATABASE_URL': 'postgresql://postgres:postgres@localhost:5432/maxun',
                  'S3_STORAGE': 'true',
                  'AWS_REGION': 'us-east-1',
                  'AWS_ACCESS_KEY_ID': 'maxun_minio',
                  'AWS_SECRET_ACCESS_KEY': 'LfIEGyNGQuSQ3KwhpsZs9yqe',
                  'S3_ENDPOINT': 'http://localhost:9000',
                  'S3_BUCKET_NAME': 'maxun-test'}
    subprocess.Popen(['npm', 'run', 'server'], cwd=str(MAXUN_DIR), env=server_env, 
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    wait_for(8080, timeout=20)
    
    # 5. Verify everything
    print("\n[5/6] Verifying services...")
    checks = [
        ('MinIO', 'http://127.0.0.1:9000/minio/health/live'),
        ('Maxun API', 'http://127.0.0.1:8080/api/robots'),
        ('Browser', 'http://127.0.0.1:3001'),
        ('UI', 'http://127.0.0.1:5173'),
    ]
    for name, url in checks:
        try:
            resp = requests.get(url, timeout=3)
            print(f"  ✓ {name}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
    
    # 6. Instructions
    print("\n[6/6] Next Steps:")
    print("="*60)
    print("""
1. Open http://127.0.0.1:5173 in Chrome
2. Login/Register with:
   - Email: scoutveda@maxun.local
   - Password: ScoutMaxun2026!
3. Click "Record Robot" for each category:
   - Navigate to https://www.amazon.in/gp/bestsellers/ELECTRONICS/
   - Click "Record Robot" button (top right)
   - Select product cards on the page
   - Click "Record Selection" → "Finish Recording"
   - Name it: "Electronics Bestsellers"
   - Note the Robot ID (shown after saving)

4. Save Robot IDs to laptop.env:
   MAXUN_ROBOTS="robot_id_1=Electronics;robot_id_2=Home&Kitchen;..."
   
5. Run the bridge to forward data:
   cd scout-cloud/scraper
   python maxun_bridge.py --loop
""")
    print("="*60)
    print("✓ Setup complete!")

if __name__ == '__main__':
    main()
