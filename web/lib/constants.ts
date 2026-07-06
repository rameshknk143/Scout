// Plain constants, safe to import from Client Components — kept separate
// from api.ts (which has a `server-only` guard) so client bundles never
// pull that module in.

export const CATEGORIES = [
  "Electronics Accessories", "Home & Kitchen", "Beauty & Personal Care",
  "Sports & Fitness", "Toys & Games", "Stationery/Office", "Pet Supplies",
  "Car Accessories", "Garden & Outdoors", "Baby Products", "Watches & Gifting",
] as const;

export const FEE_CATEGORIES = [
  "electronics_accessories", "fashion_apparel", "home_kitchen",
  "beauty_personal_care", "grocery", "books", "sports_fitness", "toys",
  "automotive_parts", "other_default",
] as const;
