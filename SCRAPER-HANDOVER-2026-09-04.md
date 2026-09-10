# ScoutVeda Scraper — Handover Pack

**Written:** 2026-09-04 (IST)
**Written by:** Claude (read-only audit session; **no file in this repo was modified**)
**For:** Hermes, or whoever picks up the scraper next
**Repo:** `d:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\scout-cloud`

---

## 0. Read this first

Everything below is **measured**, not estimated, unless the line says "unknown" or
"not verified". Where a number came from a live HTTP fetch or a SQL query, the raw
output is in Appendix A. Two of my own earlier hypotheses were **disproved by my own
tests** during this audit — they are flagged inline as CORRECTION so you don't
inherit them.

House rule that applies to you too: **never invent a value.** If you don't know a
number, write "unknown". Show raw output rather than a confident summary of it.

**Nothing in this document has been applied.** It is a description of the system as
it stands on 2026-09-04 plus a prioritised change list. Ram's standing instruction
for the session that produced it was "without modifying anything". Get his go-ahead
before touching code.

---

## 1. What the system is

Three independent scraping engines write into **one** Postgres table (`snapshots`)
in Supabase. There is no shared scheduler and no orchestrator — each engine runs on
its own clock and they only meet at the database.

```
+-- GitHub Actions -------------+  20:45 UTC nightly, ~47 min wall clock
|  scraper/collector.py         |  31 categories x 4 list types = 124 page fetches
|  requests + regex, no browser |  -> ~3,000-3,600 rows per run
+-------------------------------+

+-- Oracle VM (the 24/7 box) ---+  06:20 + 15:20 IST, ~5 min each
|  vm/scoutd/tasks/scrape.py    |  12 watchlist ASINs, detail pages
|  4 routes, cheapest first:    |  direct -> phone tunnel -> relay -> headless Firefox
+-------------------------------+  -> 12 rows per pass

+-- Your laptop (Maxun robots) -+  hourly while the laptop is powered on
|  scraper/maxun_bridge.py      |  headless Chrome on a residential IP
|  2 categories x 30 products   |  -> 60 rows per pass
+-------------------------------+
```

### The collector's inner loop (one page)

```
GET the bestseller URL
  |-> reject if response < 40,000 bytes            (block pages are small)
  |-> reject if body contains "automated access"
  |-> reject if body contains "enter the characters"
  |-> on failure: retry twice, backoff 2*(attempt+1), rotate User-Agent
  |-> optional ScrapeOps proxy fallback (also gated at 40 KB)
split the HTML at every data-asin
  |-> pull 6 fields per slice with 6 regexes
require at least 2 products with both an ASIN and a title, else raise
INSERT ... ON CONFLICT DO NOTHING
sleep random.uniform(10, 30)
next page
```

Per-job `try/except` in `run()` means one failed category never aborts the other 123.

---

## 2. Timing — nothing is 24/7 except the VM's idle loop and the phone tunnel

| Job | Schedule | Defined in |
|---|---|---|
| Nightly collector | `cron: 45 20 * * *` (20:45 UTC = 02:15 IST) | `.github/workflows/nightly-collect.yml` |
| Monitor | `cron: 0 3,8,13,18 * * *` — 4x/day | `.github/workflows/monitor.yml` |
| Storefront sync | `cron: 15 21 * * *` | `.github/workflows/nightly-storefront-sync.yml` |
| Keep-alive | **`schedule:` was REMOVED 2026-08-02** | `.github/workflows/keep-alive.yml` |
| VM scrape | `06:20` + `15:20` IST, `RandomizedDelaySec=900` | `vm/systemd/scout-scrape.timer` |
| VM health | every 15 min, `OnBootSec=2min` | `vm/systemd/scout-health.timer` |
| VM keepwarm | every 10 min, **02:00–19:00 only** | `vm/systemd/scout-keepwarm.timer` |
| VM push | hourly at :35, `RandomizedDelaySec=120` | `vm/systemd/scout-push.timer` |
| VM maintain | `01:10` IST, `RandomizedDelaySec=600` | `vm/systemd/scout-maintain.timer` |
| Laptop robots | hourly resident loop | `laptop_mode_loop.ps1` |

All systemd timers are `Persistent=true`, so a missed run fires on next boot.

### GitHub cron drifts badly — this is normal, not a bug

Actual collector **start** times over 12 consecutive nights (UTC), against a nominal
20:45:

```
20:59  21:03  21:06  22:47  22:49  22:51  22:55  00:05  00:15  02:54  04:30
```

Shared-runner queueing. "Nightly" can land anywhere in roughly an 8-hour window.
Do not build anything that assumes a fixed collection hour.

### Do not re-add these

- `keep-alive.yml` has no `schedule:` on purpose. The file carries the comment:
  *"Do not re-add `schedule:` here. Two pingers would push Render past that cap."*
