"""
Google Sign-In for ScoutVeda.

Standard OAuth 2.0 authorization-code flow: the frontend sends the visitor to
Google's own consent screen, Google redirects back with a one-time `code`,
and THIS server (never the browser) exchanges it for tokens using the client
secret. The redirect_uri passed here must be byte-identical to the one used
to obtain the code, per the OAuth spec -- Google rejects a mismatch.

Kept as its own module (rather than folded into auth.py) so it stays a clean,
independent unit: what it does (verify a Google identity), how it's used (one
function call), and what it depends on (GOOGLE_CLIENT_ID/SECRET) are all
visible at a glance.
"""

import os

import requests

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")


class GoogleAuthError(Exception):
    pass


def exchange_google_code(code: str, redirect_uri: str) -> dict:
    """POST the authorization code to Google's token endpoint. Returns the
    verified {email, name} on success; raises GoogleAuthError with a
    user-safe message otherwise."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise GoogleAuthError("Google sign-in is not configured on the server yet.")

    try:
        token_res = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
    except requests.RequestException:
        raise GoogleAuthError("Couldn't reach Google. Please try again.")

    if token_res.status_code != 200:
        raise GoogleAuthError("Google sign-in failed or was cancelled. Please try again.")

    id_token = token_res.json().get("id_token")
    if not id_token:
        raise GoogleAuthError("Google did not return an identity token.")

    # Verify the ID token's signature and audience via Google's tokeninfo
    # endpoint (a plain HTTPS call -- avoids pulling in a JWT/crypto library
    # for what is, at ScoutVeda's current scale, a low-volume check. Google
    # documents this endpoint as valid for verification, just rate-limited;
    # revisit with the google-auth library if Google sign-in volume grows).
    try:
        info_res = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
            timeout=15,
        )
    except requests.RequestException:
        raise GoogleAuthError("Couldn't verify your Google identity. Please try again.")

    if info_res.status_code != 200:
        raise GoogleAuthError("Couldn't verify your Google identity. Please try again.")

    payload = info_res.json()
    if payload.get("aud") != GOOGLE_CLIENT_ID:
        raise GoogleAuthError("Google identity verification failed.")
    if payload.get("email_verified") not in ("true", True):
        raise GoogleAuthError("Your Google email isn't verified. Please verify it with Google first.")

    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise GoogleAuthError("Google did not share an email address.")

    return {"email": email, "name": payload.get("name") or email.split("@")[0]}
