import CompetitorAnalysisClient from "./competitor-analysis-client";

export default function CompetitorAnalysisPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-950">Competitor Analysis</h1>
      <p className="text-zinc-500 text-xs font-medium mt-1 mb-6">
        Input up to 5 ASINs to audit and compare competitor pricing, BSR, ratings, and opportunity metrics side-by-side.
      </p>
      <CompetitorAnalysisClient />
    </div>
  );
}
