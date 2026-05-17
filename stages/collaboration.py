"""
stages/collaboration.py — Collaboration & community presence score.

Measures how much a candidate interacts with the broader developer community:
  - Pull requests to OTHER repos (team-player signal)
  - Issues opened/closed (communication & problem-solving)
  - Stars received (community recognition)
  - Forked by others (code is useful)
  - Public contributions to organizations

Uses PyGithub user events and repo metadata.
"""

from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor


def analyze_collaboration(user) -> dict:
    """
    Analyze the collaboration and community presence of a GitHub user.

    Returns:
        {
          "collab_score":        int (0-100)
          "collab_label":        str
          "label_color":         str
          "prs_to_others":       int
          "issues_opened":       int
          "orgs_count":          int
          "stars_received":      int
          "forked_by_others":    int
          "followers":           int
          "following":           int
          "public_gists":        int
          "breakdown":           dict
          "top_contributed_repos": [str]
        }
    """
    # ── Parallel data fetch ───────────────────────────────────────────────
    try:
        followers      = user.followers
        following      = user.following
        public_gists   = user.public_gists
    except Exception:
        followers = following = public_gists = 0

    # Count PRs + issues from events (last 300 events)
    prs_to_others    = 0
    issues_opened    = 0
    contributed_repos = set()

    try:
        events = list(user.get_events())[:300]
        for ev in events:
            etype = ev.type
            repo_name = ev.repo.name if ev.repo else ""

            # PR to someone else's repo
            if etype == "PullRequestEvent":
                owner = repo_name.split("/")[0] if "/" in repo_name else ""
                if owner and owner.lower() != user.login.lower():
                    prs_to_others += 1
                    contributed_repos.add(repo_name)

            # Issue opened
            elif etype == "IssuesEvent":
                payload = ev.payload or {}
                if payload.get("action") == "opened":
                    issues_opened += 1
    except Exception:
        pass

    # Stars received + forked by others (from all repos)
    stars_received   = 0
    forked_by_others = 0

    try:
        repos = [r for r in user.get_repos() if not r.fork][:20]
        for repo in repos:
            stars_received   += repo.stargazers_count
            forked_by_others += repo.forks_count
    except Exception:
        pass

    # Org memberships (public)
    orgs_count = 0
    try:
        orgs_count = sum(1 for _ in user.get_orgs())
    except Exception:
        pass

    # ── Score calculation (0-100) ─────────────────────────────────────────
    # PRs to others: 0-30 pts (each PR = 5 pts, max 30)
    pts_prs     = min(30, prs_to_others * 5)
    # Issues: 0-15 pts (each issue = 3 pts, max 15)
    pts_issues  = min(15, issues_opened * 3)
    # Stars: 0-20 pts (logarithmic)
    import math
    pts_stars   = min(20, int(math.log2(stars_received + 1) * 3))
    # Forks by others: 0-15 pts
    pts_forks   = min(15, int(math.log2(forked_by_others + 1) * 3))
    # Followers: 0-10 pts
    pts_follow  = min(10, int(math.log2(followers + 1) * 2))
    # Orgs: 0-10 pts (2 pts per org)
    pts_orgs    = min(10, orgs_count * 2)

    total = pts_prs + pts_issues + pts_stars + pts_forks + pts_follow + pts_orgs
    collab_score = min(100, total)

    # Label
    if collab_score >= 70:   label, color = "Team Player",      "#1D9E75"
    elif collab_score >= 45: label, color = "Engaged",          "#40cef3"
    elif collab_score >= 20: label, color = "Solo Developer",   "#E6A817"
    else:                    label, color = "Minimal Presence", "#888"

    return {
        "collab_score":          collab_score,
        "collab_label":          label,
        "label_color":           color,
        "prs_to_others":         prs_to_others,
        "issues_opened":         issues_opened,
        "orgs_count":            orgs_count,
        "stars_received":        stars_received,
        "forked_by_others":      forked_by_others,
        "followers":             followers,
        "following":             following,
        "public_gists":          public_gists,
        "top_contributed_repos": list(contributed_repos)[:5],
        "breakdown": {
            "prs_score":     pts_prs,
            "issues_score":  pts_issues,
            "stars_score":   pts_stars,
            "forks_score":   pts_forks,
            "followers_score": pts_follow,
            "orgs_score":    pts_orgs,
        },
    }
