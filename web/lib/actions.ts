"use server";

import { updateTag } from "next/cache";
import { api } from "./api";

export async function getCategoryTable(category: string, listType?: string) {
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
  const result = await api.score(input);
  // score_asin() writes a new row to the validations table server-side.
  // updateTag (not revalidateTag) is the correct primitive here: this is a
  // Server Action and we need read-your-own-writes — the very next request
  // for the watchlist must wait for fresh data, not serve the 60s-stale copy.
  updateTag("watchlist");
  return result;
}

export async function analyzeListing(input: { asin: string; category?: string }) {
  return api.analyzeListing(input);
}

export async function suggestListingImprovements(input: {
  title: string | null;
  bullets: string[];
  category?: string | null;
  gaps: string[];
}) {
  return api.suggestListingImprovements(input);
}

export async function getWatchlist() {
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
  return api.profitCalculator(input);
}