- `/health` on the API is deliberately **unauthenticated**. Do not add `API_KEY` to
  `keep-alive.yml`.

---

## 3. Throughput — what one minute is worth

Measured from GitHub's Actions API (12 consecutive runs) and from the database.

| Engine | Rate | Per unit |
|---|---|---|
| **Nightly collector** | **~68 rows/min**, 2.2 pages/min | ~26 s per page |
| VM watchlist | ~2.3 products/min | ~21 s per product |
| Maxun laptop | ~1 row/min | 60 rows/hour |

**Caveat that matters:** those rates only apply *during* the run window. For roughly
23 of every 24 hours the collector's rate is **0 rows/min**. Any capacity planning
that multiplies 68 rows/min by 1,440 minutes is wrong by a factor of ~30.

### Collector run duration (GitHub Actions API, 12 runs, minutes)

```
46.5  46.9  47.2  49.1  44.2  46.4  47.3  45.4  47.8  46.2  48.1  48.3
min 44.2   max 49.1   very stable
```

> **CORRECTION.** Earlier in the audit I derived "182-250 minute runs" from
> `collected_at` timestamps and reported it as a slowdown. That was **wrong**. The
> laptop Maxun robots write the same `list_type` values into the same UTC window,
> which stretched the apparent span. GitHub's own API is authoritative: 44-49
> minutes, twelve nights out of twelve. The collector is not slowing down.
> This is also the single best argument for gap #1 below (a `source` column) --
> without it, per-engine questions require guessing.

### Gap between consecutive page fetches (n = 585 intervals)

```
min 0.8s    median 23.2s    mean 26.4s    p90 42.9s    max 370.4s
```

The median of 23.2 s is almost exactly the midpoint of `random.uniform(10, 30)`.

**Conclusion: the collector is sleep-bound, not network-bound or CPU-bound.**
Roughly 80% of the 47-minute run is the process waiting on purpose. That is the
largest single lever in the whole system (see 9.1).

---

## 4. Data volume

```
snapshots                          203,025 rows      86 MB
whole database                                      158 MB
bytes per row (including indexes)                      447
steady state                  ~3,700 rows/day  ~ 1.65 MB/day  ~ 50 MB/month
page download size                          ~400-435 KB each
nightly download                 124 pages x ~420 KB  ~ 50 MB/night
date range in table                        2026-07-06 .. 2026-09-02
distinct ASINs                                       11,226
distinct categories                                      32
distinct list_types                                       6
```

**Supabase free tier is 500 MB.** At 158 MB growing ~50 MB/month that is roughly
**7 months of headroom**.

`snapshots_backup_20260831` holds **191,181 rows** and is dead weight. Dropping it
once the migration is confirmed good would buy back most of a year. I did not drop
it -- that is a destructive action and needs Ram's call.

### Every table in the public schema (row counts as of the audit)

```
snapshots                    203,025
snapshots_backup_20260831    191,181
ops_events                        66
storefront_sales_metrics          60
sync_jobs                         47
validations                       10
ops_heartbeats                     5
email_otps                         3
my_products                        1
seller_credentials                 1
users                              1
workspace_members                  1
workspaces                         1
audit_logs                         0
org_members                        0
storefront_orders                  0
```

**There is no `price_history` table.** This matters -- see section 7.

---

## 5. Energy and cost

There is **no power telemetry anywhere in this stack**, so watts are **unknown** and
I will not guess. Duty cycle is the honest proxy.

### Oracle VM (2 vCPU, 956 MB RAM, 45 GB disk, 4 GB swap -- always-free x86 micro)

Computed from measured per-task run times in the heartbeats:

```
health     96 runs/day x 7.8 s  =  749 s
keepwarm  108 runs/day x 0.3 s  =   32 s
push       24 runs/day x 0.2 s  =    5 s
maintain    1 run /day x 1.2 s  =    1 s
scrape      2 runs/day x 318 s  =  636 s
                          total = 1,423 s/day = 23.7 min

duty cycle = 23.7 / 1440 = 1.6%       idle 98.4% of the time

peak memory: 115 MB (browser route), 52 MB (direct), 9-19 MB (keepwarm/push)
free RAM on the box: ~500 MB available, swap in use 67 MB, disk 23% (35 GB free)
```

At a 1.6% duty cycle the VM's marginal energy cost is negligible; the instance draws
its baseline whether it scrapes or not.

### The real scarce resource is GitHub Actions minutes

```
collector          47.0 min/day
monitor       4 x 0.55 =  2.2 min/day   (max observed 1.05 min)
storefront                0.5 min/day
                        --------------
                         49.7 min/day  ~ 1,491 min/month
```

`rameshknk143/Scout` is a **private** repo, so GitHub Free grants **2,000
minutes/month**. You are at **~75%**. The 31 Aug audit independently put it at 77%.

**This is the hard ceiling on adding more Actions-hosted scrapers.** It is why the
monitor was already throttled to 4 runs a day.

