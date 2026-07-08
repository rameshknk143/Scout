// Shared loading placeholder — used both for Suspense fallbacks (page.tsx
// files) and inline "waiting on data" states (Table's loading prop, etc.).
// A gentle pulse instead of static text so it reads as "working," not "stuck" —
// worth the one extra Tailwind class on a screen that can sit on a cold Render
// start for 10-30s.
export default function LoadingPanel({ text = "Loading…" }: { text?: string }) {
  return (
    <div className="glass-panel p-8 text-center text-muted text-sm animate-pulse">
      {text}
    </div>
  );
}
