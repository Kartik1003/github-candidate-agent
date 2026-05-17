"""
pipeline.py — Hybrid orchestrator with PARALLEL stage execution.

Flow:
  1. [RULES]      Fetch GitHub profile → check location for India match
     └─ [PARALLEL] 2a. [EMBEDDINGS] embed_and_classify(bio)
                   2b. [LLM]        classify_candidate(bio, readme)
                   2c. [LLM]        extract_links(bio + readme)
                   2d. [LLM]        llm_score_candidate(full_profile)
  3. [ML]         ml_rank_candidate(features)  — needs 2a + 2d results
  4. Merge all signals → final_score
  5. Save to SQLite
  6. Return structured JSON

Latency improvement:
  Before: ~20-30s  (6 sequential steps + 3×sleep(1) + 5×sleep(0.3))
  After : ~7-10s   (parallel LLM + embedding calls, no artificial sleeps)
"""

import re
import time
import traceback
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from db import init_hybrid_db, upsert_candidate
from embeddings import embed_and_classify
from llm_classifier import classify_candidate, llm_score_candidate, extract_links
from feedback import ml_rank_candidate, has_trained_model
from utils.github_client import gh

import config

# ---------------------------------------------------------------------------
# Rule-based India detection (fast pre-filter)
# ---------------------------------------------------------------------------

_INDIA_RE = re.compile(
    r"\b(india|bharat|bangalore|bengaluru|mumbai|delhi|hyderabad|chennai|pune|kolkata|"
    r"ahmedabad|jaipur|lucknow|noida|gurgaon|gurugram|kerala|karnataka|"
    r"tamil\s?nadu|maharashtra|telangana|andhra\s?pradesh|iit|iiit|nit|bits)\b",
    re.IGNORECASE,
)


def _rule_is_indian(location: str, bio: str) -> bool:
    """Fast regex check for Indian location/bio keywords."""
    text = f"{location or ''} {bio or ''}"
    return bool(_INDIA_RE.search(text))


# ---------------------------------------------------------------------------
# GitHub profile fetcher (with internal parallelism for repos)
# ---------------------------------------------------------------------------

def _fetch_repo_details(user, repo, username: str, since: datetime) -> dict:
    """Fetch language list, topics, and commit count for a single repo."""
    repo_data = {
        "name": repo.name,
        "description": repo.description or "",
        "stars": repo.stargazers_count,
        "languages": [],
        "topics": [],
        "commits": 0,
    }
    try:
        repo_data["languages"] = list(repo.get_languages().keys())
    except Exception:
        pass
    try:
        repo_data["topics"] = repo.get_topics() if hasattr(repo, "get_topics") else []
    except Exception:
        pass
    try:
        repo_data["commits"] = repo.get_commits(since=since, author=username).totalCount
    except Exception:
        pass
    return repo_data


def _fetch_profile(username: str) -> dict | None:
    """Fetch full GitHub profile data via the REST API.
    
    Repo details (languages, topics, commits) are fetched in parallel
    across repos using a thread pool, removing the sequential sleep loop.
    """
    try:
        user = gh.get_user(username)
    except Exception as e:
        print(f"[pipeline] Failed to fetch user '{username}': {e}")
        return None

    # Fetch non-fork repos sorted by stars
    try:
        all_repos_raw = sorted(
            [r for r in user.get_repos() if not r.fork],
            key=lambda r: r.stargazers_count,
            reverse=True,
        )[:10]
    except Exception as e:
        print(f"[pipeline] Error listing repos: {e}")
        all_repos_raw = []

    since = datetime.now(timezone.utc) - timedelta(days=config.COMMITS_LOOKBACK)

    # ── Fetch per-repo details IN PARALLEL (replaces the sequential sleep loop) ──
    repos_raw = []
    commit_count = 0
    if all_repos_raw:
        with ThreadPoolExecutor(max_workers=5) as ex:
            futures = {
                ex.submit(_fetch_repo_details, user, repo, username, since): repo
                for repo in all_repos_raw
            }
            for fut in as_completed(futures):
                try:
                    data = fut.result()
                    repos_raw.append(data)
                    commit_count += data.pop("commits", 0)
                except Exception:
                    pass
        # Re-sort by stars after parallel collection
        repos_raw.sort(key=lambda r: r["stars"], reverse=True)

    # Top languages
    lang_set: set[str] = set()
    for r in repos_raw:
        lang_set.update(r.get("languages", []))
    top_languages = list(lang_set)[:8]

    # README from top repo
    readme_sample = ""
    if repos_raw:
        try:
            top_repo = user.get_repo(repos_raw[0]["name"])
            readme_content = top_repo.get_readme().decoded_content.decode("utf-8", errors="ignore")
            readme_sample = readme_content[:1500]
        except Exception:
            pass

    return {
        "username": username,
        "name": user.name or username,
        "bio": user.bio or "",
        "location": user.location or "",
        "company": user.company or "",
        "repos": repos_raw,
        "repo_count": len(repos_raw),
        "commit_count": commit_count,
        "top_languages": top_languages,
        "readme_sample": readme_sample,
        "followers": user.followers,
        "public_repos": user.public_repos,
        "blog": user.blog or "",
    }


