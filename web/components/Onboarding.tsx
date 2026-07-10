"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function OnboardingPage() {
  const router = useRouter();

  useEffect(() => {
    // Navigation effect - in real app this would come from auth state
  }, []);

  return (
    <div className="flex min-h-screen justify-center items-center bg-bg">
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="text-center space-y-8 max-w-xl px-4"
      >
        <div className="flex justify-center">
          <span className="text-4xl">🔭</span>
        </div>
        
        <motion.h1
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-6xl md:text-7xl font-extrabold text-text tracking-tight"
        >
          Scout
        </motion.h1>
        
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.35 }}
          className="text-base md:text-lg text-muted leading-relaxed"
        >
          Personal product-intelligence radar for Amazon India sellers.
          Discover winning products, track market trends, and make data-driven decisions.
        </motion.p>
        
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="pt-4"
        >
          <button
            className="btn-primary"
            onClick={() => router.push("/")}
          >
            Get Started
          </button>
        </motion.div>
        
        <div className="text-xs text-muted/50 pt-8">
          Version 1.0 • © 2026 KNK Enterprises
        </div>
      </motion.div>
    </div>
  );
}