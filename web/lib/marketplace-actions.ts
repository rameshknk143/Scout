"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { MARKETPLACES, DEFAULT_MARKETPLACE_ID } from "./marketplaces";

export async function setMarketplacePreference(val: string) {
  let mktId: string = DEFAULT_MARKETPLACE_ID;

  if (val in MARKETPLACES) {
    mktId = MARKETPLACES[val as keyof typeof MARKETPLACES].id;
  } else {
    const found = Object.values(MARKETPLACES).find((m) => m.id === val);
    if (found) {
      mktId = found.id;
    } else {
      mktId = val;
    }
  }

  const cookieStore = await cookies();

  // Set the cookie securely
  cookieStore.set({
    name: "scout_marketplace",
    value: mktId,
    path: "/",
    maxAge: 31536000, // 1 year
    sameSite: "lax",
  });

  // Revalidate to instantly update server components and fetched data
  revalidatePath("/");
}
