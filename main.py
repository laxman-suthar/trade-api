import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from config import get_settings
from auth import (
    LoginRequest,
    TokenResponse,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from rate_limiter import check_rate_limit, get_usage_stats
from data_collector import collect_sector_data
from analyzer import analyze_sector
from session_tracking import log_request, get_session

# ---------- Logging setup ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# ---------- Valid sectors ----------
VALID_SECTORS = {
    "pharmaceuticals",
    "technology",
    "agriculture",
    "banking",
    "finance",
    "automobile",
    "energy",
    "infrastructure",
    "fmcg",
    "real estate",
    "healthcare",
    "metals",
    "chemicals",
    "textiles",
    "telecom",
}

# ---------- FastAPI app ----------
app = FastAPI(
    title=settings.APP_TITLE,
    description=(
        "Analyzes Indian market sectors using live web data and Gemini AI. "
        "Returns structured markdown trade opportunity reports."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------- Health check (public) ----------

@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
)
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
    }


# ---------- Login (public) ----------

@app.post(
    "/login",
    response_model=TokenResponse,
    tags=["Auth"],
    summary="Get JWT access token",
    description=(
        "Login with username and password to receive a JWT token. "
        "Use this token as `Bearer <token>` in the Authorization header for protected endpoints.\n\n"
        "**Demo credentials:** `demo / demo123` or `admin / admin123`"
    ),
)
async def login(body: LoginRequest):
    username = authenticate_user(body.username, body.password)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(username)
    logger.info(f"Login successful: {username}")

    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.JWT_EXPIRY_MINUTES,
    )


# ---------- Core endpoint (protected) ----------

@app.get(
    "/analyze/{sector}",
    response_class=PlainTextResponse,
    tags=["Analysis"],
    summary="Get trade opportunities report for a sector",
    description=(
        "Accepts an Indian market sector name and returns a structured markdown report "
        "with current trade opportunities, key stocks, risks, and analyst recommendations.\n\n"
        "**Requires:** Bearer JWT token from `/login`\n\n"
        "**Rate limit:** 5 requests per hour per user\n\n"
        "**Example sectors:** pharmaceuticals, technology, banking, agriculture, energy"
    ),
    responses={
        200: {"content": {"text/plain": {}}, "description": "Markdown report"},
        400: {"description": "Invalid sector name"},
        401: {"description": "Missing or invalid token"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def analyze(
    sector: str,
    current_user: str = Depends(get_current_user),
):
    # 1. Validate sector name
    sector_clean = sector.strip().lower()

    if not sector_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sector name cannot be empty.",
        )

    if len(sector_clean) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sector name too long. Max 50 characters.",
        )

    if sector_clean not in VALID_SECTORS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"'{sector}' is not a supported sector. "
                f"Valid sectors: {', '.join(sorted(VALID_SECTORS))}"
            ),
        )

    # 2. Rate limit check
    check_rate_limit(current_user)

    # 3. Log request
    stats = get_usage_stats(current_user)
    logger.info(
        f"Analyze request | user={current_user} | sector={sector_clean} | "
        f"usage={stats['requests_used']}/{stats['limit']}"
    )

    # 4. Collect market data
    try:
        market_data = collect_sector_data(sector_clean)
    except Exception as e:
        logger.warning(f"Data collection failed for '{sector_clean}': {e}. Proceeding without it.")
        market_data = None

    # 5. Run Gemini analysis
    try:
        report = analyze_sector(sector_clean, market_data)
        log_request(current_user, sector_clean, status="success")
    except RuntimeError as e:
        log_request(current_user, sector_clean, status="failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    # 6. Return markdown report as plain text
    filename = f"{sector_clean}_trade_report.md"

    return PlainTextResponse(
        content=report,
         media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Sector": sector_clean,
            "X-User": current_user,
            "X-Requests-Used": str(stats["requests_used"]),
            "X-Requests-Remaining": str(stats["requests_remaining"]),
        },
    )


# ---------- Usage stats endpoint (protected) ----------

@app.get(
    "/usage",
    tags=["Auth"],
    summary="Check your current rate limit usage",
)
async def usage(current_user: str = Depends(get_current_user)):
    stats = get_usage_stats(current_user)
    return {
        "user": current_user,
        **stats,
    }


# ---------- Session endpoint (protected) ----------

@app.get(
    "/session",
    tags=["Session"],
    summary="Get your current session details",
    description="Returns your session info — when it started, which sectors you queried, total requests made.",
)
async def session(current_user: str = Depends(get_current_user)):
    return {
        "user": current_user,
        **get_session(current_user),
    }
 
 