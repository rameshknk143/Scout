"use client";

import { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { Table, MiniStat } from "@/components/ui";
import { getListingHealth } from "@/lib/actions";

type AuditedProduct = {
  asin: string;
  title: string;
  score: number;
  verdict: string;
  gaps: string[];
  price: number | null;
};

export default function ListingHealthClient() {
  const [products, setProducts] = useState<AuditedProduct[]>([]);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    startTransition(async () => {
      try {
        const res = await getListingHealth();
        setProducts(res.products);
      } catch (err) {
        console.error("Failed to fetch listing health:", err);
      }
    });
  }, []);

  // Compute metrics
  const totalAudited = products.length;
  const criticalAlerts = products.filter((p) => p.score < 60 || p.gaps.length > 1).length;
  
  const avgQualityScore = totalAudited
    ? products.reduce((acc, p) => acc + p.score, 0) / totalAudited
    : 0;

  const columns = [
    {
      key: "asin",
      header: "ASIN",
      render: (p: AuditedProduct) => (
        <span className="font-mono text-xs font-semibold text-zinc-300 bg-[#181d2c] px-1.5 py-0.5 rounded border border-white/5">
          {p.asin}
        </span>
      ),
    },
    {
      key: "title",
      header: "Product Title",
      render: (p: AuditedProduct) => (
        <span className="font-medium text-white max-w-sm truncate block" title={p.title}>
          {p.title}
        </span>
      ),
    },
    {
      key: "score",
      header: "Listing Quality Score",
      render: (p: AuditedProduct) => (
        <div className="flex items-center gap-3">
          <div className="flex-1 w-20 bg-[#181d2c] rounded-full h-2 overflow-hidden border border-white/5">
            <div
              className={`h-full rounded-full transition-all ${
                p.score >= 80 ? "bg-emerald-500" : p.score >= 60 ? "bg-amber-500" : "bg-red-500"
              }`}
              style={{ width: `${p.score}%` }}
            />
          </div>
          <span className="font-bold text-white shrink-0 font-mono">{p.score}%</span>
        </div>
      ),
    },
    {
      key: "gaps",
      header: "Audited Optimization Gaps",
      render: (p: AuditedProduct) => (
        <div className="flex flex-wrap gap-1.5 max-w-md">
          {p.gaps.map((gap, i) => (
            <span
              key={i}
              className="text-[9px] font-bold text-red-400 bg-red-500/10 border border-red-500/20 px-1.5 py-0.5 rounded"
            >
              ⚠️ {gap}
            </span>
          ))}
          {p.gaps.length === 0 && (
            <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
              ✓ All Checks Passed
            </span>
          )}
        </div>
      ),
    },
    {
      key: "action",
      header: "Action",
      render: (p: AuditedProduct) => (
        <Link
          href={`/listing?asin=${p.asin}`}
          className="text-[10px] font-bold text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-2 py-1 rounded transition-colors"
        >
          Optimize Listing
        </Link>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Metrics Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MiniStat label="Audited Listings" value={totalAudited.toString()} />
        <MiniStat
          label="Average Quality Score"
          value={totalAudited ? `${avgQualityScore.toFixed(1)}%` : "—"}
        />
        <MiniStat
          label="Listing Alerts (Needs Fix)"
          value={criticalAlerts.toString()}
        />
      </div>

      {/* Main Audit Grid */}
      <div className="glass-panel p-5 bg-[#111625]/20 border border-white/5 rounded-xl shadow-sm space-y-4">
        <div className="text-sm font-semibold text-white">Active Audit Logs</div>
        {isPending ? (
          <div className="flex flex-col items-center justify-center py-16 space-y-3">
            <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <div className="text-xs text-zinc-500 font-semibold font-mono">Running listing diagnostics...</div>
          </div>
        ) : (
          <Table
            columns={columns}
            rows={products}
            rowKey={(p) => p.asin}
            emptyText="No listings have been scored yet. Validate an ASIN to log listing health stats!"
          />
        )}
      </div>
    </div>
  );
}
