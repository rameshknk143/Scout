"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { createSessionToken, SESSION_COOKIE, SESSION_MAX_AGE_SECONDS } from "./session";

/* Server actions for the ScoutVeda account flow. All password checking, OTP
   generation, and validation happen in the FastAPI backend (see api/auth.py);
   these actions call it with the shared server key and, on success, mint a
   signed per-user session cookie. */

const API_URL = process.env.API_URL!;
const API_KEY = process.env.API_KEY!;

type AuthResult<T = Record<string, unknown>> =
  | ({ ok: true } & T)
  | { ok: false; error: string; status?: number };

async function callAuth<T = Record<string, unknown>>(
  path: string,
  body: Record<string, unknown>
): Promise<AuthResult<T>> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "X-Scout-Key": API_KEY, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return { ok: false, error: data?.detail || "Something went wrong. Please try again.", status: res.status };
    }
    return { ok: true, ...(data as T) };
  } catch {
    return { ok: false, error: "Couldn't reach the server. Check your connection and try again." };
  }
}

async function setSession(userId: number) {
  const store = await cookies();
  store.set(SESSION_COOKIE, await createSessionToken(userId), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
  });
}

/* ---- Sign up (email OTP verification, account created only after verify) ---- */
export async function signupStart(input: { full_name: string; email: string; password: string }) {
  return callAuth("/auth/register/start", input);
}

export async function signupVerify(input: { email: string; code: string }) {
  const res = await callAuth<{ user_id: number }>("/auth/register/verify", input);
  if (res.ok) await setSession(res.user_id);
  return res;
}

/* ---- Returning login (email + password only) ---- */
export async function login(input: { email: string; password: string }) {
  const res = await callAuth<{ user_id: number }>("/auth/login", input);
  if (res.ok) await setSession(res.user_id);
  return res;
}

/* ---- Google sign-in (works for both new and returning accounts) ----
   The backend exchanges the code with Google server-side (client secret never
   reaches the browser), verifies the identity token, and get-or-creates the
   account by verified email — no OTP step needed since Google already
   confirmed the address. */
export async function googleLogin(input: { code: string; redirect_uri: string }) {
  const res = await callAuth<{ user_id: number }>("/auth/google", input);
  if (res.ok) await setSession(res.user_id);
  return res;
}

/* ---- Password reset (OTP, never reveals whether the email exists) ---- */
export async function forgotStart(email: string) {
  return callAuth("/auth/password/forgot", { email });
}

export async function forgotReset(input: { email: string; code: string; new_password: string }) {
  return callAuth("/auth/password/reset", input);
}

/* ---- Resend an OTP (server enforces cooldown + hourly cap) ---- */
export async function resendOtp(email: string, purpose: "signup" | "reset") {
  return callAuth("/auth/otp/resend", { email, purpose });
}

export async function logout() {
  const store = await cookies();
  store.delete(SESSION_COOKIE);
  redirect("/login");
}
