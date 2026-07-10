"use client";

import PremiumLanding from "@/components/PremiumLanding";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function LoginForm() {
  const searchParams = useSearchParams();
  const from = searchParams.get("from") || "/";

  return (
    <PremiumLanding from={from} />
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-bg flex items-center justify-center text-muted text-sm">Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
}