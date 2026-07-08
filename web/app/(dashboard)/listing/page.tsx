import ListingClient from "./listing-client";

export default function ListingPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Listing Quality Score</h1>
      <p className="text-muted text-sm mb-6">
        Paste an ASIN, get a rule-based read on title/bullet/image completeness and how it
        stacks up against its category — no AI, just objective checks against the live page.
      </p>
      <ListingClient />
    </div>
  );
}
