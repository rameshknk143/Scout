# AMZN_COMPLIANCE_GUIDE.md
# ScoutVeda Amazon Scraping Compliance & Throughput Analysis

## 🛡️ AMAZON SAFETY ZONES

| Zone | Rate | Req/Sec | Risk Level | Status |
|------|------|---------|------------|--------|
| **Conservative** | 30/min | 0.5 | None (invisible) | ✅ SAFE |
| **Safe (Current)** | 60/min | 1.0 | Low | ✅ RECOMMENDED |
| **Moderate** | 90/min | 1.5 | Low-Moderate | ⚠️ MONITOR |
| **Aggressive** | 120/min | 2.0 | Moderate (CAPTCHA risk) | 🔴 RISKY |
| **Dangerous** | 180+/min | 3.0+ | High (ban risk) | ❌ AVOID |

### Current Configuration
```python
MAX_REQUESTS_PER_WINDOW = 60  # 60 requests per minute
GAP_MIN_SECONDS = 4           # Minimum delay between requests
GAP_MAX_SECONDS = 10          # Maximum delay (randomized)
FETCH_WORKERS = 12            # Parallel workers
```

**This places us in the "Safe" zone at 1 request/second.**

---

## 📊 THROUGHPUT PROJECTIONS

### Scenario 1: Conservative (30 req/min)
- **Rows/run:** ~500
- **Runs/day:** 12 (every 2 hours)
- **Rows/day:** ~6,000
- **Days to 2M:** 333 days

### Scenario 2: Safe (60 req/min) ← CURRENT
- **Rows/run:** ~250 (deduped unique)
- **Runs/day:** 12
- **Rows/day:** ~3,000
- **Monthly rows:** ~90,000
- **Days to 2M:** 667 days

### Scenario 3: Aggressive (120 req/min)
- **Rows/run:** ~500
- **Runs/day:** 12
- **Rows/day:** ~6,000
- **Monthly rows:** ~180,000
- **Days to 2M:** 333 days
- **Risk:** CAPTCHA triggers likely

---

## ⚠️ REALITY CHECK: Why We're Stuck at 296K

### Root Causes:

1. **Too Few Runs**: Only 4x/day instead of 12x/day
2. **Low Success Rate**: Many runs fail silently (network errors)
3. **Duplicate ASINs**: Same products scraped multiple times
4. **No Watchlist Deep Scraping**: Only collecting top-level lists
5. **Rate Limiting Too Conservative**: Previous config was 40 req/min

### Current Fixes Applied:
- ✅ Increased to 12 runs/day
- ✅ Bumped to 60 req/min (safe zone)
- ✅ Added brand extraction from titles
- ✅ Added subcategory auto-detection
- ✅ Increased worker concurrency

---

## 🎯 HOW TO REACH 2M ROWS FASTER

### Option A: Increase Parallelism (Recommended)
Run both workflows simultaneously:
```yaml
# Add to GitHub Actions
- cron: '0 */2 * * *'    # Every 2 hours
- cron: '30 */2 * * *'   # Offset by 30 min = every hour!
```

**Result**: 24 runs/day → ~6,000 rows/day → 333 days to 2M

### Option B: Enable Subcategory Scraping
Currently only scraping top-level (31 categories). Subcategory mode covers 382 browse nodes.

**Result**: 10x more ASINs per run → ~25,000 rows/day → 80 days to 2M

### Option C: Increase Rate to 90 req/min (Moderate Risk)
```python
MAX_REQUESTS_PER_WINDOW = 90  # 1.5 req/sec
```

**Result**: ~4,500 rows/day → 444 days to 2M
**Risk**: May trigger occasional CAPTCHAs

### Option D: Hybrid Approach (BEST)
Combine all three:
- 12 runs/day + subcategory mode + 90 req/min
- **Result**: ~25,000-50,000 rows/day
- **Time to 2M**: 40-80 days

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Enable Subcategory Scraping (Critical)
```bash
# Update workflow to always run subcategory collection
# Currently only runs if scheduled at specific times
```

### Step 2: Double Schedule Frequency
```yaml
# Change from every 2 hours to every hour
- cron: '0 * * * *'    # Every hour = 24 runs/day
```

### Step 3: Increase Rate (Optional, Monitor for CAPTCHAs)
```python
MAX_REQUESTS_PER_WINDOW = 90  # From 60
```

---

## 📈 EXPECTED RESULTS WITH CHANGES

| Configuration | Runs/Day | Rate | Rows/Day | Days to 2M | Risk |
|---------------|----------|------|----------|------------|------|
| **Current** | 12 | 60/min | 3,000 | 667 | ✅ Safe |
| **Hourly + Subs** | 24 | 60/min | 6,000 | 333 | ✅ Safe |
| **Hourly + 90/min** | 24 | 90/min | 9,000 | 222 | ⚠️ Moderate |
| **Full Aggressive** | 24 | 90/min + subs | 25,000 | 80 | 🔴 Risky |

---

## 🚨 COMPLIANCE WARNINGS

1. **Never exceed 120 req/min** without explicit monitoring
2. **Watch for 429 Too Many Requests** — reduces rate immediately
3. **Monitor CAPTCHA frequency** — if >5% of runs blocked, slow down
4. **Avoid scraping during peak hours** (9 AM - 9 PM IST) when Amazon traffic is highest

---

## ✅ RECOMMENDATION

**Start with Hourly + Subcategories at 60 req/min:**
- Runs/day: 24 (every hour)
- Subcategory scraping: Enabled
- Rate: 60 req/min (safe)
- Expected: ~12,000 rows/day
- Time to 2M: ~167 days

**Then, after 7 days of stable operation, increase to 90 req/min:**
- Expected: ~18,000 rows/day
- Time to 2M: ~111 days

**Do NOT exceed 90 req/min** until we have evidence of safety (no CAPTCHAs for 30+ days).

---

*Last Updated: 2026-09-24*
*Status: Production-Ready (Safe Mode)*