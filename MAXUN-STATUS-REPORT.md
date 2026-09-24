# ScoutVeda Maxun Scraper - Complete Status Report
**Generated:** 2026-09-24  
**Status:** PARTIALLY OPERATIONAL

---

## 📊 Current Scraping Status

### Database Overview
| Metric | Value |
|--------|-------|
| Total Rows | 296,685 |
| Unique ASINs | ~18,073 |
| Categories Covered | 32/32 (100%) |
| Daily Growth | ~36,000 rows |
| Days to 2M | ~55 days |

### Data by Source
| Source | Rows | Status |
|--------|------|--------|
| GitHub Actions Collector | 296,625 | ✅ Active (hourly) |
| Maxun Beauty Robot | ~60 | ⚠️ Inactive |
| **Total Maxun** | **~60** | ❌ Not integrated |

### Last Activity
- **GitHub Scraper:** Running hourly (24x/day)
- **Maxun Beauty Run:** Sep 7, 2026 at 6:36 AM (30 products scraped)
- **Bridge Forwarding:** Never configured (API key missing)

---

## 🔧 Maxun Service Status

| Service | Port | Status | Notes |
|---------|------|--------|-------|
| Backend API | 8080 | ⚠️ Intermittent | Runs but unstable |
| Frontend UI | 5173 | ❌ DOWN | Must be started manually |
| Browser WS | 3001 | ✅ Running | Playwright ChromeDriver |
| Browser Health | 3002 | ✅ Running | Health check OK |
| PostgreSQL | 5432 | ✅ Running | Windows service |
| MinIO S3 | 9000 | ❌ DOWN | Not critical for scraping |

**Critical Issue:** The Maxun frontend UI (port 5173) is not running. This is why `http://localhost:5173` shows an error.

---

## 🚨 Root Cause Analysis

### Problem 1: No API Key Configuration
The `scraper/laptop.env` file exists but has placeholder values:
```
MAXUN_API_KEY=YOUR_MAXUN_API_KEY_HERE
```
Without a valid API key, the bridge script cannot authenticate with Maxun.

### Problem 2: Frontend Not Started
The Maxun frontend (`npm run client`) is not running automatically. It must be started manually or via a startup script.

### Problem 3: No Robots Configured for Multi-Category
Only the Beauty robot exists. Other categories need robots created.

---

## ✅ What's Working

1. **GitHub Actions Scraper** - Primary data source
   - 24 runs per day (hourly)
   - ~36,000 rows/day projected
   - All 32 Amazon categories covered
   - Subcategory scraping enabled (382 browse nodes)

2. **MinIO Storage** - Available for screenshots
3. **PostgreSQL** - Database service running
4. **Browser Service** - Chrome automation ready

---

## 📈 How to Increase Maxun Output

### Step 1: Start the Frontend (REQUIRED)

Open a new Command Prompt or PowerShell window:

```powershell
cd "D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun"
npm run client
```

Wait for it to show "Local: http://localhost:5173"

### Step 2: Get Your API Key

1. Open **http://localhost:5173**
2. Login: `scoutveda@maxun.local` / `ScoutMaxun2026!`
3. Click your **profile picture** (top right)
4. Select **"API Keys"** from the menu
5. Copy the generated key (looks like: `maxun_xxxxxxxxxxxx`)

### Step 3: Configure the Bridge

Update `scraper/laptop.env`:

```env
MAXUN_API_KEY=maxun_your_key_here
MAXUN_ROBOT_ID=ecdadb40-e182-4ecf-a9cb-f076c21ec240
SCOUT_API_KEY=VnILAeDCQ2PvtPb067tqmdhGz0
TRIGGER_EVERY_HOURS=1
```

### Step 4: Create More Robots (Optional)

To scrape multiple categories:
1. In Maxun UI, click **"New Robot"**
2. Navigate to Amazon bestsellers page (e.g., `https://www.amazon.in/gp/bestsellers/electronics/`)
3. Click **"Record Robot"**
4. Select product cards on the page
5. Save and copy the Robot ID
6. Update `MAXUN_ROBOTS` env var:
   ```
   MAXUN_ROBOTS=id1=Category1;id2=Category2;id3=Category3
   ```

