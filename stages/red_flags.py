"""
stages/red_flags.py — Automatic red flag detection for candidate profiles.

Uses cached pipeline data only (no extra API calls for most flags).
Raises flags when a candidate looks good on paper but has serious warning signs.

Flags:
  ghost_developer    → Active days = 0, 90+ days inactive
  copy_paste_coder   → Majority of repos are forks
  tutorial_only      → All repo names match course/bootcamp patterns
  padded_portfolio   → Many repos but suspiciously few files per repo
  ghost_account      → Very new account, 0 followers, generic bio
  no_original_work   → 0 original (non-forked) repos with stars
  single_language    → Entire portfolio is one language (low versatility)
  no_readme          → None of the repos have README files
"""

import re
from datetime import datetime, timezone

# ── Heuristic patterns ────────────────────────────────────────────────────────

_TUTORIAL_RE = re.compile(
    r"(tutorial|course|bootcamp|udemy|coursera|leetcode|hackerrank|"
    r"hello[_-]world|practice|learning|study|exercise|assignment|"
    r"week\d|day\d|module\d|project[-_]?\d|todo[-_]?app|"
    r"weather[-_]?app|calculator|portfolio[-_]?template)",
    re.IGNORECASE,
)

_GENERIC_BIO_RE = re.compile(
    r"^(student|developer|programmer|coder|"
    r"i am a|i'm a|software engineer|"
    r"learning to code|aspiring developer)$",
    re.IGNORECASE,
)


