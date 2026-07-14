"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { MARKETPLACES, type MarketplaceDomain } from "./marketplaces";

export async function setMarketplacePreference(domain: string) {
  if (!(domain in MARKETPLACES)) {
    throw new Error("Invalid marketplace");
  }
  
  const mkt = MARKETPLACES[domain as MarketplaceDomain];
  const cookieStore = await cookies();
  
  // Set the cookie securely
  cookieStore.set({
    name: "scout_marketplace",
    value: mkt.id,
    path: "/",
    maxAge: 31536000, // 1 year
    sameSite: "lax",
  });

  // Revalidate to instantly update server components and fetched data
  revalidatePath("/");
}
