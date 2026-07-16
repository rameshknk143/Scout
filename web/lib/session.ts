import { createHmac } from "crypto";

/**
 * Per-user session token: `uid.issuedAt.signature`, where the signature is
 * HMAC-SHA256 of `uid.issuedAt` keyed by SESSION_SECRET. This replaces the old
 * single-shared-password token so each account gets its own signed session.
 *
 * Kept string-only (no Buffer/base64) to match the runtime the existing
 * middleware already relies on. Fails closed: no secret ⇒ nothing verifies.
 */

const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

function secret(): string {
  // SESSION_SECRET is preferred; fall back to SITE_PASSWORD so existing
  // deployments keep a working signing key until SESSION_SECRET is set.
  return process.env.SESSION_SECRET || process.env.SITE_PASSWORD || "";
}

function sign(payload: string): string {
  return createHmac("sha256", secret()).update(payload).digest("hex");
}

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export function createSessionToken(userId: number): string {
  const payload = `${userId}.${Date.now()}`;
  return `${payload}.${sign(payload)}`;
}

export function verifySessionToken(token: string | undefined): { uid: number } | null {
  if (!token || !secret()) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [uid, iat, sig] = parts;
  if (!safeEqual(sig, sign(`${uid}.${iat}`))) return null;
  const issued = Number(iat);
  const userId = Number(uid);
  if (!Number.isInteger(userId) || userId <= 0) return null;
  if (!Number.isFinite(issued) || Date.now() - issued > MAX_AGE_MS || Date.now() - issued < 0) return null;
  return { uid: userId };
}

export const SESSION_COOKIE = "scout_auth";
export const SESSION_MAX_AGE_SECONDS = MAX_AGE_MS / 1000;
