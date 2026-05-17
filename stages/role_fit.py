"""
stages/role_fit.py — CEO-defined job requirements → candidate % match score.

The CEO defines a RoleProfile once. This module scores every candidate against it
using a weighted multi-signal comparison.

Signal sources (all from cached data — no GitHub API calls needed):
  - Required languages / tech stack  (from activity.top_languages + code_quality tools)
  - Nice-to-have skills              (partial credit)
  - Minimum commit count             (from activity.total_commits)
  - Minimum stars                    (from activity.stars_total)
  - Has tests requirement            (from code_quality.has_tests)
  - Domain match                     (from category.primary_domain)
  - Activity recency                 (from activity.active_days + scoring.score)
"""

import re
from typing import Any

# ── Tech alias normalization ─────────────────────────────────────────────────
# Maps common CEO shorthand → normalized tags that match our pipeline output

_ALIASES: dict[str, list[str]] = {
    "python":      ["Python"],
    "js":          ["JavaScript"],
    "javascript":  ["JavaScript"],
    "ts":          ["TypeScript"],
    "typescript":  ["TypeScript"],
    "react":       ["React", "JavaScript", "TypeScript"],
    "node":        ["JavaScript", "TypeScript"],
    "nodejs":      ["JavaScript", "TypeScript"],
    "java":        ["Java"],
    "kotlin":      ["Kotlin", "Java"],
    "swift":       ["Swift"],
    "go":          ["Go"],
    "rust":        ["Rust"],
    "c++":         ["C++"],
    "cpp":         ["C++"],
    "c#":          ["C#"],
    "csharp":      ["C#"],
    "php":         ["PHP"],
    "ruby":        ["Ruby"],
    "dart":        ["Dart"],
    "flutter":     ["Dart", "Flutter"],
    "django":      ["Python", "Django"],
    "fastapi":     ["Python", "FastAPI"],
    "flask":       ["Python", "Flask"],
    "nextjs":      ["Next.js", "TypeScript", "JavaScript"],
    "vue":         ["Vue", "JavaScript"],
    "android":     ["Kotlin", "Java"],
    "ios":         ["Swift"],
    "ml":          ["Python", "Jupyter Notebook"],
    "ai":          ["Python", "Jupyter Notebook"],
    "data":        ["Python", "Jupyter Notebook"],
    "devops":      ["Docker", "GitHub Actions"],
    "docker":      ["Docker"],
    "kubernetes":  ["Kubernetes"],
    "postgres":    ["PostgreSQL"],
    "postgresql":  ["PostgreSQL"],
    "sql":         ["PostgreSQL", "MySQL", "SQLite"],
    "mongodb":     ["MongoDB"],
    "redis":       ["Redis"],
    "graphql":     ["GraphQL"],
    "testing":     ["Pytest", "Jest", "Vitest", "Mocha"],
    "tests":       ["Pytest", "Jest"],
}

COMPLEXITY_ORDER = ["HTML", "CSS", "JavaScript", "Python", "TypeScript", "Go", "Rust", "C++", "Java", "Kotlin"]


def _normalize_skill(skill: str) -> list[str]:
    """Expand a shorthand skill to its canonical names."""
    s = skill.strip().lower()
    return _ALIASES.get(s, [skill.strip()])


def _candidate_tech_set(candidate: dict, enrichment: dict | None) -> set[str]:
    """Build a unified set of all technologies we know about this candidate."""
    tech = set()

    # From pipeline: top languages
    for lang in candidate.get("activity", {}).get("top_languages", []):
        tech.add(lang)

    # From pipeline: project languages
    for proj in candidate.get("projects", []):
        for lang in proj.get("languages", []):
            if lang != "url":
                tech.add(lang)

    # From enrichment: code quality tools
    if enrichment and isinstance(enrichment, dict):
        for tool in enrichment.get("all_tools", []):
            tech.add(tool)
        for lang in enrichment.get("top_languages", []):
            tech.add(lang)

    return tech


