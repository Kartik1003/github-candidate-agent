from github import Github, RateLimitExceededException
from ratelimit import limits, sleep_and_retry
import time, config

gh = Github(config.GITHUB_TOKEN, per_page=100)

@sleep_and_retry
@limits(calls=30, period=60)   # stay inside secondary rate limits
def search_users(query: str, max_results: int = 1000):
    """Return a list of login strings matching the search query."""
    results = []
    try:
        users = gh.search_users(query)
        for u in users:
            results.append(u.login)
            if len(results) >= max_results:
                break
    except RateLimitExceededException:
        print("Rate limit hit — sleeping 60s")
        time.sleep(60)
    return results

def get_user(login: str):
    try:
        return gh.get_user(login)
    except Exception:
        return None