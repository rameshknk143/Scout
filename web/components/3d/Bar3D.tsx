"use client";

// 3D Bar Chart -- SVG, pure CSS, with a 3D extrusion illusion: each bar is a
// front face plus a top face and a right face, drawn as polygons. No 3D
// library, no WebGL. Renders 30+ bars smoothly because it's one SVG.

type Datum = { label: string; value: number; sublabel?: string };

type Props = {
  data: Datum[];
  /** Title shown above the chart. */
  title: string;
  /** Y-axis label, e.g. "ASINs landed". */
  yLabel?: string;
  /** Max for the Y axis. Defaults to max(value) + small headroom. */
  max?: number;
  /** Bar color: usually green=ok, red=down. */
  tone?: "ok" | "warn" | "error" | "amber";
  /** Optional unit suffix on the value tooltip, e.g. " ASINs". */
  unit?: string;
};

const TONE = {
  ok: { face: "#10b981", side: "#059669", top: "#34d399", soft: "rgba(16,185,129,0.12)" },
  warn: { face: "#f59e0b", side: "#d97706", top: "#fbbf24", soft: "rgba(245,158,11,0.12)" },
  error: { face: "#ef4444", side: "#dc2626", top: "#f87171", soft: "rgba(239,68,68,0.12)" },
  amber: { face: "#d97706", side: "#b45309", top: "#f59e0b", soft: "rgba(217,119,6,0.12)" },
};

export default function Bar3D({ data, title, yLabel, max, tone = "amber", unit = "" }: Props) {
  const t = TONE[tone];
  const W = 640;
  const H = 220;
  const padL = 36;
  const padR = 16;
  const padT = 16;
  const padB = 32;
  const chartW = W - padL - padR;
  const chartH = H - padT - padB;
  const yMax = max ?? Math.max(1, ...data.map((d) => d.value)) * 1.15;
  const bw = Math.min(28, (chartW / Math.max(1, data.length)) * 0.7);
  const gap = (chartW - bw * data.length) / Math.max(1, data.length + 1);
  // 3D extrusion depth, in px
  const depth = 6;
  // hover state
  // (kept intentionally simple — the chart re-renders on hover via CSS only)

  return (
    <div className="w-full">
      <div className="flex items-baseline justify-between mb-2">
        <div className="text-xs font-bold uppercase tracking-wide text-zinc-400">{title}</div>
        {yLabel && <div className="text-[10px] text-zinc-400 uppercase tracking-wider">{yLabel}</div>}
      </div>
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id={`bar-grad-${tone}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={t.top} />
              <stop offset="100%" stopColor={t.face} />
            </linearGradient>
            <linearGradient id={`bar-side-${tone}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={t.face} />
              <stop offset="100%" stopColor={t.side} />
            </linearGradient>
          </defs>
          {/* gridlines + y axis ticks */}
          {[0, 0.25, 0.5, 0.75, 1].map((p, i) => {
            const y = padT + chartH * (1 - p);
            return (
              <g key={i}>
                <line
                  x1={padL}
                  y1={y}
                  x2={W - padR}
                  y2={y}
                  stroke="rgba(0,0,0,0.06)"
                  strokeWidth="1"
                />
                <text
                  x={padL - 6}
                  y={y + 3}
                  textAnchor="end"
                  fontSize="9"
                  fill="rgba(0,0,0,0.4)"
                  fontFamily="var(--font-mono)"
                >
                  {Math.round(yMax * p)}
                </text>
              </g>
            );
          })}
          {/* bars */}
          {data.map((d, i) => {
            const x = padL + gap + i * (bw + gap);
            const h = (d.value / yMax) * chartH;
            const y = padT + chartH - h;
            return (
              <g key={i} className="bar3d-row" style={{ transition: "transform 0.3s" }}>
                {/* back-shadow bar (the depth on the floor) */}
                <ellipse
                  cx={x + bw / 2}
                  cy={y + h + 4}
                  rx={bw / 2}
                  ry={3}
                  fill="rgba(0,0,0,0.12)"
                />
                {/* right face (3D side) */}
                <polygon
                  points={`${x + bw},${y},${x + bw + depth},${y - depth},${x + bw + depth},${y + h - depth},${x + bw},${y + h}`}
                  fill={`url(#bar-side-${tone})`}
                  opacity="0.85"
                />
                {/* top face */}
                <polygon
                  points={`${x},${y},${x + bw},${y},${x + bw + depth},${y - depth},${x + depth},${y - depth}`}
                  fill={`url(#bar-grad-${tone})`}
                />
                {/* front face */}
                <rect
                  x={x}
                  y={y}
                  width={bw}
                  height={h}
                  fill={`url(#bar-grad-${tone})`}
                  rx="2"
                />
                {/* value on top of bar */}
                <text
                  x={x + bw / 2}
                  y={y - depth - 4}
                  textAnchor="middle"
                  fontSize="10"
                  fontFamily="var(--font-mono)"
                  fontWeight="700"
                  fill={t.side}
                >
                  {d.value}
                  {unit}
                </text>
                {/* x label */}
                <text
                  x={x + bw / 2}
                  y={padT + chartH + 16}
                  textAnchor="middle"
                  fontSize="9"
                  fill="rgba(0,0,0,0.5)"
                >
                  {d.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
