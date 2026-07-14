"use client";

import { useEffect, useState } from "react";

export default function MarketplaceIndicator() {
  const [mkt, setMkt] = useState("amazon.in");

  useEffect(() => {
    const handleSync = () => {
      const stored = localStorage.getItem("selectedMarketplace") || "amazon.in";
      setMkt(stored);
    };

    handleSync();
    window.addEventListener("marketplaceChanged", handleSync);
    return () => window.removeEventListener("marketplaceChanged", handleSync);
  }, []);

  const config: Record<string, { flag: string; name: string }> = {
    "amazon.in": { flag: "🇮🇳", name: "AMAZON.IN" },
    "amazon.com": { flag: "🇺🇸", name: "AMAZON.COM" },
    "amazon.co.uk": { flag: "🇬🇧", name: "AMAZON.CO.UK" },
  };

  const active = config[mkt] || config["amazon.in"];

  return (
    <span className="hidden md:inline-flex items-center gap-1.5 text-[10px] font-bold text-zinc-300 bg-[#111625] border border-white/5 px-2 py-1 rounded font-mono uppercase tracking-wider">
      {active.flag} {active.name}
    </span>
  );
}
