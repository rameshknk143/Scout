"""
Clone an existing Maxun robot onto another Amazon bestseller category.

Maxun's own duplicate endpoint is not enough on its own. It rewrites the workflow
only when it can find an entry step whose `where.url` is "about:blank":

    const entryStep = steps.findLast((step) => step.where?.url === 'about:blank');

Robots recorded against a real page have no such step, so `originalEntryUrl` comes
back null, the rewrite loop no-ops, and you get a robot whose *metadata* says the
new category while its *workflow* still navigates to the old one. Verified on
2026-08-11: a robot duplicated onto /hpc/ returned grocery products
(ref=zg_bs_g_grocery_d_sccl_1).

So this does the duplicate, then repairs the workflow itself via
PUT /api/sdk/robots/:id, then proves the fix by running the robot and checking the
`ref=zg_bs_g_<slug>_` marker Amazon puts in every bestseller link.

    python add_category_robot.py --slug hpc --name "Health & Personal Care"
    python add_category_robot.py --slug beauty --name Beauty --no-verify

Reads MAXUN_API_URL / MAXUN_API_KEY / MAXUN_ROBOT_ID from the environment, same as
maxun_bridge.py. MAXUN_ROBOT_ID is the robot to clone from.
"""

import argparse
import json
import os
import sys

import requests

MAXUN_API_URL = os.environ.get("MAXUN_API_URL", "http://127.0.0.1:8080").rstrip("/")
MAXUN_API_KEY = os.environ.get("MAXUN_API_KEY")
SOURCE_ROBOT_ID = os.environ.get("MAXUN_ROBOT_ID")

BESTSELLER_URL = "https://www.amazon.in/gp/bestsellers/%s/"


def headers():
    if not MAXUN_API_KEY:
        sys.exit("MAXUN_API_KEY is not set.")
    return {"x-api-key": MAXUN_API_KEY, "Content-Type": "application/json"}


def find_workflow(blob):
    """The SDK response nests the workflow differently depending on the route."""
    if isinstance(blob, dict):
        if isinstance(blob.get("workflow"), list):
            return blob["workflow"]
        for value in blob.values():
            found = find_workflow(value)
            if found:
                return found
    return None


def source_url(robot_id):
    """The URL the source robot actually navigates to, read from its workflow."""
    blob = requests.get("%s/api/sdk/robots/%s" % (MAXUN_API_URL, robot_id),
                        headers=headers(), timeout=60).json()
    workflow = find_workflow(blob)
    if not workflow:
        sys.exit("Could not read a workflow for robot %s" % robot_id)
    for step in workflow:
        for action in step.get("what") or []:
            if action.get("action") == "goto" and action.get("args"):
                return action["args"][0], workflow
    sys.exit("Source robot %s has no goto step to clone from." % robot_id)


def duplicate(robot_id, target_url):
    r = requests.post("%s/api/robots/%s/duplicate" % (MAXUN_API_URL, robot_id),
                      headers=headers(), json={"targetUrl": target_url}, timeout=120)
    if r.status_code not in (200, 201):
        sys.exit("duplicate failed HTTP %s: %s" % (r.status_code, r.text[:300]))
    robot = r.json().get("robot") or {}
    new_id = (robot.get("recording_meta") or {}).get("id") or robot.get("id")
    if not new_id:
        sys.exit("duplicate returned no robot id: %s" % r.text[:300])
    return new_id


def retarget(new_id, old_url, new_url):
    """Repair what duplicate() left behind: swap the URL everywhere in the workflow."""
    blob = requests.get("%s/api/sdk/robots/%s" % (MAXUN_API_URL, new_id),
                        headers=headers(), timeout=60).json()
    workflow = find_workflow(blob)
    if not workflow:
        sys.exit("Could not read the new robot's workflow.")

    patched = json.loads(json.dumps(workflow).replace(old_url, new_url))
    r = requests.put("%s/api/sdk/robots/%s" % (MAXUN_API_URL, new_id),
                     headers=headers(), json={"workflow": patched}, timeout=90)
    if r.status_code != 200:
        sys.exit("workflow update failed HTTP %s: %s" % (r.status_code, r.text[:300]))

    after = json.dumps(requests.get("%s/api/sdk/robots/%s" % (MAXUN_API_URL, new_id),
                                    headers=headers(), timeout=60).json())
    if old_url in after:
        sys.exit("the old URL is still in the workflow - refusing to call this done.")


def verify(new_id, slug):
    """Run it and confirm Amazon's own ref= marker names the category we asked for."""
    r = requests.post("%s/api/robots/%s/runs" % (MAXUN_API_URL, new_id),
                      headers=headers(), timeout=600)
    run = (r.json() or {}).get("run") or {}
    if str(run.get("status", "")).lower() not in ("success", "completed"):
        return False, "run status=%s" % run.get("status"), 0

    detail = requests.get("%s/api/robots/%s/runs/%s"
                          % (MAXUN_API_URL, new_id, run.get("runId")),
                          headers=headers(), timeout=90).json()
    rows = ((detail.get("run") or {}).get("data") or {}).get("listData") or []
    if isinstance(rows, dict):
        rows = list(rows.values())[0]
    if not rows:
        return False, "run succeeded but scraped 0 rows", 0

    marker = "zg_bs_g_%s_" % slug
    blob = json.dumps(rows)
    if marker not in blob:
        # Amazon sometimes uses a different marker segment; report rather than guess.
        return False, "no '%s' marker in the scraped links" % marker, len(rows)
    return True, "ok", len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True,
                    help="Amazon bestseller slug, e.g. hpc, beauty, kitchen")
    ap.add_argument("--name", required=True,
                    help="category name to file the rows under in ScoutVeda")
    ap.add_argument("--from-robot", default=SOURCE_ROBOT_ID,
                    help="robot to clone (default: MAXUN_ROBOT_ID)")
    ap.add_argument("--no-verify", action="store_true",
                    help="skip the proving run")
    args = ap.parse_args()

    if not args.from_robot:
        sys.exit("No source robot. Set MAXUN_ROBOT_ID or pass --from-robot.")

    target = BESTSELLER_URL % args.slug
    old_url, _ = source_url(args.from_robot)
    print("cloning %s\n  from %s\n  to   %s" % (args.from_robot, old_url, target))

    new_id = duplicate(args.from_robot, target)
    print("  duplicated -> %s" % new_id)

    retarget(new_id, old_url, target)
    print("  workflow retargeted")

    if args.no_verify:
        print("  (skipped verification)")
    else:
        ok, why, count = verify(new_id, args.slug)
        print("  verify: %s (%d rows) %s" % ("PASS" if ok else "FAIL", count, why))
        if not ok:
            sys.exit(1)

    print("\nAdd to laptop.env MAXUN_ROBOTS:  %s=%s" % (new_id, args.name))


if __name__ == "__main__":
    main()
