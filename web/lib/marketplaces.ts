export const MARKETPLACES = {
  "amazon.in": {
    id: "A21TJRUUN4KGV",
    name: "🇮🇳 Amazon.in",
    domain: "amazon.in",
    currency: "INR",
    symbol: "₹",
  },
  "amazon.com": {
    id: "ATVPDKIKX0DER",
    name: "🇺🇸 Amazon.com",
    domain: "amazon.com",
    currency: "USD",
    symbol: "$",
  },
  "amazon.co.uk": {
    id: "A1F83G8C2ARO7P",
    name: "🇬🇧 Amazon.co.uk",
    domain: "amazon.co.uk",
    currency: "GBP",
    symbol: "£",
  },
  "amazon.de": {
    id: "A1PA6795UKMFR9",
    name: "🇩🇪 Amazon.de",
    domain: "amazon.de",
    currency: "EUR",
    symbol: "€",
  },
  "amazon.fr": {
    id: "A13V1IB3VIYZZH",
    name: "🇫🇷 Amazon.fr",
    domain: "amazon.fr",
    currency: "EUR",
    symbol: "€",
  },
  "amazon.it": {
    id: "APJ6JRA9NG5V4",
    name: "🇮🇹 Amazon.it",
    domain: "amazon.it",
    currency: "EUR",
    symbol: "€",
  },
  "amazon.es": {
    id: "A1RKKUPIHCS9HS",
    name: "🇪🇸 Amazon.es",
    domain: "amazon.es",
    currency: "EUR",
    symbol: "€",
  },
  "amazon.ca": {
    id: "A2EUQ1WTGCTBG2",
    name: "🇨🇦 Amazon.ca",
    domain: "amazon.ca",
    currency: "CAD",
    symbol: "$",
  },
  "amazon.com.au": {
    id: "A39IBJ37TRP1C6",
    name: "🇦🇺 Amazon.com.au",
    domain: "amazon.com.au",
    currency: "AUD",
    symbol: "$",
  },
  "amazon.co.jp": {
    id: "A1VC38T7YXB528",
    name: "🇯🇵 Amazon.co.jp",
    domain: "amazon.co.jp",
    currency: "JPY",
    symbol: "¥",
  },
  "amazon.com.mx": {
    id: "A1AM78C64UM0Y8",
    name: "🇲🇽 Amazon.com.mx",
    domain: "amazon.com.mx",
    currency: "MXN",
    symbol: "$",
  },
  "amazon.ae": {
    id: "A2VIGQ35RCS4UG",
    name: "🇦🇪 Amazon.ae",
    domain: "amazon.ae",
    currency: "AED",
    symbol: "AED",
  },
} as const;

export type MarketplaceDomain = keyof typeof MARKETPLACES;

export const DEFAULT_MARKETPLACE: MarketplaceDomain = "amazon.in";
export const DEFAULT_MARKETPLACE_ID: string = MARKETPLACES[DEFAULT_MARKETPLACE].id;
