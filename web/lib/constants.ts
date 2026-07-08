// Plain constants, safe to import from Client Components — kept separate
// from api.ts (which has a `server-only` guard) so client bundles never
// pull that module in.

// Keep in sync with scraper/collector.py's CATEGORIES dict keys.
export const CATEGORIES = [
  "Electronics Accessories", "Home & Kitchen", "Beauty & Personal Care",
  "Sports & Fitness", "Toys & Games", "Stationery/Office", "Pet Supplies",
  "Car Accessories", "Garden & Outdoors", "Baby Products", "Watches & Gifting",
  "Clothing & Accessories", "Amazon Launchpad", "Amazon Renewed",
  "Apps & Games", "Bags, Wallets & Luggage", "Books", "Computers & Accessories",
  "Gift Cards", "Grocery & Gourmet Foods", "Health & Personal Care",
  "Home Improvement", "Industrial & Scientific", "Jewellery", "Kindle Store",
  "Movies & TV Shows", "Music", "Musical Instruments", "Shoes & Handbags",
  "Software", "Video Games",
] as const;

// Keep in sync with scraper/collector.py's LIST_TYPES dict keys. Movers &
// Shakers deliberately excluded — see collector.py's module docstring.
export const LIST_TYPES = [
  { value: "bestsellers", label: "Best Sellers" },
  { value: "new-releases", label: "New Releases" },
  { value: "most-wished-for", label: "Most Wished For" },
  { value: "most-gifted", label: "Most Gifted" },
] as const;

export const FEE_CATEGORIES = [
  "electronics_accessories", "fashion_apparel", "home_kitchen",
  "beauty_personal_care", "grocery", "books", "sports_fitness", "toys",
  "automotive_parts", "other_default",
] as const;
