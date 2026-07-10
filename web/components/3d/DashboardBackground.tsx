"use client";

import { useState, useEffect } from "react";

export default function DashboardBackground() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return null;
}
