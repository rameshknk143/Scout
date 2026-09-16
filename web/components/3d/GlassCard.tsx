"use client";

import { useEffect, useRef, useState } from "react";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  elevation?: "low" | "medium" | "high";
  delay?: number;
  style?: React.CSSProperties;
}

export function GlassCard({
  children,
  className = "",
  elevation = "medium",
  delay = 0,
  style,
}: GlassCardProps) {
  const [visible, setVisible] = useState(false);
  const [hovered, setHovered] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const elevationStyles = {
    low: {
      boxShadow: "var(--shadow-sm)",
      border: "1px solid var(--hairline)",
    },
    medium: {
      boxShadow: "var(--shadow-lg)",
      border: "1px solid var(--hairline)",
    },
    high: {
      boxShadow: "var(--shadow-xl)",
      border: "1px solid var(--accent-glow)",
    },
  };

  return (
    <div
      ref={cardRef}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={`sv-glass rounded-2xl relative overflow-hidden transition-all duration-500 ${className}`}
      style={{
        ...elevationStyles[elevation],
        opacity: visible ? 1 : 0,
        transition: `opacity var(--dur-slow) var(--ease-out) ${delay}ms, transform var(--dur-slow) var(--ease-out) ${delay}ms, box-shadow var(--dur-base) var(--ease-out), border-color var(--dur-base) var(--ease-out)`,
        boxShadow: hovered
          ? `${elevationStyles[elevation].boxShadow}, 0 0 30px -8px var(--accent-glow)`
          : elevationStyles[elevation].boxShadow,
        borderColor: hovered ? "var(--accent)" : "var(--hairline)",
        transform: !visible
          ? "translateY(20px)"
          : hovered
            ? "translateY(-2px) translateZ(8px)"
            : "translateY(0) translateZ(0)",
        ...style,
      }}
    >
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 20% 20%, var(--accent-soft) 0%, transparent 70%)`,
          opacity: hovered ? 0.8 : 0.4,
          transition: "opacity var(--dur-base) var(--ease-out)",
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
}