"""One-off: poll the nightly-collect workflow's latest run until it completes."""

import time

import requests


def load_env():
    env = {}
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v
    return env


def main():
    env = load_env()
    headers = {"Authorization": f"Bearer {env['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"}
    repo = env["GITHUB_REPO"]

    for _ in range(40):
        r = requests.get(
            f"https://api.github.com/repos/{repo}/actions/workflows/nightly-collect.yml/runs?per_page=1",
            headers=headers,
        )
        runs = r.json().get("workflow_runs", [])
        if not runs:
            print("no_runs_yet")
        else:
            run = runs[0]
            print(f"status={run['status']} conclusion={run.get('conclusion')} run_id={run['id']}")
            if run["status"] == "completed":
                print(f"RUN_FINISHED conclusion={run.get('conclusion')} url={run['html_url']}")
                return
        time.sleep(15)
    print("TIMED_OUT waiting for run to complete")


if __name__ == "__main__":
    main()
