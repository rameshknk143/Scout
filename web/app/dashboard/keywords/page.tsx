import KeywordsClient from "./keywords-client";

export const dynamic = "force-dynamic";

export default function KeywordsPage() {
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-black/5">
        <h1 className="text-xl font-bold text-zinc-900 tracking-tight font-sans">Keyword Suggestion Harvester</h1>
        <p className="text-xs text-zinc-400 font-medium mt-1">
          ScoutVeda's alternative to Helium 10 Magnet. Harvest high-intent search terms directly from Amazon's autocomplete search database for free.
        </p>
      </div>
      <KeywordsClient />
    </div>
  );
}
