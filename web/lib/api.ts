import "server-only";
import { cookies } from "next/headers";
import { verifySessionToken, SESSION_COOKIE } from "./session";

// Fetched from Server Components / Server Actions only — API_KEY never
// reaches the browser bundle this way (unlike a NEXT_PUBLIC_ var would).
const API_URL = process.env.API_URL!;
const API_KEY = process.env.API_KEY!;

type NextFetchOptions = { revalidate?: number | false; tags?: string[] };

// The signed-in account id, read from the session cookie. Forwarded to the
// backend as X-Scout-User so every data query is scoped to one tenant.
async function currentUserId(): Promise<number | null> {
  try {
    const store = await cookies();
    return (await verifySessionToken(store.get(SESSION_COOKIE)?.value))?.uid ?? null;
  } catch {
    return null;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  next?: NextFetchOptions
): Promise<T> {
  const uid = await currentUserId();
  const headers: Record<string, string> = {
    "X-Scout-Key": API_KEY,
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (uid !== null) headers["X-Scout-User"] = String(uid);

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    // With a signed-in user the response is tenant-specific, so never let it
    // sit in Next's shared data cache — force a fresh fetch. Anonymous/global
    // reads keep the time-based revalidation window.
    cache: options.cache ?? (uid !== null ? "no-store" : next ? undefined : "no-store"),
    next: uid !== null ? undefined : next ?? undefined,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${path} failed: ${res.status} ${text}`);
  }
  return res.json();
}

export type SnapshotRow = {
  rank: number | null;
  asin: string;
  title: string | null;
  price: number | null;
  rating: number | null;
  review_count: number | null;
  image_url: string | null;
  category: string | null;
  list_type: string | null;
  collected_at: string | null;
};

export type MoverRow = {
  asin: string;
  title: string;
  category: string;
  first_rank: number;
  latest_rank: number;
  delta: number;
};

export type CrossCategoryRow = {
  asin: string;
  title: string;
  categories: string;
  num_categories: number;
  best_rank: number;
};

export type Digest = {
  new_entrants: SnapshotRow[];
  top_movers: MoverRow[];
  cross_category: CrossCategoryRow[];
  collection_dates: string[];
};

export type ScoreResult = {
  asin: string;
  title: string | null;
  category: string | null;
  sell_price: number | null;
  buy_price: number;
  components: Record<string, number>;
  weights: Record<string, number>;
  score: number;
  verdict: "PURSUE" | "WATCH" | "SKIP";
  margin_detail: {
    net_margin_pct: number;
    net_margin_rupees: number;
    verdict: string;
    breakeven_price: number | null;
    breakeven_acos_pct: number;
    [k: string]: unknown;
  };
  caveats: string[];
};

export type MyProduct = {
  asin: string;
  title: string | null;
  sku: string | null;
  supplier_cost: number;
  shipping_fee: number;
  target_margin: number;
  supplier_details: string;
  current_stock: number;
  lead_time_days: number;
  created_at: string;
};

export type Alert = {
  asin: string;
  title: string | null;
  category: string | null;
  list_type: string;
  alert_type:
    | "price_change"
    | "entered_top3"
    | "rank_climbing"
    | "rank_sliding"
    | "review_surge"
    | "dropped_from_list";
  severity: "high" | "medium" | "low";
  message: string;
  detail: Record<string, unknown>;
  detected_at: string;
};

export type Validation = {
  id: number;
  asin: string;
  title: string | null;
  category: string | null;
  score: number;
  verdict: string;
  buy_price: number;
  notes: string | null;
  validated_at: string;
  price?: number | null;
  review_count?: number | null;
};

export type ListingPeer = {
  asin: string;
  title: string | null;
  rank: number | null;
  price: number | null;
  rating: number | null;
  review_count: number | null;
};

export type ListingReview = {
  text: string;
  rating: number | null;
};

export type ListingAnalysis = {
  asin: string;
  title: string | null;
  category: string | null;
  score: number;
  components: { title: number; bullets: number; images: number };
  bullets: string[];
  image_count: number;
  rating: number | null;
  price: number | null;
  review_count: number | null;
  benchmark: {
    price_percentile?: number;
    category_median_price?: number;
    review_percentile?: number;
    category_median_reviews?: number;
  } | null;
  peers: ListingPeer[];
  reviews: ListingReview[];
  gaps: string[];
};

export type ListingSuggestion = {
  title: string | null;
  bullets: string[];
};

export type ReviewSummary = {
  pros: string[];
  cons: string[];
};

export type ProfitResult = {
  referral_fee: number;
  closing_fee: number;
  weight_or_pickpack_fee: number;
  amazon_fees_subtotal: number;
  gross_margin_pre_fee: number;
  returns_provision: number;
  net_margin_rupees: number;
  net_margin_pct: number;
  breakeven_price: number | null;
  breakeven_acos_pct: number;
  verdict: string;
};

export const api = {
  // Nightly collector runs once/day, so a short revalidation window is safe:
  // fresh data still shows up within a minute, but repeated dashboard loads
  // in between don't each trigger a full Render cold-start + full-table scan.
  digest: () =>
    request<Digest>("/trend-radar/digest", {}, { revalidate: 60 }),
  categoryTable: (category: string, listType: string = "bestsellers") =>
    request<{ category: string; list_type: string; products: SnapshotRow[] }>(
      `/trend-radar/category/${encodeURIComponent(category)}?list_type=${encodeURIComponent(listType)}`,
      {},
      { revalidate: 60 }
    ),
  score: (body: {
    asin: string;
    buy_price: number;
    category?: string;
    weight_grams?: number;
    fulfillment?: string;
    gst_rate_pct?: number;
    zone?: string;
    differentiation?: number;
    operational_fit?: number;
    notes?: string;
  }) =>
    request<ScoreResult>("/validator/score", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  // Tagged (not just time-revalidated) because a new validation must show
  // up immediately after scoreAsin() — see updateTag("watchlist") in
  // lib/actions.ts, called right after a successful score.
  watchlist: () =>
    request<{ validations: Validation[] }>(
      "/watchlist",
      {},
      { revalidate: 60, tags: ["watchlist"] }
    ),
  updateWatchlistNotes: (body: { asin: string; notes: string }) =>
    request<{ ok: boolean }>("/watchlist/notes", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  // Alerts are derived from watched (validated) ASINs, so they ride the
  // same "watchlist" tag -- a new Validator run can change which ASINs
  // get checked, and should be reflected immediately, same as the list itself.
  alerts: () =>
    request<{ alerts: Alert[] }>(
      "/alerts",
      {},
      { revalidate: 60, tags: ["watchlist"] }
    ),
  // Live on-demand scrape + rule-based scoring, not cached -- every click
  // should hit the real, current page (and Amazon's bot-check means results
  // can genuinely differ run to run, so caching a failure would be worse
  // than just re-fetching).
  analyzeListing: (body: { asin: string; category?: string; marketplace_id?: string }) =>
    request<ListingAnalysis>("/listing/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  // Deliberately separate call from analyzeListing -- this is the one AI
  // step in Scout (a free-tier model router), can be slow or occasionally
  // unavailable, and shouldn't hold up or risk the rule-based score above.
  suggestListingImprovements: (body: {
    title: string | null;
    bullets: string[];
    category?: string | null;
    gaps: string[];
  }) =>
    request<ListingSuggestion>("/listing/suggest", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  // Also deliberately separate from analyzeListing -- same reasoning as
  // suggestListingImprovements above.
  summarizeReviews: (body: { reviews: ListingReview[] }) =>
    request<ReviewSummary>("/listing/review-summary", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  profitCalculator: (body: {
    sell_price: number;
    buy_price: number;
    category: string;
    weight_grams: number;
    fulfillment: string;
    gst_rate_pct: number;
    zone?: string;
    is_oversize?: boolean;
    returns_pct?: number;
    ppc_per_unit?: number;
    own_shipping_cost?: number;
  }) =>
    request<ProfitResult>("/profit-calculator", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  productDatabase: (params: {
    q?: string;
    category?: string;
    min_price?: number;
    max_price?: number;
    min_rank?: number;
    max_rank?: number;
    limit?: number;
    offset?: number;
  }) => {
    const qps = new URLSearchParams();
    if (params.q) qps.set("q", params.q);
    if (params.category) qps.set("category", params.category);
    if (params.min_price !== undefined) qps.set("min_price", params.min_price.toString());
    if (params.max_price !== undefined) qps.set("max_price", params.max_price.toString());
    if (params.min_rank !== undefined) qps.set("min_rank", params.min_rank.toString());
    if (params.max_rank !== undefined) qps.set("max_rank", params.max_rank.toString());
    if (params.limit !== undefined) qps.set("limit", params.limit.toString());
    if (params.offset !== undefined) qps.set("offset", params.offset.toString());
    return request<{ products: SnapshotRow[]; total: number }>(`/product-database?${qps.toString()}`);
  },
  myProducts: () => request<{ products: MyProduct[] }>("/my-products"),
  saveMyProduct: (body: {
    asin: string;
    title?: string | null;
    sku?: string | null;
    supplier_cost: number;
    shipping_fee: number;
    target_margin: number;
    supplier_details: string;
    current_stock?: number;
    lead_time_days?: number;
  }) =>
    request<{ ok: boolean }>("/my-products", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteMyProduct: (asin: string) =>
    request<{ ok: boolean }>(`/my-products/${asin}`, {
      method: "DELETE",
    }),
  compareCompetitors: (body: { asins: string[] }) =>
    request<{
      comparisons: {
        asin: string;
        title: string | null;
        price: number | null;
        rank: number | null;
        rating: number | null;
        review_count: number | null;
        score: number;
        verdict: "PURSUE" | "WATCH" | "SKIP";
        found: boolean;
      }[];
    }>("/competitor-analysis", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  listingHealth: () =>
    request<{
      products: {
        asin: string;
        title: string;
        score: number;
        verdict: string;
        gaps: string[];
        price: number | null;
      }[];
    }>("/listing-health"),
  drawerDetails: (asin: string) =>
    request<{
      asin: string;
      title: string;
      category: string;
      price: number;
      buy_price: number;
      sell_price: number;
      shipping_cost: number;
      fees: number;
      net_margin: number;
      rating: number;
      reviews: number;
      score: number;
      verdict: "PURSUE" | "WATCH" | "SKIP";
      notes: string;
      trend_data: { day: string; BSR: number; Price: number }[];
      audit_checklist: { check: string; pass: boolean }[];
    }>(`/products/${asin}/drawer-details`),
  amazonCallback: (body: { code: string; selling_partner_id: string; marketplace_id?: string }) =>
    request<{ ok: boolean; selling_partner_id: string }>("/auth/amazon/callback", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  amazonStatus: () =>
    request<{
      connected: boolean;
      accounts: {
        selling_partner_id: string;
        marketplace_id: string;
        connected_at: string;
      }[];
    }>("/auth/amazon/status"),
  deleteAmazonAccount: (sellingPartnerId: string) =>
    request<{ ok: boolean }>(`/auth/amazon/${sellingPartnerId}`, {
      method: "DELETE",
    }),
  syncStorefront: () =>
    request<{ ok: boolean; message: string; warning?: string }>("/storefront/sync", {
      method: "POST",
    }),
  storefrontSales: () =>
    request<{ metrics: StorefrontSalesMetric[] }>(
      "/storefront/sales",
      {},
      { revalidate: 60, tags: ["storefront-status"] }
    ),
  storefrontOrders: () =>
    request<{ orders: StorefrontOrder[] }>(
      "/storefront/orders",
      {},
      { revalidate: 60, tags: ["storefront-status"] }
    ),
  saasAuditLogs: () =>
    request<{ logs: any[] }>("/saas/audit-logs", {}, { revalidate: 0 }),
  saasOrgMembers: () =>
    request<{ members: any[] }>("/saas/org-members", {}, { revalidate: 0 }),
  addSaasOrgMember: (body: { email: string; role: string; name?: string }) =>
    request<{ ok: boolean }>("/saas/org-members", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  ppcAnalytics: () =>
    request<any>("/analytics/ppc", {}, { revalidate: 60 }),
  // System Health page: the ops heartbeat board + pipeline freshness. Both are
  // read-only summaries; a short revalidation window keeps a dashboard session
  // from hammering the cold-start-prone Render API on every click.
  opsStatus: () =>
    request<OpsStatus>("/ops/status", {}, { revalidate: 60 }),
  pipelines: () =>
    request<Pipelines>("/pipelines", {}, { revalidate: 60 }),
};

// --- System Health types ---------------------------------------------------

export type OpsHeartbeat = {
  component: string;
  status: string;
  last_seen: string | null;
  last_seen_ist: string;
  age_minutes: number;
  detail: Record<string, unknown> | null;
};

export type OpsEvent = {
  component: string;
  severity: "warn" | "error" | "resolved" | "info";
  event: string;
  message: string;
  created_at: string | null;
  created_at_ist: string;
  notified_at: string | null;
};

export type OpsStatus = {
  heartbeats: OpsHeartbeat[];
  recent_events: OpsEvent[];
  generated_at_ist: string;
};

export type Pipeline = {
  last_seen: string | null;
  age_hours: number;
  rows: number;
  last_pass_asins?: number;
  targets?: number;
};

export type Pipelines = Record<string, Pipeline>;

export type StorefrontSalesMetric = {
  id: number;
  selling_partner_id: string;
  marketplace_id: string;
  interval_start: string;
  order_count: number;
  unit_count: number;
  total_sales_amount: number;
  currency: string;
  updated_at: string;
};

export type StorefrontOrder = {
  id: number;
  amazon_order_id: string;
  purchase_date: string;
  order_status: string;
  amount: number | null;
  currency: string | null;
  items_count: number;
  updated_at: string;
};

