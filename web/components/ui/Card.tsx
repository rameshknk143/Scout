"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

// Generalized glass-panel card with the same fade/slide-in entrance already
// used ad hoc for the Validator/Profit Calculator result panels. StatCard
// keeps its own definition (small, stable, not worth touching) — this is for
// every other "put a glass panel here" spot.
export default function Card({
  children,
  className = "",
  delay = 0,
  animate = true,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  animate?: boolean;
}) {
  if (!animate) {
    return <div className={`glass-panel p-6 ${className}`}>{children}</div>;
  }
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay }}
      className={`glass-panel p-6 ${className}`}
    >
      {children}
    </motion.div>
  );
}
