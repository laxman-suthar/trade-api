from datetime import datetime, timezone
from collections import defaultdict

# Structure:
# {
#   "demo": {
#       "started_at": datetime,
#       "last_active": datetime,
#       "total_requests": 3,
#       "sectors_queried": ["pharmaceuticals", "textiles"],
#       "request_log": [
#           {"sector": "pharmaceuticals", "timestamp": datetime, "status": "success"},
#           ...
#       ]
#   }
# }

_sessions: dict[str, dict] = {}


def init_session(username: str) -> None:
    """
    Create a new session for user if one doesn't exist.
    Called on first request after login.
    """
    if username not in _sessions:
        _sessions[username] = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_active": datetime.now(timezone.utc).isoformat(),
            "total_requests": 0,
            "sectors_queried": [],
            "request_log": [],
        }


def log_request(username: str, sector: str, status: str = "success") -> None:
    """
    Log each analyze request against the user's session.
    status: "success" | "failed"
    """
    init_session(username)

    session = _sessions[username]
    session["total_requests"] += 1
    session["last_active"] = datetime.now(timezone.utc).isoformat()

    # Track unique sectors only
    if sector not in session["sectors_queried"]:
        session["sectors_queried"].append(sector)

    # Full request log
    session["request_log"].append({
        "sector": sector,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
    })


def get_session(username: str) -> dict:
    """Returns session data for a user."""
    init_session(username)
    return _sessions[username]


def get_all_sessions() -> dict:
    """Returns all active sessions — useful for admin/debug."""
    return _sessions