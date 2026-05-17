import json, os

CACHE_FILE = "candidates_cache.json"

def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {"processed": [], "enriched": []}

def save_to_cache(login: str, data: dict):
    cache = load_cache()
    cache["processed"].append(login)
    cache["enriched"].append(data)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2, default=str)

def already_processed(login: str) -> bool:
    cache = load_cache()
    return login in cache["processed"]

def clear_cache():
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    print("Cache cleared.")