def score_candidate(candidate: dict, role: dict, enrichment: dict | None = None) -> dict:
    """
    Score a single candidate against a CEO role profile.

    Args:
        candidate: enriched candidate dict from candidates_cache.json
        role:      role profile dict (see RoleProfile schema below)
        enrichment: optional code quality enrichment for the candidate

    RoleProfile schema:
        {
          "title":          str,
          "required":       [str],   # must-have skills (lang/tool names)
          "nice_to_have":   [str],   # bonus skills
          "min_commits":    int,
          "min_stars":      int,
          "needs_tests":    bool,
          "domain":         str | None,  # "backend", "ai_ml", "frontend" etc.
          "needs_live_project": bool,
          "weights": {               # optional custom weights (must sum to 1.0)
              "skills": 0.40,
              "activity": 0.20,
              "code_quality": 0.20,
              "nice_to_have": 0.10,
              "thresholds": 0.10,
          }
        }

    Returns:
        {
          "match_pct":     int (0-100),
          "match_label":   str ("Strong Match" / "Good Fit" / "Partial Fit" / "Poor Fit"),
          "breakdown":     {...},
          "missing":       [str],    # required skills this candidate lacks
          "matched":       [str],    # required skills confirmed
          "bonuses":       [str],    # nice-to-have skills matched
          "flags":         [str],    # threshold violations
        }
    """
    weights = role.get("weights") or {}   # guard: None → {}
    w_skills    = weights.get("skills",       0.40)
    w_activity  = weights.get("activity",     0.20)
    w_quality   = weights.get("code_quality", 0.20)
    w_nice      = weights.get("nice_to_have", 0.10)
    w_thresh    = weights.get("thresholds",   0.10)

    tech_set    = _candidate_tech_set(candidate, enrichment)
    activity    = candidate.get("activity", {}) or {}
    scoring     = candidate.get("scoring", {}) or {}
    category    = candidate.get("category", {}) or {}
    quality     = enrichment or {}

    # ── 1. Required skills score (0-1) ───────────────────────────────────
    required    = role.get("required", [])
    matched     = []
    missing     = []

    for skill in required:
        canonical = _normalize_skill(skill)
        if any(c in tech_set for c in canonical):
            matched.append(skill)
        else:
            missing.append(skill)

    skills_score = len(matched) / max(len(required), 1)

    # ── 2. Nice-to-have score (0-1) ──────────────────────────────────────
    nice     = role.get("nice_to_have", [])
    bonuses  = []
    for skill in nice:
        canonical = _normalize_skill(skill)
        if any(c in tech_set for c in canonical):
            bonuses.append(skill)

    nice_score = len(bonuses) / max(len(nice), 1) if nice else 1.0

    # ── 3. Activity score (0-1) ──────────────────────────────────────────
    # Uses existing pipeline score (0-1) as proxy for activity quality
    activity_score = float(scoring.get("score", 0))
    # Bonus for consistency
    consistency = float(activity.get("consistency_score", 0))
    activity_score = min(1.0, activity_score + consistency * 0.3)

    # ── 4. Code quality score (0-1) ──────────────────────────────────────
    grade_pts = {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.4, "E": 0.2, "F": 0.1}
    overall_grade  = quality.get("overall_grade") or scoring.get("breakdown", {}).get("project_quality")
    quality_score  = grade_pts.get(overall_grade, 0.3)

    # ── 5. Threshold score (0-1) ─────────────────────────────────────────
    flags = []
    thresh_hits = 0
    thresh_total = 0

    min_commits = role.get("min_commits", 0)
    if min_commits > 0:
        thresh_total += 1
        if activity.get("total_commits", 0) >= min_commits:
            thresh_hits += 1
        else:
            flags.append(f"Only {activity.get('total_commits', 0)} commits (need {min_commits})")

    min_stars = role.get("min_stars", 0)
    if min_stars > 0:
        thresh_total += 1
        if activity.get("stars_total", 0) >= min_stars:
            thresh_hits += 1
        else:
            flags.append(f"Only {activity.get('stars_total', 0)} stars (need {min_stars})")

    if role.get("needs_tests"):
        thresh_total += 1
        if quality.get("has_tests") or (quality.get("repos_with_tests", 0) > 0):
            thresh_hits += 1
        else:
            flags.append("No test files found")

    if role.get("domain") and category.get("primary_domain"):
        thresh_total += 1
        if category["primary_domain"] == role["domain"]:
            thresh_hits += 1
        else:
            flags.append(f"Domain is '{category['primary_domain']}' (need '{role['domain']}')")

    if role.get("needs_live_project"):
        thresh_total += 1
        # Check enrichment for live projects
        if quality.get("has_live_project") or quality.get("live_count", 0) > 0:
            thresh_hits += 1
        else:
            flags.append("No deployed/live project found")

    thresh_score = thresh_hits / max(thresh_total, 1) if thresh_total else 1.0

    # ── Weighted total ────────────────────────────────────────────────────
    total = (
        w_skills   * skills_score   +
        w_activity * activity_score +
        w_quality  * quality_score  +
        w_nice     * nice_score     +
        w_thresh   * thresh_score
    )
    match_pct = round(total * 100)

    # Label
    if match_pct >= 80:   label = "Strong Match"
    elif match_pct >= 65: label = "Good Fit"
    elif match_pct >= 45: label = "Partial Fit"
    else:                 label = "Poor Fit"

    label_color = {
        "Strong Match": "#1D9E75",
        "Good Fit":     "#40cef3",
        "Partial Fit":  "#E6A817",
        "Poor Fit":     "#E64D4D",
    }[label]

    return {
        "match_pct":   match_pct,
        "match_label": label,
        "label_color": label_color,
        "breakdown": {
            "skills":      round(skills_score * 100),
            "activity":    round(activity_score * 100),
            "code_quality":round(quality_score * 100),
            "nice_to_have":round(nice_score * 100),
            "thresholds":  round(thresh_score * 100),
        },
        "matched":  matched,
        "missing":  missing,
        "bonuses":  bonuses,
        "flags":    flags,
    }


def score_all_candidates(candidates: list[dict], role: dict, enrichment_cache: dict | None = None) -> list[dict]:
    """Score all candidates and return sorted list with match scores attached."""
    results = []
    for c in candidates:
        login = c.get("login", "")
        enrich = None
        if enrichment_cache:
            enrich = enrichment_cache.get(f"{login}__code_quality")
        fit = score_candidate(c, role, enrich)
        results.append({**c, "role_fit": fit})
    results.sort(key=lambda x: x["role_fit"]["match_pct"], reverse=True)
    return results
