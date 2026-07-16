"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { signupStart, signupVerify, resendOtp } from "@/lib/auth-actions";
import { AuthShell, ErrorNote, OtpBoxes, Wordmark } from "@/components/auth-ui";

const RULES = [
  { key: "len", label: "12+ characters", test: (p: string) => p.length >= 12 },
  { key: "upper", label: "Uppercase letter", test: (p: string) => /[A-Z]/.test(p) },
  { key: "lower", label: "Lowercase letter", test: (p: string) => /[a-z]/.test(p) },
  { key: "num", label: "A number", test: (p: string) => /[0-9]/.test(p) },
  { key: "special", label: "A special character", test: (p: string) => /[^A-Za-z0-9]/.test(p) },
];

export default function SignupPage() {
  const router = useRouter();
  const [step, setStep] = useState<"form" | "otp" | "done">("form");

  // form state
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [terms, setTerms] = useState(false);
  const [show, setShow] = useState(false);

  // flow state
  const [masked, setMasked] = useState("");
  const [mock, setMock] = useState(false);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  const met = useMemo(() => RULES.map((r) => ({ ...r, ok: r.test(password) })), [password]);
  const pwStrong = met.every((r) => r.ok);
  const canSubmit = fullName.trim() && email.trim() && pwStrong && password === confirm && terms;

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setInterval(() => setCooldown((c) => c - 1), 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  async function start(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) { setError("Passwords don't match."); return; }
    setBusy(true);
    const res = await signupStart({ full_name: fullName.trim(), email: email.trim(), password });
    setBusy(false);
    if (res.ok) {
      setMasked((res as { masked_email?: string }).masked_email || email);
      setMock(Boolean((res as { mock?: boolean }).mock));
      setCooldown(60);
      setStep("otp");
    } else {
      setError(res.error);
    }
  }

  async function verify(v?: string) {
    const c = v ?? code;
    if (c.length !== 6) return;
    setError(null);
    setBusy(true);
    const res = await signupVerify({ email: email.trim(), code: c });
    if (res.ok) {
      setStep("done");
      setTimeout(() => router.push("/dashboard"), 1400);
    } else {
      setError(res.error);
      setBusy(false);
    }
  }

  async function resend() {
    if (cooldown > 0) return;
    setError(null);
    const res = await resendOtp(email.trim(), "signup");
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
          <h1 style={{ fontSize: "1.35rem", margin: 0 }}>You&apos;re all set</h1>
          <p style={{ color: "var(--muted)", margin: 0, fontSize: "0.9rem" }}>Taking you to your dashboard…</p>
        </div>
      </AuthShell>
    );
  }

  if (step === "otp") {
    return (
      <AuthShell>
        <div className="sv-auth-head">
          <Wordmark />
          <h1>Verify your email</h1>
          <p>We sent a verification code to <b style={{ color: "var(--text)" }}>{masked}</b>.</p>
        </div>
        {mock && <div className="sv-note">Dev mode: email delivery isn&apos;t configured, so no real email was sent. Check the API server logs for the code.</div>}
        {error && <ErrorNote>{error}</ErrorNote>}
        <OtpBoxes value={code} onChange={setCode} onComplete={(v) => verify(v)} />
        <button className="sv-btn sv-btn-primary sv-btn-block" disabled={busy || code.length !== 6} onClick={() => verify()}>
          {busy ? "Verifying…" : "Verify and create account"}
        </button>
        <p className="sv-resend">
          {cooldown > 0
            ? <>Resend code in <b style={{ color: "var(--text)" }}>{cooldown}s</b></>
            : <button className="sv-linkbtn" onClick={resend}>Resend code</button>}
        </p>
        <p className="sv-auth-alt">
          <button className="sv-linkbtn" onClick={() => { setStep("form"); setCode(""); setError(null); }}>Use a different email</button>
        </p>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <div className="sv-auth-head">
        <Wordmark />
        <h1>Create your ScoutVeda account</h1>
        <p>Start researching products in minutes.</p>
      </div>
      {error && <ErrorNote>{error}</ErrorNote>}
      <form onSubmit={start}>
        <div className="sv-field">
          <label htmlFor="name">Full name</label>
          <input id="name" className="sv-inp" autoComplete="name" required placeholder="Ramesh K"
            value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </div>
        <div className="sv-field">
          <label htmlFor="email">Email address</label>
          <input id="email" type="email" className="sv-inp" autoComplete="email" required placeholder="you@example.com"
            value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="sv-field">
          <label htmlFor="pw">Password</label>
          <div className="sv-inp-wrap">
            <input id="pw" type={show ? "text" : "password"} className="sv-inp" autoComplete="new-password" required
              placeholder="Create a strong password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <button type="button" className="sv-inp-btn" onClick={() => setShow((s) => !s)}>{show ? "Hide" : "Show"}</button>
          </div>
        </div>
        <div className="sv-reqs">
          {met.map((r) => (
            <span key={r.key} className={`sv-req${r.ok ? " met" : ""}`}>
              <span className="dot" />{r.label}
            </span>
          ))}
        </div>
        <div className="sv-field">
          <label htmlFor="confirm">Confirm password</label>
          <input id="confirm" type={show ? "text" : "password"} className="sv-inp" autoComplete="new-password" required
            placeholder="Re-enter your password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          {confirm && confirm !== password && (
            <span style={{ color: "var(--red)", fontSize: "0.75rem", marginTop: 6, display: "block" }}>Passwords don&apos;t match.</span>
          )}
        </div>
        <label style={{ display: "flex", gap: 10, alignItems: "flex-start", fontSize: "0.82rem", color: "var(--muted)", margin: "4px 0 18px", cursor: "pointer" }}>
          <input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} style={{ marginTop: 2, accentColor: "var(--sv-teal)" }} />
          <span>I agree to the <a href="#" style={{ color: "var(--sv-teal)" }}>Terms</a> and <a href="#" style={{ color: "var(--sv-teal)" }}>Privacy Policy</a>.</span>
        </label>
        <button type="submit" className="sv-btn sv-btn-primary sv-btn-block" disabled={busy || !canSubmit}>
          {busy ? "Sending code…" : "Continue"}
        </button>
      </form>
      <p className="sv-auth-alt">Already have an account? <Link href="/login">Log in</Link></p>
    </AuthShell>
  );
}
