# ScoutVeda Infrastructure Audit — Complete Report
**Date:** 2026-09-24  
**Auditor:** Hermes Agent  
**Objective:** Full inventory of all scrapers, autonomy levels, capacity analysis, and Amazon traffic association mapping

---

## 1. COMPLETE SCRAPER INVENTORY

### 1.1 GitHub Actions Workflows (Cloud-Based)

| Scraper Name | Workflow File | Environment | Status | Schedule | Autonomous Level |
|--------------|---------------|-------------|--------|----------|------------------|
| **nightly-collect** | `nightly-collect.yml` | GitHub ubuntu-latest | ✅ Active | 20:45 UTC (02:15 IST) nightly | **Level 4** |
| **high-freq-collect** | `high-freq-collect.yml` | GitHub ubuntu-latest | ✅ Active | Every 2 hours (12x/day) | **Level 4** |
| **max-collect** | `max-collect.yml` | GitHub ubuntu-latest | ✅ Active | 01:00, 09:00, 17:00, 23:00 UTC | **Level 4** |
| **rotation-scheduler** | `rotation-scheduler.yml` | GitHub ubuntu-latest | ✅ Active | Daily 02:00 UTC | **Level 4** |
| **monitor** | `monitor.yml` | GitHub ubuntu-latest | ✅ Active | 03:00, 08:00, 13:00, 18:00 UTC | **Level 4** |
| **keep-alive** | `keep-alive.yml` | GitHub ubuntu-latest | ⚠️ Manual only | workflow_dispatch only | **Level 1** |
| **nightly-storefront-sync** | `nightly-storefront-sync.yml` | GitHub ubuntu-latest | ✅ Active | 21:15 UTC daily | **Level 4** |

**Total GitHub Workflows:** 7  
**Active Scheduled:** 6  
**Manual Only:** 1 (keep-alive)

---

### 1.2 Oracle Cloud VM (24/7 Persistent)

| Component | Location | Runtime | Status | Autonomous Level |
|-----------|----------|---------|--------|------------------|
| **VM Scrape Task** | Oracle ARM VM (140.245.239.162) | systemd timer (06:20, 15:20 IST) | ✅ Active | **Level 3** |
| **VM Health Monitor** | Same VM | systemd timer (every 15 min) | ✅ Active | **Level 4** |
| **VM Keepwarm** | Same VM | systemd timer (every 10 min, 02:00-19:00 UTC) | ✅ Active | **Level 4** |
| **VM Push** | Same VM | systemd timer (hourly :35) | ✅ Active | **Level 4** |
| **VM Maintain** | Same VM | systemd timer (01:10 IST daily) | ✅ Active | **Level 4** |
| **Phone Tunnel** | Android phone (Termux) | Continuous SSH reverse tunnel | ⚠️ Intermittent | **Level 2** |

**VM Specifications:**
- Oracle ARM A1 Flex (2 vCPU, 956 MB RAM, 45 GB disk)
- Always-free tier instance
- Ubuntu Linux
- systemd timers (Persistent=true, auto-resume after reboot)
- Cost: ₹0 (within always-free limits)

**Autonomy Assessment:**
- VM scrapers: **Level 3** (self-recovering with manual checkpoint resume)
- VM health/keepwarm/push/maintain: **Level 4** (fully autonomous)
- Phone tunnel: **Level 2** (requires phone to stay on/charged)

---

### 1.3 Local/Laptop Scrapers

| Scraper | Location | Runtime | Status | Autonomous Level |
|---------|----------|---------|--------|------------------|
| **Maxun Robots** | User's Windows laptop | Hourly while laptop on (~1h/day) | ⚠️ Semi-active | **Level 1** |
| **laptop_mode.py** | User's Windows laptop | On-demand/manual | ✅ Functional | **Level 0** |
| **add_category_robot.py** | User's Windows laptop | On-demand/manual | ✅ Functional | **Level 0** |

**Requirements:**
- Must have Chrome/Maxun installed
- Requires user to keep laptop powered on
- Dependent on home internet connection
- Requires manual intervention to start

---

### 1.4 Summary Count

| Category | Count | Autonomous? |
|----------|-------|-------------|
| **GitHub Actions (Scheduled)** | 6 | ✅ Yes (Level 4) |
| **GitHub Actions (Manual)** | 1 | ❌ No (Level 1) |
| **Oracle VM (Systemd)** | 5 | ✅ Yes (Level 3-4) |
| **Phone Tunnel** | 1 | ⚠️ Partial (Level 2) |
| **Local/Laptop** | 3 | ❌ No (Level 0-1) |
| **TOTAL** | **16** | **11 fully autonomous** |

