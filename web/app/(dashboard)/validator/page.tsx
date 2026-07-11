import ValidatorClient from "./validator-client";

export default function ValidatorPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-950">Product Sourcing Validator</h1>
      <p className="text-zinc-500 text-xs font-medium mt-1 mb-6">
        Audit ASIN suitability, margin structure, and operational fit for new product private labeling.
      </p>
      <ValidatorClient />
    </div>
  );
}
