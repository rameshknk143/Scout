"""
ScoutVeda authentication core.

Multi-tenant, passwordless-verification model:
  - Passwords are hashed with Argon2id (never stored in plaintext).
  - Email OTPs back the signup and password-reset flows, with all generation,
    validation, expiry, resend cooldown, and attempt limiting done here on the
    server. Codes are stored only as peppered hashes.
  - Delivery goes through Resend. If RESEND_API_KEY is not set we DO NOT pretend
    an email was sent: send_otp_email() reports mock=True, and the code is only
    surfaced (via logs) in development.

The endpoints in main.py never reveal whether an email is already registered —
these helpers return generic results and the caller keeps responses uniform.
"""

import hashlib
import hmac
import os
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

# --- Policy constants (server-authoritative; the client mirrors these) --------
OTP_TTL_MINUTES = 10
RESEND_COOLDOWN_SECONDS = 60
MAX_VERIFY_ATTEMPTS = 5          # per active OTP, before it's invalidated
MAX_SENDS_PER_HOUR = 5          # per email, to throttle abuse

MIN_PASSWORD_LEN = 12

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "ScoutVeda <noreply@scoutveda.com>")
IS_PRODUCTION = os.environ.get("ENV", "production") == "production" or os.environ.get("RENDER") == "true"

# SMTP Configuration
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = os.environ.get("SMTP_PORT")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_SECURE = os.environ.get("SMTP_SECURE", "tls").strip().lower()

_ph = PasswordHasher()


# --- Passwords ----------------------------------------------------------------
def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        return _ph.verify(stored_hash, password)
    except (VerifyMismatchError, InvalidHashError, Exception):
        return False


def password_needs_rehash(stored_hash: str) -> bool:
    try:
        return _ph.check_needs_rehash(stored_hash)
    except Exception:
        return False


def validate_password_strength(password: str) -> str | None:
    """Returns an error message if the password fails policy, else None."""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LEN:
        return f"Password must be at least {MIN_PASSWORD_LEN} characters."
    if not re.search(r"[A-Z]", password):
        return "Password must include an uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must include a lowercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must include a number."
    if not re.search(r"[^A-Za-z0-9]", password):
        return "Password must include a special character."
    return None


# --- OTP codes ----------------------------------------------------------------
def generate_otp() -> str:
    """Cryptographically-random 6-digit code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _otp_pepper() -> str:
    # A server-side secret so a DB dump alone can't reverse live codes.
    return os.environ.get("OTP_PEPPER", os.environ.get("SESSION_SECRET", "scoutveda-dev-pepper"))


def hash_otp(code: str, email: str) -> str:
    return hashlib.sha256(f"{_otp_pepper()}:{email.strip().lower()}:{code}".encode()).hexdigest()


def otp_matches(code: str, email: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(code, email), stored_hash or "")


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def mask_email(email: str) -> str:
    try:
        local, domain = email.split("@", 1)
    except ValueError:
        return email
    if len(local) <= 2:
        shown = local[0]
    else:
        shown = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{shown}@{domain}"


# --- Delivery -----------------------------------------------------------------
def _email_html(code: str, purpose: str) -> str:
    heading = "Verify your email" if purpose == "signup" else "Reset your password"
    intro = (
        "Use this code to finish creating your ScoutVeda account."
        if purpose == "signup"
        else "Use this code to reset your ScoutVeda password."
    )
    return f"""\
<div style="background:#0b0f1a;padding:40px 0;font-family:-apple-system,Segoe UI,Roboto,sans-serif">
  <div style="max-width:440px;margin:0 auto;background:#121826;border:1px solid rgba(255,255,255,.08);
       border-radius:16px;padding:32px;color:#e7ebf4">
    <div style="font-family:ui-monospace,monospace;letter-spacing:.16em;font-weight:700;
         color:#e2b45f;font-size:13px;margin-bottom:24px">SCOUTVEDA</div>
    <h1 style="font-size:20px;margin:0 0 8px">{heading}</h1>
    <p style="color:#98a2b8;font-size:14px;margin:0 0 24px">{intro}</p>
    <div style="background:#0b0f1a;border:1px solid rgba(255,255,255,.08);border-radius:12px;
         padding:20px;text-align:center;font-family:ui-monospace,monospace;font-size:32px;
         font-weight:700;letter-spacing:.3em;color:#34d399">{code}</div>
    <p style="color:#6b7488;font-size:12px;margin:24px 0 0">
      This code expires in {OTP_TTL_MINUTES} minutes. If you didn't request it, you can ignore this email.
    </p>
  </div>
</div>"""


def send_otp_email(to_email: str, code: str, purpose: str) -> dict:
    """Send an OTP email. Returns {"sent": bool, "mock": bool}.

    Supports Resend API and Standard SMTP. Falls back to mock mode if neither is configured."""
    subject = (
        "Your ScoutVeda verification code" if purpose == "signup"
        else "Reset your ScoutVeda password"
    )

    # 1. Try Resend if API key is set
    if RESEND_API_KEY:
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": EMAIL_FROM,
                    "to": [to_email],
                    "subject": subject,
                    "html": _email_html(code, purpose),
                },
                timeout=15,
            )
            return {"sent": 200 <= resp.status_code < 300, "mock": False}
        except requests.RequestException as e:
            print(f"[OTP] Resend delivery failed: {e}")
            return {"sent": False, "mock": False}

    # 2. Try SMTP if host is configured
    elif SMTP_HOST:
        try:
            port = int(SMTP_PORT) if SMTP_PORT else (465 if SMTP_SECURE == "ssl" else 587)

            # Construct MIME message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = EMAIL_FROM
            msg["To"] = to_email
            msg.attach(MIMEText(_email_html(code, purpose), "html"))

            # Parse clean envelope sender from "Name <email@domain.com>"
            sender_match = re.search(r"<([^>]+)>", EMAIL_FROM)
            envelope_sender = sender_match.group(1) if sender_match else EMAIL_FROM

            # `with` guarantees the connection is closed even if login/send raises,
            # instead of leaking a dangling socket until the OS times it out.
            smtp_cls = smtplib.SMTP_SSL if SMTP_SECURE == "ssl" else smtplib.SMTP
            with smtp_cls(SMTP_HOST, port, timeout=15) as server:
                if SMTP_SECURE == "tls":
                    server.starttls()
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(envelope_sender, [to_email], msg.as_string())
            return {"sent": True, "mock": False}
        except Exception as e:
            print(f"[OTP] SMTP delivery failed: {e}")
            return {"sent": False, "mock": False}

    # 3. Fallback to mock mode
    else:
        if not IS_PRODUCTION:
            print(f"[OTP:MOCK] ({purpose}) code for {to_email}: {code}")
        return {"sent": False, "mock": True}
