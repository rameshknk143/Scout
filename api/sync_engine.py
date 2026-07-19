"""Orchestrates the nightly/manual storefront sync across every connected
seller account: batches accounts into waves (pacing insurance against
Amazon's rate limits as account count grows), and persists a sync_jobs row
for every account attempted. See
docs/superpowers/specs/2026-07-19-sync-engine-design.md."""

import time

import amazon_sp_api
import db

WAVE_SIZE = 5
WAVE_PAUSE_SECONDS = 2


def run_all_syncs() -> dict:
    """Refreshes every connected seller's storefront data. Accounts are
    processed in waves of WAVE_SIZE, with a WAVE_PAUSE_SECONDS pause between
    waves. Each account gets a sync_jobs row recording the outcome — a
    failure for one seller never fabricates data, blocks other sellers, or
    aborts the batch."""
    user_ids = db.get_user_ids_with_credentials()
    waves = [user_ids[i:i + WAVE_SIZE] for i in range(0, len(user_ids), WAVE_SIZE)]

    results = []
    for wave_number, wave in enumerate(waves, start=1):
        for uid in wave:
            job_id = db.start_sync_job(uid, wave_number)
            try:
                r = amazon_sp_api.sync_storefront_data(uid)
                status = "ok" if r.get("ok") else "error"
                db.finish_sync_job(job_id, status, r.get("attempts", 1), r.get("error"))
                results.append({"user_id": uid, "ok": bool(r.get("ok")), "error": r.get("error")})
            except Exception as e:
                # sync_storefront_data already catches its own exceptions and
                # returns {"ok": False, ...} — this is a last-resort guard so
                # a genuinely unexpected crash still closes out the job row
                # instead of leaving it stuck at status='running' forever.
                db.finish_sync_job(job_id, "error", 1, str(e))
                results.append({"user_id": uid, "ok": False, "error": str(e)})

        if wave_number < len(waves):
            time.sleep(WAVE_PAUSE_SECONDS)

    return {
        "sellers": len(user_ids),
        "succeeded": sum(1 for r in results if r["ok"]),
        "results": results,
    }
