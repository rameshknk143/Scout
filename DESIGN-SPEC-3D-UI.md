# ScoutVeda UI/UX Redesign — Complete Strategy & Design Spec
**Date:** 2026-09-02 · **Status:** Draft v1 (video-frame analysis pending — will refine when vision returns)

---

## 0. The Objective (corrected)

ScoutVeda is a **professional SaaS platform for Amazon sellers** — scraped and enriched market intelligence, in the same category as Jungle Scout, Helium 10, Keepa, SmartScout, DataHawk.

It must communicate: **professionalism, trust, intelligence, speed, data-driven decisions, premium quality, scalability, innovation.**

It must NOT communicate: Iron Man, Marvel, superheroes, sci-fi characters, comic-book or entertainment themes.

The reference videos are a **craft benchmark only**: cinematic lighting, motion quality, UI polish, futuristic design *language* — the discipline, not the costume.

---

## 1. What the reference videos teach (design principles, not themes)

From the videos' documented methods (v2's narration describes its technique precisely; v3's frames pending vision):

| Principle | What the videos do | How ScoutVeda uses it |
|---|---|---|
| **Hero product render** | One premium 3D product shot, studio-lit, horizontal, hero-scale | Landing hero: a data-visualization "product" — an animated opportunity-score render, not a headphone |
| **Cinematic motion** | Slow eased animations, never linear; things assemble/explode on scroll | Section reveals, KPI count-ups, chart draw-in — 600–900ms, cubic-bezier(0.16,1,0.3,1) |
| **Depth via layers** | Foreground/mid/background separation, parallax on scroll | Layered cards (translateZ), sticky-scroll feature sections, subtle parallax — not gimmicky |
| **HUD-style data polish** | Futuristic readouts: glowing values, monospace numbers, scan effects | Number typography (mono, tabular), status glows, live-updating tickers — the *finish*, without sci-fi chrome |
| **Restraint** | Few elements, executed precisely; dark/neutral field; one accent | Neutral surfaces, one accent (amber), semantic tokens, no decoration for its own sake |
| **Frame-perfect sequencing** | Every animation lands on a beat | Orchestrated page-load sequence (nav → KPIs → chart → table) |

**The core lesson:** premium = motion that serves comprehension + lighting/depth that creates hierarchy + absolute restraint. Not 3D everywhere. Not a theme.

---

## 2. Competitor patterns (researched)

| Platform | IA / Navigation | Dashboard signature | What to adopt |
|---|---|---|---|
| **Jungle Scout** | Sidebar grouped: Product Research / Keyword / Suppliers / ToolBox | Saved filters, Opportunity Score (1–10) per niche, AI assist | **Saved filter views**, visible opportunity score on every row |
| **Helium 10** | Header nav + mega menu grouped by function; favorites | Insights Dashboard: "Grow Your Business" action list with **impact level + Take Action**, Revenue/Top Products/Advertising graphs (ACoS/TACoS), My Products table with per-ASIN insights & alerts, marketplace selector top-right | **Next-Best-Action card strip**, per-ASIN alert chips in tables, marketplace selector pattern |
| **Keepa** | Minimal chrome; extreme information density | Price-history graph as the hero of every product page | **Sparklines in table rows**; time-series as first-class citizen |
| **SmartScout** | Left sidebar with 6 grouped categories; top search bar | Brand/Seller/Category/Keyword lenses; per-tool tutorial videos | **Grouped nav + global search**; empty states that teach |
| **DataHawk** | Tracking-first IA: everything is "tracked + alerting" | Daily/historical rank tracking, custom alert rules, exports | **Alert rules surfaced as a product**, export affordances |

### 2026 SaaS dashboard best practice (researched)
- Sidebar 240–280px, collapsible; **not** top-nav for tools
- Top 80–120px of content = **KPI strip** (4–6 cards): one big number + delta vs period + sparkline. No paragraphs.
- F-pattern: **North-Star metric top-left**
- **Operational dashboards**: every screen ends in an action, not just a chart
- **Modular**: rearrangeable widgets, saved views, global date/marketplace filter
- **Dark-first** for professional tools; light mode via tokens
- **Semantic color tokens** — rebrand by changing 6–8 CSS variables
- Empty states = teaching CTAs; skeleton screens, not spinners
- Information density > whitespace (power users); minimal chrome

---