# ---------------------------------------------------------------------------
# Score merging
# ---------------------------------------------------------------------------

def _compute_final_score(
    llm_score: float,
    ml_score: float | None,
    embedding_scores: dict,
) -> float:
    """
    Merge all signal sources into a single final score (0–100).

    Weights: 0.5 * llm + 0.3 * ml + 0.2 * embedding
    If ML model unavailable, redistribute: 0.7 * llm + 0.3 * embedding
    """
    emb_avg = (
        embedding_scores.get("student_score", 0) +
        embedding_scores.get("job_seeker_score", 0)
    ) / 2.0 * 100  # similarity scores are 0–1

    if ml_score is not None:
        final = 0.5 * llm_score + 0.3 * (ml_score * 100) + 0.2 * emb_avg
    else:
        final = 0.7 * llm_score + 0.3 * emb_avg

    return round(max(0, min(100, final)), 2)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(github_username: str) -> dict:
    """
    Run the full hybrid pipeline for a single GitHub user.

    Steps 2–5 (Embeddings, Classification, Link Extraction, LLM Scoring)
    run IN PARALLEL after the GitHub profile is fetched.

    Returns the final structured JSON result.
    """
    init_hybrid_db()
    t_start = time.perf_counter()

    print(f"\n{'='*60}")
    print(f"  HYBRID PIPELINE (PARALLEL) — {github_username}")
    print(f"{'='*60}\n")

    # ── Step 1: Fetch profile & quick India check ────────────────────────
    print("[1/6] Fetching GitHub profile (with parallel repo details)…")
    t1 = time.perf_counter()
    profile = _fetch_profile(github_username)
    if profile is None:
        return {"error": f"Could not fetch GitHub profile for '{github_username}'"}

    rule_is_indian = _rule_is_indian(profile["location"], profile["bio"])
    print(f"  ✓ Profile fetched in {time.perf_counter()-t1:.1f}s")
    print(f"  Rule-based Indian: {rule_is_indian}")
    print(f"  Location: {profile['location']!r}")
    print(f"  Repos: {profile['repo_count']} | Commits ({config.COMMITS_LOOKBACK}d): {profile['commit_count']}")

    # ── Steps 2-5: RUN IN PARALLEL ──────────────────────────────────────
    print("\n[2-5/6] Running Embeddings + Classification + Links + Scoring IN PARALLEL…")
    t2 = time.perf_counter()

    bio_text   = f"{profile['bio']} {profile['readme_sample'][:500]}"
    link_text  = f"{profile['bio']} {profile['blog']} {profile['readme_sample'][:500]}"

    emb_result     = None
    classification = None
    links          = None
    score_result   = None

    def _run_embeddings():
        return embed_and_classify(bio_text)

    def _run_classification():
        return classify_candidate(profile["bio"], profile["readme_sample"])

    def _run_links():
        return extract_links(link_text)

    def _run_scoring():
        return llm_score_candidate(profile)

    tasks = {
        "embeddings":     _run_embeddings,
        "classification": _run_classification,
        "links":          _run_links,
        "scoring":        _run_scoring,
    }

    with ThreadPoolExecutor(max_workers=4) as ex:
        future_map = {ex.submit(fn): name for name, fn in tasks.items()}
        for fut in as_completed(future_map):
            name = future_map[fut]
            try:
                result = fut.result()
                if name == "embeddings":
                    emb_result = result
                    print(f"  ✓ Embeddings done  "
                          f"Student={result['student_score']:.3f}  "
                          f"JobSeeker={result['job_seeker_score']:.3f}  "
                          f"Dev={result['developer_score']:.3f}  "
                          f"→ {result['top_match']}")
                elif name == "classification":
                    classification = result
                    print(f"  ✓ Classification done  "
                          f"Indian={result.get('is_indian')}  "
                          f"Student={result.get('is_student')}  "
                          f"JobSeeker={result.get('is_job_seeker')}")
                elif name == "links":
                    links = result
                    found = sum(1 for v in result.values() if v and v != [])
                    print(f"  ✓ Links done  Found {found} link categories")
                elif name == "scoring":
                    score_result = result
                    print(f"  ✓ LLM Scoring done  Total={result.get('total_score', 0)}/100")
            except Exception as e:
                print(f"  ✗ Task '{name}' failed: {e}")

    print(f"  → Parallel block finished in {time.perf_counter()-t2:.1f}s")

    # ── Provide safe defaults if any task failed ─────────────────────────
    if emb_result is None:
        import numpy as np
        emb_result = {
            "student_score": 0.0, "job_seeker_score": 0.0,
            "developer_score": 0.0, "top_match": "unclear",
            "embedding": np.zeros(384, dtype="float32"),
        }
    if classification is None:
        classification = {
            "is_indian": False, "is_student": False, "is_job_seeker": False,
            "confidence": {"indian": 0.0, "student": 0.0, "job_seeker": 0.0},
            "reasoning": "Classification task failed.",
        }
    if links is None:
        links = {"linkedin": None, "portfolio": None, "resume": None,
                 "twitter": None, "github_pages": None, "other": []}
    if score_result is None:
        score_result = {
            "total_score": 0,
            "breakdown": {"project_quality":0,"consistency":0,"tech_stack":0,"documentation":0,"open_source":0},
            "strengths": [], "weaknesses": ["Scoring task failed"],
            "recruiter_summary": "Score unavailable.",
        }

    embedding_scores = {
        "student_score":   emb_result["student_score"],
        "job_seeker_score":emb_result["job_seeker_score"],
        "developer_score": emb_result["developer_score"],
        "top_match":       emb_result["top_match"],
    }
    embedding_vector = emb_result["embedding"]
    llm_total = score_result.get("total_score", 0)

    # ── Step 6: ML ranking (needs embedding + llm scores) ────────────────
    print("\n[6/6] ML ranking…")
    ml_score = None
    if has_trained_model():
        ml_features = {
            "llm_score":       llm_total,
            "student_score":   emb_result["student_score"],
            "job_seeker_score":emb_result["job_seeker_score"],
            "repo_count":      profile["repo_count"],
            "commit_count":    profile["commit_count"],
        }
        ml_score = ml_rank_candidate(ml_features)
        print(f"  ML probability (good): {ml_score:.4f}" if ml_score else "  ML model returned None")
    else:
        print("  No trained model found — skipping ML ranking.")

    # ── Step 7: Merge signals ─────────────────────────────────────────────
    final_score = _compute_final_score(llm_total, ml_score, embedding_scores)
    is_indian   = rule_is_indian or classification.get("is_indian", False)
    skills      = profile["top_languages"][:10]

    # ── Build final result ────────────────────────────────────────────────
    result = {
        "username":         github_username,
        "name":             profile["name"],
        "is_indian":        is_indian,
        "is_student":       classification.get("is_student", False),
        "is_job_seeker":    classification.get("is_job_seeker", False),
        "confidence":       classification.get("confidence", {}),
        "links": {
            "linkedin":     links.get("linkedin"),
            "portfolio":    links.get("portfolio"),
            "resume":       links.get("resume"),
            "twitter":      links.get("twitter"),
            "github_pages": links.get("github_pages"),
            "other":        links.get("other", []),
        },
        "skills":           skills,
        "github_stats": {
            "repos":     profile["public_repos"],
            "commits":   profile["commit_count"],
            "followers": profile["followers"],
        },
        "llm_score":        llm_total,
        "llm_breakdown":    score_result.get("breakdown", {}),
        "embedding_scores": embedding_scores,
        "ml_score":         round(ml_score, 4) if ml_score is not None else None,
        "final_score":      final_score,
        "strengths":        score_result.get("strengths", []),
        "weaknesses":       score_result.get("weaknesses", []),
        "recruiter_summary":score_result.get("recruiter_summary", ""),
        "labeled":          None,
        "timestamp":        datetime.utcnow().isoformat(),
    }

    # ── Step 8: Save to SQLite ────────────────────────────────────────────
    upsert_candidate(
        username=github_username,
        profile=result,
        llm_score=llm_total,
        embedding_vector=embedding_vector,
    )

    elapsed = time.perf_counter() - t_start
    print(f"\n✅ Saved to DB. Final score: {final_score}/100")
    print(f"\n{'─'*60}")
    print(f"  {github_username}: {final_score}/100  "
          f"(LLM={llm_total}, ML={ml_score}, Emb={emb_result['top_match']})")
    print(f"  ⏱  Total pipeline time: {elapsed:.1f}s")
    print(f"{'─'*60}\n")

    return result


# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------

def run_batch(usernames: list[str], delay: float = 1.0) -> list[dict]:
    """Run the pipeline on a list of GitHub usernames."""
    results = []
    for i, username in enumerate(usernames, 1):
        print(f"\n[{i}/{len(usernames)}] Processing {username}…")
        try:
            result = run_pipeline(username)
            results.append(result)
        except Exception as e:
            print(f"  ❌ Error on {username}: {e}")
            traceback.print_exc()
            results.append({"username": username, "error": str(e)})
        if i < len(usernames):
            time.sleep(delay)  # reduced from 2.0s to 1.0s between candidates
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <github_username> [username2 ...]")
        print("Example: python pipeline.py torvalds gvanrossum")
        sys.exit(1)

    usernames = sys.argv[1:]

    if len(usernames) == 1:
        result = run_pipeline(usernames[0])
    else:
        result = run_batch(usernames)

    output = json.dumps(result, indent=2, default=str)
    print(f"\n{'='*60}")
    print("FINAL OUTPUT")
    print(f"{'='*60}")
    print(output)
