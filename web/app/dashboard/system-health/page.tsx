import { Suspense } from "react";
import { api } from "@/lib/api";
import SystemHealthClient from "./system-health-client";

// Live ops data -- never statically prerendered (same reason as every other
// data page here: the build must not race the Render API).
export const dynamic = "force-dynamic";

async function SystemHealthData() {
  const [status, pipelines] = await Promise.all([
    api.opsStatus().catch(() => null),
    api.pipelines().catch(() => null),
  ]);
  return <SystemHealthClient status={status} pipelines={pipelines} />;
}

export default function SystemHealthPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-900 font-sans">
        System Health
      </h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">
        The scraping platform behind your data: phone tunnel, VM, pipelines, and alerts — live.
      </p>
      <Suspense
        fallback={<div className="text-muted text-sm">Loading system status...</div>}
      >
        <SystemHealthData />
      </Suspense>
    </div>
  );
}
