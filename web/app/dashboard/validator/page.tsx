import { Suspense } from "react";
import ValidatorClient from "./validator-client";

export default function ValidatorPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-white font-sans">Product Sourcing Validator</h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">
        Audit ASIN suitability, margin structure, and operational fit for new product private labeling.
      </p>
      <Suspense fallback={<div className="text-xs text-zinc-400 font-semibold animate-pulse">Loading validator...</div>}>
        <ValidatorClient />
      </Suspense>
    </div>
  );
}
