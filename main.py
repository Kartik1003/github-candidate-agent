import sys, os
os.environ["PYTHONUNBUFFERED"] = "1"
sys.stdout.reconfigure(encoding='utf-8')

import config
from database import init_db, mark_processed, was_processed_recently
from checkpoint import load_cache, save_to_cache
from stages.search            import fetch_candidate_logins
from stages.filters           import filter_candidates
from stages.link_extractor    import extract_links
from stages.activity_analyzer import analyze_activity
from stages.project_analyzer  import analyze_projects
from stages.categorizer       import categorize
from stages.scorer            import score_candidate
from stages.sheets_writer     import write_candidates

def run_pipeline():
    print("=== GitHub Candidate Agent ===\n")
    init_db()

    cache = load_cache()
    already_enriched = cache["enriched"]
    print(f"Resuming from cache: {len(already_enriched)} candidates already processed.\n")

    logins = fetch_candidate_logins(max_per_query=50)
    print(f"Total profiles found: {len(logins)}\n")

    candidates = filter_candidates(logins)

    import concurrent.futures
    new_this_run = 0
    skipped      = 0

    to_process = []
    for user in candidates:
        if was_processed_recently(user.login, days=30):
            print(f"  (skipping {user.login} — processed in last 30 days)")
            skipped += 1
        else:
            to_process.append(user)

    def process_user(user):
        print(f"Processing {user.login}...")
        try:
            links    = extract_links(user)
            activity = analyze_activity(user)
            projects = analyze_projects(user)
            category = categorize(activity, projects)
            scoring  = score_candidate(activity, projects, category)

            entry = {
                "login":    user.login,
                "name":     user.name or user.login,
                "location": user.location or "",
                "bio":      user.bio or "",
                "links":    links,
                "activity": activity,
                "projects": projects,
                "category": category,
                "scoring":  scoring,
            }
            save_to_cache(user.login, entry)
            mark_processed(user.login, scoring["score"], category["primary_domain"])
            print(f"  [✓] {user.login} | Score: {scoring['score']} | Domain: {category['primary_domain']}")
            return True
        except Exception as e:
            print(f"  [✗] Error on {user.login}: {e}")
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_user, u) for u in to_process]
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                new_this_run += 1

    print(f"\nThis run: {new_this_run} new | {skipped} skipped (already processed)")

    all_enriched = load_cache()["enriched"]
    ranked = sorted(all_enriched, key=lambda x: x["scoring"]["score"], reverse=True)
    top    = ranked[:config.TOP_N]

    print(f"\nWriting top {len(top)} candidates to Google Sheet...")
    try:
        write_candidates(top)
        print("Sheet updated successfully.")
    except Exception as e:
        print(f"Sheet write failed: {e}")
        import pandas as pd
        rows = [{"Rank": i+1, "Name": c.get("name",""), "GitHub": f"https://github.com/{c['login']}",
                 "Score": c["scoring"]["score"], "Domain": c["category"]["primary_domain"]}
                for i, c in enumerate(top)]
        import pandas as pd
        pd.DataFrame(rows).to_csv("candidates_output.csv", index=False)
        print("Saved to candidates_output.csv as fallback.")

    print(f"\n=== Done. Top {len(top)} candidates written. ===")
    from notifier import notify_run_complete
    notify_run_complete(
        new=new_this_run,
        skipped=skipped,
        total=len(all_enriched),
        top_candidates=top[:10],
    )
    return {"new": new_this_run, "skipped": skipped, "total": len(all_enriched)}

if __name__ == "__main__":
    run_pipeline()