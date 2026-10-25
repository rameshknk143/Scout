import Link from "next/link";
import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";
import { SESSION_COOKIE, verifySessionToken } from "@/lib/session";
import { ARCHIVES, ARCHIVE_OWNER_ID } from "@/lib/archive-catalog";

export const dynamic = "force-dynamic";

const number = (value: number) => value.toLocaleString("en-IN");

export default async function HistoryPage() {
  const session = await verifySessionToken((await cookies()).get(SESSION_COOKIE)?.value);
  if (!session) redirect("/login?from=%2Fdashboard%2Fhistory");
  if (session.uid !== ARCHIVE_OWNER_ID) notFound();

  const archived = ARCHIVES.reduce((sum, archive) => sum + archive.snapshots, 0);
  const fields = ARCHIVES.reduce((sum, archive) => sum + archive.fields, 0);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Collection history</p>
        <h1 className="mt-2 text-2xl font-bold text-zinc-900">Archives &amp; history</h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-600">
          Older observations are preserved in verified, encrypted archives. Recent products remain searchable in the live database.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {[
          ["Archived product observations", number(archived)],
          ["Archived field values", number(fields)],
          ["Verified archives", String(ARCHIVES.length)],
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl border border-black/10 bg-white p-5">
            <p className="text-xs text-zinc-500">{label}</p>
            <p className="mt-2 text-2xl font-bold tabular-nums text-zinc-900">{value}</p>
          </div>
        ))}
      </div>

      <section className="rounded-xl border border-blue-200 bg-blue-50 p-5 text-sm text-blue-950" aria-labelledby="archive-access">
        <h2 id="archive-access" className="font-semibold">How to access your history</h2>
        <p className="mt-2">Open an archive in Google Drive while signed in to your archive-owner Google account, then download the encrypted ZIP. Drive access remains owner-only.</p>
        <p className="mt-2">Archive contents require the protected recovery key and verified restore helper. This page does not decrypt files or search archived rows. Keep the recovery key off the website.</p>
        <Link href="/dashboard/product-database" className="mt-3 inline-block font-semibold underline underline-offset-4">Search recent live products →</Link>
      </section>

      <div className="space-y-4">
        {ARCHIVES.map((archive) => (
          <article key={archive.id} className="rounded-xl border border-black/10 bg-white p-5 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-zinc-900">{archive.date}</h2>
                <p className="mt-1 text-xs text-zinc-500">Verified encrypted backup · {(archive.bytes / 1048576).toFixed(1)} MiB</p>
              </div>
              <a href={archive.driveUrl} target="_blank" rel="noopener noreferrer" className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-600">
                Open private archive ↗<span className="sr-only"> for {archive.date}, opens Google Drive in a new tab</span>
              </a>
            </div>
            <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2">
              <div><dt className="text-zinc-500">Product observations</dt><dd className="mt-1 font-semibold text-zinc-900">{number(archive.snapshots)}</dd></div>
              <div><dt className="text-zinc-500">Product capture cutoff</dt><dd className="mt-1 text-zinc-900">Before {archive.snapshotBefore}</dd></div>
              {archive.fields > 0 && <>
                <div><dt className="text-zinc-500">Field values</dt><dd className="mt-1 font-semibold text-zinc-900">{number(archive.fields)}</dd></div>
                <div><dt className="text-zinc-500">Field capture cutoff</dt><dd className="mt-1 text-zinc-900">Before {archive.fieldBefore}</dd></div>
              </>}
              {archive.legacyBackup > 0 && <div className="sm:col-span-2"><dt className="text-zinc-500">Separate legacy backup</dt><dd className="mt-1 text-zinc-900">{number(archive.legacyBackup)} rows. Possible overlap; excluded from product totals.</dd></div>}
            </dl>
            <details className="mt-5 border-t border-black/5 pt-4 text-xs text-zinc-500">
              <summary className="cursor-pointer font-medium">Verification details</summary>
              <p className="mt-2">Export receipt: {archive.id}</p>
              <p className="mt-2 break-all font-mono">SHA-256: {archive.sha256}</p>
            </details>
          </article>
        ))}
      </div>
      <p className="text-xs text-zinc-500">Archived observations include repeat captures. They are not counts of distinct products. Minimum retention remains seven days for live product snapshots and one day for field values.</p>
    </div>
  );
}

