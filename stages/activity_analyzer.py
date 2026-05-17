import re
from datetime import datetime, timedelta, timezone
import config


# ---------------------------------------------------------------------------
# Commit-message quality heuristic
# ---------------------------------------------------------------------------

_GARBAGE_RE = re.compile(
    r"^(initial commit|update|fix|wip|test|asdf|\.+|merge branch|"
    r"auto-?commit|commit|changes|no message|untitled|misc)$",
    re.IGNORECASE,
)


def _is_quality_message(msg: str) -> bool:
    """Return True if the commit message looks meaningful."""
    msg = msg.strip()
    if len(msg) < 5:
        return False
    if _GARBAGE_RE.match(msg):
        return False
    return True


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_activity(user) -> dict:
    """
    Analyze a GitHub user's recent commit activity across their repos.

    Returns a dict with keys consumed by scorer.py and categorizer.py:
        - total_commits      (int)
        - consistency_score  (float 0-1)
        - top_languages      (list[str])
        - stars_total        (int)
        - commit_quality_ratio (float 0-1)
        - garbage_commits    (int)
        - active_days        (int)
    """
    lookback = config.COMMITS_LOOKBACK
    since = datetime.now(timezone.utc) - timedelta(days=lookback)

    total_commits = 0
    quality_commits = 0
    garbage_commits = 0
    active_dates = set()
    language_bytes = {}
    stars_total = 0

    try:
        repos = list(user.get_repos())
    except Exception:
        repos = []

    for repo in repos:
        stars_total += repo.stargazers_count

        # Aggregate languages
        try:
            for lang, byte_count in repo.get_languages().items():
                language_bytes[lang] = language_bytes.get(lang, 0) + byte_count
        except Exception:
            pass

        # Scan commits within lookback window
        try:
            commits = repo.get_commits(since=since, author=user.login)
            for c in commits:
                total_commits += 1
                msg = (c.commit.message or "").split("\n")[0]
                if _is_quality_message(msg):
                    quality_commits += 1
                else:
                    garbage_commits += 1

                # Track distinct active dates
                if c.commit.author and c.commit.author.date:
                    active_dates.add(c.commit.author.date.date())
        except Exception:
            # Rate-limited or empty repo — skip gracefully
            continue

    # Consistency: fraction of days in lookback window with at least one commit
    consistency_score = round(len(active_dates) / max(lookback, 1), 4)

    # Top languages by bytes written
    sorted_langs = sorted(language_bytes, key=language_bytes.get, reverse=True)
    top_languages = sorted_langs[:8]

    # Quality ratio
    commit_quality_ratio = (
        round(quality_commits / total_commits, 4) if total_commits else 0.0
    )

    return {
        "total_commits":        total_commits,
        "consistency_score":    consistency_score,
        "top_languages":        top_languages,
        "stars_total":          stars_total,
        "commit_quality_ratio": commit_quality_ratio,
        "garbage_commits":      garbage_commits,
        "active_days":          len(active_dates),
    }