## 3. Current ScoutVeda audit (from the code)

### What's good (keep)
- Real data layer (Supabase via API, typed) — no fake UI
- `sv-` public design system is coherent (cream field, amber accent, glass, grid, tilt)
- Component primitives exist: `Table, Tabs, Select, ChartCard, MetricCard, AlertStrip, ProductDetailDrawer, VerdictBadge`
- Idempotent ingest, honest alerts, live ops heartbeats — the "truthful system" ethos is premium behavior

### Issues found (by priority)

| # | Issue | Where | Severity |
|---|---|---|---|
| 1 | **Two disjoint design languages**: marketing site (sv- premium) vs dashboard (plain white utility) | app/page.tsx vs app/dashboard/* | High |
| 2 | **No semantic token system** — hardcoded hex scattered (e.g., `#d97706` in globals.css AND components); no dark mode possible without rewrite | globals.css, ui/* | High |
| 3 | **Kitchen-sink main dashboard**: trend-radar-client.tsx is 1,048 lines, 4 tabs (watchlist/radar/bestsellers/storefront), mixed concerns | dashboard/page.tsx | High |
| 4 | **No KPI strip** — dashboard opens into tables, no North-Star numbers | dashboard/page.tsx | High |
| 5 | **Emoji in production UI** ("🕒 Synchronizing…", "✅ Sync completed") | trend-radar-client | Medium |
| 6 | **Inconsistent page headers** — some h1+subtitle, some none; "Good evening, Ram" hardcoded (time-blind) | all dashboard pages | Medium |
| 7 | **Nav labels mislead**: "Trend Explorer" = watchlist; "Product Opportunity Finder" = validator | Sidebar.tsx | Medium |
| 8 | **No global search / command palette**; no saved filter views | dashboard | Medium |
| 9 | **No skeleton loaders standardized** (text-pulse only); no empty-state teaching | all clients | Medium |
| 10 | **Chart theming ad hoc** — recharts defaults per page, inconsistent colors | all charts | Medium |
| 11 | **Style islands** — System Health (glass+grid) looks like a different app than the rest of the dashboard | system-health | Medium |
| 12 | **Tables not dense/configurable** — no density toggle, no column choice, no sparklines | all tables | Medium |
| 13 | **Mobile**: tables overflow-scroll only; no card-list responsive pattern | all tables | Low-Med |
| 14 | **No motion system** — hover states vary; no load choreography | everywhere | Medium |
| 15 | **Unused 3D deps shipped** (three, R3F, gsap ~heavy) while actual 3D is CSS-only | package.json | Low (bundle weight) |

---

## 4. Redesign strategy

**One sentence:** merge the dashboard into the marketing site's design language, re-found on semantic tokens, restructure around a KPI-first operational dashboard, and apply cinematic motion with total restraint.

### 4.1 Design foundation — semantic token system (do this FIRST)

```css
:root /* LIGHT */
--surface-0: #F7F8FA;      /* app field */
--surface-1: #FFFFFF;      /* cards */
--surface-2: #F1F3F7;      /* inset wells, table headers */
--text-primary: #0F172A;
--text-secondary: #475569;
--text-tertiary: #94A3B8;
--accent: #D97706;          /* amber — the ScoutVeda brand accent, kept */
--accent-strong: #B45309;
--accent-soft: rgba(217,119,6,.08);
--positive: #059669;  --positive-soft: rgba(5,150,105,.08);
--warning: #D97706;   --warning-soft: rgba(217,119,6,.08);
--critical: #DC2626;  --critical-soft: rgba(220,38,38,.08);
--info: #2563EB;     --info-soft: rgba(37,99,235,.08);
--hairline: rgba(15,23,42,.08);
--hairline-strong: rgba(15,23,42,.14);
--radius-card: 14px; --radius-control: 10px;
--shadow-card: 0 1px 2px rgba(15,23,42,.04), 0 4px 16px -6px rgba(15,23,42,.08);
--shadow-card-hover: 0 2px 4px rgba(15,23,42,.05), 0 12px 28px -8px rgba(15,23,42,.14);
--font-sans: Inter var, Fira Sans, system-ui;  /* upgrade — see §6 */
--font-mono: "JetBrains Mono", Fira Code, monospace;
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--dur-fast: 150ms; --dur-med: 300ms; --dur-cine: 700ms;

