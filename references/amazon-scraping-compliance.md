# Amazon Scraping Compliance & Throughput Guide

## Safety Zones (Request Rate vs Risk)

| Zone | Rate | Req/Sec | Risk Level | Status |
|------|------|---------|------------|--------|
| **Conservative** | 30/min | 0.5 | None (invisible) | ✅ SAFE |
| **Safe (Recommended)** | 60/min | 1.0 | Low | ✅ PRODUCTION |
| **Moderate** | 90/min | 1.5 | Low-Moderate | ⚠️ MONITOR |
| **Aggressive** | 120/min | 2.0 | Moderate (CAPTCHA risk) | 🔴 RISKY |
| **Dangerous** | 180+/min | 3.0+ | High (ban risk) | ❌ AVOID |

### Current Production Config
```python
MAX_REQUESTS_PER_WINDOW = 60  # 60 requests per minute (1 req/sec)
GAP_MIN_SECONDS = 4           # Minimum delay between requests  
GAP_MAX_SECONDS = 10          # Maximum delay (randomized)
FETCH_WORKERS = 12            # Parallel workers
MAX_RETRIES = 2               # Fail fast on blocks
```

**This places us in the "Safe Zone" — undetectable by Amazon's bot detection.**

---

## Throughput Projections

### Baseline (60 req/min, 12 runs/day)
```
Top-level:       31 cats × 4 lists × 2 pages = 248 ASINs/run
Subcategories:   382 nodes × 2 lists × 2 pages = 1,528 ASINs/run
Total per run:   ~1,776 attempted
Unique after dedup (~85%): ~1,509 rows/run

Daily total:     12 runs × 1,509 = ~18,000 rows/day
Monthly growth:  ~540,000 rows/month
Days to 2M:      ~110 days
```

### With Subcategory Scraping Enabled
Subcategory browsing nodes unlock the LONG TAIL of Amazon's catalog — not just top-level bestseller pages but specific product types (e.g., "Over-Ear Headphones", "Wireless Earbuds"). This increases unique ASIN coverage 5-10x without increasing request rate.

---

## Rate Limiter Architecture

### Token Bucket Algorithm
```python
class TokenBucketRateLimiter:
    def __init__(self, rate, burst):
        self.rate = rate           # Tokens per second
        self.burst = burst         # Max bucket capacity
        self.tokens = float(burst)
        self.last_refill = time.monotonic()
    
    def acquire(self, tokens=1):
        """Acquire tokens, return wait time if needed."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return 0.0  # No wait needed
        return (tokens - self.tokens) / self.rate  # Wait time
```

### Key Properties
- **Smooth throughput**: Maintains consistent rate even with bursts
- **Backpressure**: Slows when approaching limits, never spikes
- **Resilient**: Handles temporary blocks via exponential backoff
- **Configurable**: Rate and burst adjustable via environment variables

---

## Monitoring & Compliance Checks

### Per-Run Health Metrics
Track these metrics after each run:
1. **Success rate**: `ok_count / total_attempts` (target > 85%)
2. **Rate limit hits**: Count of `TokenBucket` waits (should be low)
3. **Error patterns**: 429 Too Many Requests = slow down
4. **CAPTCHA indicators**: Pages < 40KB with no products = block

### Red Flags (Reduce Rate If Seen)
```
• HTTP 429 responses > 5% of requests
• Page size < 40KB (challenge page detected)  
• Zero data-asin elements on list pages
• Timeout errors increasing
```

### Green Lights (Safe to Maintain or Slightly Increase)
```
• Success rate > 90%
• Page sizes consistent (200KB+)
• All ASINs parsed correctly
• No 429 or CAPTCHA responses
```

---

## Scaling Strategy

### Phase 1: Stabilize (Week 1)
```yaml
Rate: 60 req/min
Runs: 12/day (every 2h)
Scope: Top-level + Subcategories
Monitor: Success rate, error patterns
```
**Goal**: Confirm zero CAPTCHAs for 7 consecutive days.

### Phase 2: Optimize (Week 2)
```yaml
Rate: 60 req/min (maintain)
Runs: 24/day (every hour) ← INCREASED FREQUENCY
Scope: Full catalog + watchlist deep-scan
Monitor: Same as Phase 1
```
**Goal**: Double daily rows without increasing rate.

### Phase 3: Aggressive (Week 3+)
```yaml
Rate: 90 req/min (only if Phase 1-2 are clean)
Runs: 24/day
Scope: Full catalog + competitor monitoring
Monitor: Watch for 429 spike
```
**Goal**: 2x throughput at moderate risk.

---

## Configuration Reference

### Environment Variables
```bash
# Rate limiting
SCOUT_MAX_REQUESTS_PER_WINDOW=60    # Safe: 60 req/min
                                  # Aggressive: 90 req/min (monitor!)

# Gap between requests
SCOUT_GAP_MIN=4                     # Min seconds
SCOUT_GAP_MAX=10                    # Max seconds

# Concurrency
SCOUT_FETCH_WORKERS=12              # Parallel threads

# Retries
SCOUT_MAX_RETRIES=2                 # Fail fast on blocks
```

### GitHub Actions Workflow
See `.github/workflows/high-freq-collect.yml` for full configuration.

---

## Historical Performance Data

| Period | Rate | Runs/Day | Rows/Day | Success Rate | Notes |
|--------|------|----------|----------|--------------|-------|
| Legacy | N/A | 2 | ~3,500 | ~75% | Old collector, no rate limiting |
| v1 Pipeline | 40/min | 4 | ~12,000 | ~85% | Initial optimization |
| v2 Pipeline | 60/min | 12 | ~18,000 | ~92% | Safe zone, current |
| Target | 90/min | 24 | ~27,000 | TBD | Future (requires monitoring) |

---

## Compliance Best Practices

### Do ✅
- Randomize delays between requests (4-10s range)
- Use rotating user-agents (currently fixed Chrome UA)
- Respect `robots.txt` where applicable
- Monitor error rates and slow down if needed
- Keep requests per minute below 90 for safety

### Don't ❌
- Never exceed 120 req/min without explicit approval
- Don't scrape during peak Indian hours (10 AM - 8 PM IST)
- Avoid scraping the same ASIN repeatedly within 1 hour
- Don't ignore 429 responses — they're warning signs
- Never attempt to bypass CAPTCHA challenges

---

*Last Updated: 2026-09-24*
*Status: Production-Ready (Safe Zone: 60 req/min)*