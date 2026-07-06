const STYLES: Record<string, string> = {
  PURSUE: "badge-pursue",
  WATCH: "badge-watch",
  SKIP: "badge-skip",
};

export default function VerdictBadge({ verdict }: { verdict: string }) {
  return (
    <span className={`badge ${STYLES[verdict] ?? "badge-watch"}`}>
      {verdict}
    </span>
  );
}