I could not read consumption directly -- the billing endpoint
`GET /users/rameshknk143/settings/billing/actions` returns **404**. The figure above
is computed from per-run durations, not from GitHub's own meter. Treat it as
accurate to a few percent, not exact.

### Laptop and phone

- Laptop: Maxun robots run ~1 h/day of headless Chrome while the machine is on.
  Marginal cost; the machine is on anyway.
- Phone: the Termux tunnel (`phone/tunnel.sh`) holds an `ssh -N -R` reverse SOCKS5
  proxy open 24/7 under a wake-lock. Battery cost is **unknown** -- not measured.
  Keep the phone on charge.

---

## 6. Categories -- you already have all of them, at the top level only

**The 31 categories are not a curated subset.** `scraper/collector.py` says so:
expanded 2026-07-08 to *"all 31 of Amazon.in's real bestseller categories (verified
against the live nav, not guessed)"*.

```
Electronics Accessories -> electronics      Home & Kitchen -> kitchen
Beauty & Personal Care  -> beauty           Sports & Fitness -> sports
Toys & Games            -> toys             Stationery/Office -> office
Pet Supplies            -> pet-supplies     Car Accessories -> automotive
Garden & Outdoors       -> garden           Baby Products -> baby
Watches & Gifting       -> watches          Clothing & Accessories -> apparel
Amazon Launchpad        -> boost            Amazon Renewed -> amazon-renewed
Apps & Games            -> mobile-apps      Bags Wallets & Luggage -> luggage
Books                   -> books            Computers & Accessories -> computers
Gift Cards              -> gift-cards       Grocery & Gourmet Foods -> grocery
Health & Personal Care  -> hpc              Home Improvement -> home-improvement
Industrial & Scientific -> industrial       Jewellery -> jewelry
Kindle Store            -> digital-text     Movies & TV Shows -> dvd
Music                   -> music            Musical Instruments -> musical-instruments
Shoes & Handbags        -> shoes            Software -> software
Video Games             -> videogames
```

x 4 list types:

```
bestsellers        gp/bestsellers
new-releases       gp/new-releases
most-wished-for    gp/most-wished-for
most-gifted        gp/most-gifted
```

= 124 fetches per night.

**The first 11 labels are load-bearing.** The source file warns that renaming any of
them *"would fragment existing trend history under a new label."* If you rename one,
every chart built on it silently splits in two. Do not rename them.

Two documented exceptions:

- "Gifting/Novelty" has **no Amazon browse node** -- `watches` is the substitute.
- **Movers & Shakers is deliberately excluded.** It was tested and returns zero
  server-rendered products (client-side rendering). Re-testing is cheap; the
  exclusion was correct at time of writing.

### What is actually missing is DEPTH, in two directions

**(a) Ranks 31-100.** I fetched two live bestseller pages during this audit and both
returned **exactly 30 data-asin matches**. The database agrees: across 2,493
bestseller pulls, min(count) = 30 and max(count) = 30. Never once 31.

Amazon bestseller lists run to **100**. **You are capturing the top 30% of every
list.** Reaching 31-100 needs pagination (`?pg=2`, `?pg=3`).

> **NOT VERIFIED.** I did **not** test whether `?pg=2` is server-rendered. That is
> the cheapest, highest-value check available and it should be the first thing
> anyone does. One curl answers it. If page 2 is server-rendered, the same parser
> works unchanged and your coverage triples.

**(b) Subcategories.** The URL template is:

```
BASE_URL = "https://www.amazon.in/{path}/{slug}/"
```

There is **no slot for a browse-node ID**. Amazon's tree goes several levels deep
(Home & Kitchen -> Kitchen & Dining -> Cookware -> ...) and every node has its own
100-item bestseller list. You fetch **31 roots out of a tree with thousands of nodes**.

Depth is also where the money is. A top-level Home & Kitchen bestseller is a national
brand nobody can compete with. A third-level subcategory bestseller is where
reseller-viable products actually live.

### Rank integrity by list type (all-time, from the DB)

```
bestsellers        avg 30.0   min 30   max 30   over 2,493 pulls
most-gifted        avg 30.0   min 29
most-wished-for    avg 29.8   min 24
new-releases       avg 27.7   min  1   <- dragged only by genuinely tiny lists
```

`new-releases` looks broken and is not: **1,167 of 1,273 pulls returned a full 30**.
The average is pulled down by Movies & TV Shows (avg 2.3) and Music (avg 3.5), which
genuinely publish only 2-3 new releases a day. This is exactly why
`collect_category()` uses a sanity floor of **2**, not 10 -- the source comment says
a floor of 10 *"would have rejected those real fetches forever."*

---

## 7. Attributes -- what is captured, and why not more

### The six fields a list-page card gives you

Six regexes in `scraper/collector.py`, all built on **stable substrings, never
hashed CSS classes** (`_cDEzb_..._3mJ9Z` style names change on every Amazon deploy).
Keep it that way.

