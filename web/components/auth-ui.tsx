"use client";

import Link from "next/link";
import { useRef } from "react";

export function Wordmark() {
  return (
    <Link href="/" className="sv-mark" style={{ justifyContent: "center" }}>
      <span className="sv-mark-dot" />
      Scout<b>Veda</b>
    </Link>
  );
}

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="sv-page">
      <div className="sv-bg" aria-hidden />
      <div className="sv-auth">
        <div className="sv-glass sv-auth-card">{children}</div>
      </div>
    </div>
  );
}

/** "Continue with Google" — sends the visitor to Google's own consent screen.
    ScoutVeda never sees a Google password; the backend exchanges the returned
    code for an identity server-side. Renders nothing if Google sign-in isn't
    configured yet, rather than showing a button that would just fail. */
export function GoogleButton() {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  if (!clientId) return null;

  function handleClick() {
    const redirectUri = `${window.location.origin}/auth/google/callback`;
    const url = new URL("https://accounts.google.com/o/oauth2/v2/auth");
    url.searchParams.set("client_id", clientId!);
    url.searchParams.set("redirect_uri", redirectUri);
    url.searchParams.set("response_type", "code");
    url.searchParams.set("scope", "openid email profile");
    url.searchParams.set("access_type", "online");
    url.searchParams.set("prompt", "select_account");
    window.location.href = url.toString();
  }

  return (
    <>
      <div className="sv-auth-divider"><span>or</span></div>
      <button type="button" className="sv-btn sv-btn-ghost sv-btn-block" onClick={handleClick}>
        <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden style={{ flex: "none" }}>
          <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 8 3l5.7-5.7C34.6 6.1 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.6-.4-3.5z" />
          <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.5 15.9 18.9 13 24 13c3.1 0 5.8 1.1 8 3l5.7-5.7C34.6 6.1 29.6 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
          <path fill="#4CAF50" d="M24 44c5.5 0 10.4-1.9 14.3-5.1l-6.6-5.6C29.6 34.9 26.9 36 24 36c-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.6 39.6 16.3 44 24 44z" />
          <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.2 4.2-4.1 5.6l6.6 5.6C40.9 36.5 44 30.9 44 24c0-1.3-.1-2.6-.4-3.5z" />
        </svg>
        Continue with Google
      </button>
    </>
  );
}

export function ErrorNote({ children }: { children: React.ReactNode }) {
  return (
    <div className="sv-error" role="alert">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flex: "none", marginTop: 1 }}>
        <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
      </svg>
      <span>{children}</span>
    </div>
  );
}

/** Six-digit OTP input with auto-advance, backspace, and paste support. */
export function OtpBoxes({
  value,
  onChange,
  onComplete,
}: {
  value: string;
  onChange: (v: string) => void;
  onComplete?: (v: string) => void;
}) {
  const refs = useRef<(HTMLInputElement | null)[]>([]);
  const digits = value.padEnd(6, " ").slice(0, 6).split("");

  function setAt(i: number, d: string) {
    const next = (value.padEnd(6, " ").slice(0, 6).split("").map((c, idx) => (idx === i ? d : c)).join("").replace(/ /g, ""));
    onChange(next);
    if (d && i < 5) refs.current[i + 1]?.focus();
    if (next.length === 6) onComplete?.(next);
  }

  return (
    <div className="sv-otp">
      {digits.map((d, i) => (
        <input
          key={i}
          ref={(el) => { refs.current[i] = el; }}
          inputMode="numeric"
          maxLength={1}
          aria-label={`Digit ${i + 1}`}
          value={d.trim()}
          onChange={(e) => {
            const v = e.target.value.replace(/\D/g, "").slice(-1);
            setAt(i, v);
          }}
          onKeyDown={(e) => {
            if (e.key === "Backspace" && !digits[i].trim() && i > 0) refs.current[i - 1]?.focus();
          }}
          onPaste={(e) => {
            e.preventDefault();
            const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
            if (pasted) { onChange(pasted); if (pasted.length === 6) onComplete?.(pasted); else refs.current[pasted.length]?.focus(); }
          }}
        />
      ))}
    </div>
  );
}
