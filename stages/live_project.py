"""
stages/live_project.py — Detect deployed, live projects in a candidate's GitHub repos.

Uses only GitHub metadata (has_pages, homepage, topics, README badges) — no HTTP requests
to third-party sites, so no extra rate limiting.
"""

import re
import base64


_DEPLOY_BADGE_RE = re.compile(
    r"(vercel\.com|netlify\.app|netlify\.com|railway\.app|render\.com|"
    r"fly\.io|heroku\.com|github\.io|pages\.github\.com|"
    r"digitalocean\.com|supabase\.co|firebase\.google|"
    r"!\[.*deploy.*\]|!\[.*live.*\]|!\[.*production.*\])",
    re.IGNORECASE,
)

_PLATFORM_RE = {
    "Vercel":       re.compile(r"vercel\.com", re.IGNORECASE),
    "Netlify":      re.compile(r"netlify\.(app|com)", re.IGNORECASE),
    "Railway":      re.compile(r"railway\.app", re.IGNORECASE),
    "Render":       re.compile(r"render\.com", re.IGNORECASE),
    "Fly.io":       re.compile(r"fly\.io", re.IGNORECASE),
    "Heroku":       re.compile(r"heroku\.com", re.IGNORECASE),
    "GitHub Pages": re.compile(r"github\.io|pages\.github\.com", re.IGNORECASE),
    "Firebase":     re.compile(r"firebase\.google|firebaseapp\.com", re.IGNORECASE),
    "Supabase":     re.compile(r"supabase\.co|supabase\.com", re.IGNORECASE),
}


def detect_live_projects(user) -> dict:
    """
    Scan all public repos for signs of live deployment.

    Returns:
        has_live_project  (bool)
        live_count        (int)
        live_projects     (list[dict]) — [{name, url, platform, source}]
        deployment_score  (int) — 0–10 bonus score signal
    """
    live = []

    try:
        repos = [r for r in user.get_repos() if not r.fork][:20]
    except Exception:
        return {"has_live_project": False, "live_count": 0, "live_projects": [], "deployment_score": 0}

    for repo in repos:
        found_urls = set()
        platform   = "Unknown"
        source     = []

        # ── 1. GitHub Pages ───────────────────────────────────────────
        if getattr(repo, "has_pages", False):
            url = f"https://{user.login}.github.io/{repo.name}"
            found_urls.add(url)
            platform = "GitHub Pages"
            source.append("github_pages")

        # ── 2. Homepage field ─────────────────────────────────────────
        homepage = repo.homepage or ""
        if homepage and "github.com" not in homepage and homepage.startswith("http"):
            found_urls.add(homepage)
            source.append("homepage")
            for pname, pattern in _PLATFORM_RE.items():
                if pattern.search(homepage):
                    platform = pname
                    break

        # ── 3. README badge scan ──────────────────────────────────────
        if not found_urls:  # Only scan README if no URL found yet (saves API calls)
            try:
                readme = repo.get_readme()
                content = base64.b64decode(readme.content).decode("utf-8", errors="ignore")
                if _DEPLOY_BADGE_RE.search(content):
                    # Try to extract a URL from the README
                    urls_in_readme = re.findall(
                        r"https?://[^\s\)\]\"\']+(?:vercel|netlify|railway|render|fly\.io|heroku|github\.io)[^\s\)\]\"\']*",
                        content, re.IGNORECASE
                    )
                    for u in urls_in_readme[:1]:
                        found_urls.add(u)
                        source.append("readme_badge")
                        for pname, pattern in _PLATFORM_RE.items():
                            if pattern.search(u):
                                platform = pname
                                break
            except Exception:
                pass

        # ── 4. Topics check ───────────────────────────────────────────
        topics = repo.topics or []
        live_topics = {"deployed", "live", "production", "web-app", "open-source"}
        if live_topics.intersection(set(topics)) and not found_urls:
            source.append("topics")

        if found_urls or "homepage" in source or "github_pages" in source:
            for url in (found_urls or {""}):
                live.append({
                    "name":     repo.name,
                    "url":      url or homepage or "",
                    "platform": platform,
                    "stars":    repo.stargazers_count,
                    "source":   source,
                })
            break  # 1 confirmed live project is enough per repo

    # Deduplicate by repo name
    seen = set()
    unique_live = []
    for p in live:
        if p["name"] not in seen:
            seen.add(p["name"])
            unique_live.append(p)

    # Deployment score: each live project = 3pts, max 10
    deployment_score = min(10, len(unique_live) * 3)

    return {
        "has_live_project": len(unique_live) > 0,
        "live_count":       len(unique_live),
        "live_projects":    unique_live,
        "deployment_score": deployment_score,
    }