:root[data-theme="dark"]  /* DARK-FIRST pro mode */
--surface-0: #0B0F17;  --surface-1: #111826;  --surface-2: #1A2332;
--text-primary: #F1F5F9; --text-secondary: #94A3B8; --text-tertiary: #64748B;
--hairline: rgba(241,245,249,.08); --hairline-strong: rgba(241,245,249,.14);
/* accent + semantic stay same hue, slightly lifted for contrast */
```

**Rationale:** tokens make dark mode + future white-label trivial; kill every hardcoded hex. This is what 2026 dashboards converge on.

### 4.2 Information architecture

**New nav (grouped by user job, not by internal history):**

```
OVERVIEW
  Dashboard          ← KPI strip + Next-Best-Actions + activity feed
RESEARCH
  Opportunity Finder  (was Validator)
  Product Database
  Trend Explorer      (watchlist + movers)
  Competitor Analysis
KEYWORDS
  Keyword Research
LISTINGS
  Listing Optimizer
  Listing Health
BUSINESS
  My Products · Inventory · Profit & Fees · Storefront (tab) · Analytics
SYSTEM
  System Health
```

**Rationale:** Helium 10's redesign found grouping **by core function** beats tool names (their UX case study); SmartScout's 6-category sidebar is the same lesson. "Trend Explorer"/"Opportunity Finder" rename fix issue #7.

**Global elements:** marketplace selector (top-right, Helium 10 pattern), ⌘K command palette / global search (SmartScout pattern), date-range filter in the top bar that re-scopes every widget on the page.

### 4.3 Landing page (hierarchy fix)

Keep the sv- system (it's the strongest part) with these changes:

1. **Hero:** keep headline + trust line; replace static browser mockup with a **live-feeling product render** — an animated "Opportunity Score" dial that counts up (82 → PURSUE) with a slow eased draw, on the existing cream field. One hero object, cinematic timing. (This is the videos' hero-render principle, expressed as ScoutVeda's actual product: a score, not a gadget.)
2. **Social proof numbers row** under hero: `195K+ snapshots · 16 departments · 12 ASINs tracked live · 2× daily` in mono type — data as trust.
3. **Feature grid → job-based:** group features under "Find it / Validate it / Track it / Grow it" (matches nav).
4. **Comparison table:** ScoutVeda vs spreadsheet-vs-nothing framing (not fake competitor logos).
5. CTA: primary "Start free research" (keep), secondary → live demo video section.
6. Motion: scroll-triggered section reveals (translateY 24px → 0, 700ms, ease-out) — already half-present via sv-glass; add count-up animations to the proof row. **No parallax gimmicks on the landing.**

### 4.4 Dashboard (the core rebuild)

**Main Dashboard page becomes the operational hub (Helium 10 pattern + 2026 practice):**

```
┌──────────────────────────────────────────────────────────┐
│ KPI STRIP (4 cards, top 80-120px)                        │
│ [Watchlist opportunities] [Avg net margin %]             │
│ [Active alerts]        [Data freshness (System)]         │
│   big number + Δ vs last week + sparkline                │
├──────────────────────────────────────────────────────────┤
│ NEXT BEST ACTIONS (alert strip → action cards)           │
│ e.g. "Cetaphil BSR climbed 12% — review buy price" [→]   │
├──────────────────────────────────────────────────────────┤
│ [ Trend radar digest: movers + entrants charts ]         │
│ [ Watchlist table (top 5, dense, sparklines) ]  [→ full] │
└──────────────────────────────────────────────────────────┘
```

- Every card ends in an action (operational-dashboard principle).
- The 1,048-line trend-radar-client splits into: `DashboardOverview`, `WatchlistTable`, `BestsellersExplorer`, `StorefrontPanel` — each its own route/tab, shared via components.

**Tables (Keepa density + Helium 10 chips):**
- Density toggle (comfortable / compact), sticky header, row hover, per-row sparkline (7-day price/BSR), verdict chips colored by semantic tokens, per-ASIN alert chip, saved filter views ("Save this search" → named chip row), export CSV.
- Mobile: tables become stacked cards (title + 3 key figures + sparkline + chevron).

**Charts:** one shared `<ChartTheme>` — mono axis labels, hairline grid, accent series, semantic overlays; entry animation = 700ms eased draw; tooltips = surface-2 cards with mono numbers.

**System Health page** keeps its 3D/depth layer (it's the showpiece) but re-skins onto the same tokens so it stops being a style island — glass cards adopt token surfaces; perspective grid stays.

### 4.5 Motion & micro-interactions system (the "cinematic" layer)

| Interaction | Spec |
|---|---|
| Page load | Staggered: nav(0ms) → KPI strip(80ms apart) → charts(240ms) → tables(400ms), each translateY 12px→0 + fade, 700ms ease-out |
| KPI numbers | Count-up over 900ms, mono font, tabular-nums; delta arrow fades in after |
| Card hover | border-color→hairline-strong + shadow-card-hover + translateY(-2px), 300ms (already half-implemented on .bento-card) |
| Button press | scale(0.98) → 1, 150ms |
| Drawer (product detail) | Backdrop fade 200ms; panel slide 320ms ease-out; content stagger 60ms/row |
| Toasts | Slide-up + fade; auto-dismiss 4s; severity-colored left rail |
| Chart interaction | Crosshair hairline + tooltip card; series emphasis dims others to 40% opacity |
| Reduced motion | `@media (prefers-reduced-motion: reduce)` → all of the above collapse to opacity-only or none |

**Rationale:** every timing above comes from the video references' feel (slow, eased, decisive) — motion serves hierarchy and comprehension. The restraint is the premium part.

### 4.6 Typography (upgrade)

| Role | Now | New |
|---|---|---|
| Display/H1 | Fira Sans 700, text-xl | **Inter var** 650, 24–28px, -0.02em tracking |
| Section labels | mixed | 12px, 600, 0.08em uppercase, text-secondary |
| Body | 14–15px Fira Sans | Inter 14px/1.55 |
| Numbers/data | mixed mono | **JetBrains Mono**, tabular-nums everywhere a number can change |
| Landing display | keep sv- (works) | keep, + Inter display weights |

**Rationale:** Inter's larger x-height + t-nums mono is the 2026 SaaS default for a reason — data legibility at small sizes. Fira Sans stays as fallback.

### 4.7 Component library (build on existing ui/)

Extend `components/ui/` into a real kit — all token-driven:

`Button (primary/secondary/ghost/destructive, sizes)` · `Input/Select/DatePicker` · `KpiCard` · `MetricCard` · `ActionCard` · `Table (dense, sparkline cell, chip cell, saved views)` · `ChartCard` · `VerdictBadge` (token colors) · `AlertChip` · `Drawer` · `Tabs` · `Toast` · `Skeleton` · `EmptyState` (teaching CTA) · `CommandPalette (⌘K)` · `MarketplaceSelector` · `DensityToggle` · `ThemeToggle (light/dark)`

**shadcn-style composition, not a new dependency** — copy patterns, own the code. (Fits the ₹0 + minimal-deps rule; removes nothing.)

### 4.8 Responsive

- ≥1280: sidebar 256px + content max-w-6xl
- 1024–1279: sidebar 64px icons + flyout on hover
- 768–1023: sidebar → bottom sheet menu; KPI strip 2×2
- <768: single column; tables → cards; KPI strip horizontal scroll-snap; charts full-bleed; System Health 3D grid hidden (GPU mercy)

### 4.9 Rollout order (working software, not big bang)

1. **Tokens + theme toggle** (foundation; no visual break, enables everything after)
2. **ui/ component kit** on tokens; replace emoji statuses; skeletons + empty states
3. **Dashboard rebuild** — split trend-radar; KPI strip; Next-Best-Actions; dense tables w/ sparklines + saved views
4. **Nav + labels + ⌘K + marketplace/date global filter**
5. **Landing hero motion pass + proof numbers row**
6. **System Health re-skin onto tokens** (keep 3D layer)
7. **Dark mode QA** (it should "just work" post-tokens)

Each step ships, deploys, and is verifiable — no long-lived redesign branch.

---

## 5. What the pending video analysis will add

When vision returns (hourly job armed): exact color-grading reads (dominant hues, contrast ratios), specific motion beats (what transitions at which scroll %), HUD overlay anatomy (what specifically reads as "futuristic data" vs costume), and lighting direction (rim/key/fill) — all folded into §1's principle table and §4.5's motion specs as refinements, **not** direction changes. The direction is locked here: premium SaaS, amber accent, dark-first option, restrained cinematic motion.
