// Small, non-animated stat box — the flavor used inside a result card's grid
// (fee breakdown, component scores) as opposed to StatCard.tsx, which is the
// large animated headline metric at the top of a page. Extracted from the
// local `Stat` in profit-calculator-client.tsx; validator-client.tsx's inline
// score-component boxes now use it too instead of a third hand-rolled copy.
import type { ReactNode } from "react";

export default function MiniStat({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="rounded-lg bg-white/5 px-3 py-2.5">
      <div className="text-xs text-muted">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
