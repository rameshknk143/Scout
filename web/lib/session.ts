/**
 * Per-user session token: `uid.issuedAt.signature`, where the signature is
 * HMAC-SHA256 of `uid.issuedAt` keyed by SESSION_SECRET. Replaces the old
 * single-shared-password token so each account gets its own signed session.
 *
 * Uses the Web Crypto API (globalThis.crypto.subtle) rather than Node's
 * `crypto` module so it runs in BOTH the Edge middleware runtime and Node
 * server actions. That makes signing/verifying async — callers await them.
 * Fails closed: no secret ⇒ nothing verifies.
 */

const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

export const SESSION_COOKIE = "scout_auth";
export const SESSION_MAX_AGE_SECONDS = MAX_AGE_MS / 1000;

function secret(): string {
  return process.env.SESSION_SECRET || process.env.SITE_PASSWORD || "";
}

async function hmacHex(payload: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret()),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(payload));
  return Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function createSessionToken(userId: number): Promise<string> {
  const payload = `${userId}.${Date.now()}`;
  return `${payload}.${await hmacHex(payload)}`;
}

export async function verifySessionToken(
  token: string | undefined
): Promise<{ uid: number } | null> {
  if (!token || !secret()) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [uid, iat, sig] = parts;
  if (!safeEqual(sig, await hmacHex(`${uid}.${iat}`))) return null;
  const issued = Number(iat);
  const userId = Number(uid);
  if (!Number.isInteger(userId) || userId <= 0) return null;
  if (!Number.isFinite(issued) || Date.now() - issued > MAX_AGE_MS || Date.now() - issued < 0) return null;
  return { uid: userId };
}
