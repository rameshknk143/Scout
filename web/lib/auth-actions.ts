"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export type LoginState = { error?: string } | undefined;

export async function login(
  _prevState: LoginState,
  formData: FormData
): Promise<LoginState> {
  const password = formData.get("password");
  const from = (formData.get("from") as string) || "/";

  if (typeof password !== "string" || password !== process.env.SITE_PASSWORD) {
    return { error: "Wrong password." };
  }

  const cookieStore = await cookies();
  cookieStore.set("scout_auth", process.env.SITE_PASSWORD!, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 90, // 90 days — personal device, no need to re-login often
  });

  redirect(from);
}