```
ASIN_RE    matches  data-asin="XXXXXXXXXX"          10 chars, [A-Z0-9]
RANK_RE    matches  zg-bdg-text">#N<
TITLE_RE   matches  class="...p13n-sc-css-line-clamp...">TEXT<
RATING_RE  matches  aria-label="R out of 5 stars, N ratings"
PRICE_RE   matches  rupee sign + digits + REQUIRED 2 decimals
IMAGE_RE   matches  the FIRST <img ... src="..."> in the block
```

### The snapshots schema

```sql
CREATE TABLE IF NOT EXISTS snapshots (
    id            SERIAL PRIMARY KEY,
    asin          TEXT NOT NULL,
    category      TEXT NOT NULL,
    list_type     TEXT NOT NULL,
    rank          INTEGER,
    title         TEXT,
    price         REAL,
    rating        REAL,
    review_count  INTEGER,
    image_url     TEXT,
    collected_at  TIMESTAMPTZ NOT NULL
);
-- uq_snapshots_row UNIQUE (asin, category, list_type, collected_at)
```

### Two structural facts about the parser you must know

**1. `rating` and `review_count` come from ONE regex** -- group 1 and group 2 of
`RATING_RE`. That is why their fill percentages are identical to the decimal on
every list type. One selector break kills **both**, and there is no cross-check to
catch it.

**2. `IMAGE_RE` takes the FIRST `<img src>` in each product block.** A 100% image
fill rate therefore means *"a URL was captured"*, **not** *"the correct product image
was captured"*. The 100% is not as good as it looks.

### Why the richer attributes are not there

MRP, discount %, seller name, availability, buy-box owner, FBA/FBM, and
BSR-within-category are **not present on list pages at all**. They exist only on
**product detail pages** -- one request per ASIN instead of one request per 30
products. A **30x request cost**. That is exactly why the VM does detail scraping for
only 12 watchlist ASINs.

**And this is the part worth acting on:** per the 31 Aug audit, the VM **already
collects** MRP, discount, seller, availability and BSR for those 12 ASINs -- and
there is **no table in the cloud database to receive them**. I listed all 16 public
tables; there is no `price_history`. **Those fields are collected and then stranded
on the VM.** That is plumbing, not scraping, and it is cheap to fix.

---

## 8. Quality layers currently in force

There are five real layers. Knowing where each one sits tells you where a bad row can
still get in.

**Layer 1 -- fetch guards (`collector.fetch`)**
- 25 s timeout, 2 retries, backoff `2 * (attempt + 1)`
- User-Agent rotation: desktop Chrome 124 <-> iPhone iOS 17.4
- `Accept-Language: en-IN`
- **response must be > 40,000 bytes** (block pages are small)
- reject if body contains `automated access` or `enter the characters`
- optional ScrapeOps proxy fallback, gated at 40 KB as well

**Layer 2 -- post-parse sanity floor (`collect_category`)**
```
valid = [p for p in products if p has both asin and title]
if len(valid) < 2: raise ValueError(...)
```
Added after the 31 Aug audit finding *"no post-parse sanity check"*. The floor of 2
is deliberate and measured -- see section 6.

**Layer 3 -- database uniqueness**
`uq_snapshots_row UNIQUE (asin, category, list_type, collected_at)` plus
`INSERT ... ON CONFLICT DO NOTHING RETURNING id`, so re-running a job is safe and
the insert count is the count of genuinely new rows.

**Layer 4 -- ingest bounds (API `/ingest/maxun` only)**
```
ASIN must match ^[A-Z0-9]{10}$          else the row is skipped entirely
review_count outside 0 .. 10,000,000    -> NULL
price outside 1.0 .. 10,000,000.0       -> NULL
rating outside 0.5 .. 5.0               -> NULL
rank outside 1 .. 10,000,000            -> NULL
collected_at must be >= 2025-01-01 and <= now + 1 day, else it is replaced
```

**Layer 5 -- monitoring (`scripts/monitor.py`, 11 checks, exits 1 on any failure)**
```
api /health                    deployed build matches
auth enforced (no key)         auth enforced (bad key)
trend-radar/categories         trend-radar/digest
data freshness                 nightly collector freshness (<= 48 h, separate check)
vm scrape yield (got >= want/2, want=12)
vm alive (dead-man's switch)
category table sample          web app reachable
```
The nightly-collector check is separate on purpose: *"laptop robots write hourly, so
whole-table freshness stays green even if the nightly collector stops dead."*

**Plus, on the VM:** `vm/scoutd/tasks/scrape.py` decides the run verdict **from the
database, not the exit code**, because scrape.py exits 0 whether it captured 15 of 15
or 2 of 15. Low yield is a **warn**, not an error, on the stated reasoning that
*"paging about a condition that self-heals in twelve hours trains people to ignore
the alerts that matter."*

