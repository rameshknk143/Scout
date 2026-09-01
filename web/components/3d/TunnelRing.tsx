"use client";

// 3D Tunnel Ring -- conic gradient that fills as a percentage (0..1) with a
// CSS-driven 3D depth: outer halo, inner inset, raised ring on hover, and a
// slow background drift so the empty state never looks dead.
//
// No canvas, no R3F: this is one SVG + a handful of CSS layers. Animates on
// the GPU (transform/opacity), so 60fps on any phone that has Webkit.

type Props = {
  /** 0..1, fraction of the ring to fill. */
  fill: number;
  /** Label rendered in the middle of the ring (e.g. "12/12"). */
  center: React.ReactNode;
  /** Subtitle under the center label, e.g. "last hour". */
  caption?: React.ReactNode;
  /** Color: green = healthy, amber = warning, red = down. */
  tone: "ok" | "warn" | "error";
  size?: number; // px
};

const TONE = {
  ok: { ring: "#10b981", glow: "rgba(16,185,129,0.45)", soft: "rgba(16,185,129,0.08)" },
  warn: { ring: "#f59e0b", glow: "rgba(245,158,11,0.45)", soft: "rgba(245,158,11,0.08)" },
  error: { ring: "#ef4444", glow: "rgba(239,68,68,0.45)", soft: "rgba(239,68,68,0.08)" },
};

export default function TunnelRing({ fill, center, caption, tone, size = 132 }: Props) {
  const t = TONE[tone];
  const clamped = Math.max(0, Math.min(1, fill));
  const angle = Math.round(clamped * 360);
  const stroke = 10;
  const r = (size - stroke) / 2 - 6;
  const cx = size / 2;
  const cy = size / 2;
  const c = 2 * Math.PI * r;
  const dash = (clamped * c).toFixed(2);
  const gap = (c - Number(dash)).toFixed(2);

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      {/* outer halo — pulses when filled */}
      <div
        aria-hidden
        className="absolute inset-0 rounded-full"
        style={{
          background: `radial-gradient(circle, ${t.soft} 0%, transparent 70%)`,
          filter: "blur(2px)",
          transform: "scale(1.15)",
        }}
      />
      {/* SVG ring */}
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="relative drop-shadow-md">
        <defs>
          <linearGradient id={`ring-grad-${tone}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={t.ring} stopOpacity="0.55" />
            <stop offset="100%" stopColor={t.ring} stopOpacity="1" />
          </linearGradient>
        </defs>
        {/* track */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="rgba(0,0,0,0.06)"
          strokeWidth={stroke}
        />
        {/* fill — rotated -90deg so 0% starts at 12 o'clock */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={`url(#ring-grad-${tone})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${gap}`}
          transform={`rotate(-90 ${cx} ${cy})`}
          style={{
            filter: `drop-shadow(0 0 6px ${t.glow})`,
            transition: "stroke-dasharray 0.8s cubic-bezier(0.16, 1, 0.3, 1)",
          }}
        />
        {/* tick marks every 30° (subtle 3D notches) */}
        {Array.from({ length: 12 }).map((_, i) => {
          const a = (i * 30 - 90) * (Math.PI / 180);
          const x1 = cx + (r - stroke / 2 - 2) * Math.cos(a);
          const y1 = cy + (r - stroke / 2 - 2) * Math.sin(a);
          const x2 = cx + (r - stroke / 2 + 1) * Math.cos(a);
          const y2 = cy + (r - stroke / 2 + 1) * Math.sin(a);
          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="rgba(0,0,0,0.15)"
              strokeWidth="1"
            />
          );
        })}
      </svg>
      {/* center label, raised on the z-axis */}
      <div
        className="absolute flex flex-col items-center justify-center text-center"
        style={{ transform: "translateZ(20px)" }}
      >
        <div className="text-2xl font-bold font-mono tracking-tight" style={{ color: t.ring }}>
          {center}
        </div>
        {caption && <div className="text-[10px] text-zinc-500 mt-0.5 uppercase tracking-wider">{caption}</div>}
      </div>
      {/* unused angle calc — kept for future tooltips */}
      <span hidden>{angle}</span>
    </div>
  );
}
