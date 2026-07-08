"use client";

import { AnimatePresence, motion } from "framer-motion";
import type { ReactNode } from "react";

// Tab nav + animated underline + fade/slide panel transition, extracted from
// trend-radar-client.tsx (the only page that had it, hand-rolled). Any future
// tabbed page (Listing Optimization variants, Review Miner views, ...) reuses
// this instead of re-implementing the layoutId underline dance.
export type Tab = { key: string; label: string };

export default function Tabs({
  tabs,
  active,
  onChange,
  children,
  layoutId = "tab-underline",
}: {
  tabs: Tab[];
  active: string;
  onChange: (key: string) => void;
  children: ReactNode;
  // Override when a page ever renders more than one Tabs instance at once,
  // so the shared-layout animation doesn't jump between them.
  layoutId?: string;
}) {
  return (
    <div>
      <div className="flex gap-1 mb-4 border-b border-white/8">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => onChange(key)}
            className={`relative px-4 py-2.5 text-sm font-medium transition-colors ${
              active === key ? "text-amber" : "text-muted hover:text-text"
            }`}
          >
            {label}
            {active === key && (
              <motion.div
                layoutId={layoutId}
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber"
              />
            )}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={active}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.2 }}
        >
          {children}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
