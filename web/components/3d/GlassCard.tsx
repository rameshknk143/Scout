"use client";

// GlassCard -- frosted-glass surface used for every panel on the System
// Health page. Pulls together the tokens that already exist in globals.css
// (.sv-glass, .layer-middle) so the look is consistent with the public
// landing without copy-pasting styles.

import { forwardRef } from "react";

type Props = {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  /** Higher = more depth. "middle" raises the card; "high" raises more. */
  depth?: "base" | "middle" | "high" | "top";
};

const DEPTH = {
  base: "layer-base",
  middle: "layer-middle",
  high: "layer-high",
  top: "layer-top",
} as const;

const GlassCard = forwardRef<HTMLDivElement, Props>(function GlassCard(
  { title, subtitle, children, className = "", depth = "middle" },
  ref
) {
  return (
    <div
      ref={ref}
      className={`sv-glass ${DEPTH[depth]} p-4 ${className}`}
      style={{
        transformStyle: "preserve-3d",
        // perspective on the parent lets child translateZ read as depth, not
        // as scale. The dashboard's main element has perspective too, but
        // declaring it here makes the card survive being moved around.
        perspective: "1200px",
      }}
    >
      {(title || subtitle) && (
        <div className="mb-3">
          {title && (
            <h2 className="text-xs font-bold uppercase tracking-wide text-zinc-500">
              {title}
            </h2>
          )}
          {subtitle && (
            <p className="text-[11px] text-zinc-400 mt-0.5">{subtitle}</p>
          )}
        </div>
      )}
      {children}
    </div>
  );
});

export default GlassCard;
