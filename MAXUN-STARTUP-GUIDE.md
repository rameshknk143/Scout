# Maxun Service Startup Guide
**Date:** 2026-09-24  
**Status:** Backend and Browser are RUNNING

---

## Current Status
| Service | Port | Status |
|---------|------|--------|
| Backend API | 8080 | ✅ RUNNING |
| Browser Service | 3001/3002 | ✅ RUNNING |
| Frontend UI | 5173 | ❌ NEEDS STARTUP |

---

## How to Start the Frontend (One-Time)

Open a **NEW Command Prompt or PowerShell window** and run:

```powershell
cd "D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\self-hosted-stack\maxun"
npx vite
```

Wait until you see:
```
  VITE v6.4.3  ready in XXX ms
  ➜  Local:   http://localhost:5173/
```

Then open your browser and go to: **http://localhost:5173**

---

## Login Credentials
- **Email:** scoutveda@maxun.local
- **Password:** ScoutMaxun2026!

---

## Next Steps After Login

1. Click your profile picture (top right) → **API Keys**
2. Copy the generated API key
3. Update `scraper/laptop.env`:
   ```env
   MAXUN_API_KEY=maxun_your_key_here
   ```
4. Run the scraper:
   ```powershell
   cd D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\scout-cloud\scraper
   python maxun_multi_scrape.py --limit 5
   ```

---

## What This Will Do

Once configured, Maxun will:
- Run all robots hourly (24x/day)
- Forward 30 products per robot to ScoutVeda
- Provide residential IP data for better scraping diversity

**Projected output:** 720+ rows/day from Maxun alone
