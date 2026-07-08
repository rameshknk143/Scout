// Replaces the `Empty` helper that used to live inline in trend-radar-client.tsx
// (and the equivalent ad hoc div in watchlist-client.tsx) with one shared version.
export default function EmptyState({
  text,
  icon,
}: {
  text: string;
  icon?: string;
}) {
  return (
    <div className="glass-panel p-8 text-center text-muted text-sm">
      {icon && (
        <div className="text-2xl mb-2" aria-hidden>
          {icon}
        </div>
      )}
      {text}
    </div>
  );
}
