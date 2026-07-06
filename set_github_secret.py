"""
One-off helper: sets/updates a GitHub Actions repo secret via the API.
Reads GITHUB_TOKEN, GITHUB_REPO, and the secret to push from local .env —
never prints any secret values, only success/failure.

Usage: python set_github_secret.py SECRET_NAME
(reads the value for SECRET_NAME out of .env's matching key)
"""

import base64
import sys

import requests
from nacl import encoding, public


def load_env():
    env = {}
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v
    return env


def encrypt(public_key_b64: str, secret_value: str) -> str:
    public_key = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def main():
    secret_name = sys.argv[1]
    env = load_env()
    token = env["GITHUB_TOKEN"]
    repo = env["GITHUB_REPO"]
    value = env[secret_name]

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    key_resp = requests.get(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers=headers,
    )
    key_resp.raise_for_status()
    key_data = key_resp.json()

    encrypted_value = encrypt(key_data["key"], value)

    put_resp = requests.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}",
        headers=headers,
        json={"encrypted_value": encrypted_value, "key_id": key_data["key_id"]},
    )
    print(f"{secret_name}: HTTP {put_resp.status_code} ({'ok' if put_resp.ok else 'FAILED'})")


if __name__ == "__main__":
    main()
