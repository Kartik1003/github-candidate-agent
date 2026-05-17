"""
stages/growth.py — Growth trajectory detection.

Analyzes whether a candidate is improving, plateauing, or declining.

Signals:
  - Language complexity progression (HTML → JS → TS → Go/Rust = growth)
  - Repo creation frequency trend (are they building more lately?)
  - Stars trend (growing community interest?)
  - Commit message quality improvement
  - Tech stack expansion (adding new tools over time)

Uses only repo metadata (created_at, pushed_at, language, stars) — no content fetching.
"""

from datetime import datetime, timezone
from collections import defaultdict
import math


# Language complexity ranking (higher = more complex/senior)
LANG_COMPLEXITY = {
    "HTML":              1,
    "CSS":               1,
    "Markdown":          1,
    "JSON":              1,
    "Jupyter Notebook":  2,
    "PHP":               2,
    "JavaScript":        3,
    "Python":            3,
    "Ruby":              3,
    "Shell":             3,
    "TypeScript":        4,
    "Java":              4,
    "Kotlin":            4,
    "Swift":             4,
    "C#":                4,
    "Go":                5,
    "Rust":              5,
    "C++":               5,
    "C":                 4,
    "Scala":             5,
    "Haskell":           5,
    "Elixir":            5,
}

# Tech stack progression tiers
TECH_TIERS = [
    {"tier": 1, "label": "Beginner",      "langs": {"HTML", "CSS", "Markdown"}},
    {"tier": 2, "label": "Learner",       "langs": {"JavaScript", "Python", "PHP", "Jupyter Notebook"}},
    {"tier": 3, "label": "Intermediate",  "langs": {"TypeScript", "Java", "Kotlin", "C#", "Ruby"}},
    {"tier": 4, "label": "Advanced",      "langs": {"Go", "Rust", "C++", "Swift", "Scala"}},
]


def _repo_half_point(repos: list, key="created_at") -> tuple[list, list]:
    """Split repos into older half and newer half by creation date."""
    sorted_repos = sorted(repos, key=lambda r: r.get(key) or "")
    mid = len(sorted_repos) // 2
    return sorted_repos[:mid], sorted_repos[mid:]


