import ProfitCalculatorClient from "./profit-calculator-client";

export default function ProfitCalculatorPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-900 font-sans">Profit & Amazon Fees Calculator</h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">
        Calculate exact Amazon India category referral fees, closing fees, logistics costs, and GST to audit net profit margins.
      </p>
      <ProfitCalculatorClient />
    </div>
  );
}
