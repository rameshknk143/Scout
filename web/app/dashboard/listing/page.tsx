import ListingClient from "./listing-client";

export default function ListingPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1 font-sans">Listing Quality Score</h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">
        Paste an ASIN, get a rule-based read on title/bullet/image completeness and how it
        stacks up against its category — no AI, just objective checks against the live page.
      </p>
      <ListingClient />
    </div>
  );
}
