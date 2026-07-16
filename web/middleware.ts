import { NextRequest, NextResponse } from "next/server";
import { verifySessionToken, SESSION_COOKIE } from "./lib/session";

// Public pages (landing + auth). Everything under /dashboard requires a valid
// per-user session; otherwise the visitor is sent to /login. Optimistic cookie
// check only (no DB), per Next.js middleware guidance.
const AUTH_PAGES = ["/login", "/signup", "/forgot-password"];

export function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname;
  const session = verifySessionToken(req.cookies.get(SESSION_COOKIE)?.value);

  // Already signed in? Skip the auth pages and go to the dashboard.
  if (session && AUTH_PAGES.includes(path)) {
    return NextResponse.redirect(new URL("/dashboard", req.nextUrl));
  }

  // Protect the app.
  if (path === "/dashboard" || path.startsWith("/dashboard/")) {
    if (!session) {
      const loginUrl = new URL("/login", req.nextUrl);
      loginUrl.searchParams.set("from", path);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  // Exclude Next internals and static public assets (by extension) so files
  // like /studio_small_03_1k.hdr aren't redirected to HTML.
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:hdr|svg|png|jpg|jpeg|gif|webp|ico|woff2?|ttf|otf|txt|xml|json|map)).*)",
  ],
};
