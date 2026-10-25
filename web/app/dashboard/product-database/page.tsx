import Link from "next/link";
import { cookies } from "next/headers";
import { SESSION_COOKIE, verifySessionToken } from "@/lib/session";
import { ARCHIVE_OWNER_ID } from "@/lib/archive-catalog";
import ProductDatabaseClient from "./product-database-client";

export default async function ProductDatabasePage() {
  const session = await verifySessionToken((await cookies()).get(SESSION_COOKIE)?.value);

  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-900 font-sans">Amazon Product Database</h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">
        Search recent observations from your laptop, phone, cloud collectors and watchlist. Each product shows its latest matching observation.
      </p>
      {session?.uid === ARCHIVE_OWNER_ID && (
        <div className="mb-6 rounded-xl border border-black/10 bg-white p-4 text-sm text-zinc-600">
          Older records are preserved separately. <Link href="/dashboard/history" className="font-semibold text-blue-700 underline underline-offset-4">Open archives &amp; history →</Link>
        </div>
      )}
      <ProductDatabaseClient />
    </div>
  );
}
