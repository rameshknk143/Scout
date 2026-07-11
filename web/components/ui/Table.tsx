import type { ReactNode } from "react";
import EmptyState from "./EmptyState";
import LoadingPanel from "./LoadingPanel";

// Generic data table — the shared `.glass-panel` table shell that was
// previously hand-rolled 4x across trend-radar-client.tsx and
// watchlist-client.tsx. Column-config driven so every page defines *what*
// to show, never *how* the table looks.
export type Column<T> = {
  key: string;
  header: string;
  render: (row: T, index?: number) => ReactNode;
  headerClassName?: string;
  cellClassName?: string;
};

export default function Table<T>({
  columns,
  rows,
  rowKey,
  loading,
  loadingText = "Loading…",
  emptyText = "Nothing here yet.",
}: {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  loading?: boolean;
  loadingText?: string;
  emptyText?: string;
}) {
  if (loading) return <LoadingPanel text={loadingText} />;
  if (!rows.length) return <EmptyState text={emptyText} />;

  return (
    <div className="glass-panel overflow-hidden overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-muted text-[10px] tracking-wider uppercase border-b border-white/5">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 ${col.headerClassName ?? ""}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={rowKey(row)} className="border-b border-white/5 last:border-0 hover:bg-white/[0.015] transition-colors">
              {columns.map((col) => (
                <td key={col.key} className={`px-4 py-3 ${col.cellClassName ?? ""}`}>
                  {col.render(row, index)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
