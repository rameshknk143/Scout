"""
Scout's business-logic API. Thin FastAPI wrapper around the same
profit_calculator / scorer / trend_radar logic Scout has always used —
only the data layer (db.py) changed, to talk to Supabase instead of a
local SQLite file.

Every endpoint except /health requires an X-Scout-Key header matching the
API_KEY environment variable. The Next.js frontend calls this server-side
(Server Components / Server Actions), so the key never reaches the browser
bundle. Still worth knowing: it's one shared key for a single personal user,
not a real per-user auth model — fine for this tool's scope, not something
to reuse if it ever stopped being personal-only.
"""

import html
import json
import logging
import math
import os
import re
from datetime import datetime, timedelta, timezone

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

import alerts
import amazon_sp_api
import auth
import db
import google_auth
import listing_analyzer
import password_breach
import profit_calculator
import ppc_analytics
import scorer
import sync_engine
import trend_radar

logger = logging.getLogger(__name__)

API_KEY = os.environ["API_KEY"]

# Developer sideload testing only. Never set on Render — with the flag absent,
# the mock-code path below cannot be reached in production.
ALLOW_MOCK_LWA = os.environ.get("ALLOW_MOCK_LWA") == "1"

# Amazon ASINs are exactly 10 chars, A-Z/0-9. Validating before the value is
# interpolated into amazon.in URLs or used in queries keeps those paths inert.
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")

# Floor for a caller-supplied collected_at. This project began in 2026, so a
# timestamp before this is a parsing accident (epoch 0, a two-digit year) rather
# than real history, and would drag trend charts back to 1970.
EARLIEST_PLAUSIBLE = datetime(2025, 1, 1, tzinfo=timezone.utc)


def day_label(value) -> str:
    """Short MM-DD label for a chart x-axis.

    Takes either a datetime or an ISO-8601 string, because collected_at is being
    migrated from TEXT to timestamptz and psycopg2 returns str for one and
    datetime for the other. This used to be `value[-5:]`, which on a full ISO
    string takes the last five characters of "...+00:00" and labelled every
    point "00:00" - it only ever worked back when the column held bare dates.
    """
    if not value:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%m-%d")
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%m-%d")
    except ValueError:
        return text[:10] or "—"


def clean_asin(asin: str) -> str:
    asin = (asin or "").strip().upper()
    if not ASIN_RE.match(asin):
        raise HTTPException(status_code=400, detail=f"Invalid ASIN format: {asin!r}")
    return asin

# Keep in sync with scraper/collector.py's CATEGORIES dict keys.
CATEGORIES = [
    "Electronics Accessories", "Home & Kitchen", "Beauty & Personal Care",
    "Sports & Fitness", "Toys & Games", "Stationery/Office", "Pet Supplies",
    "Car Accessories", "Garden & Outdoors", "Baby Products", "Watches & Gifting",
    "Clothing & Accessories", "Amazon Launchpad", "Amazon Renewed",
    "Apps & Games", "Bags, Wallets & Luggage", "Books", "Computers & Accessories",
    "Gift Cards", "Grocery & Gourmet Foods", "Health & Personal Care",
    "Home Improvement", "Industrial & Scientific", "Jewellery", "Kindle Store",
    "Movies & TV Shows", "Music", "Musical Instruments", "Shoes & Handbags",
    "Software", "Video Games",
]