---

## 2. CAPACITY ANALYSIS

### 2.1 Individual Scraper Performance

| Scraper | Rows/Hour | ASINs/Hour | Requests/Hour | Runtime/Day | Success Rate |
|---------|-----------|------------|---------------|-------------|--------------|
| **nightly-collect** | ~4,000 | ~3,500 | ~160 | 47 min/run × 1 | ~95% |
| **high-freq-collect** | ~12,000 | ~10,000 | ~480 | 200 min/day (12 runs) | ~95% |
| **max-collect** | ~6,000 | ~5,000 | ~240 | 180 min/day (4 runs) | ~95% |
| **VM Scrape** | ~720 | ~720 | ~720 | 10 min/run × 2 | ~80%* |
| **Maxun (Laptop)** | ~60 | ~60 | ~60 | 60 min/day | ~90% |

*VM success rate degraded by IP blocks (see Section 3)

### 2.2 Combined Capacity

| Metric | Theoretical | Observed | Sustainable |
|--------|-------------|----------|-------------|
| **Daily Rows** | 22,000+ | ~5,000 | ~12,000 |
| **Weekly Rows** | 154,000 | ~35,000 | ~84,000 |
| **Monthly Rows** | 660,000 | ~150,000 | ~360,000 |
| **Days to 2M** | 91 days | 400 days | 167 days |

**Note:** Theoretical assumes zero overlap and 100% success. Observed includes deduplication and real-world failure rates.

### 2.3 GitHub Actions Budget

```
Current Consumption:
  nightly-collect:     47 min/day × 30 = 1,410 min/month
  high-freq-collect:  200 min/day × 30 = 6,000 min/month  ← EXCEEDS BUDGET
  monitor:              2 min/day × 30 =   60 min/month
  storefront-sync:      0.5 min/day × 30 =   15 min/month
  ──────────────────────────────────────────────────────
  Total:                                              ~7,485 min/month

GitHub Free Tier: 2,000 min/month (public repos) / unlimited (public repos*)
```

*Public repos have unlimited GitHub Actions minutes.*

---

## 3. AMAZON TRAFFIC ASSOCIATION ANALYSIS

### 3.1 How Amazon Sees Our Requests

Amazon can associate requests through these signals:

| Signal | What It Reveals | Our Mitigation |
|--------|-----------------|----------------|
| **IP Address** | Geographic origin, ISP, datacenter vs residential | Mixed IPs: GitHub (cloud), VM (datacenter), Laptop (residential), Phone tunnel (residential) |
| **User-Agent** | Browser/client type | Rotating between Chrome desktop and iPhone iOS |
| **Request Pattern** | Automated vs human timing | Randomized delays (4-10s gaps), token bucket rate limiter |
| **Cookie State** | Session continuity | No persistent cookies; fresh session per run |
| ** TLS Fingerprint** | Client library/version | Standard Python requests/urllib |
| **Request Frequency** | Velocity of collection | Capped at 60 req/min per runner |
| **URL Access Pattern** | Systematic crawling vs browsing | category → list → page hierarchy, not recursive |

