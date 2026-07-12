// Scout audit — owner-authorized data extraction with provenance.
// Reads API key at runtime from web/.env.local; never writes the key to outputs.
// Rate limit: 700ms between requests. Retries: 3 with exponential backoff.
import { readFileSync, writeFileSync, appendFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = join(here, "..");
const API = "https://scout-api-3yvy.onrender.com";
const envText = readFileSync(join(here, "..", "..", "web", ".env.local"), "utf8");
const KEY = envText.match(/^API_KEY=(.+)$/m)[1].trim();

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = [];
const t0 = Date.now();

async function get(path, attempt = 1) {
  const started = new Date().toISOString();
  try {
    const res = await fetch(`${API}${path}`, { headers: { "X-Scout-Key": KEY } });
    const status = res.status;
    if (!res.ok) throw new Error(`HTTP ${status}`);
    const json = await res.json();
    log.push({ ts: started, path, status, attempt, ok: true });
    return json;
  } catch (e) {
    log.push({ ts: started, path, status: String(e.message), attempt, ok: false });
    if (attempt < 3) {
      await sleep(1500 * attempt);
      return get(path, attempt + 1);
    }
    return null;
  }
}

const jsonl = [];
const errors = [];
function record(source_endpoint, obj) {
  jsonl.push({ ...obj, _source_endpoint: source_endpoint, _retrieved_at: new Date().toISOString() });
}

// ---- small datasets ----
const cats = await get("/trend-radar/categories");
if (cats) cats.categories.forEach((c) => record("/trend-radar/categories", { category: c }));
await sleep(700);

const digest = await get("/trend-radar/digest");
if (digest) {
  digest.new_entrants.forEach((r) => record("/trend-radar/digest#new_entrants", r));
  digest.top_movers.forEach((r) => record("/trend-radar/digest#top_movers", r));
  digest.cross_category.forEach((r) => record("/trend-radar/digest#cross_category", r));
  record("/trend-radar/digest#collection_dates", { collection_dates: digest.collection_dates });
}
await sleep(700);

const watchlist = await get("/watchlist");
if (watchlist) watchlist.validations.forEach((r) => record("/watchlist", r));
await sleep(700);

const alerts = await get("/alerts");
if (alerts) alerts.alerts.forEach((r) => record("/alerts", r));
await sleep(700);

const myprods = await get("/my-products");
if (myprods) myprods.products.forEach((r) => record("/my-products", r));
await sleep(700);

const lh = await get("/listing-health");
if (lh) lh.products.forEach((r) => record("/listing-health", r));
await sleep(700);

// ---- main dataset: /product-database, paginated ----
const LIMIT = 100;
let total = null;
let offset = 0;
const products = [];
const seen = new Set();
let dupes = 0, malformed = 0, pages = 0;

while (true) {
  const page = await get(`/product-database?limit=${LIMIT}&offset=${offset}`);
  if (!page) { errors.push(`page offset=${offset} failed after retries`); break; }
  pages++;
  if (total === null) total = page.total;
  for (const p of page.products) {
    if (typeof p.asin !== "string" || !p.asin) { malformed++; continue; }
    const k = JSON.stringify([p.asin, p.category ?? "", p.rank ?? "", p.price ?? "", p.title ?? ""]);
    if (seen.has(k)) { dupes++; continue; }
    seen.add(k);
    products.push({ ...p, _source_endpoint: `/product-database?limit=${LIMIT}&offset=${offset}`, _page: pages, _retrieved_at: new Date().toISOString() });
  }
  offset += LIMIT;
  if (offset >= total || page.products.length === 0) break;
  await sleep(700);
}

// ---- outputs ----
mkdirSync(outDir, { recursive: true });
const allRecords = [...jsonl, ...products];
writeFileSync(join(outDir, "scraped-data.jsonl"), allRecords.map((r) => JSON.stringify(r)).join("\n") + "\n");

// CSV for the product-database dataset (the tabular one)
const cols = ["asin", "title", "category", "rank", "price", "rating", "review_count", "image_url", "_page", "_retrieved_at"];
const esc = (v) => v == null ? "" : `"${String(v).replaceAll('"', '""')}"`;
const csv = [cols.join(",")].concat(products.map((p) => cols.map((c) => esc(p[c])).join(","))).join("\n");
writeFileSync(join(outDir, "scraped-data.csv"), csv + "\n");

const summary = {
  finished_at: new Date().toISOString(),
  elapsed_s: Math.round((Date.now() - t0) / 1000),
  requests: log.length,
  request_failures: log.filter((l) => !l.ok).length,
  product_database_total_reported: total,
  product_database_rows_extracted: products.length,
  duplicates_skipped: dupes,
  malformed_skipped: malformed,
  pages_fetched: pages,
  small_dataset_records: jsonl.length,
  watchlist_rows: watchlist ? watchlist.validations.length : "FAILED",
  alerts_rows: alerts ? alerts.alerts.length : "FAILED",
  my_products_rows: myprods ? myprods.products.length : "FAILED",
  listing_health_rows: lh ? lh.products.length : "FAILED",
  categories: cats ? cats.categories.length : "FAILED",
};
writeFileSync(join(outDir, "tools", "extract-summary.json"), JSON.stringify(summary, null, 2));
writeFileSync(join(outDir, "tools", "request-log.json"), JSON.stringify(log, null, 2));
console.log(JSON.stringify(summary, null, 2));
if (errors.length) console.log("ERRORS:", errors.join("; "));
