"use server";

import { cookies } from "next/headers";
import { updateTag } from "next/cache";
import { api, type ListingReview } from "./api";
import { verifySessionToken, SESSION_COOKIE } from "./session";

/**
 * Validates the current per-user session and returns the account id.
 * Throws if the session cookie is missing or invalid. The account id is used
 * to scope data (api.ts forwards it to the backend as X-Scout-User).
 */
async function requireSession(): Promise<number> {
  const cookieStore = await cookies();
  const session = await verifySessionToken(cookieStore.get(SESSION_COOKIE)?.value);
  if (!session) {
    throw new Error("Unauthorized: Invalid session");
  }
  return session.uid;
}

export async function getCategoryTable(category: string, listType?: string) {
  await requireSession();
  return api.categoryTable(category, listType);
}

export async function scoreAsin(input: {
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
}) {
  await requireSession();
  const result = await api.score(input);
  // score_asin() writes a new row to the validations table server-side.
  // updateTag (not revalidateTag) is the correct primitive here: this is a
  // Server Action and we need read-your-own-writes — the very next request
  // for the watchlist must wait for fresh data, not serve the 60s-stale copy.
  updateTag("watchlist");
  return result;
}

export async function analyzeListing(input: { asin: string; category?: string }) {
  await requireSession();
  const cookieStore = await cookies();
  const { DEFAULT_MARKETPLACE_ID } = await import("./marketplaces");
  const marketplace_id = cookieStore.get("scout_marketplace")?.value || DEFAULT_MARKETPLACE_ID;
  return api.analyzeListing({ ...input, marketplace_id });
}

export async function suggestListingImprovements(input: {
  title: string | null;
  bullets: string[];
  category?: string | null;
  gaps: string[];
}) {
  await requireSession();
  return api.suggestListingImprovements(input);
}

export async function summarizeReviews(reviews: ListingReview[]) {
  await requireSession();
  return api.summarizeReviews({ reviews });
}

export async function getWatchlist() {
  await requireSession();
  return api.watchlist();
}

export async function calcProfit(input: {
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
}) {
  await requireSession();
  return api.profitCalculator(input);
}

export async function gatherKeywords(seed: string) {
  await requireSession();
  if (!seed || seed.trim().length === 0) return [];
  const alphabet = "abcdefghijklmnopqrstuvwxyz".split("");
  const results: Record<string, { term: string; score: number; occurrences: number }> = {};

  // 1. Gather suggestions for the base query
  const baseSuggestions = await fetchSuggestions(seed.trim());
  processSuggestions(baseSuggestions, 15); // base suggestions have higher initial weight

  // 2. Fetch suggestions for query + alphabet letter to get deep suggestions
  // Run in chunks of 5 parallel requests to be polite to Amazon completions servers
  const chunkSize = 5;
  for (let i = 0; i < alphabet.length; i += chunkSize) {
    const chunk = alphabet.slice(i, i + chunkSize);
    await Promise.all(
      chunk.map(async (letter) => {
        const queryWithLetter = `${seed.trim()} ${letter}`;
        try {
          const suggestions = await fetchSuggestions(queryWithLetter);
          processSuggestions(suggestions, 10);
        } catch {
          // ignore transient fetch failures
        }
      })
    );
  }

  function processSuggestions(list: string[], multiplier: number) {
    list.forEach((term, index) => {
      const normalized = term.trim().toLowerCase();
      if (!normalized) return;
      // Points based on position: index 0 (top suggestion) gets 10 points, index 9 gets 1 point
      const positionPoints = Math.max(0, 10 - index);
      const points = positionPoints * multiplier;

      if (results[normalized]) {
        results[normalized].score += points;
        results[normalized].occurrences += 1;
      } else {
        results[normalized] = {
          term: term.trim(),
          score: points,
          occurrences: 1,
        };
      }
    });
  }

  // 3. Compile and sort results
  const compiled = Object.values(results);
  if (compiled.length === 0) {
    throw new Error("No suggestion keywords returned from Amazon autocomplete. The upstream service may be temporarily rate-limiting requests. Please try again in a few minutes.");
  }

  // Normalize scores to a 1-100 scale
  const maxScore = Math.max(...compiled.map((c) => c.score));
  return compiled
    .map((c) => ({
      keyword: c.term,
      relevancy: maxScore > 0 ? Math.round((c.score / maxScore) * 100) : 10,
      intent: (c.term.split(" ").length > 3 ? "HIGH" : c.term.split(" ").length > 1 ? "MEDIUM" : "LOW") as "HIGH" | "MEDIUM" | "LOW",
      occurrences: c.occurrences,
    }))
    .sort((a, b) => b.relevancy - a.relevancy)
    .slice(0, 100); // return top 100 results
}