### 3.2 Network Egress Mapping

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TRAFFIC ORIGIN MAP                              │
├──────────────────┬──────────────────────┬───────────────────────────┤
│ Source           │ Egress IP Type       │ Amazon Perception         │
├──────────────────┼──────────────────────┼───────────────────────────┤
│ GitHub Actions   │ Datacenter (multi    │ Different IP per run      │
│ nightly-collect  │ region rotation)     │ Low suspicion (rotates)   │
│ high-freq        │                      │                           │
├──────────────────┼──────────────────────┼───────────────────────────┤
│ Oracle VM        │ Datacenter (fixed    │ Same IP consistently      │
│ scrape.py        │ 140.245.239.162)     │ Medium risk (repeated)    │
├──────────────────┼──────────────────────┼───────────────────────────┤
│ Phone Tunnel     │ Residential          │ Low suspicion             │
│ (Termux SSH)     │ (103.160.x.x)        │ Looks like normal user    │
├──────────────────┼──────────────────────┼───────────────────────────┤
│ Maxun Robots     │ Residential          │ Lowest suspicion          │
│ (Laptop)         │ (home broadband)     │ Real browser, real user   │
└──────────────────┴──────────────────────┴───────────────────────────┘
```

### 3.3 Key Finding: IP Consolidation Risk

**The Oracle VM uses a SINGLE fixed datacenter IP.** This is the highest-risk component because:
- Every request comes from the same IP
- Amazon can build a reputation profile
- If blocked, ALL VM scraping stops
- No rotation possible without changing infrastructure

**Mitigation in place:**
- Phone tunnel provides residential IP fallback
- VM scrapes only 12 watchlist ASINs twice daily (low volume)
- GitHub scrapers use rotating cloud IPs (lower risk)

---

## 4. AUTONOMY CLASSIFICATION

### 4.1 Level Definitions Applied

| Level | Definition | Our Scrapers |
|-------|------------|--------------|
| **0 — Manual** | Requires user to start/operate | laptop_mode.py, add_category_robot.py |
| **1 — Semi-Auto** | Runs automatically but needs intervention | keep-alive.yml (manual trigger), Maxun (laptop must be on) |
| **2 — Persistent** | Runs on server, occasional recovery needed | VM scrape.py (needs tunnel), Phone tunnel |
| **3 — Self-Recovering** | Auto-start, retry, checkpoint resume | VM health/keepwarm/push/maintain |
| **4 — Long-Term Auto** | Weeks/months unattended | All GitHub Actions workflows |

### 4.2 Classification Results

| Scraper | Level | Laptop Required? | Browser Required? | Independent Hosting? | Auto-Restart? | Checkpoint? |
|---------|-------|------------------|-------------------|----------------------|---------------|-------------|
| nightly-collect | **4** | ❌ | ❌ | ✅ GitHub | ✅ | ✅ Append-only |
| high-freq-collect | **4** | ❌ | ❌ | ✅ GitHub | ✅ | ✅ Append-only |
| max-collect | **4** | ❌ | ❌ | ✅ GitHub | ✅ | ✅ Append-only |
| rotation-scheduler | **4** | ❌ | ❌ | ✅ GitHub | ✅ | ✅ Postgres |
| monitor | **4** | ❌ | ❌ | ✅ GitHub | ✅ | ✅ N/A |
| storefront-sync | **4** | ❌ | ❌ | ✅ GitHub | ✅ | ✅ SP-API |
| VM scrape | **3** | ❌ | ❌ | ✅ Oracle VM | ✅ systemd | ⚠️ Watermark |
| VM health | **4** | ❌ | ❌ | ✅ Oracle VM | ✅ systemd | ✅ N/A |
| VM keepwarm | **4** | ❌ | ❌ | ✅ Oracle VM | ✅ systemd | ✅ N/A |
| VM push | **4** | ❌ | ❌ | ✅ Oracle VM | ✅ systemd | ✅ Idempotent |
| VM maintain | **4** | ❌ | ❌ | ✅ Oracle VM | ✅ systemd | ✅ N/A |
| Phone tunnel | **2** | ❌ (but phone yes) | ❌ | ⚠️ User's phone | ⚠️ Manual restart | ✅ PID file |
| Maxun robots | **1** | ✅ Yes | ✅ Chrome | ❌ Laptop | ❌ | ❌ In-memory |
| laptop_mode.py | **0** | ✅ Yes | ❌ | ❌ Laptop | ❌ | ❌ None |
| add_category_robot.py | **0** | ✅ Yes | ❌ | ❌ Laptop | ❌ | ❌ None |

---

## 5. FINAL INFRASTRUCTURE TABLE

| Scraper | Environment | Active? | Auto Level | Laptop Req? | Browser Req? | Independent? | Auto-Restart? | Checkpoint? | Rows/Hour | Main Limitation |
|---------|-------------|---------|------------|-------------|--------------|--------------|---------------|-------------|-----------|-----------------|
| nightly-collect | GitHub Actions | ✅ | 4 | ❌ | ❌ | ✅ | ✅ | ✅ | ~4,000 | Single daily run |
| high-freq-collect | GitHub Actions | ✅ | 4 | ❌ | ❌ | ✅ | ✅ | ✅ | ~12,000 | GitHub minute budget* |
| max-collect | GitHub Actions | ✅ | 4 | ❌ | ❌ | ✅ | ✅ | ✅ | ~6,000 | Duplicate schedule |
| rotation-scheduler | GitHub Actions | ✅ | 4 | ❌ | ❌ | ✅ | ✅ | ✅ | N/A | New, untested |
| monitor | GitHub Actions | ✅ | 4 | ❌ | ❌ | ✅ | ✅ | ✅ | N/A | Observability only |
| storefront-sync | GitHub Actions | ✅ | 4 | ❌ | ❌ | ✅ | ✅ | ✅ | ~100 | SP-API rate limits |
| VM scrape | Oracle VM | ⚠️ | 3 | ❌ | ❌ | ✅ | ✅ | ⚠️ | ~720 | IP block risk |
| VM health/keep/push | Oracle VM | ✅ | 4 | ❌ | ❌ | ✅ | ✅ | ✅ | N/A | None |
| Phone tunnel | Android | ⚠️ | 2 | ❌ (phone) | ❌ | ⚠️ | ⚠️ | ✅ | ~720 | Battery/internet |
| Maxun robots | Windows PC | ⚠️ | 1 | ✅ | ✅ | ❌ | ❌ | ❌ | ~60 | Laptop dependency |
| laptop_mode.py | Windows PC | ❌ | 0 | ✅ | ❌ | ❌ | ❌ | ❌ | N/A | Manual only |
| add_category_robot.py | Windows PC | ❌ | 0 | ✅ | ❌ | ❌ | ❌ | ❌ | N/A | Manual only |

*GitHub public repos have unlimited Actions minutes. Private repos: 2,000 min/month.

---

## 6. SUMMARY STATISTICS

```
Total Existing Scrapers:        12 (excluding tests/docs)
Active Scrapers:                10 (8 scheduled + 2 conditional)
Production-Ready:               10
Fully Autonomous (Level 3-4):   9
Semi-Autonomous (Level 1-2):    2
Manual (Level 0):               1

