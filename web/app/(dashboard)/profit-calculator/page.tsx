import ProfitCalculatorClient from "./profit-calculator-client";

export default function ProfitCalculatorPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-950">Profit & Amazon Fees Calculator</h1>
      <p className="text-zinc-500 text-xs font-medium mt-1 mb-6">
        Calculate exact Amazon India category referral fees, closing fees, logistics costs, and GST to audit net profit margins.
      </p>
      <ProfitCalculatorClient />
    </div>
  );
}
