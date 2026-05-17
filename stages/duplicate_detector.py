"""
stages/duplicate_detector.py — Detect candidates who may be the same person.

Uses cached data only (no GitHub API calls) — compares:
  1. Bio text similarity (using scikit-learn TF-IDF cosine similarity)
  2. Blog/website URL match
  3. Overlapping public repo names (2+ shared names)
  4. Location + name similarity

Runs only on-demand via the /duplicates API endpoint.
"""

import json
import os
import re
import traceback
from difflib import SequenceMatcher


CACHE_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "candidates_cache.json")
)

CONFIDENCE_THRESHOLD = 0.55  # Minimum combined score to flag as duplicate


def _load_candidates() -> list[dict]:
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("enriched", [])
    except Exception:
        return []


def _str_sim(a: str, b: str) -> float:
    """Fast fuzzy string similarity using SequenceMatcher."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _normalize_url(url: str) -> str:
    url = url.lower().strip().rstrip("/")
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)
    return url


def detect_duplicates() -> list[dict]:
    """
    Find candidates in the cache that are likely the same person.

    Returns a list of duplicate clusters:
    [
      {
        "primary": "login_a",
        "aliases": ["login_b"],
        "confidence": 0.85,
        "signals": ["same_blog", "bio_similarity_0.92"]
      }
    ]
    """
    candidates = _load_candidates()
    n = len(candidates)

    if n < 2:
        return []

    # Pre-compute lookup values — guard against None/unexpected types
    logins    = [str(c.get("login") or "") for c in candidates]
    bios      = [str(c.get("bio") or "") for c in candidates]
    # links may be None, {}, or a proper dict — handle all cases
    blogs = []
    for c in candidates:
        raw_links = c.get("links")
        if isinstance(raw_links, dict):
            portfolio = raw_links.get("portfolio") or ""
        else:
            portfolio = ""
        blogs.append(_normalize_url(str(portfolio)))
    locations = [str(c.get("location") or "") for c in candidates]
    names     = [str(c.get("name") or "") for c in candidates]
    # Repo names from projects
    repo_sets = []
    for c in candidates:
        projects = c.get("projects")
        if isinstance(projects, list):
            repo_sets.append(set(str(p.get("name") or "").lower() for p in projects if isinstance(p, dict)))
        else:
            repo_sets.append(set())

    clusters = []
    paired   = set()  # logins already in a cluster

    for i in range(n):
        if logins[i] in paired:
            continue

        for j in range(i + 1, n):
            if logins[j] in paired:
                continue

            signals = []
            score   = 0.0

            # ── Signal 1: Blog/portfolio URL match ────────────────────
            if blogs[i] and blogs[j] and blogs[i] == blogs[j]:
                signals.append("same_blog_url")
                score += 0.6

            # ── Signal 2: Bio text similarity ─────────────────────────
            bio_sim = _str_sim(bios[i], bios[j])
            if bio_sim > 0.75:
                signals.append(f"bio_similarity_{bio_sim:.2f}")
                score += bio_sim * 0.4

            # ── Signal 3: Shared repo names (>= 2) ────────────────────
            shared_repos = repo_sets[i].intersection(repo_sets[j])
            shared_repos.discard("")
            if len(shared_repos) >= 2:
                signals.append(f"shared_repos_{len(shared_repos)}")
                score += min(0.4, len(shared_repos) * 0.15)

            # ── Signal 4: Same full name (non-trivial) ────────────────
            name_sim = _str_sim(names[i], names[j])
            if name_sim > 0.85 and len(names[i]) > 3:
                signals.append(f"same_name_{name_sim:.2f}")
                score += 0.25

            # ── Signal 5: Same location + similar name ────────────────
            loc_sim = _str_sim(locations[i], locations[j])
            if loc_sim > 0.8 and name_sim > 0.7:
                signals.append("same_location_and_name")
                score += 0.2

            if score >= CONFIDENCE_THRESHOLD and signals:
                # Sort: lower-ranked (worse score) is the alias
                try:
                    scoring_i = candidates[i].get("scoring")
                    scoring_j = candidates[j].get("scoring")
                    c_i = (scoring_i.get("score", 0) if isinstance(scoring_i, dict) else 0)
                    c_j = (scoring_j.get("score", 0) if isinstance(scoring_j, dict) else 0)
                except Exception:
                    c_i, c_j = 0, 0

                primary = logins[i] if c_i >= c_j else logins[j]
                alias   = logins[j] if primary == logins[i] else logins[i]

                clusters.append({
                    "primary":      primary,
                    "aliases":      [alias],
                    "confidence":   round(min(score, 1.0), 3),
                    "signals":      signals,
                    "shared_repos": list(shared_repos)[:5],
                })
                paired.add(logins[i])
                paired.add(logins[j])

    # Merge overlapping clusters (if A≈B and B≈C, merge into one)
    return _merge_clusters(clusters)


def _merge_clusters(clusters: list[dict]) -> list[dict]:
    """Merge clusters that share a primary or alias login."""
    merged = []
    used   = set()
    for i, c in enumerate(clusters):
        if i in used:
            continue
        members = set([c["primary"]] + c["aliases"])
        for j, d in enumerate(clusters):
            if j <= i or j in used:
                continue
            d_members = set([d["primary"]] + d["aliases"])
            if members.intersection(d_members):
                members.update(d_members)
                c["aliases"] = list(members - {c["primary"]})
                c["confidence"] = max(c["confidence"], d["confidence"])
                c["signals"]    = list(set(c["signals"] + d["signals"]))
                used.add(j)
        merged.append(c)
        used.add(i)
    return merged
