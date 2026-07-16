"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { login } from "@/lib/auth-actions";
import { AuthShell, ErrorNote, Wordmark } from "@/components/auth-ui";

function LoginCard() {
  const router = useRouter();
  const params = useSearchParams();
  const from = params.get("from") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const res = await login({ email: email.trim(), password });
    if (res.ok) {
      router.push(from.startsWith("/") ? from : "/dashboard");
    } else {
      setError(res.error);
      setBusy(false);
    }
  }

  return (
    <>
      <div className="sv-auth-head">
        <Wordmark />
        <h1>Welcome back</h1>
        <p>Sign in to continue your product research.</p>
      </div>

      {error && <ErrorNote>{error}</ErrorNote>}

      <form onSubmit={submit}>
        <div className="sv-field">
          <label htmlFor="email">Email address</label>
          <input id="email" type="email" autoComplete="email" required className="sv-inp"
            placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>

        <div className="sv-field">
          <label htmlFor="password">Password</label>
          <div className="sv-inp-wrap">
            <input id="password" type={show ? "text" : "password"} autoComplete="current-password" required
              className="sv-inp" placeholder="••••••••••••" value={password}
              onChange={(e) => setPassword(e.target.value)} />
            <button type="button" className="sv-inp-btn" onClick={() => setShow((s) => !s)}
              aria-label={show ? "Hide password" : "Show password"}>{show ? "Hide" : "Show"}</button>
          </div>
          <div style={{ textAlign: "right", marginTop: 8 }}>
            <Link href="/forgot-password" style={{ color: "var(--sv-teal)", fontSize: "0.8rem", textDecoration: "none", fontWeight: 600 }}>
              Forgot password?
            </Link>
          </div>
        </div>

        <button type="submit" className="sv-btn sv-btn-primary sv-btn-block" disabled={busy || !email || !password}>
          {busy ? "Signing in…" : "Log in"}
        </button>
      </form>

      <p className="sv-auth-alt">New to ScoutVeda? <Link href="/signup">Create an account</Link></p>
    </>
  );
}

export default function LoginPage() {
  return (
    <AuthShell>
      <Suspense fallback={null}>
        <LoginCard />
      </Suspense>
    </AuthShell>
  );
}
