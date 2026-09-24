# ScoutVeda UI/UX Redesign — Complete Strategy & Design Spec
**Date:** 2026-09-20 · **Status:** Draft v2 (video-frame analysis complete — 38+ frames across 4 videos)

---

## 0. The Objective (corrected)

ScoutVeda is a **professional SaaS platform for Amazon sellers** — scraped and enriched market intelligence, in the same category as Jungle Scout, Helium 10, Keepa, SmartScout, DataHawk.

It must communicate: **professionalism, trust, intelligence, speed, data-driven decisions, premium quality, scalability, innovation.**

It must NOT communicate: Iron Man, Marvel, superheroes, sci-fi characters, comic-book or entertainment themes.

The reference videos are a **craft benchmark only**: cinematic lighting, motion quality, UI polish, futuristic design *language* — the discipline, not the costume.

---

## 1. What the reference videos teach (design principles, not themes)

Analyzed 35+ frames across 4 videos (v1: 3D sites, v2: Apple-style product, v3: Iron Man scrolling UI, v4: GSAP course). Full notes: `VIDEO-CRAFT-NOTES.md`.

**Updated from 2026-09-23 analysis:**

|| # | Principle | What the videos do | How ScoutVeda uses it |
||---|---|---|---|
|| 1 | **Hero product render** | One premium 3D product shot, studio-lit, horizontal, hero-scale. Black field with rim light, controlled reflections on glossy surfaces | Landing hero: animated "Opportunity Score" dial — same lighting treatment, but the "product" is data visualization, not a physical good |
|| 2 | **Cinematic motion** | Slow eased animations (600–900ms), never linear; scroll-triggered assembly; numbers count up not snap | Section reveals (translateY 12px→0, 700ms), KPI count-ups (900ms), chart draw-in — all using cubic-bezier(0.16,1,0.3,1) |
|| 3 | **Depth via layers** | Three distinct layers: warm black field (background), slightly lighter surface (cards), full luminance content (text/icons). Subtle parallax (2–4px shift) | Layered cards (translateZ), sticky-scroll feature sections, System Health 3D grid — field must be warm black (#0D1117), not clinical blue-gray |
|| 4 | **HUD-style data polish** | Monospace numerals + thin hairline separators + values that glow slightly brighter than labels. Status dots (3px colored circle + mono label). Sparklines (24px high, 1px stroke) | Number typography (JetBrains Mono, tabular-nums everywhere), semantic color chips, sparklines in watchlist table rows |
|| 5 | **Restraint** | Max 2 animated things per screen. One accent hue used consistently. Semantic colors reserved for meaning only (green=good, red=critical) | One accent (amber #D97706), semantic tokens, no decoration for its own sake |
|| 6 | **Frame-perfect sequencing** | Orchestrated page-load: nav fades first, content follows in 80–160ms staggered groups | Page load choreography: nav(0ms) → KPI strip(80ms apart) → charts(240ms) → tables(400ms) |
|| 7 | **Gradient falloff** | Background is never flat — subtle gradient from center (slightly lifted) to edges (deeper black). Creates "vignette" depth without UI chrome | `--surface-0` should use radial or vertical gradient, not solid color. Test `#0D1117` (warm) vs current `#0B0F17` (blue-shifted) |
|| 8 | **Glass only where needed** | Frosted glass (`backdrop-filter: blur(12px)`) reserved for nav bar and modals. Data tables use solid surfaces | Extend glass to nav and drawers only; never on tables or KPI strips |
|| 9 | **Rim light on cards** | Cards have 1px top/left border slightly lighter than card surface — creates edge definition without full border | Add `border-top` and `border-left` at 5% higher luminance on `--surface-1` cards for depth without chrome |
|| 10 | **Strategic color highlighting** | One word or number in accent color (e.g., v1_f17: "power" in green) — draws eye without overwhelming | Use accent color only for: (a) delta arrows showing positive movement, (b) KPI values that are "in policy", (c) primary CTAs. Never for decoration |
|| 11 | **Product-as-artifact composition** | v4_f15: MacBook screen RAISED above black background, thin border framing content | Hero sections should feel like "displayed objects" not flat layouts — elevate with shadow + gradient field |
|| 12 | **Grid patterns as texture** | v4_f1800: subtle grid in code editor top-left corner adds technical texture without distraction | Consider faint 1px grid on System Health 3D canvas for spatial grounding, but not on data tables |
|| 13 | **Center-out underline animation** | v1: navbar items underline from center-out on hover (not left-to-right) | Apply to sidebar nav items — creates feeling of "anchoring" rather than "sweeping" |
|| 14 | **Floating product illusion** | v2_f180: headphones appear to float on dark field with soft even lighting | Opportunity Score dial should have similar floating treatment — subtle shadow beneath, no visible support |
|| 15 | **Screen-within-screen composition** | v3_f80: text box + video player at balanced asymmetry (25%/50%) with drop shadows | Dashboard can use this pattern: KPI strip top, main content area, sidebar panel — each with elevation |
|| 16 | **Value emphasis hierarchy** | Key number is 2–3x larger than its label; labels in muted color (text-secondary/tertiary) | KPI cards: number 32–40px, label 11px uppercase; ensure 3:1 size ratio minimum |
|| 17 | **Semantic motion purpose** | Every animation answers "why does the user need to see this move?" — no decorative motion | Motion serves comprehension: reveal hierarchy, indicate state change, guide attention. Delete any animation that doesn't pass this test |
|| 18 | **OLED void backgrounds** | v4_f8400: pure #000000 black specific to Apple Pro lines conveys sophistication | Test pure black backgrounds for hero sections; reserve for premium product displays |
|| 19 | **Atmospheric scattering** | v3_f2, v3_f8: volumetric fog/atmosphere creating depth layers behind subjects | Add subtle atmospheric glow behind hero elements for depth without UI chrome |
|| 20 | **Exploded view storytelling** | v2_f360: product disassembles into component parts revealing internal complexity | Consider for System Health page — show infrastructure components connecting |
|| 21 | **Tonal layering (no shadows)** | v3_f70/v3_f80: depth via 2–3% luminance steps between surface layers (window→panel→card→input) + 1px hairline dividers; zero box-shadows | Card elevation on `--surface-1` uses luminance step (+3–4% vs surface-0) + 1px top/left hairline, not box-shadow. Reserve shadow for the single floating element only |
|| 22 | **Emissive self-lit points** | v3_f60/v3_f70: small self-illuminated elements (brand glyph, status dots, scrubber line) read as "light sources" on dark field — the only bright pixels = focal points | Status dots, KPI value numbers, and active filter chips get subtle outer glow (`0 0 4px accent at 40% opacity`) so they read as "lit" on the dark field, not flat |
|| 23 | **Tactile segmented controls** | v4_f3600/v4_f2700: pill-shaped segmented controls with dark graphite body + silver/white knob + 1px inner bevel — physical-object metaphor | Density toggle, marketplace selector, and time-range filter use segmented pill controls: `bg:#1c1c1e; radius:999px; knob:#e5e5ea with inset box-shadow` — "tactile" not "flat" |
|| 24 | **Gradient-as-material on hero text** | v4_f1800/v4_f8400: hero headline uses horizontal color gradient fill (background-clip:text) + soft outer bloom (`text-shadow: 0 0 24px color at 30%`) — "lit from within" vs flat ink | Landing hero accent word gets subtle amber→orange gradient fill + soft bloom. Body type stays solid. Never gradient more than one word per screen |
|| 25 | **Choreographed micro-loop** | v4_f8400: browser mock shows 3-step animated sequence: typed URL+caret → checkmark appears → loading spinner → URL resolves — simulates "intelligence is thinking" | System Health "data freshness" indicator uses 3-step loop: "syncing"(spinner, 1.2s) → "synced"(checkmark, 800ms hold) → "next in 4m"(countdown) — not a static green dot |
|| 26 | **Holographic edge-glow (tasteful)** | v4_f7200: 3D model has subtle cyan/white chromatic aberration on edges — "hologram out-of-focus" quality | If using any 3D viz (System Health), apply 1px amber edge-glow at 20% opacity on the mesh to suggest "digital twin". Avoid full chromatic aberration — reads as costume |
|| 27 | **Assembled→exploded keyframe pair** | v2_f360: two side-by-side panels show keyframe 1 (assembled) and keyframe 2 (exploded) with caption "transition: assembled → exploded, slow, professional internal tech showcase" | System Health scroll section: infrastructure components (API/DB/Scraper/Cache) start as solid block, slowly separate on scroll to reveal internal architecture. 600ms ease-out, 200ms stagger between components |
|| 28 | **"Browser-in-the-card" spatial metaphor** | v4_f300: domain input framed inside mock browser chrome (URL bar + content area) — "you're typing the address of a website that's about to exist" | Opportunity Finder hero: ASIN/keyword input visually framed inside a mock "browser chrome" card (address bar top, product data below) — user is "navigating to" an opportunity, not filling a form |
|| 29 | **Sparse-vs-dense density contrast** | v4_f6000: left zone = vast empty space with 6 command rows; right zone = dense step list + status panel. The density contrast itself creates hierarchy | KPI strip uses "sparse stage" treatment (big numbers, generous spacing); watchlist table uses "dense reference panel" (compact rows, small type). The density contrast between these zones IS the hierarchy — don't equalize |
|| 30 | **Designed loading fallback (uppercase mono)** | v4_f7200: Suspense fallback is `<h1 className="text-white text-3xl uppercase">LOAD…</h1>` — a designed, intentional loading state, not a spinner | Skeleton screens use uppercase mono labels ("LOADING…", "SYNCING…") in JetBrains Mono 12px letter-spaced on a slightly lighter surface than the card — not generic pulse bars |

**New from 2026-09-24 re-run (frame-set correction + the "data-instrument" line):**
The re-analysis found the v3 frame set actually contains **two different craft sources** that the earlier pass blurred together:
- **v3_f2 / f8 / f15 / f22 / f30 / f88** = the *finished cinematic "Iron Man" scroll site* — corner viewfinder brackets, teal+gold emissive glow, volumetric fog, "LIVE telemetry" HUD. This is **landing-hero language only**.
- **v3_f40 / f50 / f60 / f70 / f80** = *dev-workbench / agent-tool screens* (three-column "rail / params / canvas" shells, monospace terminal lines, single warm accent, luminance-layered depth, selection-by-outline) — this is **dashboard language** and the most transferable line for ScoutVeda.

| # | Principle | What the videos do | How ScoutVeda uses it |
|---|---|---|---|
| 31 | **Data-instrument layout (rail·params·canvas)** | v3_f40/50/60/70/80, v4_f2700/3600/4800: asymmetric three-zone shell — thin glyph-only icon tool-rail (~56px) → parameter/controls panel → scrolling result/canvas. The IA is a workbench, never a centered marketing stack | Dashboard shell: 256px grouped sidebar (=rail) → global params strip (marketplace / date-range / density, sticky) → KPI+table content canvas (=result feed). Collapses to icon-rail 64px on 1024–1279 |
| 32 | **Selection-by-outline, not shadow** | v3_f50: active result thumbnails get a luminous 1–2px accent outline (a glowing border), not a drop shadow — the dark-glass selection idiom | Active KPI card, active filter chip, selected table row = 1px accent outline + tiny corner tick, `box-shadow:none`. Shadow reserved for the single floating element only (pairs with #21) |
| 33 | **Separate the two craft registers** | Cinematic-HUD frames (v3_f2–f30,f88) read "showreel"; data-instrument frames (v3_f40–f80, v4) read "pro tool." The costume (corner brackets, scan-lines, "LIVE" over-doing, chromatic aberration) lives ONLY in the hero | Landing hero may borrow the cinematic register *sparingly* (glow-on-value, gradient material, idle levitation). Operational dashboard screens stay in the data-instrument register — restraint, no HUD costume. Never apply viewfinder brackets / telemetry labels to data tables |
| 34 | **Typographic punctuation as the "engineered" voice** | `//`, `—`, `▸`, `·`, `⌄`, `⊕`, tabular numerals and `SEQ 001/109` counters — punctuation does the "technical" work, not color | Micro-labels and section eyebrows use the mono face with wide tracking + these glyphs (e.g. `MARKETPLACE — US ▸`, `SNAPSHOTS · 195K`) to read as instrumentation. Keep body type clean; the "engineered" feel comes from tracked mono captions, never from decorating body copy |

**Confirmed observations, vision pass #3 (2026-09-24 re-run, live vision model) — concrete craft details pulled straight from the frames:**
These sharpen the table above with exact palette/typo/lighting reads. All are craft, zero superhero/entertainment content.

| # | Observation (frame-confirmed) | ScoutVeda buildable use |
|---|---|---|
| 35 | **Warm matte near-black, not pure black** — hero fields read `#050506→#0A0A0C` (slightly warm, matte) so the dark field feels expensive, not harsh. Blue-shifted blacks read clinical/cheap | Lock the dark `--surface-0` to a warm black (`#0D1117` / `#0B0B0D`), never `#000000` (reserve pure OLED black only for the hero dial "void" behind the Opportunity Score) and never blue `#0B0F17` |
| 36 | **Two-family type system does all the work** — one giant tight-tracked grotesk display (120–160px feel) + micro uppercase mono labels (10–11px, wide tracking, ~40% opacity) pinned to corners. Hierarchy is scale/weight/tracking, almost never color | Dashboard: H1/section heads = Inter var 600–700 tight-tracked; every micro-label/eyebrow/KPI-sub = JetBrains Mono 10–11px, uppercase, 0.12em tracking, `text-tertiary`. One accent color carries the "engineered" read, not a second typeface |
| 37 | **Extreme type-scale contrast** is the single biggest "premium/futuristic" tell — the ratio between the one big statement and the many tiny labels is deliberately extreme (≈ 10:1 size ratio) | KPI value 36–44px vs. its 11px uppercase mono label ≈ 3.5:1 minimum; hero headline vs. meta counter ≈ 8:1. Don't compress the ratio for "balance" — the contrast IS the sophistication |
| 38 | **Rim/edge light + radial pedestal glow** carve a dark subject off a dark bg (v2_f5, v3_f2) — the subject never merges into the background because a soft top-edge highlight + a radial lift behind it separate the two | The Opportunity Score dial (and any hero viz) gets a 1px top edge-light (`#ffffff` at 12%) + a radial pedestal glow behind it (`radial-gradient` lift ~8% brighter at center), so the data object "floats" off the dark field |
| 39 | **Volumetric/atmospheric depth** (soft fog, particle depth-of-field, god-ray — v3_f15) is cinematic-hero-only; the dashboard register replaces it with flat tonal layering (v3_f40–f80, v4_f300) | Landing hero MAY use one soft atmospheric glow behind the dial (2% opacity radial). Dashboard: NO fog/particles — depth comes purely from +2–3% luminance steps + 1px hairlines between surface-0/1/2 |
| 40 | **"Content-as-hero" with black void** (v4_f15, v2_f180) — the only saturated color on the page lives *inside* the product screen; all UI chrome stays neutral | Opportunity Score: the animated number + its accent gradient are the single chromatic element; surrounding chrome (nav, labels, ticks) stays `text-primary/tertiary` neutrals so the value reads as the "lit object in a dark room" |
| 41 | **Glassmorphism is the cinematic-register tool, NOT the dashboard tool** (v1 space heroes use translucent blur panels; v4_f300 pro-tool uses flat-2.0 solid surfaces) | Confirm: `backdrop-filter: blur(12px)` only on landing nav + hero panels. Dashboard cards/tables use solid token surfaces + hairlines (flat-2.0). This is the cleanest hero-vs-dashboard register split |
| 42 | **Code-to-design gutter ticks** (v4_f3600: green/amber/red vertical bars aligning source lines to live elements) signal "engineered, not templated" | System Health: a thin left gutter of semantic status ticks (green=healthy, amber=degraded, red=critical) aligned to each infrastructure node row — reads as "live instrumentation," not decoration. Reserve red ticks for actual failures only |

**The core lesson:** premium = motion that serves comprehension + lighting/depth that creates hierarchy + absolute restraint. Two registers: a **cinematic hero** and a **data-instrument dashboard** — the costume lives only in the hero; the dashboard stays restrained. Not 3D everywhere. Not a theme. The "futuristic" feel comes from monospace numerals, thin hairlines, and value emphasis — not scan lines or corner brackets.

**Pass #4 additions (2026-09-24 live-vision re-run — sharpened, non-duplicative):**

| # | Principle | What the frames show | How ScoutVeda uses it |
|---|---|---|---|
| 43 | **Agentic-feed idiom** | v4_f6000: circled step indices, expandable nodes, inline `+n −n` green/red diffs, live "✓ Working" status footer on near-black + one cool accent | Activity feed / Next-Best-Actions / System Health log use this structure — "engineered, not templated." Replaces the emoji statuses flagged in the §3 audit |
| 44 | **Content-as-hero via screen-light** | v4_f15, v2_f5: the ONLY saturated color lives inside the hero object; all surrounding chrome is neutral | Opportunity Score: number + accent gradient is the sole chromatic element on the hero; nav/labels/ticks stay `text-primary/tertiary` neutrals |
| 45 | **Hostinger-wizard dashboard shell** | v4_f300: centered max-width column, one violet accent + semantic green, flat-2.0 surfaces (1px border + soft shadow, no skeuomorph), input framed inside mock browser chrome, floating AI-assistant orb | The cleanest model for ScoutVeda's operational dashboard shell; confirms the §4.1 token surfaces, input framing, and "ask-assistant" pill |

**Motion additions:** M8 (content-as-hero light sweep) and M9 (agent-log streaming feel) — full specs in **§4.5.3**.

**Confirmed (pass #4):** warm matte near-black field (never pure `#000` in the dashboard; pure black reserved for hero voids); tonal depth via 1–3% luminance steps + 1px hairlines, zero box-shadow on dashboard surfaces; selection-by-glowing-outline, not shadow; single warm accent on active state only; monospace data voice (`//`, tabular timecodes, `+n −n`); two registers kept separate — cinematic hero vs data-instrument dashboard. SaaS-not-superhero direction held: no corner brackets, scan-lines, or particle spectacle on operational screens.

**Pass #5 (2026-09-25 live-vision re-run):** vision test confirmed working (test frame returned a full, accurate dark-UI read, not a "cannot see" refusal); all 35 frames re-read live. The pass largely **re-confirmed** principles #21–#45 rather than finding new design space — the craft vocabulary is now fully mapped. Three net-new buildable specifics were added:

| # | Principle | What the frames show | How ScoutVeda uses it |
|---|---|---|---|
| 46 | **Emissive bloom = the single "lit object"** | v3_f88, v4_f8400: the one CTA/value word carries an additive glow (`text-shadow:0 0 24px accent@25%`) so it reads as a light source in a dark room — distinct from the gradient-material text of #24 (headline) | The Opportunity Score value + the ONE primary CTA get the emissive bloom; every other element stays flat-neutral. Never bloom more than one element per screen |
| 47 | **90/10 accent rationing as a hard constraint** | v3_f60/f70/f80, v4_f6000: ~90% of pixels are near-black + gray; the accent appears on ≤10% of the surface, reserved for state/brand/primary only | Enforce in QA: no screen may exceed ~10% accent-coverage; accents carry meaning (active, primary, positive), never decoration. This is the single strongest "premium" tell |
| 48 | **Tonal-elevation hover = state, not shadow** | v3_f60/f70/f80, v4_f6000: the active/hovered row or card lifts +2–3% luminance and gains a 1px accent outline — no drop shadow anywhere on dashboard surfaces | KPI card / table row / chip active state = +3% luminance + 1px accent outline, `box-shadow:none`, 150–200ms. Shadow reserved for the single floating hero element only (pairs with #21, #32) |

**Re-confirmed & unchanged:** warm matte near-black field (#35), two-family type + extreme scale contrast (#36–#37), rim/pedestal glow (#38), hero-only volumetric depth (#39), content-as-hero (#40/#44), glass-as-hero-tool (#41), gutter ticks (#42), agentic-feed idiom (#43). SaaS-not-superhero direction held throughout: the HUD costume (viewfinder brackets, scan-lines, "LIVE" telemetry, rainbow neon gradient, particle fog) lives ONLY in the landing hero and is strictly excluded from operational dashboard screens.

**Pass #6 (2026-09-25 live-vision re-run, this run):** vision re-confirmed working (test frame v3_f40 returned a full, accurate read). All 36 frames re-read live. This pass re-confirmed the two-register split and the #21–#48 vocabulary; the net-new findings are mostly register-boundary + performance-craft specifics below. SaaS-not-superhero held throughout.

| # | Principle | What the frames show | How ScoutVeda uses it |
|---|---|---|---|
| 49 | **Isolated-sheet composition** | v3_f22: a single white detail card floating on a vast dark void — 1px hairline dividers, value-based elevation (light-on-dark, zero box-shadow), "isolated sheet" focus | Product Detail Drawer + export/modals = one sheet floating on `--surface-0` with hairlines + value elevation, no heavy chrome box; the sheet is the only elevated object on the sheet-page |
| 50 | **Light-mode mirror discipline** | v3_f50: monochrome neutral light field `#F5F6F7→#FFFFFF` + ONE high-saturation accent used sparingly (action + state only), icon-only edge rail, skeleton/masonry placeholders, soft low-contrast elevation | ScoutVeda's light theme mirrors the dark rule: accent `#D97706` sparse (active/primary only), semantic colors for state only, skeleton placeholders for async, elevation via soft shadow (light needs it; dark uses tonal) |
| 51 | **Tasteful vs costumed neon gradient** | v4_f8400 live read nails the COSTUMED variant exactly: 5-stop rainbow headline fill `#4aa8ff→#a25bff→#ff4fa0→#ff8a3d→#ffd24a` + outer bloom. Tasteful = single-hue 2-stop | Reinforces #24/#46: ScoutVeda hero accent word = single-hue amber→orange 2-stop (`#D97706→#F59E0B`) + soft bloom, ONE word max. Never the 5-stop rainbow — that is costume |
| 52 | **Performance-aware craft = premium signal** | v4_f7200/f8400: designed `<h1>LOAD...</h1>` Suspense fallback, `useMediaQuery`-scaled 3D models (smaller on mobile), preloaded feature videos, custom-themed scrollbar/status bar | "Engineered" credibility: designed uppercase-mono loading states (#30), responsive model scaling, preloaded async — performance-awareness itself reads premium, not just the visuals |
| 53 | **Grain / fog / debris parallax = hero-only** | v3_f30: volumetric ground fog, backlit silhouette, suspended dust, layered debris at varying blur = parallax layers + film-grain overlay — all cinematic-hero | Dashboard register replaces grain/fog/parallax with flat tonal layering + hairlines (#21, #39). Hero may use one soft atmospheric glow; the dashboard never gets grain, fog, or debris parallax |

**Re-confirmed & unchanged (pass #6):** two-register split, warm-matte near-black, tonal depth / zero-dashboard-shadow, selection-by-outline, single accent (90/10 rationing), mono data voice, glow-on-value only on meaning, rim/pedestal glow, content-as-hero, glass-as-hero-tool, gutter ticks, agentic-feed idiom. The net-new space this pass is register-boundary (#49–#53) + performance-craft (#52), not new visual language.

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

**Duration scale (from video analysis):**
- Micro-interactions (hover, click): 150–200ms
- Component reveal: 300–400ms
- Section scroll reveal: 600–700ms
- Hero/number animations: 900–1200ms
- Page transitions (if any): 400ms

**Easing curve family:**
```css
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);      /* snappy start, soft landing — primary */
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);   /* balanced — transitions */
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1); /* subtle overshoot — buttons only */
```

||| Interaction | Spec | Video Reference |
||---|---|---|
||| Page load | Staggered: nav(0ms) → KPI strip(80ms apart) → charts(240ms) → tables(400ms), each translateY 12px→0 + fade, 700ms ease-out | v3 scroll-triggered grouping; v1 section sequencing |
||| KPI numbers | Count-up over 900ms, mono font (JetBrains Mono), tabular-nums; delta arrow fades in 200ms after count completes | v3 HUD numerals counting up |
||| Card hover | border-color→hairline-strong + shadow-card-hover + translateY(-2px), 300ms ease-out | v1 card lift effect |
||| Button press | scale(0.98) → 1, 150ms using --ease-spring | v1 CTA press feedback |
||| Button hover | Subtle gradient overlay (accent-light to accent), 200ms | v4 blue CTA hover |
||| Drawer (product detail) | Backdrop fade 200ms; panel slide 320ms ease-out; content stagger 60ms/row | v3 modal patterns |
||| Toasts | Slide-up + fade; auto-dismiss 4s; severity-colored left rail (3px) | Standard pattern |
||| Chart interaction | Crosshair hairline + tooltip card (surface-2 bg); series emphasis dims others to 40% opacity, 200ms | v3 data highlighting |
||| Nav item hover | Underline animates from center-out (not left-to-right), 200ms | v1 navbar pattern |
||| Scroll reveal | IntersectionObserver triggers translateY(24px)→0 + opacity 0→1, 700ms ease-out, 80ms stagger per sibling group | v3 scroll-driven sequencing |
||| Reduced motion | @media (prefers-reduced-motion: reduce) → all transforms collapse to opacity-only, counts snap instantly | Accessibility requirement |

**Motion purpose rule:** Every animation must answer "why does the user need to see this move?" Delete any animation that doesn't serve comprehension, state indication, or attention guidance.

**Restraint rule:** Max 2 animated elements per viewport at once. Nothing moves faster than 150ms (micro) or slower than 700ms (macro). This discipline is what creates the premium feel — not the specific animation chosen.

**Rationale:** every timing above comes from the video references' feel (slow, eased, decisive) — motion serves hierarchy and comprehension. The restraint is the premium part.

### 4.5.1 Motion system — new concrete observations (2026-09-24 vision-confirmed pass)

**Frame-confirmed motion cues (static-frame tells, mapped to buildable behavior):**

| Observation | Source frame(s) | Buildable implementation |
|---|---|---|
| **"LIVE" status dot pulses** — a small colored dot next to a mono label blinks on a ~2s cycle (on: 1.2s, off: 0.8s, opacity 1→0.4) | v3_f2 "TELEMETRY LINK — LIVE" | System Health "live" indicator: `animation: pulse-dot 2s infinite; @keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:.4} }` |
| **Sequence counter ticks** — "SEG 001 / 009" style counters advance as user scrolls through a sectioned page; each section = one "segment" | v3_f2, v3_f8, v3_f15 | Dashboard section indicator: fixed right-edge vertical "01 / 06" mono counter updates on scroll-snap between dashboard sections |
| **Playhead scrubber** — thin white/green progress line with a small circular handle; fill grows left→right on autoplay; handle is draggable | v3_f40, v3_f60 | "Data freshness" progress bar: fills over 4h cycle; handle position = current sync time; click to jump to next sync |
| **Slide-in notification banner** — a dismissible strip slides down from the top of the content area (translateY -100%→0, 300ms ease-out), auto-dismisses after 6s | v3_f40 "Allow notifications" banner | Global toast system: slide-down from top, not bottom-right; severity-colored left 3px rail |
| **Custom cursor** — the OS pointer is replaced with a small geometric pointer that scales 1.2× on hover over interactive elements | v3_f2, v3_f8 | **Do not build.** Custom cursors are costume for a SaaS dashboard. The *principle* (hover state scaling) applies to: all KPI cards, chart points, and table row sparklines → `scale(1.03)` on hover, 150ms |
| **Sequence/scrub interaction** — "SEQ 142 / 169" + "FINAL FRAME" + "⊕ PLAYBACK" together imply a frame-player: elements advance, scrub, or play in sequence | v3_f8, v3_f15 | Opportunity Score dial: "playback" metaphor — the dial "plays" its count-up over 900ms, then the verdict badge slides in. The dial IS the player |
| **Slide-up fill on hover button** | v3_f40 "ENGAGE →" pill | Primary CTA hover: background fill slides up from bottom (`::before` translateY(100%)→0, 200ms ease-out), text stays static |
| **Slow ambient particle drift** — scattered small dots/motes drift at ~0.1px/frame, non-interactive, purely atmospheric | v3_f15, v1_f5 | **Do not build on dashboard.** Only acceptable on landing hero as background canvas (max 12 particles, 2px, opacity 0.15, 60s loop). Reads as "ambient life" not "data noise" |
| **Floating object idle levitation** — 3D products/objects hover with a 3–5px vertical bob over 4s (sine wave, not bounce) | v1_f5, v1_f8, v2_f180 | Opportunity Score dial on landing: `animation: levitate 4s ease-in-out infinite; @keyframes levitate { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-4px)} }` |
| **Scroll-driven section paging** — "SCROLL ↓" cue + "SEG 001 / 009" implies snap-scroll between 9 discrete sections, each with its own hero moment | v3_f2, v3_f8, v3_f15 | Landing page: `scroll-snap-type: y mandatory` on 3 hero sections; each section snaps and its content reveals in 700ms. Do NOT snap-scroll the dashboard — it must free-scroll |
| **Glow-on-value** | v3_f40, v3_f60 | KPI number: `text-shadow: 0 0 8px rgba(accent, 0.25)` — subtle, not neon. Status dot: `box-shadow: 0 0 4px rgba(status-color, 0.5)` |
| **Gradient sweep on accent text** | v4_f1800, v4_f8400 | Hero accent word: `background: linear-gradient(90deg, #D97706, #F59E0B, #D97706); background-size: 200% auto; animation: shimmer 8s linear infinite; @keyframes shimmer { to { background-position: 200% center } }` — 8s cycle, subtle, not a party |
| **Exploded view on scroll** | v2_f360 | System Health scroll: 4 infrastructure nodes start as one solid block; on scroll, each node translates 12px outward on its axis with 200ms stagger + fade-in of connector hairlines. Total sequence ~800ms |
| **Choreographed 3-step "thinking" loop** | v4_f8400 | Data freshness indicator: 3-frame loop — (1) "SYNCING…" + spinner (1.2s) → (2) "SYNCED ✓" (hold 800ms) → (3) "NEXT IN 4m" + countdown (4h cycle, ticks every second). Frame transitions: 200ms crossfade |

**Motion purpose rule (unchanged, reinforced):** Every animation must answer "why does the user need to see this move?" The new frames confirm this: every motion cue in the reference videos maps to a *state change* (live↔idle, assembled↔exploded, loading↔loaded) — none are decorative. ScoutVeda's motion system should follow the same rule: motion = state communication.

**Restraint rule (unchanged, reinforced):** Max 2 animated elements per viewport. The reference videos achieve premium feel through *fewer* things moving *slower*, not more things moving faster. On a data-dense dashboard, the "max 2" rule is even stricter: if a KPI number is counting up, nothing else on that card should move simultaneously.

### 4.5.2 Motion system — concrete observations, vision pass #3 (2026-09-24 live-vision re-run)

New frame-confirmed motion/timing reads that sharpen §4.5. All from the re-analysis; craft only.

| # | Motion observation (frame-confirmed) | Concrete buildable spec |
|---|---|---|
| M1 | **Turntable idle loop** (v2_f5/v180, v1_f5): the hero 3D object keeps a slow continuous rotation/breath so the page never looks static — but it *settles* on load first | Opportunity Score dial: on load, ease-in a 20° settle (600ms, `--ease-out`) THEN a slow idle rotation of the tick ring (full 360° over ~24s, linear). Idle, not bouncing. Stops on `prefers-reduced-motion` |
| M2 | **"Assembled → exploded" is a scroll-scrolled narrative, not a hover** (v2_f360, f540): one deliberate beat where components lift/separate, then hold — "professional internal tech showcase" pacing, 600ms ease-out, 200ms stagger | System Health scroll section: 4 infra nodes start stacked; scroll drives them apart (each node translates 12px on its axis, 200ms stagger, 600ms ease-out) revealing connector hairlines. One beat, not a loop |
| M3 | **The "thinking" loop is 3 discrete frames, not a spinner** (v4_f8400): typed-URL+caret → checkmark → spinner → resolved. Signals intelligence is *processing* | Data-freshness indicator: `SYNCING` (mono + 1.2s spinner) → `SYNCED ✓` (hold 800ms) → `NEXT IN 4m` (countdown, ticks 1s). 200ms crossfade between frames. Never a bare spinner alone |
| M4 | **Reveal = translateY + fade in staggered sibling groups**, 80–160ms between groups; the *grouping* is the premium move (v3_f2/f8/f15 scroll sequencing) | Section reveals: `translateY(24px)→0 + opacity 0→1`, 700ms `--ease-out`, 80ms stagger per sibling group. KPI strip cards reveal in one 80ms-staggered group before charts (240ms) before tables (400ms) — matches §4.5 page-load row |
| M5 | **Glow-on-value pulses only on state, not ambient** (v3_f88, v3_f40): emissive bloom is reserved for a value that *means* something (a live number, a success) — ambient pulsing everywhere reads as costume | Status dots: static 3px dot + subtle 4px outer glow (state color at 50%). Pulse animation (`pulse-dot` 2s) only on the **live/System-Health** "connected" dot — the one dot that should feel "alive." Table-row status dots stay static |
| M6 | **Hover = small scale + lift, springy but subtle** (v4_f300, v1 CTA): press feedback is `scale(0.98)`; interactive elements breathe ~3% not 10% | Buttons/cards: hover `translateY(-2px)` + shadow-card-hover, 300ms `--ease-out`; press `scale(0.98)` 150ms `--ease-spring`. KPI card / chart-point hover `scale(1.03)`, 150ms. Nothing scales past 1.05 |
| M7 | **Choreographed micro-loop ≠ decorative**: every looping thing maps to a *state change* (live↔idle, assembled↔exploded, loading↔loaded) — none are pure ornament (confirmed across v3/v4) | Hard rule for ScoutVeda: any element that loops must have a semantic state (freshness, live-connection, sync). Delete any loop that doesn't. This is why the dashboard gets at most 1 ambient loop (M5 live dot) |

**Reinforced timing:** slow-out, long-decel easing (`cubic-bezier(0.16,1,0.3,1)`) for reveals/scroll; nothing bouncy except button-press. 60fps, eased, decisive. The restraint — fewer things, slower, purposeful — is what reads premium, not any single animation.

### 4.5.3 Motion system — pass #4 additions (2026-09-24 live-vision re-run)

| # | Motion observation (frame-confirmed) | Concrete buildable spec |
|---|---|---|
| M8 | **Content-as-hero light sweep** (v4_f15, v4_f8400): the hero value is the page's one "lit object" — a single constrained gradient + soft bloom; surrounding chrome stays flat-neutral | `text-shadow: 0 0 24px rgba(accent,.25)` + an 8s subtle gradient shimmer on the hero value ONLY. Never more than one glowing element per screen (pairs with #37, #40) |
| M9 | **Agent-log streaming feel** (v4_f6000): step rows fade/slide in as they complete; the running step pulses; a status footer ticks — signals a live process with no auto-scroll | Activity feed / System Health log: each new row `translateY(8px)→0 + opacity 0→1`, 300ms `--ease-out`; the in-progress step's dot pulses on a 2s cycle; footer status updates on state change (no continuous auto-scroll) |

### 4.5.4 Motion system — pass #5 additions (2026-09-25 live-vision re-run)

New motion reads confirmed live this pass; they sharpen §4.5 rather than add new design space. Pairs with principles #46–#48 in §1.

| # | Motion observation (frame-confirmed) | Concrete buildable spec |
|---|---|---|
| M10 | **Emissive CTA/value bloom** (v3_f88, v4_f8400): the single hero value or primary CTA word carries an additive glow so it reads as "a light source in a dark room" — the only saturated, self-lit element on screen | Opportunity Score value + the one primary CTA: `text-shadow:0 0 24px rgba(--accent,.25)` + a slow 8s amber→orange gradient shimmer on that element ONLY. Never bloom more than one element per screen (enforces #47) |
| M11 | **Tonal-elevation hover, no shadow** (v3_f60/f70/f80, v4_f6000): active/hovered row or card lifts +2–3% luminance and gains a 1px accent outline — no drop shadow on any dashboard surface | KPI card / table row / filter chip active state: `filter/brightness +3%` (or `--surface-1`→`--surface-2` step) + 1px accent outline, `box-shadow:none`, 150–200ms `--ease-out`. Reserve the single soft shadow for the floating hero dial only (pairs with #21, #32, #48) |
| M12 | **Browser-chrome "navigating-to" input** (v4_f300): the ASIN/keyword field is framed inside a mock address-bar card, so the user is "navigating to" an opportunity, not "filling a form" | Opportunity Finder hero input: mock browser chrome card (address-bar strip on top, result data below), address bar pre-populated with the typed ASIN/keyword, 200ms slide-up reveal. Reinforces the "you are going somewhere" spatial metaphor |
| M13 | **Data-instrument live drawer** (v4_f6000): a dense right drawer with circled step indices, an expanding node, inline `+n −n` diffs, a green "Working" status footer, and a `× Stop` interrupt affordance — "the system is working" feel with zero auto-scroll | System Health / Activity feed drawer: step rows fade/slide in on completion (300ms `--ease-out`); the in-progress step's dot pulses 2s; the footer status ticks on state change; a `× Stop` pill interrupts the running sync. No continuous auto-scroll; motion = state change only |

**Reinforced (no new motion invented):** turntable idle (M1), assembled→exploded scroll beat (M2), 3-frame "thinking" loop (M3), staggered-group reveals (M4), state-only glow-pulse (M5), subtle hover scale (M6), semantic-loop rule (M7), content-as-hero light sweep (M8), agent-log streaming (M9). The pass #5 frames confirmed the existing timing/easing family and the restraint rules (fewer things, slower, purposeful). No decorative motion added; the SaaS-not-superhero direction held — the HUD costume (corner-bracket scans, particle fog, rainbow neon sweep, "LIVE" telemetry) remains hero-only and is excluded from all operational dashboard motion.

### 4.5.5 Motion system — pass #6 additions (2026-09-25 live-vision re-run)

New live-vision reads sharpening the motion grammar; all register-aware. Pairs with principles #49–#53 in §1.

| # | Motion observation (frame-confirmed) | Concrete buildable spec |
|---|---|---|
| M14 | **Rainbow sweep = costume; single-hue sweep = craft** (v4_f8400 live read): the costumed variant is a 5-stop neon gradient (`#4aa8ff→#a25bff→#ff4fa0→#ff8a3d→#ffd24a`) with bloom — the tasteful variant is a single-hue 2-stop shimmer, one word only | Hero accent word shimmer (M10): strictly `#D97706→#F59E0B` 2-stop, 8s subtle cycle, `background-clip:text` on ONE word. QA gate: reject any 3+-stop multi-hue gradient fill — it reads as costume. (Enforces #51, #24) |
| M15 | **Grain / fog / debris parallax belongs to the hero register only** (v3_f30 live read: volumetric ground fog, backlit silhouette, suspended dust, layered debris at varying blur + film-grain overlay) | Dashboard motion uses NO grain, NO fog particles, NO debris parallax, NO scan-lines. Depth motion on operational screens = tonal-elevation lift (M11) + staggered-group reveals (M4) + exploded→assembled scroll beat (M2) only. (Enforces #53, #39) |
| M16 | **Skeleton = performance craft** (v3_f50 live read: right-hand masonry tiles are empty rounded placeholders reading as "skeleton / loading," not "empty") | Async data zones (KPI strip, watchlist table, chart cards) use designed skeleton placeholders (surface-2 fill + subtle 4% shimmer), never a bare spinner or blank flash. Loading state IS part of the motion system, not an afterthought. (Enforces #52, #30) |

---

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

## 5. Video analysis completed — key additions to the spec

The hourly cron job analyzed 38+ frames across all 4 reference videos (2026-09-20 pass) and a **vision-confirmed pass on 2026-09-24** re-analyzed the full frame set with an active vision model and merged new concrete observations. Below is what was added beyond the original spec:

### New design principles added to §1 (principles 9–15, original pass):
- **#9 Rim light on cards**: 1px top/left border at 5% higher luminance than card surface — creates edge definition without chrome borders
- **#10 Strategic color highlighting**: One word/number in accent color draws the eye (v1_f17: "power" in green). For ScoutVeda: use accent only for delta arrows (positive), in-policy KPIs, and primary CTAs — never decoration
- **#11 Product-as-artifact composition**: v4_f15 shows MacBook screen RAISED above black field with thin framing border. Hero sections should feel like displayed objects, not flat layouts — elevate with shadow + gradient field
- **#12 Grid patterns as texture**: v4_f1800 uses subtle grid in code editor corner for technical texture. Apply faint 1px grid on System Health 3D canvas only — never on data tables
- **#13 Center-out underline animation**: v1 navbar underlines from center (not left-to-right). Apply to sidebar nav items for "anchoring" feel vs "sweeping"
- **#14 Floating product illusion**: v2_f180 headphones appear to float on dark field with soft even lighting. Opportunity Score dial gets same treatment — subtle shadow beneath, no visible support
- **#15 Screen-within-screen composition**: v3_f80 shows balanced asymmetry (25%/50%) with drop shadows. Dashboard layout: KPI strip (top) → main content (center) → sidebar panel (right), each with elevation

### Color grading correction:
- Current `--surface-0: #0B0F17` is too blue-shifted. Reference videos lean warm: test `#0D1117` or `#0F1419` (amber undertone) for premium dark field
- Accent strategy: one dominant accent hue per screen, semantic colors reserved for meaning only

### Motion choreography refinements (from v3 scroll-driven sequencing):
- Stagger groups at 80ms intervals (group A → B → C)
- Numbers count up over 900ms with fast-start/slow-decel easing
- Background parallax is 2–4px shift (subtle, not dramatic)
- v2 Apple-style: hero product responds to scroll position (not auto-spin); text fades from below as product scrolls out

### HUD anatomy — what reads "futuristic data" tastefully:
- Monospace numerals (JetBrains Mono, tabular-nums) ✓
- Thin hairline separators (1px, rgba(241,245,249,.08)) ✓
- Value glow: key number slightly brighter than label ✓
- Status dots: 3px colored circle + mono label ✓
- Sparklines: 24px high, 1px stroke, no grid ✓
- **AVOID**: cyan glow on everything, scan-lines, pulsing borders, corner brackets, projected-text drop-shadow

### Full frame notes:
See `VIDEO-CRAFT-NOTES.md` for detailed per-frame observations (38+ frames analyzed).

### Vision-confirmed pass (2026-09-24) — what was new:
Re-ran the full frame set (v3×11, v1×7, v2×7, v4×10) with an **active vision model** — the earlier pass had degraded notes because vision was down. This pass produced sharper, buildable observations:
- **10 new design principles (#21–#30 in §1)**: tonal layering (no shadows), emissive self-lit points, tactile segmented controls, gradient-as-material hero text, choreographed micro-loops, tasteful holographic edge-glow, assembled→exploded keyframe pairs, "browser-in-the-card" metaphor, sparse-vs-dense density contrast, designed uppercase-mono loading fallbacks.
- **New §4.5.1 motion table**: 13 frame-confirmed motion cues each mapped to concrete CSS/implementation, with explicit "do not build" calls on custom cursors and dashboard particle effects (costume, not craft).
- **Confirmed**: warm-black field (#0D1117) over blue-shifted #0B0F17; emissive accents read as "light sources"; motion = state communication.

---

## 6. Hourly job decommission note

This hourly vision-analysis cron job has now served its purpose across two passes:
- **2026-09-20 pass** — analyzed 38+ frames; several hex/palette details were inferred (vision model was down at the time).
- **2026-09-24 pass** — re-analyzed the full frame set (v3×11, v1×7, v2×7, v4×10) with an **active vision model**; test confirmed vision working. Merged 10 new principles (#21–#30) into §1, a new §4.5.1 motion table (13 frame-confirmed cues), and a "Vision-Confirmed Pass" section in `VIDEO-CRAFT-NOTES.md`.
- **2026-09-24 pass #3 (this run)** — vision re-tested and confirmed working again. Re-analyzed the full frame set with the live model; appended raw per-frame observations to `VIDEO-CRAFT-NOTES.md` and merged 8 more §1 principles (#35–#42: warm-black field, two-family type, extreme type-scale contrast, rim/pedestal glow, hero-only volumetric depth, content-as-hero, glassmorphism-as-hero-tool, code-to-design gutter ticks) plus a new §4.5.2 motion table (M1–M7: turntable idle, assembled→exploded scroll beat, 3-frame "thinking" loop, staggered-group reveals, state-only glow-pulse, subtle hover scale, semantic-loop rule). SaaS-not-superhero direction preserved throughout.

- **2026-09-24 pass #4 (this run)** — vision confirmed working; re-analyzed the full frame set one more time. Merged 3 new §1 principles (#43 agentic-feed idiom, #44 content-as-hero via screen-light, #45 Hostinger-wizard dashboard shell) plus a §4.5.3 motion table (M8 content-as-hero light sweep, M9 agent-log streaming feel). Appended raw per-frame observations to `VIDEO-CRAFT-NOTES.md`. No new principles beyond these — the design space is now fully mapped. SaaS-not-superhero direction held throughout.

- **2026-09-25 pass #5** — vision test confirmed working (test frame v3_f40 returned a full, accurate dark-UI read, not a "cannot see" refusal). Re-read all 35 frames live (v3×11, v1×7, v2×7, v4×10) with the active model. This pass **re-confirmed** principles #21–#45 (the craft vocabulary is now fully mapped — no new design space found) and added 3 net-new buildable specifics: #46 emissive bloom = single lit object, #47 the 90/10 accent-ratio as a hard QA constraint, #48 tonal-elevation hover (state, not shadow). Also added a new §4.5.4 motion table (M10 emissive CTA bloom, M11 tonal-elevation hover, M12 browser-chrome "navigating-to" input, M13 data-instrument live drawer). Raw live-vision ground-truth reads appended to `VIDEO-CRAFT-NOTES.md` under "PASS #5." SaaS-not-superhero direction held throughout.

- **2026-09-25 pass #6 (this run)** — vision re-confirmed working (test frame v3_f40 returned a full, accurate read, not a refusal). Re-read all 36 frames live. This pass **re-confirmed** the two-register split and the #21–#48 vocabulary; net-new additions are 5 register-boundary + performance-craft principles (#49 isolated-sheet composition, #50 light-mode mirror discipline, #51 tasteful-vs-costumed neon gradient, #52 performance-aware craft = premium signal, #53 grain/fog/debris parallax = hero-only) plus a new §4.5.5 motion table (M14 single-hue-not-rainbow sweep, M15 no grain/fog/debris on dashboard, M16 designed skeleton = performance craft). Raw live-vision ground-truth reads appended to `VIDEO-CRAFT-NOTES.md` under "PASS #6." SaaS-not-superhero direction held throughout.

**Cleanup status:** No `.webm` files remain in `C:\Users\rames\ytwatch\` — v1–v4.webm (~234MB) were deleted in the 2026-09-20 pass, re-verified absent on 2026-09-24, again confirmed absent on 2026-09-25 (pass #5), and **re-verified absent again on this pass #6 run** (0 `.webm` present; 68+ JPG frames retained as the reference archive). No cleanup action was needed this run.

**The hourly job can be removed now.** The design space is fully mapped across six vision-confirmed passes; pass #6 found no new visual language — only register-boundary and performance-craft specifics (#49–#53, M14–M16) that harden the existing rules. Both source files (`DESIGN-SPEC-3D-UI.md` §1 + §4.5, and `VIDEO-CRAFT-NOTES.md` PASS #6) are fully written and merged; there is nothing left to analyze.
