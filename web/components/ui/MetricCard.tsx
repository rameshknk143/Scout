"use client";

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string | number;
  changeType?: "positive" | "negative" | "neutral";
  tooltip?: string;
  onClick?: () => void;
  sparklineData?: number[];
}

export default function MetricCard({
  title,
  value,
  change,
  changeType = "neutral",
  tooltip,
  onClick,
  sparklineData,
}: MetricCardProps) {
  const isPositive = changeType === "positive";
  const isNegative = changeType === "negative";

  return (
    <div
      onClick={onClick}
      className={`glass-panel p-4 flex flex-col justify-between transition-all ${
        onClick ? "hover:border-zinc-300 cursor-pointer active:scale-[0.99]" : "cursor-default"
      }`}
    >
      <div className="flex items-start justify-between">
        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
          {title}
        </span>
        {tooltip && (
          <span
            className="text-[10px] text-zinc-400 hover:text-zinc-600 cursor-help"
            title={tooltip}
          >
            ⓘ
          </span>
        )}
      </div>

      <div className="mt-2 flex items-baseline justify-between gap-2">
        <span className="text-xl font-bold tracking-tight text-zinc-900">
          {value}
        </span>

        {change && (
          <span
            className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
              isPositive
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200/50"
                : isNegative
                ? "bg-red-50 text-red-700 border border-red-200/50"
                : "bg-zinc-50 text-zinc-600 border border-zinc-200/50"
            }`}
          >
            {isPositive ? "▲" : isNegative ? "▼" : ""} {change}
          </span>
        )}
      </div>

      {sparklineData && sparklineData.length > 0 && (
        <div className="mt-3 h-5 flex items-end gap-[3px]">
          {sparklineData.map((val, idx) => {
            const max = Math.max(...sparklineData);
            const min = Math.min(...sparklineData);
            const range = max - min || 1;
            const heightPct = ((val - min) / range) * 80 + 20; // scale from 20% to 100%
            return (
              <div
                key={idx}
                style={{ height: `${heightPct}%` }}
                className={`flex-1 rounded-sm transition-all ${
                  isPositive 
                    ? "bg-emerald-600/30 group-hover:bg-emerald-600/50" 
                    : isNegative 
                      ? "bg-red-600/30 group-hover:bg-red-600/50" 
                      : "bg-zinc-300 group-hover:bg-zinc-400"
                }`}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
