"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Dark-theme-styled Recharts bar chart, extracted from trend-radar-client.tsx
// so the stroke colors / tooltip box don't get hand-tuned again per chart.
export default function ChartCard({
  title,
  data,
  xKey,
  dataKey,
  barColor = "#3b82f6",
}: {
  title: string;
  data: Record<string, string | number>[];
  xKey: string;
  dataKey: string;
  barColor?: string;
}) {
  return (
    <div className="glass-panel p-5 mb-5 h-64">
      <div className="text-xs uppercase tracking-wide text-muted mb-3 font-semibold">{title}</div>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.04)" />
          <XAxis dataKey={xKey} stroke="#64748b" fontSize={11} />
          <YAxis stroke="#64748b" fontSize={11} />
          <Tooltip
            contentStyle={{
              background: "#111625",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: 8,
              fontSize: 12,
              color: "#f8fafc",
            }}
          />
          <Bar dataKey={dataKey} fill={barColor} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
