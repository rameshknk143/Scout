"use server";

import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";
import { generateToken } from "./auth-token";

export type LoginState = { error?: string } | undefined;

// In-memory brute force protection fallback for local development
const loginAttempts = new Map<string, { count: number; lockUntil: number }>();

export async function login(
  _prevState: LoginState,
  formData: FormData
): Promise<LoginState> {
  const ip = (await headers()).get("x-forwarded-for") || "127.0.0.1";
  const kvUrl = process.env.KV_REST_API_URL;
  const kvToken = process.env.KV_REST_API_TOKEN;
  const hasKV = !!(kvUrl && kvToken);
  const kvKey = `login_attempts:${ip}`;

  let attemptCount = 0;
  let lockUntil = 0;

  if (hasKV) {
    try {
      const res = await fetch(`${kvUrl}/get/${kvKey}`, {
        headers: { Authorization: `Bearer ${kvToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        if (data.result) {
          const parsed = JSON.parse(data.result);
          attemptCount = parsed.count || 0;
          lockUntil = parsed.lockUntil || 0;
        }
      }
    } catch {
      // Fallback to local memory on KV failure
      const attempt = loginAttempts.get(ip);
      if (attempt) {
        attemptCount = attempt.count;
        lockUntil = attempt.lockUntil;
      }
    }
  } else {
    const attempt = loginAttempts.get(ip);
    if (attempt) {
      attemptCount = attempt.count;
      lockUntil = attempt.lockUntil;
    }
  }

  // Check if IP is currently locked out
  if (lockUntil > Date.now()) {
    const minutesLeft = Math.ceil((lockUntil - Date.now()) / 60000);
    return { error: `Too many failed attempts. Locked out for ${minutesLeft} minutes.` };
  }

  const password = formData.get("password");
  const rawFrom = (formData.get("from") as string) || "/";
  // SEC-10: Prevent open redirects by ensuring the path is relative
  const safeFrom = rawFrom.startsWith("/") && !rawFrom.startsWith("//") && !rawFrom.startsWith("/\\") ? rawFrom : "/";

  if (typeof password !== "string" || password !== process.env.SITE_PASSWORD) {
    const count = attemptCount + 1;
    const newLockUntil = count >= 5 ? Date.now() + 15 * 60 * 1000 : 0;

    if (hasKV) {
      try {
        const val = JSON.stringify({ count, lockUntil: newLockUntil });
        // Store attempts with a 15-minute TTL
        await fetch(`${kvUrl}/set/${kvKey}/900`, {
          method: "POST",
          headers: { Authorization: `Bearer ${kvToken}` },
          body: val,
        });
      } catch {
        loginAttempts.set(ip, { count, lockUntil: newLockUntil });
      }
    } else {
      loginAttempts.set(ip, { count, lockUntil: newLockUntil });
    }

    // Throttling: Slow down brute force guesses
    await new Promise((resolve) => setTimeout(resolve, 2000));
    return { error: "Wrong password." };
  }

  // Clear attempts on success
  if (hasKV) {
    try {
      await fetch(`${kvUrl}/del/${kvKey}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${kvToken}` },
      });
    } catch {
      loginAttempts.delete(ip);
    }
  } else {
    loginAttempts.delete(ip);
  }

  const cookieStore = await cookies();
  const token = generateToken(process.env.SITE_PASSWORD!);
  cookieStore.set("scout_auth", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 90, // 90 days — personal device, no need to re-login often
  });

  redirect(safeFrom);
}

export async function logout() {
  const cookieStore = await cookies();
  cookieStore.delete("scout_auth");
  redirect("/login");
}
