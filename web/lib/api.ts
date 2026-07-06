import "server-only";

// Fetched from Server Components / Server Actions only — API_KEY never
// reaches the browser bundle this way (unlike a NEXT_PUBLIC_ var would).
const API_URL = process.env.API_URL!;
const API_KEY = process.env.API_KEY!;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "X-Scout-Key": API_KEY,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    cache: "no-store",
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
  digest: () => request<Digest>("/trend-radar/digest"),
  categoryTable: (category: string) =>
    request<{ category: string; products: SnapshotRow[] }>(
      `/trend-radar/category/${encodeURIComponent(category)}`
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
  watchlist: () => request<{ validations: Validation[] }>("/watchlist"),
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
};