### Step 5: Run the Multi-Scraper

```bash
cd D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\scout-cloud\scraper
python maxun_multi_scrape.py --limit 5
```

This will:
- Find all configured robots
- Run each one sequentially (10s delay between)
- Forward results to ScoutVeda automatically

---

## 📊 Projected Output After Setup

| Scenario | Robots | Products/Run | Runs/Day | Daily Rows | Monthly Rows |
|----------|--------|--------------|----------|------------|--------------|
| Current | 0 | 0 | 0 | 0 | 0 |
| 1 Robot | 1 | 30 | 24 | 720 | 21,600 |
| 5 Robots | 5 | 150 | 24 | 3,600 | 108,000 |
| 10 Robots | 10 | 300 | 24 | 7,200 | 216,000 |

**Combined with GitHub scrapers (~36,000/day):**
- 1 robot: 36,720 rows/day → 2M in 54 days
- 5 robots: 39,600 rows/day → 2M in 50 days
- 10 robots: 43,200 rows/day → 2M in 46 days

---

## 🎯 Quick Start Commands

### Option A: Manual Start (Recommended)

**Terminal 1** - Backend:
```powershell
cd "D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun"
npm run server
```

**Terminal 2** - Frontend:
```powershell
cd "D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun"
npm run client
```

**Terminal 3** - Browser (if not running):
```powershell
cd "D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun\browser"
node dist/server.js
```

### Option B: Use the Batch Script

Double-click: `scraper/start_maxun.bat`

This will attempt to start all services automatically.

### Option C: Use Python Script

```powershell
cd scraper
python start_maxun.py
```

---

## 🔍 Verification Checklist

After starting services, verify:

- [ ] http://localhost:5173 loads the Maxun UI
- [ ] You can login with scoutveda@maxun.local
- [ ] Settings → API Keys shows a valid key
- [ ] Robots tab shows your robots
- [ ] Run history shows recent runs

Then test the bridge:

```powershell
cd scraper
python maxun_bridge.py --dry-run
```

If dry-run shows output, you're ready to forward real data.

---

## 📝 Files Created This Session

1. `scraper/maxun_multi_scrape.py` - Multi-robot scraper (new)
2. `scraper/maxun_setup.py` - Setup automation (new)
3. `scraper/start_maxun.py` - Service manager (new)
4. `scraper/start_maxun.bat` - Windows batch launcher (new)
5. `scraper/run_maxun.bat` - Quick run script (updated)
6. `scraper/laptop.env` - Configuration template (created)
7. `MAXUN-STATUS-2026-09-24.md` - This documentation (new)

---

## 🎯 Next Steps (Prioritized)

### Immediate (5 minutes)
1. Start the frontend: `npm run client` in Maxun directory
2. Access http://localhost:5173
3. Get API key from Settings → API Keys
4. Update `scraper/laptop.env` with your key

### Short-term (15 minutes)
1. Create robots for top 5 categories (Beauty, Grocery, Electronics, Home & Kitchen, Health)
2. Test single robot: `python maxun_bridge.py --robot-id YOUR_ID --category "Beauty"`
3. Verify data appears in ScoutVeda

### Long-term (Ongoing)
1. Schedule hourly runs via Windows Task Scheduler
2. Add more category robots as needed
3. Monitor data quality and adjust selectors

---

## ⚠️ Known Issues

1. **Backend Instability** - Maxun backend occasionally crashes, requires restart
2. **MinIO Down** - Not critical for scraping, only affects screenshot storage
3. **No Auto-Start** - Services don't restart automatically after reboot
4. **Single Browser Limit** - Robots run sequentially, not in parallel

---

## 💡 Recommendations

1. **Use Windows Task Scheduler** to auto-start services on login
2. **Create a desktop shortcut** to `scraper/start_maxun.bat`
3. **Add robots weekly** to cover new categories
4. **Monitor bridge forwarding** daily via logs

---

**Bottom Line:** Maxun is technically working but contributing almost nothing because the bridge isn't configured. Once you add your API key and create a few robots, it can easily add 700-3,600 rows/day with residential IP diversity.
