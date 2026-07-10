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
  barColor = "#18181b",
}: {
  title: string;
  data: Record<string, string | number>[];
  xKey: string;
  dataKey: string;
  barColor?: string;
}) {
  return (
    <div className="glass-panel p-5 mb-5 h-64">
      <div className="text-xs uppercase tracking-wide text-muted mb-3">{title}</div>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 0, 0, 0.04)" />
          <XAxis dataKey={xKey} stroke="#71717a" fontSize={11} />
          <YAxis stroke="#71717a" fontSize={11} />
          <Tooltip
            contentStyle={{
              background: "#ffffff",
              border: "1px solid rgba(0, 0, 0, 0.06)",
              borderRadius: 8,
              fontSize: 12,
              color: "#09090b",
            }}
          />
          <Bar dataKey={dataKey} fill={barColor} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
