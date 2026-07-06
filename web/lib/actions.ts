"use server";

import { api } from "./api";

export async function getCategoryTable(category: string) {
  return api.categoryTable(category);
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
  return api.score(input);
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
