"use client";

import { useEffect, useRef, useState } from "react";

interface FeatureCard3DProps {
  title: string;
  desc: string;
  icon: string;
  delay?: number;
  className?: string;
}

export function FeatureCard3D({
  title,
  desc,
  icon,
  delay = 0,
  className = "",
}: FeatureCard3DProps) {
  const [visible, setVisible] = useState(false);
  const [hovered, setHovered] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = cardRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * 8;
    const rotateY = ((centerX - x) / centerX) * 8;
    cardRef.current!.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(20px)`;
  };

  const handleMouseLeave = () => {
    cardRef.current!.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)";
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={`sv-glass p-6 rounded-2xl relative overflow-hidden transition-all duration-500 ${className}`}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(30px)",
        transition: `opacity var(--dur-slow) var(--ease-out) ${delay}ms, transform var(--dur-slow) var(--ease-out) ${delay}ms`,
        boxShadow: hovered
          ? "var(--shadow-xl), 0 0 40px -10px var(--accent-glow)"
          : "var(--shadow-lg)",
        borderColor: hovered ? "var(--accent)" : "var(--hairline)",
      }}
    >
      {/* Floating background element */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 30% 30%, var(--accent-soft) 0%, transparent 60%)`,
          opacity: hovered ? 1 : 0.5,
          transition: "opacity var(--dur-base) var(--ease-out)",
        }}
      />

      {/* Icon with 3D depth */}
      <div
        className="relative flex items-center justify-center w-14 h-14 rounded-xl mb-4"
        style={{
          background: "var(--accent-soft)",
          border: "1px solid var(--accent-glow)",
          transform: hovered ? "translateZ(30px) scale(1.1)" : "translateZ(0)",
          transition: "transform var(--dur-base) var(--ease-spring)",
        }}
      >
        <Icon name={icon} className="text-accent" size={28} />
      </div>

      <h3 className="text-lg font-bold text-text-primary mb-2 relative z-10">
        {title}
      </h3>
      <p className="text-text-secondary text-sm leading-relaxed relative z-10">
        {desc}
      </p>

      {/* 3D corner accent */}
      <div
        className="absolute top-4 right-4 w-8 h-8 rounded-tr-2xl pointer-events-none"
        style={{
          background: "linear-gradient(135deg, var(--accent-glow), transparent)",
          opacity: hovered ? 1 : 0.3,
          transition: "opacity var(--dur-base) var(--ease-out)",
        }}
      />
    </div>
  );
}

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  if (name === "search")
    return (
      <svg {...common}>
        <circle cx="11" cy="11" r="7" />
        <path d="m21 21-4.3-4.3" />
      </svg>
    );
  if (name === "shield")
    return (
      <svg {...common}>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
      </svg>
    );
  if (name === "coin")
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v10M9.5 9.5h4a1.5 1.5 0 0 1 0 3h-3a1.5 1.5 0 0 0 0 3h4" />
      </svg>
    );
  return (
    <svg {...common}>
      <path d="M3 17l6-6 4 4 8-8" />
      <path d="M17 7h4v4" />
    </svg>
  );
}