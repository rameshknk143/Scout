# Maxun Infrastructure Status & Improvement Plan
**Date:** 2026-09-24  
**Project:** ScoutVeda Amazon Scraping System

---

## Current State

### Services Running
| Service | Port | Status | Notes |
|---------|------|--------|-------|
| Backend API | 8080 | ✅ Running | Node.js server active |
| Frontend UI | 5173 | ❌ NOT Running | UI accessible at http://localhost:5173 |
| Browser WS | 3001 | ❌ NOT Running | Playwright ChromeDriver |
| Browser Health | 3002 | ❌ NOT Running | Health check endpoint |
| PostgreSQL | 5432 | ✅ Running | Windows service `postgresql-x64-17` |
| MinIO S3 | 9000 | ✅ Running | Object storage for screenshots |

### Scraping Output (Last 30 Days)
| Source | Total Rows | Last Activity | Status |
|--------|-----------|---------------|--------|
| GitHub Actions Collector | 296,685 | Hourly | ✅ Active |
| Maxun Beauty Robot | ~60 | Sep 7, 2026 | ⚠️ Inactive |
| VM Watchlist Scraper | 0 | Never | ❌ Not configured |
| **Total** | **~296,745** | | |

### Database Composition
- **Bestsellers:** 116,512 rows
- **Most-Gifted:** 65,581 rows
- **Most-Wished-For:** 65,016 rows
- **New Releases:** 59,150 rows
- **Watchlist:** 717 rows
- **Custom-scrape (Maxun):** 60 rows

---

## The Problem

Maxun is technically working but contributing almost nothing:

1. **Frontend UI not started** → Cannot access http://localhost:5173 to manage robots
2. **Browser service not started** → Robots cannot execute new runs
3. **API key missing** → Bridge script cannot authenticate with Maxun
4. **No forwarding configured** → Scraped data stays in Maxun, never reaches ScoutVeda

The beauty robot ran successfully once (30 products at 6:36 AM), but without the bridge configured, that data was lost.

---

## How to Increase Maxun Output

### Phase 1: Start All Services (5 minutes)

```bash
# 1. Start the frontend UI
cd D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun
npm run dev:frontend

# 2. Start the browser service (in another terminal)
cd browser
node dist/server.js
```

### Phase 2: Get API Key (2 minutes)

1. Open **http://localhost:5173**
2. Login (email: `scoutveda@maxun.local`, password: `ScoutMaxun2026!`)
3. Click your **profile picture** → **API Keys**
4. Copy the generated key (looks like: `maxun_xxxxxxxxxxxx`)

### Phase 3: Configure Bridge (2 minutes)

Update `scraper/laptop.env`:

```env
MAXUN_API_URL=http://127.0.0.1:8080
MAXUN_API_KEY=maxun_your_key_here
MAXUN_ROBOT_ID=ecdadb40-e182-4ecf-a9cb-f076c21ec240
SCOUT_API_URL=https://scout-api-3yvy.onrender.com
SCOUT_API_KEY=VnILAeDCQ2PvtPb067tqmdhGz0
TRIGGER_EVERY_HOURS=1
```

### Phase 4: Run Multi-Categor scraper (Automated)

```bash
cd scraper
python maxun_multi_scrape.py --limit 5
```

This will:
- Find all robots in Maxun
- Run each one sequentially
- Forward results to ScoutVeda automatically

---

## Projected Output After Setup

| Scenario | Products/Run | Runs/Day | Daily Rows | Monthly Rows |
|----------|-------------|----------|------------|--------------|
| Current | 0 | 0 | 0 | 0 |
| Single Robot | 30 | 24 | 720 | 21,600 |
| 5 Robots | 150 | 24 | 3,600 | 108,000 |
| 10 Robots | 300 | 24 | 7,200 | 216,000 |

**Combined with GitHub scrapers (~36,000/day):**
- 1 robot: 36,720 rows/day → 2M in ~54 days
- 5 robots: 39,600 rows/day → 2M in ~50 days
- 10 robots: 43,200 rows/day → 2M in ~46 days

---

## Why Maxun Matters

Even though Maxun contributes less than GitHub scrapers, it provides:

1. **Residential IP data** — Different from GitHub's datacenter IPs
2. **Visual verification** — Screenshots of actual product pages
3. **Advanced selectors** — Can scrape complex layouts that HTTP fails on
4. **Flexibility** — Easy to add new categories without code changes

---

## Quick Start Command

Copy-paste this to fix everything in one go:

```powershell
# Start all services
cd "D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun"
npm run dev:frontend  # Terminal 1
cd browser && node dist/server.js  # Terminal 2

# Then get API key from http://localhost:5173
# Update laptop.env
# Run scraper
cd ..\..\..\..\scraper
python maxun_multi_scrape.py --limit 5
```