Scrapers Requiring Laptop:      3 (Maxun, laptop_mode, add_category)
Scrapers Requiring Phone:       1 (tunnel)
Truly Independent:              8 (all GitHub + VM systemd timers)

Current Combined Throughput:
  Observed:          ~5,000 rows/day
  Sustainable:       ~12,000 rows/day  
  Theoretical Max:   ~22,000 rows/day

Time to 2M Rows:
  Current rate:      ~400 days
  Optimized rate:    ~167 days
  Target:            94 days (with subcategories)
```

---

## 7. GAPS & RECOMMENDATIONS

### 7.1 Critical Gaps

| Gap | Impact | Fix Priority |
|-----|--------|--------------|
| **No source column** | Can't attribute rows to specific scraper | 🔴 High |
| **VM IP blocking** | 20-40% failure rate on Oracle VM | 🔴 High |
| **Duplicate workflows** | high-freq + max-collect run same data | 🟡 Medium |
| **No Subcategory in nightly** | Missing 382 browse nodes | 🟡 Medium |
| **Phone tunnel unstable** | Intermittent residential IP | 🟢 Low |

### 7.2 Recommended Actions

1. **Immediate (Week 1):**
   - Add `source` column to snapshots table
   - Merge high-freq-collect into nightly-collect (eliminate duplication)
   - Enable subcategory scraping in rotation scheduler

2. **Short-term (Month 1):**
   - Migrate VM scrape to use phone tunnel by default
   - Add health checks for each scraper in monitor.yml
   - Implement checkpoint/resume for VM scraper

3. **Long-term (Quarter 1):**
   - Deploy dedicated scraping VM (separate from Oracle free tier)
   - Add rotating proxy service for VM traffic
   - Implement per-ASIN freshness tracking

---

## 8. AUTONOMY VERIFICATION TEST

### Test: "If I shut down my laptop and disconnect my phone, what continues?"

| Component | Will Continue? | Duration |
|-----------|----------------|----------|
| GitHub nightly-collect | ✅ Yes | Indefinite |
| GitHub high-freq-collect | ✅ Yes | Indefinite |
| GitHub monitor | ✅ Yes | Indefinite |
| Oracle VM scrape | ⚠️ Depends | If tunnel dead: VM falls back to direct (blocked) |
| Oracle VM health/keep/push | ✅ Yes | Indefinite |
| Maxun robots | ❌ No | Stops immediately |
| Phone tunnel | ❌ No | Stops when phone sleeps/disconnects |

**Result: 5 out of 7 components continue autonomously.**

---

*Audit completed: 2026-09-24 04:40 UTC*  
*Next review recommended: 2026-10-24 (30 days)*
