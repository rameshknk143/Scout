"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { connectAmazonAccount } from "@/lib/actions";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("exchanging"); // "exchanging" | "success" | "error"
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    const code = searchParams.get("spapi_oauth_code") || searchParams.get("code");
    const selling_partner_id = searchParams.get("selling_partner_id");
    const state = searchParams.get("state"); // Contains the marketplace_id

    if (!code || !selling_partner_id) {
      setStatus("error");
      setErrorMsg("Missing authorization code or selling partner ID from Amazon.");
      return;
    }

    const linkAccount = async () => {
      try {
        await connectAmazonAccount({
          code,
          selling_partner_id,
          marketplace_id: state || "A21TJRUUN4KGV",
        });
        setStatus("success");
        setTimeout(() => {
          router.push("/dashboard/settings");
        }, 2000);
      } catch (err: any) {
        setStatus("error");
        setErrorMsg(err.message || "Failed to exchange LWA credentials with Amazon.");
      }
    };

    linkAccount();
  }, [searchParams, router]);

  if (status === "exchanging") {
    return (
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <h1 className="text-lg font-bold text-white">Linking Amazon Account</h1>
        <p className="text-xs text-zinc-400">Exchanging credentials and securing access keys...</p>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="flex flex-col items-center justify-center space-y-4 text-center">
        <div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full flex items-center justify-center text-xl">
          ✓
        </div>
        <h1 className="text-lg font-bold text-white">Account Linked Successfully!</h1>
        <p className="text-xs text-zinc-400">Redirecting you back to settings...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center space-y-4 max-w-md text-center p-6 bg-slate-900/30 border border-white/5 rounded-2xl backdrop-blur-xl">
      <div className="w-12 h-12 bg-red-500/10 border border-red-500/30 text-red-400 rounded-full flex items-center justify-center text-xl">
        ⚠
      </div>
      <h1 className="text-lg font-bold text-white">Connection Failed</h1>
      <p className="text-xs text-red-400">{errorMsg}</p>
      <button
        onClick={() => router.push("/dashboard/settings")}
        className="mt-2 text-xs font-semibold bg-white/5 hover:bg-white/10 text-white border border-white/10 px-4 py-2 rounded-lg transition-all cursor-pointer"
      >
        Return to Settings
      </button>
    </div>
  );
}

export default function AmazonCallbackPage() {
  return (
    <div className="min-h-screen bg-[#090d16] flex items-center justify-center p-4">
      <Suspense fallback={<div className="text-xs text-zinc-400 font-mono">Loading callback data...</div>}>
        <CallbackHandler />
      </Suspense>
    </div>
  );
}
