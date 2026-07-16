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