def analyze_growth(user) -> dict:
    """
    Analyze the growth trajectory of a GitHub user.

    Returns:
        {
          "trajectory":        "📈 Growing Fast" | "➡️ Steady" | "⚠️ Plateaued" | "📉 Slowing Down"
          "trajectory_key":   str
          "trajectory_color": str
          "signals":          [str]  — human-readable signal descriptions
          "complexity_trend": "increasing" | "stable" | "decreasing"
          "current_tier":     str
          "stars_trend":      "growing" | "stable" | "none"
          "repo_trend":       "accelerating" | "steady" | "slowing"
          "tech_expansion":   int  — number of new languages in last 6 months
          "timeline":         [{year, month, repos_created, stars}]  — for charting
        }
    """
    try:
        repos = [r for r in user.get_repos() if not r.fork]
    except Exception:
        return _empty_result()

    if not repos:
        return _empty_result()

    # ── Build timeline data ───────────────────────────────────────────────
    now = datetime.now(timezone.utc)

    repo_data = []
    for r in repos:
        created = r.created_at
        pushed  = r.pushed_at
        if created and created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if pushed and pushed.tzinfo is None:
            pushed = pushed.replace(tzinfo=timezone.utc)
        repo_data.append({
            "name":      r.name,
            "language":  r.language or "Unknown",
            "stars":     r.stargazers_count,
            "created_at": created.isoformat() if created else None,
            "pushed_at":  pushed.isoformat() if pushed else None,
            "created_dt": created,
        })

    # Sort by creation
    repo_data.sort(key=lambda x: x["created_dt"] or now)

    # ── Monthly timeline for charting ─────────────────────────────────────
    monthly: dict[str, dict] = defaultdict(lambda: {"repos": 0, "stars": 0})
    for r in repo_data:
        if r["created_dt"]:
            key = r["created_dt"].strftime("%Y-%m")
            monthly[key]["repos"] += 1
            monthly[key]["stars"] += r["stars"]

    timeline = [{"period": k, **v} for k, v in sorted(monthly.items())]

    # ── Language complexity trend ─────────────────────────────────────────
    old_half, new_half = _repo_half_point(repo_data)

    def avg_complexity(half):
        scores = [LANG_COMPLEXITY.get(r["language"], 2) for r in half if r["language"] != "Unknown"]
        return sum(scores) / max(len(scores), 1)

    old_complexity = avg_complexity(old_half)
    new_complexity = avg_complexity(new_half)
    complexity_delta = new_complexity - old_complexity

    if complexity_delta >= 0.5:
        complexity_trend = "increasing"
    elif complexity_delta <= -0.5:
        complexity_trend = "decreasing"
    else:
        complexity_trend = "stable"

    # ── Current tech tier ─────────────────────────────────────────────────
    recent_langs = set(r["language"] for r in repo_data[-8:] if r["language"] != "Unknown")
    current_tier_label = "Beginner"
    current_tier_num   = 1
    for tier_info in sorted(TECH_TIERS, key=lambda t: -t["tier"]):
        if recent_langs.intersection(tier_info["langs"]):
            current_tier_label = tier_info["label"]
            current_tier_num   = tier_info["tier"]
            break

    # ── Tech expansion (new languages in last 6 months) ──────────────────
    six_months_ago = now.replace(month=now.month - 6 if now.month > 6 else now.month + 6,
                                 year=now.year if now.month > 6 else now.year - 1)
    old_langs   = set(r["language"] for r in repo_data if r["created_dt"] and r["created_dt"] < six_months_ago)
    new_langs   = set(r["language"] for r in repo_data if r["created_dt"] and r["created_dt"] >= six_months_ago)
    new_lang_count = len(new_langs - old_langs)

    # ── Repo creation trend (accelerating vs slowing) ─────────────────────
    old_count = len(old_half)
    new_count = len(new_half)
    if new_count > old_count * 1.3:
        repo_trend = "accelerating"
    elif new_count < old_count * 0.7:
        repo_trend = "slowing"
    else:
        repo_trend = "steady"

    # ── Stars trend ───────────────────────────────────────────────────────
    old_stars = sum(r["stars"] for r in old_half)
    new_stars = sum(r["stars"] for r in new_half)
    total_stars = sum(r["stars"] for r in repo_data)

    if total_stars == 0:
        stars_trend = "none"
    elif new_stars >= old_stars:
        stars_trend = "growing"
    else:
        stars_trend = "stable"

    # ── Trajectory classification ─────────────────────────────────────────
    signals = []
    score   = 0

    if complexity_trend == "increasing":
        score += 2
        signals.append(f"Tech complexity is increasing (avg {old_complexity:.1f} → {new_complexity:.1f}/5)")
    elif complexity_trend == "decreasing":
        score -= 1
        signals.append("Tech complexity appears to be decreasing in recent repos")

    if repo_trend == "accelerating":
        score += 1
        signals.append(f"Building more repos recently ({new_count} new vs {old_count} older)")
    elif repo_trend == "slowing":
        score -= 1
        signals.append(f"Creating fewer repos recently ({new_count} recent vs {old_count} older)")

    if stars_trend == "growing":
        score += 1
        signals.append("Newer repos earning more community stars")

    if new_lang_count >= 2:
        score += 1
        signals.append(f"{new_lang_count} new languages explored in last 6 months")

    if current_tier_num >= 4:
        score += 1
        signals.append(f"Working at {current_tier_label} tech level (Go, Rust, C++, Swift)")

    if score >= 4:
        trajectory     = "📈 Growing Fast"
        trajectory_key = "growing_fast"
        color          = "#1D9E75"
    elif score >= 2:
        trajectory     = "📈 Steady Growth"
        trajectory_key = "steady"
        color          = "#40cef3"
    elif score >= 0:
        trajectory     = "➡️ Plateaued"
        trajectory_key = "plateaued"
        color          = "#E6A817"
    else:
        trajectory     = "📉 Slowing Down"
        trajectory_key = "slowing"
        color          = "#E64D4D"

    if not signals:
        signals.append("Not enough repo history to determine clear trend")

    return {
        "trajectory":         trajectory,
        "trajectory_key":     trajectory_key,
        "trajectory_color":   color,
        "signals":            signals,
        "complexity_trend":   complexity_trend,
        "old_complexity":     round(old_complexity, 2),
        "new_complexity":     round(new_complexity, 2),
        "current_tier":       current_tier_label,
        "current_tier_num":   current_tier_num,
        "stars_trend":        stars_trend,
        "repo_trend":         repo_trend,
        "tech_expansion":     new_lang_count,
        "new_languages":      list(new_langs - old_langs),
        "total_repos":        len(repo_data),
        "timeline":           timeline[-18:],  # last 18 months for chart
    }


def _empty_result() -> dict:
    return {
        "trajectory":       "➡️ Plateaued",
        "trajectory_key":   "no_data",
        "trajectory_color": "#888",
        "signals":          ["No repos found to analyze"],
        "complexity_trend": "stable",
        "old_complexity":   0,
        "new_complexity":   0,
        "current_tier":     "Unknown",
        "current_tier_num": 0,
        "stars_trend":      "none",
        "repo_trend":       "steady",
        "tech_expansion":   0,
        "new_languages":    [],
        "total_repos":      0,
        "timeline":         [],
    }
