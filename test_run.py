from utils.github_client import get_user
from stages.filters         import is_indian, is_student
from stages.link_extractor  import extract_links
from stages.activity_analyzer import analyze_activity
from stages.project_analyzer  import analyze_projects
from stages.categorizer     import categorize
from stages.scorer          import score_candidate
import json

# Test with a handful of known Indian student GitHub profiles
TEST_LOGINS = [
    "dhruv-07",
    "jaiswaladitya2004",
    "priyanshu031",
    "iitml-23-25-77",
    "AnanthBtechCSE",
    "siddheshkumbhar18",
    "AkashPal10",
    "Shrishti-Sonkar",

]

for login in TEST_LOGINS:
    print(f"\n{'='*50}")
    print(f"Testing: {login}")
    user = get_user(login)
    if not user:
        print("  User not found")
        continue

    print(f"  Name: {user.name}")
    print(f"  Location: {user.location}")
    print(f"  Bio: {user.bio}")
    print(f"  Is Indian: {is_indian(user)}")
    print(f"  Is Student: {is_student(user)}")

    links = extract_links(user)
    print(f"  Links found: {links}")

    activity = analyze_activity(user)
    print(f"  Activity: commits={activity['total_commits']}, consistency={activity['consistency_score']}")

    projects = analyze_projects(user)
    print(f"  Top projects: {[p['name'] for p in projects]}")

    cat = categorize(activity, projects)
    print(f"  Domain: {cat['primary_domain']}")

    score = score_candidate(activity, projects, cat)
    print(f"  Score: {score['score']}")
    print(f"  Pros: {score['pros']}")
    print(f"  Cons: {score['cons']}")