"""
stages/commit_pattern.py — Behavioral archetype detection from commit timestamps.

Analyzes WHEN a developer commits (hour of day, day of week) to classify:
  - Night Owl      (codes late at night)
  - Weekend Warrior (commits mostly on weekends)
  - Daily Coder    (consistent every-day contributor)
  - Sprinter       (burst activity in short windows)
  - Balanced       (no dominant pattern)

Returns a heatmap_data array for visualization.
"""

from datetime import datetime, timedelta, timezone
from collections import defaultdict
import config


def analyze_commit_pattern(user) -> dict:
    """
    Fetch recent commits across all repos and classify the coding behavior archetype.

    Returns:
        archetype         (str) — one of Night Owl, Weekend Warrior, Daily Coder, Sprinter, Balanced
        peak_hour         (int) — hour of day (0-23) with most commits
        peak_day          (str) — day of week with most commits
        heatmap_data      (list[dict]) — [{hour, day, count}] for frontend heatmap
        commit_hours      (dict) — {hour: count} distribution
        commit_days       (dict) — {day_name: count} distribution
        total_analyzed    (int)
    """
    since = datetime.now(timezone.utc) - timedelta(days=config.COMMITS_LOOKBACK)

    hour_counts = defaultdict(int)   # 0-23
    day_counts  = defaultdict(int)   # 0=Mon … 6=Sun
    daily_activity = defaultdict(int) # date → count (for sprinter detection)

    total = 0

    try:
        repos = [r for r in user.get_repos() if not r.fork][:8]
    except Exception:
        repos = []

    for repo in repos:
        try:
            commits = repo.get_commits(since=since, author=user.login)
            for c in commits:
                if c.commit.author and c.commit.author.date:
                    dt = c.commit.author.date
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    hour_counts[dt.hour]      += 1
                    day_counts[dt.weekday()]  += 1
                    daily_activity[dt.date()] += 1
                    total += 1
        except Exception:
            continue

    if total == 0:
        return {
            "archetype": "No Data",
            "peak_hour": None,
            "peak_day": None,
            "heatmap_data": [],
            "commit_hours": {},
            "commit_days": {},
            "total_analyzed": 0,
        }

    # ── Archetype classification ──────────────────────────────────────────
    night_commits   = sum(hour_counts[h] for h in range(22, 24)) + sum(hour_counts[h] for h in range(0, 5))
    weekend_commits = day_counts[5] + day_counts[6]  # Sat + Sun
    distinct_days   = len(daily_activity)

    night_ratio   = night_commits / total
    weekend_ratio = weekend_commits / total

    # Sprinter: >60% commits concentrated in any 14-day window
    sprinter = False
    dates_sorted = sorted(daily_activity.keys())
    if len(dates_sorted) >= 2:
        for i, start in enumerate(dates_sorted):
            window_end   = start + timedelta(days=14)
            window_total = sum(cnt for d, cnt in daily_activity.items() if start <= d <= window_end)
            if window_total / total > 0.70:
                sprinter = True
                break

    if night_ratio > 0.40:
        archetype = "Night Owl"
    elif weekend_ratio > 0.55:
        archetype = "Weekend Warrior"
    elif distinct_days >= 18:          # commits on 18+ different days in 90d
        archetype = "Daily Coder"
    elif sprinter:
        archetype = "Sprinter"
    else:
        archetype = "Balanced"

    # ── Peak hour / day ───────────────────────────────────────────────────
    peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
    peak_day_num = max(day_counts, key=day_counts.get) if day_counts else None
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    peak_day  = day_names[peak_day_num] if peak_day_num is not None else None

    # ── Heatmap data (for frontend grid) ─────────────────────────────────
    heatmap_data = [
        {"hour": h, "day": d, "count": hour_counts.get(h, 0) if day_counts.get(d, 0) > 0 else 0}
        for d in range(7)
        for h in range(24)
    ]
    # Simplify: just return hour and day marginals for a cleaner chart
    heatmap_hours = [{"hour": h, "count": hour_counts.get(h, 0)} for h in range(24)]
    heatmap_days  = [{"day": day_names[d], "count": day_counts.get(d, 0)} for d in range(7)]

    return {
        "archetype":      archetype,
        "peak_hour":      peak_hour,
        "peak_day":       peak_day,
        "heatmap_hours":  heatmap_hours,
        "heatmap_days":   heatmap_days,
        "commit_hours":   dict(hour_counts),
        "commit_days":    {day_names[d]: cnt for d, cnt in day_counts.items()},
        "night_ratio":    round(night_ratio, 3),
        "weekend_ratio":  round(weekend_ratio, 3),
        "distinct_days":  distinct_days,
        "total_analyzed": total,
    }
