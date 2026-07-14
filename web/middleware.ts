import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "./lib/auth-token";

// Single shared-password gate — this is a personal, single-user tool, not a
// multi-tenant app, so a full auth system would be overkill. Optimistic
// check only (reads the cookie, no DB), per Next.js's own guidance for Proxy.
export function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname;
  if (path === "/login") {
    return NextResponse.next();
  }

  const cookie = req.cookies.get("scout_auth")?.value;
  // Fail closed: a missing SITE_PASSWORD must never verify tokens against an
  // empty HMAC key (which anyone could forge) — treat it as "nobody gets in".
  const sitePassword = process.env.SITE_PASSWORD;
  if (!sitePassword) {
    const loginUrl = new URL("/login", req.nextUrl);
    loginUrl.searchParams.set("from", path);
    return NextResponse.redirect(loginUrl);
  }

  if (!verifyToken(cookie, sitePassword)) {
    const loginUrl = new URL("/login", req.nextUrl);
    loginUrl.searchParams.set("from", path);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Exclude Next's internals AND static public assets (by file extension).
  // Without the extension exclusion, a request for a /public file like
  // `/studio_small_03_1k.hdr` gets 307-redirected to the login HTML, which
  // then fails to parse as its real type (e.g. THREE.RGBELoader: "no header
  // found") and crashes the page. Assets are public by design — no auth needed.
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:hdr|svg|png|jpg|jpeg|gif|webp|ico|woff2?|ttf|otf|txt|xml|json|map)).*)",
  ],
};
