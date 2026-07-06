import { NextRequest, NextResponse } from "next/server";

// Single shared-password gate — this is a personal, single-user tool, not a
// multi-tenant app, so a full auth system would be overkill. Optimistic
// check only (reads the cookie, no DB), per Next.js's own guidance for Proxy.
export function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname;
  if (path === "/login") {
    return NextResponse.next();
  }

  const cookie = req.cookies.get("scout_auth")?.value;
  if (cookie !== process.env.SITE_PASSWORD) {
    const loginUrl = new URL("/login", req.nextUrl);
    loginUrl.searchParams.set("from", path);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
