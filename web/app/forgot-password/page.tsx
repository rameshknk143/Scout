"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { forgotStart, forgotReset, resendOtp } from "@/lib/auth-actions";
import { AuthShell, ErrorNote, OtpBoxes, Wordmark } from "@/components/auth-ui";

const RULES = [
  { key: "len", label: "12+ characters", test: (p: string) => p.length >= 12 },
  { key: "upper", label: "Uppercase letter", test: (p: string) => /[A-Z]/.test(p) },
  { key: "lower", label: "Lowercase letter", test: (p: string) => /[a-z]/.test(p) },
  { key: "num", label: "A number", test: (p: string) => /[0-9]/.test(p) },
  { key: "special", label: "A special character", test: (p: string) => /[^A-Za-z0-9]/.test(p) },
];

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [step, setStep] = useState<"email" | "reset" | "done">("email");
  const [email, setEmail] = useState("");
  const [masked, setMasked] = useState("");
  const [mock, setMock] = useState(false);
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  const met = useMemo(() => RULES.map((r) => ({ ...r, ok: r.test(password) })), [password]);
  const pwStrong = met.every((r) => r.ok);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setInterval(() => setCooldown((c) => c - 1), 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  async function start(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const res = await forgotStart(email.trim());
    setBusy(false);
    if (res.ok) {
      setMasked((res as { masked_email?: string }).masked_email || email);
      setMock(Boolean((res as { mock?: boolean }).mock));
      setCooldown(60);
      setStep("reset");
    } else {
      setError(res.error);
    }
  }

  async function reset(e: React.FormEvent) {
    e.preventDefault();
    if (!pwStrong || code.length !== 6) return;
    setError(null);
    setBusy(true);
    const res = await forgotReset({ email: email.trim(), code, new_password: password });
    if (res.ok) {
      setStep("done");
      setTimeout(() => router.push("/login"), 1400);
    } else {
      setError(res.error);
      setBusy(false);
    }
  }

  async function resend() {
    if (cooldown > 0) return;
    setError(null);
    const res = await resendOtp(email.trim(), "reset");
    if (res.ok) { setCooldown(60); setMock(Boolean((res as { mock?: boolean }).mock)); }
    else setError(res.error);
  }

  if (step === "done") {
    return (
      <AuthShell>
        <div className="sv-ok">
          <div className="sv-ok-badge">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M20 6 9 17l-5-5" /></svg>
          </div>
          <h1 style={{ fontSize: "1.35rem", margin: 0 }}>Password updated</h1>
          <p style={{ color: "var(--muted)", margin: 0, fontSize: "0.9rem" }}>Redirecting you to sign in…</p>
        </div>
      </AuthShell>
    );
  }

  if (step === "reset") {
    return (
      <AuthShell>
        <div className="sv-auth-head">
          <Wordmark />
          <h1>Reset your password</h1>
          <p>Enter the code sent to <b style={{ color: "var(--text)" }}>{masked}</b> and choose a new password.</p>
        </div>
        {mock && <div className="sv-note">Dev mode: email delivery isn&apos;t configured. If this email has an account, the code is in the API server logs.</div>}
        {error && <ErrorNote>{error}</ErrorNote>}
        <form onSubmit={reset}>
          <OtpBoxes value={code} onChange={setCode} />
          <div className="sv-field">
            <label htmlFor="np">New password</label>
            <div className="sv-inp-wrap">
              <input id="np" type={show ? "text" : "password"} className="sv-inp" autoComplete="new-password" required
                placeholder="Create a strong password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button type="button" className="sv-inp-btn" onClick={() => setShow((s) => !s)}>{show ? "Hide" : "Show"}</button>
            </div>
          </div>
          <div className="sv-reqs">
            {met.map((r) => <span key={r.key} className={`sv-req${r.ok ? " met" : ""}`}><span className="dot" />{r.label}</span>)}
          </div>
          <button type="submit" className="sv-btn sv-btn-primary sv-btn-block" disabled={busy || !pwStrong || code.length !== 6}>
            {busy ? "Updating…" : "Reset password"}
          </button>
        </form>
        <p className="sv-resend">
          {cooldown > 0 ? <>Resend code in <b style={{ color: "var(--text)" }}>{cooldown}s</b></> : <button className="sv-linkbtn" onClick={resend}>Resend code</button>}
        </p>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <div className="sv-auth-head">
        <Wordmark />
        <h1>Forgot your password?</h1>
        <p>Enter your email and we&apos;ll send a code to reset it.</p>
      </div>
      {error && <ErrorNote>{error}</ErrorNote>}
      <form onSubmit={start}>
        <div className="sv-field">
          <label htmlFor="email">Email address</label>
          <input id="email" type="email" className="sv-inp" autoComplete="email" required placeholder="you@example.com"
            value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <button type="submit" className="sv-btn sv-btn-primary sv-btn-block" disabled={busy || !email}>
          {busy ? "Sending…" : "Send reset code"}
        </button>
      </form>
      <p className="sv-auth-alt"><Link href="/login">Back to sign in</Link></p>
    </AuthShell>
  );
}
