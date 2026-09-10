"use client";

import { useEffect, useRef, useState } from "react";

interface TrustBadgeProps {
  title: string;
  desc: string;
  delay?: number;
  className?: string;
}

export function TrustBadge({
  title,
  desc,
  delay = 0,
  className = "",
}: TrustBadgeProps) {
  const [visible, setVisible] = useState(false);
  const [hovered, setHovered] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      ref={cardRef}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={`p-4 rounded-xl relative overflow-hidden transition-all duration-500 ${className}`}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(20px)",
        transition: `opacity var(--dur-slow) var(--ease-out) ${delay}ms, transform var(--dur-slow) var(--ease-out) ${delay}ms`,
        background: hovered
          ? "linear-gradient(145deg, var(--surface-2), var(--surface-1))"
          : "var(--surface-1)",
        borderColor: hovered ? "var(--accent)" : "var(--hairline)",
        boxShadow: hovered
          ? "var(--shadow-xl), 0 0 30px -8px var(--accent-glow)"
          : "var(--shadow-md)",
        transform: hovered
          ? "translateY(-4px) translateZ(10px)"
          : "translateY(0) translateZ(0)",
        transition: "all var(--dur-base) var(--ease-spring)",
      }}
    >
      {/* Subtle animated background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 20% 20%, var(--accent-soft) 0%, transparent 70%)`,
          opacity: hovered ? 1 : 0.3,
          transition: "opacity var(--dur-base) var(--ease-out)",
        }}
      />

      {/* Check icon with 3D pop */}
      <div
        className="relative w-10 h-10 rounded-xl mb-3 flex items-center justify-center"
        style={{
          background: "var(--positive-soft)",
          border: "1px solid var(--positive-glow)",
          transform: hovered ? "translateZ(20px) scale(1.15) rotate(-5deg)" : "translateZ(0) rotate(0deg)",
          transition: "transform var(--dur-base) var(--ease-spring)",
        }}
      >
        <svg
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--positive)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M20 6 9 17l-5-5" />
        </svg>
      </div>

      <div className="text-xs font-bold text-accent mb-1 relative z-10">{title}</div>
      <div className="text-[11px] text-text-tertiary leading-relaxed relative z-10">{desc}</div>

      {/* Corner accent */}
      <div
        className="absolute top-3 right-3 w-6 h-6 rounded-tr-xl pointer-events-none"
        style={{
          background: "linear-gradient(135deg, var(--positive-glow), transparent)",
          opacity: hovered ? 1 : 0.4,
          transition: "opacity var(--dur-base) var(--ease-out)",
        }}
      />
    </div>
  );
}