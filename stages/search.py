from utils.github_client import search_users
import config

SEARCH_QUERIES = [
    'location:India "student" in:bio language:Python',
    'location:India "btech" in:bio',
    'location:India "undergrad" in:bio',
    'location:India "internship" in:bio followers:>5',
    'location:India "open to work" in:bio',
    'location:India "iit" OR "nit" OR "bits" in:bio',
]

import concurrent.futures

def fetch_candidate_logins(max_per_query: int = 1000) -> list[str]:
    seen = set()
    logins = []
    
    def run_query(q):
        batch = search_users(q, max_per_query)
        return q, batch

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SEARCH_QUERIES)) as executor:
        futures = {executor.submit(run_query, q): q for q in SEARCH_QUERIES}
        for future in concurrent.futures.as_completed(futures):
            q, batch = future.result()
            for login in batch:
                if login not in seen:
                    seen.add(login)
                    logins.append(login)
            print(f"Query '{q}' -> {len(batch)} results. Total unique: {len(logins)}")
            
    return logins