def detect_red_flags(candidate: dict, enrichment: dict | None = None) -> dict:
    """
    Scan a candidate's cached data for red flags.

    Args:
        candidate:  enriched candidate dict from candidates_cache.json
        enrichment: optional code quality enrichment (adds per_repo data)

    Returns:
        {
          "flags":        [{"id", "label", "severity", "detail"}],
          "flag_count":   int,
          "severity":     "high" | "medium" | "low" | "clean",
          "clean":        bool,
          "summary":      str,
        }
    """
    flags = []
    activity = candidate.get("activity", {}) or {}
    projects = candidate.get("projects", []) or []
    bio      = str(candidate.get("bio") or "").strip()
    scoring  = candidate.get("scoring", {}) or {}

    total_commits = int(activity.get("total_commits", 0))
    active_days   = int(activity.get("active_days", 0))
    stars_total   = int(activity.get("stars_total", 0))
    consistency   = float(activity.get("consistency_score", 0))

    n_projects    = len(projects)
    original_proj = [p for p in projects if p.get("is_original", False)]
    starred_proj  = [p for p in projects if p.get("stars", 0) > 0]

    # ── Flag 1: Ghost developer ───────────────────────────────────────────
    if total_commits == 0 and active_days == 0:
        flags.append({
            "id":       "ghost_developer",
            "label":    "Ghost Developer",
            "severity": "high",
            "detail":   "0 commits in the lookback window and 0 active days tracked.",
            "emoji":    "👻",
        })

    # ── Flag 2: Copy-paste coder (all repos are forks) ───────────────────
    if n_projects >= 3:
        fork_ratio = 1 - (len(original_proj) / max(n_projects, 1))
        if fork_ratio >= 0.85:
            flags.append({
                "id":       "copy_paste_coder",
                "label":    "Mostly Forks",
                "severity": "medium",
                "detail":   f"{round(fork_ratio*100)}% of top repos are forks of others' work.",
                "emoji":    "🍴",
            })

    # ── Flag 3: Tutorial-only portfolio ──────────────────────────────────
    tutorial_repos = [
        p for p in projects
        if _TUTORIAL_RE.search(p.get("name", "")) or _TUTORIAL_RE.search(p.get("description", "") or "")
    ]
    if n_projects >= 2 and len(tutorial_repos) / max(n_projects, 1) >= 0.70:
        flags.append({
            "id":       "tutorial_only",
            "label":    "Tutorial-Only Portfolio",
            "severity": "medium",
            "detail":   f"{len(tutorial_repos)}/{n_projects} repos appear to be course exercises or tutorials.",
            "emoji":    "📚",
        })

    # ── Flag 4: No original work with community traction ─────────────────
    if stars_total == 0 and n_projects >= 5:
        flags.append({
            "id":       "no_traction",
            "label":    "No Community Recognition",
            "severity": "low",
            "detail":   "0 stars across all repos — no community traction found.",
            "emoji":    "⭐",
        })

    # ── Flag 5: Ghost account (bio is generic, no activity) ───────────────
    bio_is_generic = not bio or len(bio) < 5 or _GENERIC_BIO_RE.match(bio)
    if bio_is_generic and total_commits < 5 and stars_total == 0:
        flags.append({
            "id":       "ghost_account",
            "label":    "Possibly Inactive Account",
            "severity": "medium",
            "detail":   "Minimal bio, very few commits, and no stars suggest a dormant or empty account.",
            "emoji":    "🌫️",
        })

    # ── Flag 6: Single-language portfolio (low versatility) ──────────────
    top_langs = activity.get("top_languages", []) or []
    if len(top_langs) == 1 and total_commits > 10:
        flags.append({
            "id":       "single_language",
            "label":    "Single-Language Portfolio",
            "severity": "low",
            "detail":   f"Only '{top_langs[0]}' detected across all repos — limited tech breadth.",
            "emoji":    "🔵",
        })

    # ── Flag 7: High garbage commit ratio ─────────────────────────────────
    garbage_ratio = float(activity.get("garbage_commits", 0)) / max(total_commits, 1)
    if garbage_ratio > 0.5 and total_commits > 10:
        flags.append({
            "id":       "poor_commit_hygiene",
            "label":    "Poor Commit Hygiene",
            "severity": "low",
            "detail":   f"{round(garbage_ratio*100)}% of commits have generic messages like 'update', 'fix', 'wip'.",
            "emoji":    "💬",
        })

    # ── Flag 8: Enrichment-based — padded portfolio (many repos, tiny files) ──
    if enrichment and isinstance(enrichment, dict):
        per_repo = enrichment.get("per_repo", []) or []
        tiny_repos = [r for r in per_repo if r.get("file_count", 99) < 4 and not r.get("is_fork", True)]
        if len(tiny_repos) >= 3 and len(per_repo) >= 5:
            flags.append({
                "id":       "padded_portfolio",
                "label":    "Padded Portfolio",
                "severity": "medium",
                "detail":   f"{len(tiny_repos)} original repos have fewer than 4 files — likely empty or demo repos.",
                "emoji":    "🎭",
            })

        # No README culture
        repos_with_readme = enrichment.get("repos_with_readme", 0)
        repo_count = enrichment.get("repo_count", 1)
        if repo_count >= 3 and (repos_with_readme / max(repo_count, 1)) < 0.2:
            flags.append({
                "id":       "no_documentation",
                "label":    "No Documentation Culture",
                "severity": "low",
                "detail":   f"Less than 20% of repos have a README ({repos_with_readme}/{repo_count}).",
                "emoji":    "📄",
            })

    # ── Severity rollup ───────────────────────────────────────────────────
    if any(f["severity"] == "high" for f in flags):
        severity = "high"
    elif any(f["severity"] == "medium" for f in flags):
        severity = "medium"
    elif flags:
        severity = "low"
    else:
        severity = "clean"

    summary_map = {
        "clean":  "✅ No red flags found — clean profile",
        "low":    "🟡 Minor concerns — worth discussing in interview",
        "medium": "🟠 Significant concerns — review carefully",
        "high":   "🔴 Major red flags — proceed with caution",
    }

    return {
        "flags":      flags,
        "flag_count": len(flags),
        "severity":   severity,
        "clean":      len(flags) == 0,
        "summary":    summary_map[severity],
    }
