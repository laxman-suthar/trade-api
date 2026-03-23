from collections import defaultdict
from datetime import datetime, timezone
from fastapi import HTTPException, status
from config import get_settings

settings = get_settings()

# Structure: { username: [timestamp1, timestamp2, ...] }
_request_log: dict[str, list[datetime]] = defaultdict(list)


def _clean_old_requests(username: str) -> None:
    """Remove timestamps outside the current window."""
    now = datetime.now(timezone.utc)
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    _request_log[username] = [
        ts for ts in _request_log[username]
        if (now - ts).total_seconds() < window
    ]


def check_rate_limit(username: str) -> None:
    """
    Call this at the start of every protected endpoint.
    Raises 429 if the user has exceeded their limit.
    """
    _clean_old_requests(username)

    request_count = len(_request_log[username])

    if request_count >= settings.RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Rate limit exceeded. You can make {settings.RATE_LIMIT_REQUESTS} "
                f"requests per {settings.RATE_LIMIT_WINDOW_SECONDS // 3600} hour(s). "
                f"Please try again later."
            ),
            headers={"Retry-After": str(settings.RATE_LIMIT_WINDOW_SECONDS)},
        )

    # Log this request
    _request_log[username].append(datetime.now(timezone.utc))


def get_usage_stats(username: str) -> dict:
    """Returns current usage info for a user — useful for headers/debug."""
    _clean_old_requests(username)
    used = len(_request_log[username])
    return {
        "requests_used": used,
        "requests_remaining": max(0, settings.RATE_LIMIT_REQUESTS - used),
        "limit": settings.RATE_LIMIT_REQUESTS,
        "window_seconds": settings.RATE_LIMIT_WINDOW_SECONDS,
    }