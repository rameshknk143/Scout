"use client";

import { useMemo, useState } from "react";
import SeverityBadge from "@/components/SeverityBadge";
import CaveatBox from "@/components/CaveatBox";
import { Table, Select, EmptyState, type Column } from "@/components/ui";
import type { Alert } from "@/lib/api";

const ALERT_TYPE_LABELS: Record<Alert["alert_type"], string> = {
  price_change: "Price change",
  entered_top3: "Entered top 3",
  rank_climbing: "Rank climbing",
  rank_sliding: "Rank sliding",
  review_surge: "Review surge",
  dropped_from_list: "Dropped from list",
};

export default function AlertsClient({ alerts }: { alerts: Alert[] }) {
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");

  const types = useMemo(
    () => Array.from(new Set(alerts.map((a) => a.alert_type))).sort(),
    [alerts]
  );

  const filtered = alerts.filter(
    (a) =>
      (!severityFilter || a.severity === severityFilter) &&
      (!typeFilter || a.alert_type === typeFilter)
  );

  if (!alerts.length) {
    return (
      <EmptyState text="No alerts yet — alerts need at least two nightly collection runs for a watched ASIN before there's anything to compare. Run the Validator on a few ASINs, then check back tomorrow." />
    );
  }

  const columns: Column<Alert>[] = [
    { key: "severity", header: "Severity", render: (a) => <SeverityBadge severity={a.severity} /> },
    { key: "alert_type", header: "Type", render: (a) => ALERT_TYPE_LABELS[a.alert_type], cellClassName: "text-muted" },
    {
      key: "title",
      header: "Product",
      render: (a) => (
        <span className="max-w-sm truncate block" title={a.title ?? a.asin}>
          {a.title ?? a.asin}
        </span>
      ),
    },
    { key: "category", header: "Category", render: (a) => a.category ?? "—", cellClassName: "text-muted" },
    { key: "message", header: "What changed", render: (a) => a.message },
    {
      key: "detected_at",
      header: "Detected",
      render: (a) =>
        new Date(a.detected_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }),
      cellClassName: "text-muted text-xs",
    },
  ];

  return (
    <div className="space-y-4">
      <CaveatBox>
        &quot;Dropped from list&quot; means the ASIN fell out of that category&apos;s top-30 ranked
        page — Scout reads the public bestseller/new-releases list, not live inventory, so it can&apos;t
        tell a real stock-out apart from just losing rank. Treat it as &quot;worth checking,&quot; not confirmed.
      </CaveatBox>

      <div className="flex flex-wrap gap-3">
        <Select
          value={severityFilter}
          onChange={setSeverityFilter}
          placeholder="All severities"
          options={["high", "medium", "low"].map((s) => ({ value: s, label: s }))}
        />
        <Select
          value={typeFilter}
          onChange={setTypeFilter}
          placeholder="All types"
          options={types.map((t) => ({ value: t, label: ALERT_TYPE_LABELS[t] }))}
        />
      </div>

      <Table columns={columns} rows={filtered} rowKey={(a) => `${a.asin}-${a.alert_type}-${a.detected_at}`} />

      <div className="text-xs text-muted">
        {filtered.length} of {alerts.length} alerts shown.
      </div>
    </div>
  );
}
