"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

// ==================== Type Definitions ====================

interface ScraperStatus {
  timestamp: string;
  database: {
    total_rows: number;
    unique_asins: number;
    categories: number;
    date_range: {
      oldest: string | null;
      newest: string | null;
    };
    coverage: {
      subcategory_pct: number;
      brand_pct: number;
      price_pct: number;
      rating_pct: number;
      source_pct: number;
    };
  };
  throughput: {
    daily_average: number;
    weekly_projected: number;
    monthly_projected: number;
    days_to_2m: number;
    last_7_days: Array<{
      date: string;
      rows: number;
      asins: number;
      categories: number;
    }>;
  };
  top_categories: Array<{
    category: string;
    rows: number;
    asins: number;
  }>;
  sources: Array<{
    source: string;
    count: number;
  }>;
  scrapers: {
    github_actions: Record<string, {
      status: string;
      schedule: string;
      workers: number;
      autonomous: boolean;
      level: number;
    }>;
    oracle_vm: Record<string, {
      status: string;
      schedule: string;
      workers: number;
      autonomous: boolean;
      level: number;
      issue?: string;
    }>;
    laptop: Record<string, {
      status: string;
      schedule: string;
      autonomous: boolean;
      level: number;
      dependencies?: string[];
    }>;
  };
  summary: {
    total_scrapers: number;
    active_scheduled: number;
    fully_autonomous: number;
    requires_intervention: number;
    estimated_daily_growth: number;
    health_score: string;
  };
}

// ==================== Status Badge Component ====================

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: "bg-green-100 text-green-700 border-green-200",
    deployed: "bg-blue-100 text-blue-700 border-blue-200",
    intermittent: "bg-yellow-100 text-yellow-700 border-yellow-200",
    "semi-active": "bg-orange-100 text-orange-700 border-orange-200",
    offline: "bg-red-100 text-red-700 border-red-200",
  };
  
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full border ${colors[status] || "bg-gray-100 text-gray-700 border-gray-200"}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

// ==================== Main Component ====================