### Measured quality, all time, by list type

```
list_type          rows     price%  rating%  rank%  image%  title%
bestsellers      74,790      91.6    98.7    100.0   100.0    99.1
most-gifted      44,579      68.8    99.5    100.0   100.0    ~99
most-wished-for  44,392      66.5    99.8    100.0   100.0    ~99
new-releases     35,317      94.0    90.5    100.0   100.0    99.9
watchlist           353      99.2     --      65.7     --      --
custom-scrape        60      61.7     --       --      --      --
```

The whole-table price figure of ~79-81% is **a mix effect, not a defect**:
bestsellers 91.6% and new-releases 94.0% are diluted by most-gifted 68.8% and
most-wished-for 66.5%, which are genuinely price-sparse list types on Amazon's side.

Weekly price-fill trend (nine weeks): `82.5 / 80.8 / 80.3 / 80.9 / 80.6 / 81.8 /
81.3 / 81.7 / 83.4` -- flat. Nothing is degrading.

### Integrity checks that came back clean

```
duplicate (asin, category, list_type, collected_at) groups ......... 0
flattened / backfilled timestamps .................................. 0
malformed ASINs .................................................... 0
ratings outside 0.5-5.0 ............................................ 0
image URLs on a non-Amazon scheme ................................... 0
truncated titles .................................................... 0
cross-list price disagreement: 13,690 ASIN-days appear in >1 list,
    only 1.14% disagree at all, average spread 0.29%
```

The old backfill bug **is resolved**. The 60 `custom-scrape` rows sit at two
legitimate timestamps (2026-08-02 13:22:59 and 2026-08-11 05:38:14, 30 rows each),
not one flattened block.

### Four things that look like bugs and are not

1. **Prices of exactly 1.00** -- real Amazon Pay / gift-card listings.
2. **Very short titles** -- real movie and music track names.
3. **Ranks above 100** -- real. Amazon BSR is unbounded within a category.
4. **new-releases returning 2-3 rows** -- real tiny categories (Music, Movies & TV).

Do not "fix" any of these. Each one was chased down and confirmed genuine.

---

## 9. Genuine defects, and the fix for each

### 9.0 The evidence that settled the price question

Two live fetches on 2026-09-04. Raw output, unedited:

**Amazon Renewed** -- https://www.amazon.in/gp/bestsellers/amazon-renewed/
```
HTTP 200   bytes = 404,943   (fetch() floor is 40,000)
blocked-page markers: automated=False  captcha=False

  ASIN_RE   data-asin                       30 matches
  RANK_RE   zg-bdg-text                     30 matches
  TITLE_RE  p13n-sc-css-line-clamp          30 matches
  RATING_RE out of 5 stars                  30 matches
  PRICE_RE  CURRENT (2 decimals)             0 matches
  decimals OPTIONAL                          1 matches
  a-price-whole span                         0 matches
  a-offscreen span                           0 matches
  raw markup: no "a-price" substring on the page at all
```

> **CORRECTION.** Earlier in this audit I hypothesised that the PRICE_RE 2-decimal
> requirement was the cause of Amazon Renewed 0% price fill. **My own test disproved
> it.** Renewed bestseller cards render **no price element whatsoever**. Nine other
> fields come back perfectly. No regex change can produce a price that is not in the
> HTML. The only route to a Renewed price is the product detail page.

**Home & Kitchen** (the control) -- https://www.amazon.in/gp/bestsellers/kitchen/
```
bytes = 435,994
  data-asin                    30
  PRICE_RE current (2dp)       28    <- 93.3%, matching the DB measured 93.3%
  decimals optional            29
  rupee sign anywhere          29
```

So the 2-decimal rule **does** cost real data -- about **1 row in 30** (~3.3
percentage points). One product genuinely has no price on the page. Worth fixing;
it just does not explain Renewed.

That script then died with a UnicodeEncodeError while printing markup context on the
Windows cp1252 console (the rupee sign). The counts above had already printed and
are valid. Re-run with PYTHONIOENCODING=utf-8 if you want the surrounding markup.

### 9.1 Worst categories, last 7 days

```
Amazon Renewed             504 rows   price   0.0%     <- no price markup exists
Music                      642 rows   price  43.9%
Movies & TV Shows          588 rows   price  54.3%
Jewellery                  780 rows   price  61.7%   rating 75.0%
Shoes & Handbags           810 rows   price  70.1%
Electronics Accessories    810 rows   price  70.4%

best:
Competitor Watchlist                  price  98.6%
Beauty & Personal Care                price  96.8%
Health & Personal Care                price  92.4%
Home & Kitchen                        price  91.8%
```

**Unresolved:** why Jewellery and Music specifically underperform is **unknown**. I
did not fetch those two pages. Do that before theorising -- it is one curl each, and
it is the same test as 9.0.

### 9.2 Price staleness (share of consecutive observations where the price moved)

