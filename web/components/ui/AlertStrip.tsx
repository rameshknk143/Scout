"use client";

export interface AlertItem {
  id: string;
  type: "low_stock" | "buy_box_lost" | "price_drop" | "negative_review" | "suppressed" | "opportunity";
  count: number;
  label: string;
  severity: "critical" | "warning" | "info" | "success";
  actionLabel: string;
  onClick?: () => void;
}

interface AlertStripProps {
  alerts: AlertItem[];
}

export default function AlertStrip({ alerts }: AlertStripProps) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2.5 mb-6">
      {alerts.map((alert) => {
        const isCritical = alert.severity === "critical";
        const isWarning = alert.severity === "warning";
        const isSuccess = alert.severity === "success";

        return (
          <div
            key={alert.id}
            className={`flex items-center gap-3 px-3.5 py-1.5 rounded-lg border text-xs font-semibold shadow-sm transition-all ${
              isCritical
                ? "bg-red-50 border-red-200/80 text-red-700"
                : isWarning
                ? "bg-amber-50 border-amber-200/80 text-amber-800"
                : isSuccess
                ? "bg-emerald-50 border-emerald-200/80 text-emerald-800"
                : "bg-blue-50 border-blue-200/80 text-blue-800"
            }`}
          >
            {/* Status light dot */}
            <span
              className={`h-2.5 w-2.5 rounded-full shrink-0 ${
                isCritical
                  ? "bg-red-600 animate-pulse"
                  : isWarning
                  ? "bg-amber-500"
                  : isSuccess
                  ? "bg-emerald-600"
                  : "bg-blue-600"
              }`}
            />

            <span>
              <span className="font-extrabold">{alert.count}</span> {alert.label}
            </span>

            {alert.onClick && (
              <button
                onClick={alert.onClick}
                className="underline hover:no-underline font-extrabold cursor-pointer uppercase text-[9px] tracking-widest pl-2 border-l border-current/20 hover:opacity-85"
              >
                {alert.actionLabel}
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
