"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { googleLogin } from "@/lib/auth-actions";
import { GOOGLE_OAUTH_STATE_KEY, GOOGLE_OAUTH_NONCE_KEY } from "@/components/auth-ui";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("exchanging"); // "exchanging" | "success" | "error"
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    const returnedState = searchParams.get("state");
    const deniedReason = searchParams.get("error"); // e.g. "access_denied" if the visitor cancelled

    // Read-then-clear immediately: these are single-use, and clearing them
    // right away means a replayed/reloaded callback URL can't reuse them.
    const expectedState = sessionStorage.getItem(GOOGLE_OAUTH_STATE_KEY);
    const nonce = sessionStorage.getItem(GOOGLE_OAUTH_NONCE_KEY) || undefined;
    sessionStorage.removeItem(GOOGLE_OAUTH_STATE_KEY);
    sessionStorage.removeItem(GOOGLE_OAUTH_NONCE_KEY);

    if (deniedReason) {
      setStatus("error");
      setErrorMsg("Google sign-in was cancelled.");
      return;
    }
    if (!code) {
      setStatus("error");
      setErrorMsg("Missing authorization code from Google.");
      return;
    }
    // CSRF guard: this callback must be the direct continuation of a sign-in
    // this same browser tab started -- reject anything else before it ever
    // reaches the network.
    if (!expectedState || returnedState !== expectedState) {
      setStatus("error");
      setErrorMsg("This sign-in link is invalid or expired. Please try again.");
      return;
    }

    const finish = async () => {
      try {
        // Must be byte-identical to the redirect_uri used to request this code.
        const redirect_uri = `${window.location.origin}/auth/google/callback`;
        const res = await googleLogin({ code, redirect_uri, nonce });
        if (!res.ok) throw new Error(res.error);
        setStatus("success");
        setTimeout(() => router.push("/dashboard"), 1200);
      } catch (err: any) {
        setStatus("error");
        setErrorMsg(err.message || "Couldn't complete Google sign-in.");
      }
    };

    finish();
  }, [searchParams, router]);

  if (status === "exchanging") {
    return (
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <h1 className="text-lg font-bold text-white">Signing you in with Google</h1>
        <p className="text-xs text-zinc-400">Confirming your identity...</p>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="flex flex-col items-center justify-center space-y-4 text-center">
        <div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full flex items-center justify-center text-xl">
          ✓
        </div>
        <h1 className="text-lg font-bold text-white">Signed in!</h1>
        <p className="text-xs text-zinc-400">Taking you to your dashboard...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center space-y-4 max-w-md text-center p-6 bg-slate-900/30 border border-white/5 rounded-2xl backdrop-blur-xl">
      <div className="w-12 h-12 bg-red-500/10 border border-red-500/30 text-red-400 rounded-full flex items-center justify-center text-xl">
        ⚠
      </div>
      <h1 className="text-lg font-bold text-white">Sign-in failed</h1>
      <p className="text-xs text-red-400">{errorMsg}</p>
      <button
        onClick={() => router.push("/login")}
        className="mt-2 text-xs font-semibold bg-white/5 hover:bg-white/10 text-white border border-white/10 px-4 py-2 rounded-lg transition-all cursor-pointer"
      >
        Back to login
      </button>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <div className="min-h-screen bg-[#090d16] flex items-center justify-center p-4">
      <Suspense fallback={<div className="text-xs text-zinc-400 font-mono">Loading...</div>}>
        <CallbackHandler />
      </Suspense>
    </div>
  );
}