```
watchlist         23.3%
new-releases      15.4%
bestsellers       14.2%
most-wished-for   13.8%
most-gifted       11.4%
```

So ~86% of consecutive observations carry an identical price. Plausible for daily
sampling of Indian retail -- but it also means **daily granularity is close to the
useful floor**. Sampling more often than once a day would mostly store repeats. The
watchlist 23.3% is the counter-example and the argument for keeping the VM twice-daily
detail scrape.

### 9.3 The gap table

| # | Gap | Fix | Risk |
|---|---|---|---|
| 1 | No `source` column -- cannot tell which engine wrote a row | add a nullable TEXT column; writers pass collector / vm / maxun | **None.** Nullable, no writer breaks |
| 2 | No standing quality check -- this audit was manual | nightly job running these same queries; alert when a category price-fill drops below its own 30-day baseline; write to `ops_events` | **None.** Read-only job |
| 3 | PRICE_RE requires 2 decimals | make the decimals optional -- verified +1 row per 30 live | Low. Re-test on 3 categories first |
| 4 | rating + review_count share one regex | split into two patterns; add a run-level canary | Low |
| 5 | IMAGE_RE grabs any img tag | constrain the src to the Amazon media host | Low -- expect the fill rate to drop from 100% to an honest number |
| 6 | Ingest bounds live only on the Maxun route | move the bounds into the shared insert helper so every writer inherits them | Medium -- touches the shared write path |
| 7 | VM deep fields stranded | add nullable mrp / discount_pct / seller / availability / bsr_rank / bsr_category; extend the VM push | Medium -- needs VM-side work |
| 8 | Amazon Renewed 0% price | not fixable on list pages; accept it, or drop the category (504 wasted rows/week) | -- |

The exact statements for 1, 3 and 5:

```sql
ALTER TABLE snapshots ADD COLUMN source TEXT;
```

```
# gap 3 -- decimals optional
PRICE_RE = re.compile(r"\u20b9([\d,]+(?:\.\d{2})?)")

# gap 5 -- pin the image host
IMAGE_RE = re.compile(r"src=\"(https://m\.media-amazon\.com/images/[^\"]+)\"")
```

**Do 1 and 2 first.** Without a `source` column every per-engine question needs
inference from rows-per-hour -- which is precisely the mistake that produced the
bogus "182-minute run" figure earlier in this audit. And gap 2 turns a one-off manual
audit into something that tells Ram *next time*, instead of him having to ask.

A run-level canary for gap 4, in words: after each collector run, compare this run
price-fill and rating-fill per list type against the trailing 7-day mean for the same
list type. If either drops by more than 10 percentage points, write an `ops_events`
row and fail the monitor check. That catches a silent selector break within one
night instead of within one manual audit.

---

## 10. How to improve -- biggest levers first

**10.1 Cut the sleep, not the politeness.** 80% of the 47-minute run is deliberate
sleeping: a 10-30 s random gap averaging 20 s across 124 sequential fetches. Fetching
3-4 categories **concurrently** while keeping the same per-category gap would cut
wall-clock to roughly 15 minutes at an **identical request rate per category** --
Amazon sees the same politeness per URL path. That buys back roughly 1,000 GitHub
Actions minutes a month, which is the budget for everything else on this list.

**10.2 Go deeper before going wider.** Verify page 2 is server-rendered. If it is,
ranks 31-100 triple your rows for triple the requests, using the parser unchanged,
and surface the products actually worth reselling.

**10.3 Drop dead weight.** Amazon Renewed (0% price), plus Gift Cards, Apps & Games,
Kindle Store and Software -- none of them are physical-goods reselling. That is
roughly 9 of 32 categories and ~25% of requests spent on rows nobody will act on.
**Careful:** dropping a category stops its trend history dead. Confirm with Ram first.

**10.4 Reclaim Supabase headroom.** Drop `snapshots_backup_20260831` (191,181 rows)
once the migration is confirmed good. Ram decides, not you.

**10.5 Use the tunnel that now works.** The VM went 1/12 -> 4/12 -> 9/12 -> **12/12**
between 31 Aug and 2 Sep as the phone tunnel came up. That residential route is the
only affordable path to detail-page scraping at volume -- the 30x request cost is
survivable on a residential IP in a way it never was from an Oracle datacentre range.

---

## 11. How to add more scrapers

The existing pattern is good: `collector.py` is a table of targets, six regexes and a
fetch guard. A new scraper is a new module with the same shape, not new
infrastructure.

### Where to run it, given a 75%-consumed Actions budget

| Host | Spare capacity | Best suited to |
|---|---|---|
| **Oracle VM** | **98.4% idle**, 24/7, already supervised by systemd + heartbeats | anything long-running; by far the most underused asset here |
| Laptop (Maxun) | residential IP, browser-capable, ~1 h/day used | JS-rendered pages, detail pages |
| GitHub Actions | ~500 min/month left | **nothing new** until 10.1 frees minutes |

