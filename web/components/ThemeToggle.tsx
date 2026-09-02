"use client";

// ThemeToggle — sun/moon button that flips [data-theme] on <html>.
// Persistence: localStorage("scout-theme") with three values:
//   - "dark"  → forced dark
//   - "light" → forced light
//   - "system" → follows OS preference via media query
//
// We render an inline <script> in the document <head> via the root layout
// so the theme is applied BEFORE the first paint → no flash of wrong colors.

import { useEffect, useState } from "react";

type Mode = "dark" | "light" | "system";

const STORAGE_KEY = "scout-theme";

function readMode(): Mode {
  if (typeof window === "undefined") return "system";
  const v = window.localStorage.getItem(STORAGE_KEY);
  if (v === "dark" || v === "light" || v === "system") return v;
  return "system";
}

function applyMode(mode: Mode) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (mode === "system") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", mode);
  }
}

export function ThemeBootstrapScript() {
  // Inline script that runs in the document <head> before paint.
  // Reads the stored mode and applies it synchronously to avoid a flash.
  const code = `
    (function() {
      try {
        var v = localStorage.getItem('${STORAGE_KEY}');
        if (v === 'dark' || v === 'light') {
          document.documentElement.setAttribute('data-theme', v);
        } else {
          document.documentElement.removeAttribute('data-theme');
        }
      } catch (e) {}
    })();
  `;
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}

export function ThemeToggle() {
  const [mode, setMode] = useState<Mode>("system");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const m = readMode();
    setMode(m);
    setMounted(true);
  }, []);

  function cycle() {
    const next: Mode = mode === "system" ? "dark" : mode === "dark" ? "light" : "system";
    setMode(next);
    if (next === "system") {
      window.localStorage.removeItem(STORAGE_KEY);
    } else {
      window.localStorage.setItem(STORAGE_KEY, next);
    }
    applyMode(next);
  }

  // Don't render anything until mounted — prevents hydration mismatch
  // (server thinks "system", client might have "dark" in localStorage).
  if (!mounted) return null;

  const label =
    mode === "system" ? "Auto theme" : mode === "dark" ? "Dark theme" : "Light theme";
  const Icon =
    mode === "system" ? IconSystem : mode === "dark" ? IconMoon : IconSun;

  return (
    <button
      type="button"
      onClick={cycle}
      aria-label={label}
      title={label}
      style={{
        width: 38,
        height: 38,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        borderRadius: 10,
        background: "var(--surface-2)",
        border: "1px solid var(--hairline)",
        color: "var(--text-secondary)",
        cursor: "pointer",
        transition:
          "background-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out)",
      }}
      onMouseDown={(e) => (e.currentTarget.style.transform = "scale(0.94)")}
      onMouseUp={(e) => (e.currentTarget.style.transform = "scale(1)")}
      onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
    >
      <Icon />
    </button>
  );
}

function IconSun() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

function IconMoon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function IconSystem() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="14" rx="2" />
      <path d="M8 21h8M12 18v3" />
    </svg>
  );
}