async function fetchSuggestions(term: string): Promise<string[]> {
  const encoded = encodeURIComponent(term);
  // India first — this is an Amazon India seller tool, so IN keywords must win.
  // The host matters as much as the marketplace id: completion.amazon.com returns
  // an empty suggestions array for the India mid (A21TJRUUN4KGV) under every
  // parameter combination, while completion.amazon.co.uk returns real Indian
  // suggestions for that same mid. Do not "simplify" this back to the .com host.
  const sources = [
    `https://completion.amazon.co.uk/api/2017/suggestions?limit=10&client-info=amazon-search-ui&mid=A21TJRUUN4KGV&alias=aps&prefix=${encoded}`,
    `https://suggestqueries.google.com/complete/search?client=chrome&hl=en&gl=in&q=${encoded}+amazon`,
    `https://completion.amazon.com/api/2017/suggestions?limit=10&client-info=amazon-search-ui&mid=ATVPDKIKX0DER&alias=aps&prefix=${encoded}`,
  ];

  for (const url of sources) {
    try {
      const res = await fetch(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
          "Accept": "application/json",
        },
        next: { revalidate: 3600 },
      });
      if (!res.ok) continue;
      const data = await res.json();
      
      // Amazon API format
      if (data && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
        const list = data.suggestions.map((s: any) => s.value as string).filter(Boolean);
        if (list.length > 0) return list;
      }
      
      // Google API format: ["query", ["sugg1", "sugg2", ...]]
      if (Array.isArray(data) && Array.isArray(data[1]) && data[1].length > 0) {
        const list = data[1].map((s: string) => s.replace(/amazon/gi, "").trim()).filter(Boolean);
        if (list.length > 0) return list;
      }
    } catch {
      // try next source
    }
  }

  return [];
}

export async function updateWatchlistNotes(asin: string, notes: string) {
  await requireSession();
  const result = await api.updateWatchlistNotes({ asin, notes });
  updateTag("watchlist");
  return result;
}

export async function searchProductDatabase(params: {
  q?: string;
  category?: string;
  min_price?: number;
  max_price?: number;
  min_rank?: number;
  max_rank?: number;
  limit?: number;
  offset?: number;
}) {
  await requireSession();
  return api.productDatabase(params);
}

export async function getMyProducts() {
  await requireSession();
  return api.myProducts();
}

export async function saveMyProduct(body: {
  asin: string;
  title?: string | null;
  sku?: string | null;
  supplier_cost: number;
  shipping_fee: number;
  target_margin: number;
  supplier_details: string;
  current_stock?: number;
  lead_time_days?: number;
}) {
  await requireSession();
  const result = await api.saveMyProduct(body);
  updateTag("my-products");
  return result;
}

export async function deleteMyProduct(asin: string) {
  await requireSession();
  const result = await api.deleteMyProduct(asin);
  updateTag("my-products");
  return result;
}

export async function compareCompetitors(asins: string[]) {
  await requireSession();
  return api.compareCompetitors({ asins });
}

export async function getListingHealth() {
  await requireSession();
  return api.listingHealth();
}

export async function getDrawerDetails(asin: string) {
  await requireSession();
  return api.drawerDetails(asin);
}

export async function connectAmazonAccount(body: { code: string; selling_partner_id: string; marketplace_id?: string }) {
  await requireSession();
  const result = await api.amazonCallback(body);
  updateTag("amazon-status");
  return result;
}

export async function getAmazonStatus() {
  await requireSession();
  return api.amazonStatus();
}

export async function disconnectAmazonAccount(sellingPartnerId: string) {
  await requireSession();
  const result = await api.deleteAmazonAccount(sellingPartnerId);
  updateTag("amazon-status");
  return result;
}

export async function syncStorefrontData() {
  await requireSession();
  const result = await api.syncStorefront();
  updateTag("storefront-status");
  return result;
}

export async function getStorefrontSalesData() {
  await requireSession();
  return api.storefrontSales();
}

export async function getStorefrontOrdersData() {
  await requireSession();
  return api.storefrontOrders();
}

export async function getSaasAuditLogs() {
  await requireSession();
  return api.saasAuditLogs();
}

export async function getSaasOrgMembers() {
  await requireSession();
  return api.saasOrgMembers();
}

export async function addSaasOrgMember(body: { email: string; role: string; name?: string }) {
  await requireSession();
  return api.addSaasOrgMember(body);
}

export async function getPpcAnalytics() {
  await requireSession();
  return api.ppcAnalytics();
}
