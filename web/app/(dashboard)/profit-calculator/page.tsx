import ProfitCalculatorClient from "./profit-calculator-client";

export default function ProfitCalculatorPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Profit Calculator</h1>
      <p className="text-muted text-sm mb-6">
        Real Amazon India fees, GST both directions, true net margin.
      </p>
      <ProfitCalculatorClient />
    </div>
  );
}