is_production = os.environ.get("RENDER") == "true" or os.environ.get("ENV") == "production"
app = FastAPI(
    title="Scout API",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json"
)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
origins = [origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    try:
        db.init_db()
        logger.info("Database schema & migrations verified.")
    except Exception as e:
        logger.error(f"Failed to run database migrations: {e}")


def require_key(x_scout_key: str = Header(default="")):
    if x_scout_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Scout-Key header")


def _client_ip(request: Request):
    """Best-effort client IP for audit records.

    Render terminates TLS at its own proxy and *appends* the real peer address to
    X-Forwarded-For, so anything a client forges lands to the left of it. The
    rightmost entry is the only part of that header we can trust. Returns None
    rather than a placeholder when we genuinely can't tell."""
    forwarded = request.headers.get("x-forwarded-for", "")
    parts = [p.strip() for p in forwarded.split(",") if p.strip()]
    if parts:
        return parts[-1]
    return request.client.host if request.client else None


def require_user(x_scout_user: str = Header(default="")) -> int:
    """Tenant scoping. The Next.js frontend (already authenticated by X-Scout-Key)
    forwards the signed-in user's id in X-Scout-User. Because the API is only
    reachable with the shared key held server-side, this header is trusted. Data
    endpoints depend on this so every query is scoped to one account."""
    if not x_scout_user or not x_scout_user.isdigit():
        raise HTTPException(status_code=401, detail="Missing user context")
    return int(x_scout_user)


# ============================ Authentication ================================
# All auth endpoints sit behind require_key (only the trusted frontend calls
# them). OTP generation/validation/expiry/rate-limiting all live here; responses
# never reveal whether an email is already registered.

def _uniform_otp_response(email, purpose):
    """Issue-and-send an OTP with server-side throttling, returning a response
    shape that is identical whether or not the email exists / was really sent."""
    now = datetime.now(timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()
    if db.count_recent_otps(email, purpose, hour_ago) >= auth.MAX_SENDS_PER_HOUR:
        raise HTTPException(status_code=429, detail="Too many codes requested. Try again later.")

    existing = db.get_active_otp(email, purpose)
    if existing:
        created = datetime.fromisoformat(existing["created_at"])
        elapsed = (now - created).total_seconds()
        if elapsed < auth.RESEND_COOLDOWN_SECONDS:
            wait = int(auth.RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(status_code=429, detail=f"Please wait {wait}s before requesting another code.")

    code = auth.generate_otp()
    expires = (now + timedelta(minutes=auth.OTP_TTL_MINUTES)).isoformat()
    payload = existing.get("payload") if existing else None
    db.save_otp(email, auth.hash_otp(code, email), purpose, expires, payload=payload)
    delivery = auth.send_otp_email(email, code, purpose)
    return {
        "ok": True,
        "masked_email": auth.mask_email(email),
        "resend_after": auth.RESEND_COOLDOWN_SECONDS,
        "mock": delivery["mock"],
    }


def _consume_otp(email, purpose, code):
    """Validate a submitted OTP. Raises HTTPException with a user-safe message on
    any failure; returns the OTP row's payload on success (and deletes it)."""
    otp = db.get_active_otp(email, purpose)
    if not otp:
        raise HTTPException(status_code=400, detail="That code is invalid or has expired. Request a new one.")
    if datetime.fromisoformat(otp["expires_at"]) < datetime.now(timezone.utc):
        db.delete_otps(email, purpose)
        raise HTTPException(status_code=400, detail="That code has expired. Request a new one.")
    if otp["attempts"] >= auth.MAX_VERIFY_ATTEMPTS:
        db.delete_otps(email, purpose)
        raise HTTPException(status_code=429, detail="Too many attempts. Request a new code.")
    if not auth.otp_matches((code or "").strip(), email, otp["code_hash"]):
        db.increment_otp_attempts(otp["id"])
        raise HTTPException(status_code=400, detail="Incorrect code. Please try again.")
    payload = otp.get("payload")
    db.delete_otps(email, purpose)
    return payload


class RegisterStartRequest(BaseModel):
    full_name: str
    email: str
    password: str


@app.post("/auth/register/start", dependencies=[Depends(require_key)])
def register_start(req: RegisterStartRequest):
    email = req.email.strip().lower()
    if not auth.is_valid_email(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    if not (req.full_name or "").strip():
        raise HTTPException(status_code=400, detail="Enter your name.")
    pw_error = auth.validate_password_strength(req.password)
    if pw_error:
        raise HTTPException(status_code=400, detail=pw_error)
    if password_breach.is_password_breached(req.password):
        raise HTTPException(status_code=400, detail="That password has appeared in a known data breach. Please choose a different one.")

    # Hold the pending account (name + password hash) in the OTP payload; the
    # user row is created only after the code is verified. If the email is
    # already registered we still behave identically (no enumeration) — the
    # verify step simply won't create a duplicate.
    payload = json.dumps({"full_name": req.full_name.strip(), "password_hash": auth.hash_password(req.password)})
    now = datetime.now(timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()
    if db.count_recent_otps(email, "signup", hour_ago) >= auth.MAX_SENDS_PER_HOUR:
        raise HTTPException(status_code=429, detail="Too many codes requested. Try again later.")
    code = auth.generate_otp()
    expires = (now + timedelta(minutes=auth.OTP_TTL_MINUTES)).isoformat()
    db.save_otp(email, auth.hash_otp(code, email), "signup", expires, payload=payload)
    delivery = auth.send_otp_email(email, code, "signup")
    return {"ok": True, "masked_email": auth.mask_email(email),
            "resend_after": auth.RESEND_COOLDOWN_SECONDS, "mock": delivery["mock"]}


class OtpVerifyRequest(BaseModel):
    email: str
    code: str


@app.post("/auth/register/verify", dependencies=[Depends(require_key)])
def register_verify(req: OtpVerifyRequest):
    email = req.email.strip().lower()
    payload = _consume_otp(email, "signup", req.code)
    existing = db.get_user_by_email(email)
    if existing:
        # Email already had an account; don't duplicate. Log them in.
        user = existing
    else:
        data = json.loads(payload) if payload else {}
        user = db.create_user(email, data.get("password_hash"), data.get("full_name"), email_verified=True)
    return {"user_id": user["id"], "email": user["email"], "full_name": user.get("full_name")}


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/login", dependencies=[Depends(require_key)])
def login(req: LoginRequest):
    email = req.email.strip().lower()
    user = db.get_user_by_email(email)
    # Uniform failure — same message whether the email is unknown or the
    # password is wrong — so login can't be used to enumerate accounts.
    if not user or not auth.verify_password(user["password_hash"], req.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return {"user_id": user["id"], "email": user["email"], "full_name": user.get("full_name")}


class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str
    nonce: str | None = None


@app.post("/auth/google", dependencies=[Depends(require_key)])
def google_login(req: GoogleAuthRequest):
    try:
        identity = google_auth.exchange_google_code(req.code, req.redirect_uri, expected_nonce=req.nonce)
    except google_auth.GoogleAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = db.get_user_by_email(identity["email"])
    if not user:
        # Google has already verified this email belongs to the visitor, so
        # the account is created and immediately usable — no OTP step needed.
        user = db.create_user(
            email=identity["email"],
            password_hash=None,
            full_name=identity["name"],
            email_verified=True,
            auth_provider="google",
        )
    return {"user_id": user["id"], "email": user["email"], "full_name": user.get("full_name")}


class EmailOnlyRequest(BaseModel):
    email: str


@app.post("/auth/password/forgot", dependencies=[Depends(require_key)])
def password_forgot(req: EmailOnlyRequest):
    email = req.email.strip().lower()
    # Only really send if the account exists, but ALWAYS return the same shape.
    if auth.is_valid_email(email) and db.get_user_by_email(email):
        try:
            return _uniform_otp_response(email, "reset")
        except HTTPException as e:
            if e.status_code == 429:
                raise
    return {"ok": True, "masked_email": auth.mask_email(email),
            "resend_after": auth.RESEND_COOLDOWN_SECONDS, "mock": not bool(auth.RESEND_API_KEY)}


class ResetRequest(BaseModel):
    email: str
    code: str
    new_password: str


@app.post("/auth/password/reset", dependencies=[Depends(require_key)])
def password_reset(req: ResetRequest):
    email = req.email.strip().lower()
    pw_error = auth.validate_password_strength(req.new_password)
    if pw_error:
        raise HTTPException(status_code=400, detail=pw_error)
    if password_breach.is_password_breached(req.new_password):
        raise HTTPException(status_code=400, detail="That password has appeared in a known data breach. Please choose a different one.")
    _consume_otp(email, "reset", req.code)
    if not db.update_user_password(email, auth.hash_password(req.new_password)):
        raise HTTPException(status_code=400, detail="Could not reset password. Start over.")
    return {"ok": True}


class ResendRequest(BaseModel):
    email: str
    purpose: str  # 'signup' | 'reset'


@app.post("/auth/otp/resend", dependencies=[Depends(require_key)])
def otp_resend(req: ResendRequest):
    email = req.email.strip().lower()
    purpose = req.purpose if req.purpose in ("signup", "reset") else "signup"
    return _uniform_otp_response(email, purpose)


def df_to_records(df: pd.DataFrame):
    if df is None or df.empty:
        return []
    clean = df.replace({math.nan: None})
    for col in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[col]):
            # isoformat(), not astype(str): pandas stringifies a Timestamp as
            # "2026-08-11 18:24:37+00:00" (space), and JS Date() only parses the
            # "T" form reliably. Every other path here emits ISO-8601, so keep
            # this one identical.
            clean[col] = clean[col].apply(
                lambda v: v.isoformat() if pd.notna(v) else None
            )
    records = clean.to_dict(orient="records")
    # dates (python datetime.date objects from trend_radar's collected_date column, if present)
    for r in records:
        for k, v in list(r.items()):
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()
            elif isinstance(v, float) and math.isnan(v):
                r[k] = None
            elif k == "title" and isinstance(v, str):
                # some titles were collected before html.unescape() was added
                # to collector.py — decode on read so old rows display clean too
                r[k] = html.unescape(v)
    return records


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/version", dependencies=[Depends(require_key)])
def version():
    """Which commit is actually running.

    "Pushed to main" and "live on Render" are not the same thing, and there was
    no way to tell them apart from outside: every externally reachable response
    happens to contain no field that differs between recent builds. That matters
    for changes that must be deployed BEFORE something else happens — the
    collected_at TEXT -> timestamptz migration is the case in point, because
    psycopg2 returns str for one type and datetime for the other, so running the
    ALTER against an API that predates the tolerant readers 500s the product
    drawer.

    Render injects these at build time. They are absent when running locally,
    hence the "dev" fallbacks.

    Behind require_key: a commit SHA is not a secret, but it is free to keep it
    off an unauthenticated route. /health stays as it was — no auth, no
    database, safe for the public keep-warm ping.
    """
    return {
        "commit": os.environ.get("RENDER_GIT_COMMIT", "dev"),
        "branch": os.environ.get("RENDER_GIT_BRANCH", "dev"),
        "service": os.environ.get("RENDER_SERVICE_NAME", "local"),
    }


@app.get("/trend-radar/categories", dependencies=[Depends(require_key)])
def get_categories():
    return {"categories": CATEGORIES}


@app.get("/trend-radar/digest", dependencies=[Depends(require_key)])
def get_digest():
    digest = trend_radar.weekly_digest()
    return {
        "new_entrants": df_to_records(digest["new_entrants"]),
        "top_movers": df_to_records(digest["top_movers"]),
        "cross_category": df_to_records(digest["cross_category"]),
        "collection_dates": [d.isoformat() for d in digest["collection_dates"]],
    }


@app.get("/trend-radar/category/{category}", dependencies=[Depends(require_key)])
def get_category_table(category: str, list_type: str = "bestsellers"):
    table = trend_radar.category_table(category, list_type=list_type)
    return {"category": category, "list_type": list_type, "products": df_to_records(table)}


class ScoreRequest(BaseModel):
    asin: str = Field(pattern=r"^[a-zA-Z0-9]{10}$")
    buy_price: float
    category: str | None = None
    weight_grams: int = scorer.DEFAULT_WEIGHT_GRAMS
    fulfillment: str = scorer.DEFAULT_FULFILLMENT
    gst_rate_pct: int = scorer.DEFAULT_GST_RATE_PCT
    zone: str = scorer.DEFAULT_ZONE
    differentiation: int = 3
    operational_fit: int = 3
    notes: str = ""


@app.post("/validator/score", dependencies=[Depends(require_key)])
def score_asin(req: ScoreRequest, user_id: int = Depends(require_user)):
    return scorer.score_asin(
        asin=clean_asin(req.asin),
        buy_price=req.buy_price,
        user_id=user_id,
        category=req.category,
        weight_grams=req.weight_grams,
        fulfillment=req.fulfillment,
        gst_rate_pct=req.gst_rate_pct,
        zone=req.zone,
        differentiation=req.differentiation,
        operational_fit=req.operational_fit,
        notes=req.notes,
    )


@app.get("/watchlist", dependencies=[Depends(require_key)])
def get_watchlist(user_id: int = Depends(require_user)):
    records = db.get_watchlist_with_latest_snapshots(user_id)
    for r in records:
        if r.get("title") and isinstance(r["title"], str):
            r["title"] = html.unescape(r["title"])
    return {"validations": records}


class WatchlistNotesRequest(BaseModel):
    asin: str = Field(pattern=r"^[a-zA-Z0-9]{10}$")
    notes: str


@app.post("/watchlist/notes", dependencies=[Depends(require_key)])
def update_watchlist_notes(req: WatchlistNotesRequest, user_id: int = Depends(require_user)):
    db.update_validation_notes(req.asin, req.notes, user_id)
    return {"ok": True}


class AmazonCallbackRequest(BaseModel):
    code: str
    selling_partner_id: str
    marketplace_id: str = "A21TJRUUN4KGV"


@app.post("/auth/amazon/callback", dependencies=[Depends(require_key)])
def amazon_callback(req: AmazonCallbackRequest, user_id: int = Depends(require_user)):
    import requests
    lwa_url = "https://api.amazon.com/auth/o2/token"
    client_id = os.environ.get("LWA_CLIENT_ID")
    client_secret = os.environ.get("LWA_CLIENT_SECRET")
    
    if ALLOW_MOCK_LWA and req.code.startswith("mock"):
        # Developer sideload only — unreachable unless ALLOW_MOCK_LWA=1 is set
        # (never on Render), so real deployments can't mint fake credentials.
        refresh_token = "mock_refresh_token_sideloaded_12345"
    else:
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=500,
                detail="Scout application credentials (LWA_CLIENT_ID / LWA_CLIENT_SECRET) are not configured on the Render server."
            )
            
        payload = {
            "grant_type": "authorization_code",
            "code": req.code,
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        res = requests.post(lwa_url, data=payload)
        if res.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange authorization code: {res.text}"
            )
            
        tokens = res.json()
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail="Amazon did not return a refresh token. Make sure you approved all requested catalog and order permissions."
            )
        
    db.save_seller_credentials(
        selling_partner_id=req.selling_partner_id,
        refresh_token=refresh_token,
        user_id=user_id,
        marketplace_id=req.marketplace_id
    )
    return {"ok": True, "selling_partner_id": req.selling_partner_id}


@app.get("/auth/amazon/status", dependencies=[Depends(require_key)])
def amazon_status(user_id: int = Depends(require_user)):
    credentials = db.get_seller_credentials(user_id)
    connected = len(credentials) > 0
    return {
        "connected": connected,
        "accounts": [
            {
                "selling_partner_id": c["selling_partner_id"],
                "marketplace_id": c["marketplace_id"],
                "connected_at": c["connected_at"]
            } for c in credentials
        ]
    }
@app.delete("/auth/amazon/{selling_partner_id}", dependencies=[Depends(require_key)])
def delete_amazon_account(selling_partner_id: str, user_id: int = Depends(require_user)):
    db.delete_seller_credentials(selling_partner_id, user_id)
    return {"ok": True}

@app.get("/alerts", dependencies=[Depends(require_key)])
def get_alerts(user_id: int = Depends(require_user)):
    return {"alerts": alerts.compute_alerts(user_id)}


class ListingAnalyzeRequest(BaseModel):
    asin: str = Field(pattern=r"^[a-zA-Z0-9]{10}$")
    category: str | None = None
    marketplace_id: str | None = None


@app.post("/listing/analyze", dependencies=[Depends(require_key)])
def analyze_listing(req: ListingAnalyzeRequest):
    try:
        return listing_analyzer.analyze_listing(clean_asin(req.asin), category=req.category, marketplace_id=req.marketplace_id)
    except listing_analyzer.ListingFetchError as e:
        raise HTTPException(status_code=502, detail=str(e))


class ListingSuggestRequest(BaseModel):
    title: str | None = None
    bullets: list[str] = []
    category: str | None = None
    gaps: list[str] = []


@app.post("/listing/suggest", dependencies=[Depends(require_key)])
def suggest_listing_improvements(req: ListingSuggestRequest):
    suggestions = listing_analyzer.suggest_improvements(
        req.title, req.bullets, req.category, req.gaps
    )
    if suggestions is None:
        raise HTTPException(
            status_code=503,
            detail="AI suggestions aren't available right now (no key configured, or the free model didn't respond) -- the quality score above doesn't depend on this.",
        )
    return suggestions


class ReviewItem(BaseModel):
    text: str
    rating: float | None = None


class ReviewSummaryRequest(BaseModel):
    reviews: list[ReviewItem] = []


@app.post("/listing/review-summary", dependencies=[Depends(require_key)])
def summarize_reviews(req: ReviewSummaryRequest):
    summary = listing_analyzer.summarize_reviews([r.model_dump() for r in req.reviews])
    if summary is None:
        raise HTTPException(
            status_code=503,
            detail="Couldn't summarize reviews right now (too few reviews found on the page, no AI key configured, or the free model didn't respond).",
        )
    return summary


class ProfitCalcRequest(BaseModel):
    sell_price: float
    buy_price: float
    category: str
    weight_grams: int
    fulfillment: str
    gst_rate_pct: int
    zone: str = "national"
    is_oversize: bool = False
    returns_pct: float = 5
    ppc_per_unit: float = 0
    own_shipping_cost: float = 0


@app.post("/profit-calculator", dependencies=[Depends(require_key)])
def calc_profit(req: ProfitCalcRequest):
    return profit_calculator.calculate(
        sell_price=req.sell_price,
        buy_price=req.buy_price,
        category=req.category,
        weight_grams=req.weight_grams,
        fulfillment=req.fulfillment,
        gst_rate_pct=req.gst_rate_pct,
        zone=req.zone,
        is_oversize=req.is_oversize,
        returns_pct=req.returns_pct,
        ppc_per_unit=req.ppc_per_unit,
        own_shipping_cost=req.own_shipping_cost,
    )


@app.get("/product-database", dependencies=[Depends(require_key)])
def get_product_database(
    q: str = None,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    min_rank: int = None,
    max_rank: int = None,
    limit: int = 100,
    offset: int = 0,
):
    products = db.query_snapshots(
        query_text=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rank=min_rank,
        max_rank=max_rank,
        limit=limit,
        offset=offset,
    )
    total = db.count_snapshots(
        query_text=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rank=min_rank,
        max_rank=max_rank,
    )
    return {"products": products, "total": total}


class MyProductRequest(BaseModel):
    asin: str = Field(pattern=r"^[a-zA-Z0-9]{10}$")
    title: str | None = None
    sku: str | None = None
    supplier_cost: float = 0.0
    shipping_fee: float = 0.0
    target_margin: float = 30.0
    supplier_details: str = ""
    current_stock: int = 100
    lead_time_days: int = 14


@app.get("/my-products", dependencies=[Depends(require_key)])
def get_my_products(user_id: int = Depends(require_user)):
    products = db.get_my_products(user_id)
    return {"products": products}


@app.post("/my-products", dependencies=[Depends(require_key)])
def save_my_product(req: MyProductRequest, user_id: int = Depends(require_user)):
    db.save_my_product(
        asin=clean_asin(req.asin),
        user_id=user_id,
        title=req.title,
        sku=req.sku,
        supplier_cost=req.supplier_cost,
        shipping_fee=req.shipping_fee,
        target_margin=req.target_margin,
        supplier_details=req.supplier_details,
        current_stock=req.current_stock,
        lead_time_days=req.lead_time_days,
    )
    return {"ok": True}


@app.delete("/my-products/{asin}", dependencies=[Depends(require_key)])
def delete_my_product(asin: str, user_id: int = Depends(require_user)):
    db.delete_my_product(clean_asin(asin), user_id)
    return {"ok": True}


class CompetitorCompareRequest(BaseModel):
    asins: list[str]

    @field_validator("asins")
    @classmethod
    def validate_asins(cls, v):
        for asin in v:
            if not ASIN_RE.match(asin.strip().upper()):
                raise ValueError(f"Invalid ASIN format: {asin}")
        return [asin.strip().upper() for asin in v]


@app.post("/competitor-analysis", dependencies=[Depends(require_key)])
def compare_competitors(req: CompetitorCompareRequest, user_id: int = Depends(require_user)):
    results = []
    df = db.get_all_validations_df(user_id)
    for asin in req.asins:
        asin = asin.strip().upper()
        # list input: skip malformed entries rather than failing the whole compare
        if not ASIN_RE.match(asin):
            continue
        snap = db.get_latest_snapshot(asin)
        val = None
        if not df.empty:
            matches = df[df["asin"] == asin]
            if not matches.empty:
                val = matches.iloc[0].to_dict()
                
        results.append({
            "asin": asin,
            "title": snap["title"] if snap else (val["title"] if val else None),
            "price": snap["price"] if snap else None,
            "rank": snap["rank"] if snap else None,
            "rating": snap["rating"] if snap else None,
            "review_count": snap["review_count"] if snap else None,
            "score": val["score"] if val else None,
            "verdict": val["verdict"] if val else None,
            "found": snap is not None or val is not None
        })
    return {"comparisons": results}


@app.get("/listing-health", dependencies=[Depends(require_key)])
def get_listing_health(user_id: int = Depends(require_user)):
    df = db.get_all_validations_df(user_id)
    results = []
    if df.empty:
        return {"products": []}
    
    latest = df.sort_values("validated_at").groupby("asin").last().reset_index()
    for _, row in latest.iterrows():
        asin = row["asin"]
        snap = db.get_latest_snapshot(asin)
        
        gaps = []
        listing_score = 100
        
        title_len = len(snap["title"]) if snap and snap["title"] else 0
        if title_len < 150:
            gaps.append(f"Short product title ({title_len}/150+ chars)")
            listing_score -= 25
        if not snap or not snap.get("review_count") or snap["review_count"] < 10:
            gaps.append("Low review count (under 10 reviews)")
            listing_score -= 25
        if not snap or not snap.get("rating") or snap["rating"] < 4.0:
            gaps.append("Sub-optimal rating (under 4.0 ⭐)")
            listing_score -= 25
        if not snap or not snap.get("price") or snap["price"] <= 0:
            gaps.append("Missing price snapshot")
            listing_score -= 25
            
        listing_score = max(25, listing_score)
            
        results.append({
            "asin": asin,
            "title": row["title"] or (snap["title"] if snap else "Unknown Product"),
            "score": listing_score,
            "verdict": row["verdict"],
            "gaps": gaps,
            "price": snap["price"] if snap else None
        })
    return {"products": results}


@app.get("/products/{asin}/drawer-details", dependencies=[Depends(require_key)])
def get_drawer_details(asin: str, user_id: int = Depends(require_user)):
    import profit_calculator
    from scorer import CATEGORY_TO_FEE_KEY

    asin = clean_asin(asin)
    snap, history, val, my_prod = db.get_drawer_data(asin, user_id)

    title = (snap["title"] if snap else None) or (val["title"] if val else None) or (my_prod["title"] if my_prod else None) or "Unknown Product"
    category = (snap["category"] if snap else None) or (val["category"] if val else None) or "General"
    buy_price = (my_prod["supplier_cost"] if my_prod else None) or (val["buy_price"] if val else None)
    sell_price = (snap["price"] if snap else None)
    
    # Calculate real FBA / Easy Ship margin using profit_calculator if price details exist
    calc = None
    if sell_price is not None and buy_price is not None:
        fee_category = CATEGORY_TO_FEE_KEY.get(category, "other_default")
        calc = profit_calculator.calculate(
            sell_price=sell_price,
            buy_price=buy_price,
            category=fee_category,
            weight_grams=300,
            fulfillment="fba" if my_prod else "easy_ship",
            gst_rate_pct=18,
            zone="national"
        )

    referral_fee = calc["referral_fee"] if calc else None
    closing_fee = calc["closing_fee"] if calc else None
    shipping_fee = calc["weight_or_pickpack_fee"] if calc else None
    net_margin = calc["net_margin_pct"] if calc else None

    chart_points = []
    if history:
        for s in history[-7:]:
            chart_points.append({
                "day": day_label(s["collected_at"]),
                "BSR": s["rank"] if s["rank"] is not None else None,
                "Price": s["price"] if s["price"] is not None else sell_price
            })

    title_len = len(title)
    rank = snap["rank"] if snap else None
    rating = snap["rating"] if snap else None
    reviews = snap["review_count"] if snap else None

    audit_checklist = [
        {"check": f"Title length is optimized ({title_len}/150+ chars)", "pass": title_len >= 150},
        {"check": f"Review depth checked ({reviews or 0} reviews)", "pass": (reviews or 0) >= 10},
        {"check": f"Review rating checked ({rating or 0.0} stars)", "pass": (rating or 0.0) >= 4.0},
        {"check": f"Niche rank validated (BSR #{rank or 'N/A'})", "pass": rank is not None and rank <= 5000}
    ]

    return {
        "asin": asin,
        "title": title,
        "category": category,
        "price": sell_price,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "shipping_cost": shipping_fee,
        "fees": (referral_fee + closing_fee + calc["gst_on_amazon_fees_info_only"]) if (calc and referral_fee is not None and closing_fee is not None) else None,
        "net_margin": net_margin,
        "rating": rating,
        "reviews": reviews,
        "score": val["score"] if val else None,
        "verdict": val["verdict"] if val else None,
        "notes": val["notes"] if val else "",
        "trend_data": chart_points,
        "audit_checklist": audit_checklist
    }


@app.post("/storefront/sync", dependencies=[Depends(require_key)])
def sync_storefront(user_id: int = Depends(require_user)):
    result = amazon_sp_api.sync_storefront_data(user_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "Sync failed"))
    return result


@app.post("/storefront/sync-all", dependencies=[Depends(require_key)])
def sync_all_storefronts():
    """Refresh every connected seller's storefront data, in waves, with
    retry-with-backoff on transient SP-API failures and a persisted
    sync_jobs row per attempt. Authenticated by the shared X-Scout-Key only
    (no per-user header), so a scheduled job can run it daily."""
    return sync_engine.run_all_syncs()


@app.get("/storefront/sync-jobs", dependencies=[Depends(require_key)])
def sync_jobs(user_id: int = Depends(require_user), limit: int = 20):
    """Recent sync history for the authenticated account — lets you confirm
    a night's sync actually ran (and how) without reading Render's logs."""
    return {"jobs": db.get_recent_sync_jobs(user_id=user_id, limit=min(limit, 200))}


@app.get("/storefront/sales", dependencies=[Depends(require_key)])
def get_storefront_sales(user_id: int = Depends(require_user)):
    metrics = db.get_storefront_sales_metrics(user_id)
    return {"metrics": metrics}


@app.get("/storefront/orders", dependencies=[Depends(require_key)])
def get_storefront_orders(user_id: int = Depends(require_user)):
    orders = db.get_storefront_orders(user_id, limit=20)
    return {"orders": orders}


# --- Stage 5 SaaS Controls Endpoints ----------------------------------------

@app.get("/saas/audit-logs", dependencies=[Depends(require_key)])
def get_audit_logs(user_id: int = Depends(require_user)):
    logs = db.get_audit_logs(user_id, limit=50)
    return {"logs": logs}


# NOTE: there is deliberately no POST /saas/audit-logs. An audit trail whose
# actor, action and IP are supplied by the caller records whatever the caller
# wants it to say, which is worse than no audit trail because the UI presents it
# as an immutable record. Audit events are written only by the server-side code
# paths that actually perform the sensitive action (see add_org_member below).


@app.get("/saas/org-members", dependencies=[Depends(require_key)])
def get_org_members(user_id: int = Depends(require_user)):
    members = db.get_org_members(user_id)
    return {"members": members}


ORG_MEMBER_ROLES = {"Admin", "Analyst", "Viewer"}


@app.post("/saas/org-members", dependencies=[Depends(require_key)])
def add_org_member(body: dict, request: Request, user_id: int = Depends(require_user)):
    email = body.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    role = body.get("role", "Analyst")
    if role not in ORG_MEMBER_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(sorted(ORG_MEMBER_ROLES))}")

    name = body.get("name") or email.split("@")[0]
    db.add_org_member(owner_id=user_id, email=email, name=name, role=role)

    # Actor and IP are derived server-side, never taken from the request body,
    # so an audit row cannot be attributed to someone who didn't perform the action.
    actor = db.get_user_by_id(user_id)
    db.log_audit_event(
        user_id=user_id,
        actor_email=(actor or {}).get("email") or f"user:{user_id}",
        action=f"Added Team Member ({role})",
        target=email,
        ip_address=_client_ip(request),
    )
    return {"ok": True}


# --- Stage 6 Depth & Scale PPC Analytics ------------------------------------

@app.get("/analytics/ppc", dependencies=[Depends(require_key)])
def get_ppc_analytics(user_id: int = Depends(require_user)):
    validations = db.get_validations(user_id)
    sales = db.get_storefront_sales_metrics(user_id)
    return ppc_analytics.calculate_ppc_performance(validations, sales)


# --- Maxun Visual Scraper Ingestion ----------------------------------------

class MaxunRowItem(BaseModel):
    asin: str
    title: str | None = None
    category: str | None = "Maxun Visual Scrape"
    list_type: str | None = "custom-scrape"
    rank: int | None = None
    price: float | None = None
    rating: float | None = None
    reviews: int | None = None
    review_count: int | None = None
    image_url: str | None = None
    url: str | None = None
    # When the row was actually scraped, ISO-8601. Without this every row is
    # stamped with the ingest time, which collapses a backfill of historical
    # rows onto one timestamp and destroys the price-over-time axis.
    collected_at: str | None = None


class MaxunIngestPayload(BaseModel):
    items: list[MaxunRowItem]
    category: str | None = "Maxun Visual Scrape"


@app.post("/ingest/maxun", dependencies=[Depends(require_key)])
def ingest_maxun_batch(payload: MaxunIngestPayload, request: Request):
    """Ingests raw visual scraping batches from Maxun (CSV/JSON exports).
    Sanitizes ASINs, validates ratings/prices against bounds, and inserts rows into Supabase snapshots."""
    now = datetime.now(timezone.utc).isoformat()
    default_cat = payload.category or "Maxun Visual Scrape"
    valid_rows = []

    for item in payload.items:
        raw_asin = (item.asin or "").strip().upper()
        if not ASIN_RE.match(raw_asin):
            continue

        rc = item.review_count if item.review_count is not None else item.reviews
        if rc is not None and (rc < 0 or rc > 10_000_000):
            rc = None

        p = item.price
        if p is not None and (p < 1.0 or p > 10_000_000.0):
            p = None

        r = item.rating
        if r is not None and (r < 0.5 or r > 5.0):
            r = None

        rank_val = item.rank
        if rank_val is not None and (rank_val < 1 or rank_val > 10_000_000):
            rank_val = None

        # Prefer the time the row was actually scraped. Falling back to `now`
        # for everything collapses a historical backfill onto a single
        # timestamp, which destroys the price-over-time axis those rows exist
        # for. Anything unparseable or implausible falls back rather than
        # writing a date that would silently corrupt a trend line.
        collected = now
        if item.collected_at:
            try:
                parsed = datetime.fromisoformat(item.collected_at.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                if EARLIEST_PLAUSIBLE <= parsed <= datetime.now(timezone.utc) + timedelta(days=1):
                    collected = parsed.isoformat()
            except (ValueError, TypeError):
                pass

        valid_rows.append({
            "asin": raw_asin,
            "category": item.category or default_cat,
            "list_type": item.list_type or "custom-scrape",
            "rank": rank_val,
            "title": html.unescape(item.title.strip()) if item.title else None,
            "price": p,
            "rating": r,
            "review_count": rc,
            "image_url": item.image_url,
            "collected_at": collected,
        })

    inserted_count = db.insert_snapshot_rows(valid_rows)
    return {
        "ok": True,
        "processed": len(payload.items),
        "inserted": inserted_count,
        "skipped": len(payload.items) - len(valid_rows),
    }