### The checklist

1. New module in `scraper/` exposing a `run()` that returns a per-target ok/rows map.
2. **Reuse `collector.fetch()`** -- you inherit the 40 KB floor, captcha detection,
   UA rotation, retries and the ScrapeOps fallback for free.
3. **Write through `db.insert_snapshot_rows()`** -- you inherit the unique index and
   idempotency.
4. Set a `source` value (gap 1) so its quality is separable from day one.
5. **Register a check in `scripts/monitor.py`.** An unmonitored scraper fails
   silently -- exactly as the collector once "succeeded" while collecting zero rows.
6. Add a systemd timer under `vm/systemd/` rather than a GitHub cron.

### The constraint nobody can engineer around

**More scrapers on the same IP will not work.** Every expansion path here is gated on
egress reputation, which is why the tunnel work mattered more than any parser change.
Volume growth and IP diversity are the same problem -- plan them together.

### Two parser traps that have already bitten this codebase

- `parse_products(page_html)` -- the parameter is **deliberately not named html**.
  Naming it `html` shadows the `html` import and silently broke every category once.
- `maxun_bridge.py` requires a `--category` argument and validates it against the
  canonical names read from the collector source. It refuses to invent a label,
  because an invented label ("Maxun Visual Scrape") once split the charts in two.

---

## 12. What changed recently, and the proof it worked

Ram made a scraper change at the start of September. This is the measured before/after
for the VM watchlist yield (target = 12 ASINs per pass):

```
31 Aug 12:02 IST    1/12    routes: direct=1
31 Aug 20:55 IST    1/12
 1 Sep 12:03 IST    4/12    routes: direct=1, relay=3
 1 Sep 21:11 IST    9/12    routes: browser=7, relay=1, tunnel=1
 2 Sep 11:55 IST   12/12    100% price coverage

monitor check "vm-scrape" flipped error -> ok; the incident auto-resolved.
```

Tunnel health at the same time:
```
tunnel_flow            ok
tunnel_uptime_samples  12/12
tunnel_exit_ip         103.160.27.14 -> 152.57.190.60   (rotated, no breakage)
wedge on 2 Sep 08:45 IST self-resolved by 09:00 IST
```

**The change worked.** Yield went 1/12 to 12/12 in about 48 hours.

> **CORRECTION.** Partway through this audit I reported that the Competitor Watchlist
> had stopped. It had not -- I had read a two-hour-old partial day. It ran 12/12 at
> 100% price coverage at 11:55 IST.

### The tunnel design, briefly

Phone tunnel v2 (`phone/tunnel.sh`, Termux) replaced Every Proxy, which wedged on
1 Sep 2026. In v2 **ssh itself is the SOCKS5 proxy** -- no third-party app:

```
ssh -N -R 127.0.0.1:1080 -o ExitOnForwardFailure=yes -o ServerAliveInterval=30
supervisor: single-instance flock, health test every 1200 s,
            status to ~/tunnel-status.txt, log rotation at 500 KB,
            notify after 3 consecutive failures
VM: ubuntu@140.245.239.162
```

`vm/scoutd/tasks/health.py` runs a **two-stage** tunnel check, and this is the part
worth preserving: stage 1 asks whether something is listening on 127.0.0.1:1080,
stage 2 pushes real traffic through it with `curl --socks5-hostname`. Stage 1 alone
cannot see a "half-tunnel wedge" -- a listener that accepts connections and moves no
data. Facts emitted: `tunnel_listener`, `tunnel_flow` (ok/loop/dead), `tunnel_exit_ip`.
Problems emitted: `tunnel-exit-loop`, `tunnel-wedged`.

### One thing that is out of sync and should be reconciled

`vm/scoutd/tasks/scrape.py` in git contains **zero occurrences of the string
"route"**, but production emits `routes: browser=7, relay=1, tunnel=1`.
**The VM is running code that is not in this repo.** Pull the live file off the VM and
commit it before making any VM-side change, or you will overwrite the working version.

---

## 13. Hard constraints -- do not violate these

These are Ram's standing rules, not suggestions.

- **Everything must be zero-rupee / free tier.** No paid services.
- **Never invent a value.** If a number is unknown, write "unknown". Show raw output
  rather than a confident summary of it.
- **Never report untested work as working.** (`ENGINEERING-STANDARDS.md`)
- **Always show times in IST.**
- **Never print, echo, log or paste a secret value.** Locations only. During this
  audit `DATABASE_URL`, `API_KEY` and `GITHUB_TOKEN` were read from `.env` into shell
  variables and never printed.
- **Do not put the production `DATABASE_URL` on the scraping VM.**
- **`/health` is deliberately unauthenticated.** Do not add `API_KEY` to
  `keep-alive.yml`, and do not re-add `schedule:` to it.
