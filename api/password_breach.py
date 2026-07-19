"""
Password breach checking via the Have I Been Pwned Pwned Passwords API.

Uses k-anonymity: only the first 5 characters of the password's SHA-1 hash are
ever sent over the network -- never the password itself, never the full hash.
HIBP returns every known suffix matching that prefix (a few hundred rows), and
the match is found locally. This is the standard, Google/NIST-recommended way
to check a password against known-breached corpora without a third party ever
seeing enough to reconstruct it.

Kept as its own module for the same reason as google_auth.py: a small,
independently-reviewable unit that doesn't need to touch auth.py's in-progress
SMTP-delivery work.
"""

import hashlib

import requests

HIBP_RANGE_URL = "https://api.pwnedpasswords.com/range/{prefix}"


def is_password_breached(password: str) -> bool:
    """True if the password appears in a known breach corpus.

    Fails OPEN on any network/API problem -- a third-party outage must never
    block signup or password reset. This is defense in depth on top of the
    existing strength rules, not something the whole flow should depend on."""
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        res = requests.get(
            HIBP_RANGE_URL.format(prefix=prefix),
            headers={"Add-Padding": "true"},  # HIBP-recommended: pads response size to resist traffic analysis
            timeout=5,
        )
    except requests.RequestException:
        return False

    if res.status_code != 200:
        return False

    for line in res.text.splitlines():
        parts = line.split(":")
        if len(parts) != 2:
            continue
        line_suffix, _count = parts
        if line_suffix.strip() == suffix:
            return True
    return False
