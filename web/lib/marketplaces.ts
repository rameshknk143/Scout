export const MARKETPLACES = {
  "amazon.in": {
    id: "A21TJRUUN4KGV",
    name: "🇮🇳 Amazon.in",
    domain: "amazon.in",
  },
  "amazon.com": {
    id: "ATVPDKIKX0DER",
    name: "🇺🇸 Amazon.com",
    domain: "amazon.com",
  },
  "amazon.co.uk": {
    id: "A1F83G8C2ARO7P",
    name: "🇬🇧 Amazon.co.uk",
    domain: "amazon.co.uk",
  },
} as const;

export type MarketplaceDomain = keyof typeof MARKETPLACES;

export const DEFAULT_MARKETPLACE: MarketplaceDomain = "amazon.in";
export const DEFAULT_MARKETPLACE_ID = MARKETPLACES[DEFAULT_MARKETPLACE].id;
