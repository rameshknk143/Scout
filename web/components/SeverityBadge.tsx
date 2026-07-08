const STYLES: Record<string, string> = {
  high: "badge-skip",
  medium: "badge-watch",
};

export default function SeverityBadge({ severity }: { severity: string }) {
  if (severity === "low") {
    return (
      <span className="badge bg-white/5 text-muted border border-white/10">
        {severity}
      </span>
    );
  }
  return (
    <span className={`badge ${STYLES[severity] ?? "badge-watch"}`}>
      {severity}
    </span>
  );
}
