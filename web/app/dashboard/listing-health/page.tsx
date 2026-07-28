import ListingHealthClient from "./listing-health-client";

export default function ListingHealthPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-900 font-sans">Listing Health</h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">
        Audit listing copy gaps, low star ratings, and missing search indexing factors for your tracked listings.
      </p>
      <ListingHealthClient />
    </div>
  );
}