export default function ScraperStatusClient() {
  const [data, setData] = useState<ScraperStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const result = await api.scraper_status();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch scraper status");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-sm text-zinc-500">Loading scraper status...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Data</h3>
        <p className="text-sm text-red-600">{error || "Failed to load scraper status"}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-zinc-900">Scraper Infrastructure Status</h2>
            <p className="text-sm text-zinc-500 mt-1">
              Last updated: {new Date(data.timestamp).toLocaleString()}
            </p>
          </div>
          <div className={`px-4 py-2 rounded-lg font-semibold ${
            data.summary.health_score === "good" 
              ? "bg-green-100 text-green-700" 
              : "bg-yellow-100 text-yellow-700"
          }`}>
            {data.summary.health_score === "good" ? "✓ HEALTHY" : "⚠ NEEDS ATTENTION"}
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="p-4 rounded-lg bg-indigo-50 border border-indigo-100">
            <div className="text-2xl font-bold text-indigo-700">{data.database.total_rows.toLocaleString()}</div>
            <div className="text-xs text-indigo-600 font-medium mt-1">Total Rows</div>
          </div>
          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-100">
            <div className="text-2xl font-bold text-emerald-700">{data.throughput.daily_average.toLocaleString()}</div>
            <div className="text-xs text-emerald-600 font-medium mt-1">Rows/Day Average</div>
          </div>
          <div className="p-4 rounded-lg bg-amber-50 border border-amber-100">
            <div className="text-2xl font-bold text-amber-700">{data.summary.fully_autonomous}</div>
            <div className="text-xs text-amber-600 font-medium mt-1">Autonomous Scrapers</div>
          </div>
          <div className="p-4 rounded-lg bg-purple-50 border border-purple-100">
            <div className="text-2xl font-bold text-purple-700">{data.throughput.days_to_2m}</div>
            <div className="text-xs text-purple-600 font-medium mt-1">Days to 2M</div>
          </div>
        </div>
      </div>

      {/* Scraper Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* GitHub Actions Scrapers */}
        <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-zinc-900 mb-4 flex items-center">
            <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
            GitHub Actions Scrapers
          </h3>
          <div className="space-y-3">
            {Object.entries(data.scrapers.github_actions).map(([name, config]) => (
              <div key={name} className="flex items-center justify-between p-3 rounded-lg bg-zinc-50 border border-zinc-100">
                <div>
                  <div className="font-medium text-zinc-900">{name.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</div>
                  <div className="text-xs text-zinc-500 mt-1">
                    {config.schedule} • {config.workers} workers
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={config.status} />
                  {config.autonomous && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                      Autonomous
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Oracle VM Scrapers */}
        <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-zinc-900 mb-4 flex items-center">
            <span className="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>
            Oracle VM Scrapers
          </h3>
          <div className="space-y-3">
            {Object.entries(data.scrapers.oracle_vm).map(([name, config]) => (
              <div key={name} className="p-3 rounded-lg bg-zinc-50 border border-zinc-100">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-zinc-900">{name.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</div>
                  <StatusBadge status={config.status} />
                </div>
                <div className="text-xs text-zinc-500 mt-1">
                  {config.schedule} • {config.workers} worker{config.workers > 1 ? "s" : ""}
                </div>
                {config.issue && (
                  <div className="text-xs text-amber-600 mt-1 flex items-center">
                    <span className="mr-1">⚠</span>
                    {config.issue}
                  </div>
                )}
                {config.autonomous && (
                  <div className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full mt-2 inline-block">
                    Level {config.level} - Self-recovering
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Laptop Scrapers */}
        <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-zinc-900 mb-4 flex items-center">
            <span className="w-2 h-2 rounded-full bg-gray-500 mr-2"></span>
            Local Scrapers
          </h3>
          <div className="space-y-3">
            {Object.entries(data.scrapers.laptop).map(([name, config]) => (
              <div key={name} className="p-3 rounded-lg bg-zinc-50 border border-zinc-100">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-zinc-900">{name.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</div>
                  <StatusBadge status={config.status} />
                </div>
                <div className="text-xs text-zinc-500 mt-1">
                  {config.schedule}
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {(config.dependencies || []).map((dep) => (
                    <span key={dep} className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">
                      Requires: {dep.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
                {!config.autonomous && (
                  <div className="text-xs text-red-600 mt-1">
                    ⚠ Not autonomous - needs manual intervention
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Database Stats */}
        <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-zinc-900 mb-4">Database Statistics</h3>
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b border-zinc-100">
              <span className="text-zinc-600">Total Rows</span>
              <span className="font-semibold">{data.database.total_rows.toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-zinc-100">
              <span className="text-zinc-600">Unique ASINs</span>
              <span className="font-semibold">{data.database.unique_asins.toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-zinc-100">
              <span className="text-zinc-600">Categories Covered</span>
              <span className="font-semibold">{data.database.categories}/32</span>
            </div>
            <div className="flex justify-between py-2 border-b border-zinc-100">
              <span className="text-zinc-600">Date Range</span>
              <span className="font-semibold text-sm">
                {data.database.date_range.oldest?.split("T")[0]} → {data.database.date_range.newest?.split("T")[0]}
              </span>
            </div>
            
            <div className="pt-3">
              <div className="text-sm font-medium text-zinc-700 mb-2">Data Quality</div>
              <div className="space-y-2">
                {[
                  { label: "Source Attribution", value: data.database.coverage.source_pct, color: "bg-blue-500" },
                  { label: "Price Coverage", value: data.database.coverage.price_pct, color: "bg-green-500" },
                  { label: "Rating Coverage", value: data.database.coverage.rating_pct, color: "bg-emerald-500" },
                  { label: "Brand Coverage", value: data.database.coverage.brand_pct, color: "bg-purple-500" },
                  { label: "Subcategory Coverage", value: data.database.coverage.subcategory_pct, color: "bg-amber-500" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="flex items-center gap-3">
                    <span className="text-xs text-zinc-600 w-32">{label}</span>
                    <div className="flex-1 h-2 bg-zinc-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${color} transition-all`}
                        style={{ width: `${value}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium w-12 text-right">{value.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Throughput Projections */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-zinc-900 mb-4">Throughput & Projections</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 rounded-lg bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-100">
            <div className="text-3xl font-bold text-indigo-700">
              {data.throughput.weekly_projected.toLocaleString()}
            </div>
            <div className="text-sm text-indigo-600 font-medium mt-1">Projected This Week</div>
          </div>
          <div className="text-center p-4 rounded-lg bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100">
            <div className="text-3xl font-bold text-emerald-700">
              {data.throughput.monthly_projected.toLocaleString()}
            </div>
            <div className="text-sm text-emerald-600 font-medium mt-1">Projected This Month</div>
          </div>
          <div className="text-center p-4 rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-100">
            <div className="text-3xl font-bold text-amber-700">
              ~{Math.round(data.throughput.monthly_projected / 30).toLocaleString()}/day
            </div>
            <div className="text-sm text-amber-600 font-medium mt-1">Current Daily Rate</div>
          </div>
        </div>
        
        <div className="mt-6 pt-6 border-t border-zinc-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-zinc-600">Days to reach 2,000,000 rows</div>
              <div className="text-2xl font-bold text-zinc-900">{data.throughput.days_to_2m} days</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-zinc-600">Progress</div>
              <div className="text-2xl font-bold text-zinc-900">
                {((data.database.total_rows / 2_000_000) * 100).toFixed(2)}%
              </div>
            </div>
          </div>
          <div className="mt-3 h-3 bg-zinc-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all"
              style={{ width: `${Math.min((data.database.total_rows / 2_000_000) * 100, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-zinc-900 mb-4">Last 7 Days Activity</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200">
                <th className="text-left py-2 px-3 text-zinc-600 font-medium">Date</th>
                <th className="text-right py-2 px-3 text-zinc-600 font-medium">Rows</th>
                <th className="text-right py-2 px-3 text-zinc-600 font-medium">ASINs</th>
                <th className="text-right py-2 px-3 text-zinc-600 font-medium">Categories</th>
              </tr>
            </thead>
            <tbody>
              {data.throughput.last_7_days.map((row, i) => (
                <tr key={i} className="border-b border-zinc-100 hover:bg-zinc-50">
                  <td className="py-2 px-3 text-zinc-900">{row.date}</td>
                  <td className="py-2 px-3 text-right font-semibold text-zinc-900">{row.rows.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right text-zinc-600">{row.asins.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right text-zinc-600">{row.categories}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Categories */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-zinc-900 mb-4">Top Categories by Volume</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.top_categories.slice(0, 9).map((cat) => (
            <div key={cat.category} className="p-4 rounded-lg bg-zinc-50 border border-zinc-100">
              <div className="font-medium text-zinc-900 text-sm truncate">{cat.category}</div>
              <div className="mt-2 flex justify-between text-xs">
                <span className="text-zinc-600">{cat.rows.toLocaleString()} rows</span>
                <span className="text-zinc-500">{cat.asins.toLocaleString()} ASINs</span>
              </div>
              <div className="mt-2 h-1.5 bg-zinc-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-indigo-500"
                  style={{ width: `${(cat.rows / data.top_categories[0].rows) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
