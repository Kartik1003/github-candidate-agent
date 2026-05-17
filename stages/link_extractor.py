import re

# ---------------------------------------------------------------------------
# Regex patterns for extractable links
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)

# Known portfolio / social platforms
_SOCIAL_DOMAINS = {
    "linkedin.com":    "linkedin",
    "twitter.com":     "twitter",
    "x.com":           "twitter",
    "medium.com":      "medium",
    "dev.to":          "dev.to",
    "hashnode.dev":    "hashnode",
    "stackoverflow.com": "stackoverflow",
    "kaggle.com":      "kaggle",
    "behance.net":     "behance",
    "dribbble.com":    "dribbble",
    "youtube.com":     "youtube",
    "leetcode.com":    "leetcode",
    "codeforces.com":  "codeforces",
}


def _classify_url(url: str) -> str:
    """Return a label for a known URL domain, or 'website'."""
    lower = url.lower()
    for domain, label in _SOCIAL_DOMAINS.items():
        if domain in lower:
            return label
    return "website"


def extract_links(user) -> list[dict]:
    """
    Extract links from a GitHub user's profile (bio, blog field, email).

    Returns a list of dicts:  [{"url": "...", "type": "linkedin"}, ...]
    """
    seen = set()
    links = []

    def _add(url: str):
        url = url.rstrip("/").strip()
        if url and url not in seen:
            seen.add(url)
            links.append({"url": url, "type": _classify_url(url)})

    # 1. blog / website field
    blog = getattr(user, "blog", None)
    if blog:
        # Some users put bare domains without scheme
        if not blog.startswith("http"):
            blog = "https://" + blog
        _add(blog)

    # 2. URLs embedded in bio
    bio = getattr(user, "bio", None) or ""
    for match in _URL_RE.findall(bio):
        _add(match)

    # 3. Email (not a URL, but useful contact info)
    email = getattr(user, "email", None)
    if email:
        links.append({"url": f"mailto:{email}", "type": "email"})

    return links
