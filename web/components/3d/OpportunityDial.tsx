"use client";

import { useEffect, useRef, useState } from "react";

interface OpportunityDialProps {
  score: number; // 0-100
  size?: number; // diameter in px
  label?: string;
  animate?: boolean;
}

export function OpportunityDial({
  score,
  size = 200,
  label = "Opportunity Score",
  animate = true,
}: OpportunityDialProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const [visible, setVisible] = useState(false);
  const circleRef = useRef<SVGCircleElement>(null);

  useEffect(() => {
    if (animate) {
      setVisible(true);
      const target = Math.max(0, Math.min(100, score));
      const duration = 1200;
      const start = Date.now();

      const tick = () => {
        const elapsed = Date.now() - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        setAnimatedScore(Math.round(target * eased));
        if (progress < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    } else {
      setAnimatedScore(score);
      setVisible(true);
    }
  }, [score, animate]);

  const radius = size / 2 - 8;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animatedScore / 100) * circumference;

  // Color based on score
  const getColor = (s: number) => {
    if (s >= 75) return "var(--positive)";
    if (s >= 50) return "var(--warning)";
    if (s >= 25) return "var(--info)";
    return "var(--critical)";
  };

  const color = getColor(animatedScore);

  return (
    <div
      className="relative flex flex-col items-center"
      style={{ width: size, height: size + 60 }}
      role="img"
      aria-label={`${label}: ${animatedScore} out of 100`}
    >
      {/* Outer glow ring */}
      <div
        className="absolute inset-0 rounded-full blur-[40px] opacity-30 pointer-events-none"
        style={{
          background: `radial-gradient(circle at center, ${color} 0%, transparent 70%)`,
          animation: visible ? "pulse-glow 3s ease-in-out infinite" : "none",
        }}
      />

      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="relative">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--hairline)"
          strokeWidth={8}
        />

        {/* Progress ring */}
        <circle
          ref={circleRef}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: animate
              ? "stroke-dashoffset 1200ms cubic-bezier(0.16, 1, 0.3, 1), stroke 300ms ease"
              : "stroke 300ms ease",
            transform: "rotate(-90deg)",
            transformOrigin: "center",
            filter: `drop-shadow(0 0 8px ${color})`,
          }}
        />

        {/* Inner subtle track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius * 0.6}
          fill="none"
          stroke="var(--hairline)"
          strokeWidth={1}
          strokeDasharray="4 4"
          opacity={0.3}
        />
      </svg>

      {/* Center content */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "scale(1)" : "scale(0.8)",
          transition: "opacity var(--dur-slow) var(--ease-out), transform var(--dur-slow) var(--ease-out)",
          transitionDelay: animate ? "400ms" : "0ms",
        }}
      >
        <span
          className="font-mono text-4xl font-extrabold tabular-nums"
          style={{ color: color }}
        >
          {animatedScore}
        </span>
        <span
          className="text-[10px] font-semibold uppercase tracking-widest text-text-tertiary mt-1"
        >
          {label}
        </span>
      </div>

      {/* Score tier badge */}
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 flex items-center gap-1 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider"
        style={{
          background: `var(--${animatedScore >= 75 ? "positive" : animatedScore >= 50 ? "warning" : animatedScore >= 25 ? "info" : "critical"}-soft)`,
          color: `var(--${animatedScore >= 75 ? "positive" : animatedScore >= 50 ? "warning" : animatedScore >= 25 ? "info" : "critical"})`,
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
          transition: "opacity var(--dur-slow) var(--ease-out) 600ms, transform var(--dur-slow) var(--ease-out) 600ms",
        }}
      >
        {animatedScore >= 75 && "High Opportunity"}
        {animatedScore >= 50 && animatedScore < 75 && "Moderate Opportunity"}
        {animatedScore >= 25 && animatedScore < 50 && "Low Opportunity"}
        {animatedScore < 25 && "Avoid"}
      </div>

      <style jsx>{`
        @keyframes pulse-glow {
          0%, 100% { opacity: 0.3; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.05); }
        }
      `}</style>
    </div>
  );
}