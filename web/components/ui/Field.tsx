// Form field label wrapper — was defined verbatim, twice, in
// validator-client.tsx and profit-calculator-client.tsx. Every future form
// (Listing Optimization, Keyword Research, ...) reuses this instead of
// re-pasting it a third/fourth/fifth time.
export default function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="block text-sm text-muted mb-1.5">{label}</span>
      {children}
    </label>
  );
}
