"use server";

import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";
import { generateToken } from "./auth-token";

export type LoginState = { error?: string } | undefined;

// In-memory brute force protection
const loginAttempts = new Map<string, { count: number; lockUntil: number }>();

export async function login(
  _prevState: LoginState,
  formData: FormData
): Promise<LoginState> {
  const ip = (await headers()).get("x-forwarded-for") || "127.0.0.1";

  // Check if IP is currently locked out
  const attempt = loginAttempts.get(ip);
  if (attempt && attempt.lockUntil > Date.now()) {
    const minutesLeft = Math.ceil((attempt.lockUntil - Date.now()) / 60000);
    return { error: `Too many failed attempts. Locked out for ${minutesLeft} minutes.` };
  }

  const password = formData.get("password");
  const rawFrom = (formData.get("from") as string) || "/";
  // SEC-10: Prevent open redirects by ensuring the path is relative
  const safeFrom = rawFrom.startsWith("/") && !rawFrom.startsWith("//") && !rawFrom.startsWith("/\\") ? rawFrom : "/";

  if (typeof password !== "string" || password !== process.env.SITE_PASSWORD) {
    const count = (attempt ? attempt.count : 0) + 1;
    if (count >= 5) {
      loginAttempts.set(ip, { count, lockUntil: Date.now() + 15 * 60 * 1000 }); // 15 mins lock
    } else {
      loginAttempts.set(ip, { count, lockUntil: 0 });
    }

    // Throttling: Slow down brute force guesses
    await new Promise((resolve) => setTimeout(resolve, 2000));
    return { error: "Wrong password." };
  }

  // Clear attempts on success
  loginAttempts.delete(ip);

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