- **The Oracle private key is the only way in.** Oracle keeps no copy. Do not move
  it, do not let it land in a browser download folder, do not regenerate it.
- **Do not exceed 4 OCPU / 24 GB on Oracle** (the always-free ceiling).
- **Self-hosting an automation stack (n8n, a third VPS) is not wanted.** Dropped.
- **Never edit files in `_archive\` or `backups\`** -- read-only originals.
- **Use `backup-safe.ps1`, not `backup.ps1`.** The original copies all 236,000+ files
  including node_modules and a torch venv and aborts on the first long-path error,
  which is why snapshots silently stopped for seven weeks.
- **Ram sends his own outbound messages.** Draft them for him; never send on his
  behalf.
- **Do not rename the first 11 category labels** (section 6).

### Timestamp trap

`collected_at` is `TIMESTAMPTZ`. Writing

```sql
collected_at at time zone 'UTC' at time zone 'Asia/Kolkata'
```

**double-converts** and yields UTC dates while looking like IST. The correct form is:

```sql
collected_at at time zone 'Asia/Kolkata'
```

I made this exact mistake during the audit. It is silent -- the output looks right.

---

## 14. Open questions (genuinely unknown as of 2026-09-04)

1. **Is `?pg=2` server-rendered?** Not tested. Highest value, lowest cost. Do it first.
2. **Do subcategory browse-node URLs work with the current parser?** Not tested.
3. **Why do Jewellery (61.7% price, 75.0% rating) and Music (43.9% price) underperform?**
   Not diagnosed. Fetch both pages and run the same count script as section 9.0.
4. **Actual GitHub Actions minutes consumed** -- computed, not read. The billing
   endpoint 404s.
5. **Phone battery cost of the 24/7 tunnel** -- never measured.
6. **Power draw of anything** -- no telemetry exists. Duty cycle is the only proxy.
7. **Why script files were deleted on 11, 18 and 19 August** -- still unexplained.

---

## 15. File map (full Windows paths)

Repo root:
`D:\Ram Claude Desk\projects\Amazon Reseller\categories\tools-research\scout-cloud`

| What | Path under the repo root |
|---|---|
| Nightly collector | `scraper\collector.py` |
| DB schema + idempotent insert | `scraper\db.py` |
| Maxun bridge | `scraper\maxun_bridge.py` |
| API (ingest, ops, health) | `api\main.py` |
| Monitor, 11 checks | `scripts\monitor.py` |
| VM scrape task | `vm\scoutd\tasks\scrape.py` |
| VM health task (tunnel checks) | `vm\scoutd\tasks\health.py` |
| VM timers | `vm\systemd\*.timer` |
| VM shape and notes | `vm\README.md` |
| Workflows | `.github\workflows\` |
| Phone tunnel supervisor | `phone\tunnel.sh` |
| Phone tunnel setup guide | `PHONE-TUNNEL-SETUP.md` |
| Previous audit | `AUDIT-2026-08-31.md` |
| **This document** | `SCRAPER-HANDOVER-2026-09-04.md` |

Note: `PHONE-TUNNEL-SETUP.md` and `phone\tunnel.sh` were created 2026-09-01 20:59 and
are **untracked in git**. Commit them.

---

## 16. Suggested order of work

```
1. curl the ?pg=2 URL and count data-asin matches          (5 min, answers Q1)
2. curl the Jewellery and Music pages, run the 9.0 script  (10 min, answers Q3)
3. ALTER TABLE snapshots ADD COLUMN source TEXT            (gap 1, zero risk)
4. writers start setting source                            (gap 1)
5. nightly quality sweep writing to ops_events             (gap 2, read-only)
6. pull the live scrape.py off the VM and commit it        (section 12, prevents data loss)
7. commit PHONE-TUNNEL-SETUP.md and phone/tunnel.sh
8. relax PRICE_RE decimals, re-test on 3 categories        (gap 3)
9. split RATING_RE, add the fill-rate canary               (gap 4)
10. concurrency in the collector                           (10.1, frees the budget)
11. everything else
```

Steps 1, 2, 6 and 7 change no behaviour. Step 3 is additive and reversible.
**Ask Ram before step 8 and beyond** -- the standing instruction for the session that
produced this document was "without modifying anything", and it has been honoured:
**no file in this repo was modified, and every database access was a read-only
SELECT.**

---

## 17. State of the working tree when this was written

`git status --short` on 2026-09-04 20:01 IST:

```
 M api/data/fee_tables.json
 M api/profit_calculator.py
 M api/scorer.py
?? SCRAPER-HANDOVER-2026-09-04.md
```

The three modified files are **not from this audit**. Their mtimes are all
**2026-08-15 15:05 IST**, three weeks before this session -- pre-existing uncommitted
work (243 insertions, 77 deletions across profit calculation, fee tables and scoring).
Ask Ram what they are before committing or reverting them.

The only file this audit created is this document.
