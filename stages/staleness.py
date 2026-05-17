"""
stages/staleness.py — Detect how recently a candidate was active on GitHub.

Uses only the `pushed_at` field from repos — fast, no commit fetching needed.
"""

from datetime import datetime, timezone


LABELS = {
    "active_now":  {"label": "🔥 Active Now",  "color": "#1D9E75", "days": (0,   7)},
    "recent":      {"label": "✅ Recent",        "color": "#40cef3", "days": (7,   30)},
    "cooling":     {"label": "🌡️ Cooling",       "color": "#E6A817", "days": (30,  90)},
    "gone_cold":   {"label": "❄️ Gone Cold",     "color": "#888",    "days": (90,  None)},
    "no_data":     {"label": "⚪ No Data",        "color": "#555",    "days": None},
}


def analyze_staleness(user) -> dict:
    """
    Check the candidate's most recent GitHub activity using pushed_at timestamps.

    Returns:
        staleness_key    (str)  — active_now | recent | cooling | gone_cold | no_data
        staleness_label  (str)  — human-readable label with emoji
        color            (str)  — hex color for badge
        days_since_active (int) — days since most recent push
        last_active_date (str)  — ISO date string of most recent push
        is_actively_searching (bool) — heuristic: repo count grew fast + recent activity
    """
    now = datetime.now(timezone.utc)

    try:
        repos = list(user.get_repos())
    except Exception:
        return _result("no_data", None, None)

    if not repos:
        return _result("no_data", None, None)

    # Find the most recently pushed repo
    latest_push = None
    for repo in repos:
        if repo.pushed_at:
            pushed = repo.pushed_at
            if pushed.tzinfo is None:
                pushed = pushed.replace(tzinfo=timezone.utc)
            if latest_push is None or pushed > latest_push:
                latest_push = pushed

    if latest_push is None:
        return _result("no_data", None, None)

    days_ago = (now - latest_push).days
    last_date = latest_push.strftime("%Y-%m-%d")

    # Classify
    if days_ago <= 7:
        key = "active_now"
    elif days_ago <= 30:
        key = "recent"
    elif days_ago <= 90:
        key = "cooling"
    else:
        key = "gone_cold"

    # Heuristic: actively job searching?
    # Recent activity + bio contains job-search keywords
    bio = (user.bio or "").lower()
    job_keywords = ("open to work", "looking for", "seeking", "internship", "available", "hire me")
    is_searching = days_ago <= 30 and any(k in bio for k in job_keywords)

    return _result(key, days_ago, last_date, is_searching)


def _result(key: str, days: int | None, last_date: str | None, is_searching: bool = False) -> dict:
    meta = LABELS[key]
    return {
        "staleness_key":      key,
        "staleness_label":    meta["label"],
        "color":              meta["color"],
        "days_since_active":  days,
        "last_active_date":   last_date,
        "is_actively_searching": is_searching,
    }
