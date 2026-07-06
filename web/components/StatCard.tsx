"use client";

import { motion } from "framer-motion";

export default function StatCard({
  label,
  value,
  hint,
  delay = 0,
}: {
  label: string;
  value: string | number;
  hint?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="glass-panel p-5"
    >
      <div className="text-xs uppercase tracking-wide text-muted mb-2">
        {label}
      </div>
      <div className="text-3xl font-bold text-amber amber-glow-text">
        {value}
      </div>
      {hint && <div className="text-xs text-muted mt-1">{hint}</div>}
    </motion.div>
  );
}
