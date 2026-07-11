import KeywordsClient from "./keywords-client";

export const dynamic = "force-dynamic";

export default function KeywordsPage() {
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-zinc-200/80">
        <h1 className="text-xl font-bold text-zinc-950 tracking-tight">Keyword Suggestion Harvester</h1>
        <p className="text-xs text-zinc-500 font-medium mt-1">
          Scout's alternative to Helium 10 Magnet. Harvest high-intent search terms directly from Amazon's autocomplete search database for free.
        </p>
      </div>
      <KeywordsClient />
    </div>
  );
}
