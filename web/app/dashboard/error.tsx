"use client";

// Contained error boundary for dashboard pages. Without this, any render
// throw in a dashboard page becomes Next.js's full-page
// "This page couldn't load" screen. With it, the user sees what failed
// and can retry without losing the sidebar / layout.
export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="bg-white border border-red-200 rounded-2xl p-6 shadow-sm space-y-3">
      <h2 className="text-sm font-bold text-red-800">Something went wrong on this page</h2>
      <p className="text-xs text-zinc-600 leading-relaxed">
        {error?.message || "The page hit an unexpected error while loading its data."}
      </p>
      <button
        onClick={() => reset()}
        className="px-4 py-2 bg-zinc-900 text-white rounded-xl text-xs font-bold hover:bg-black transition"
      >
        Try again
      </button>
    </div>
  );
}
