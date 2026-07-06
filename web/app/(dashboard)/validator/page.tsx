import ValidatorClient from "./validator-client";

export default function ValidatorPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Validator</h1>
      <p className="text-muted text-sm mb-6">
        Paste an ASIN, add a few judgment calls, get a PURSUE / WATCH / SKIP
        scorecard for launching it as a new private-label product.
      </p>
      <ValidatorClient />
    </div>
  );
}
