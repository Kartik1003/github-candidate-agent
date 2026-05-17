import config

def score_candidate(activity: dict, projects: list[dict], category: dict) -> dict:
    # 1. Consistency (0-1)
    consistency = activity.get("consistency_score", 0)

    # 2. Project quality (average quality_score of original repos)
    orig_projects = [p for p in projects if p.get("is_original")]
    if orig_projects:
        project_quality = sum(p["quality_score"] for p in orig_projects) / len(orig_projects)
    else:
        project_quality = 0.0

    # 3. Tech depth: distinct languages + advanced projects
    n_langs = len(activity.get("top_languages", []))
    advanced = sum(1 for p in projects if p.get("complexity") == "advanced level project")
    tech_depth = min((n_langs * 0.1) + (advanced * 0.2), 1.0)

    # 4. Activity level: commits + stars
    commit_vol = min(activity.get("total_commits", 0) / 200, 1.0)
    star_vol   = min(activity.get("stars_total", 0) / 50, 1.0)
    commit_quality = activity.get("commit_quality_ratio", 0)
    activity_score = (commit_vol * 0.4 + star_vol * 0.3 + commit_quality * 0.3)

    w = config.SCORE_WEIGHTS
    final_score = (
        w["project_quality"] * project_quality +
        w["consistency"]     * consistency +
        w["tech_depth"]      * tech_depth +
        w["activity"]        * activity_score
    )

    # Pros and cons
    pros, cons = [], []
    if consistency > 0.7:      pros.append("Highly consistent committer")
    if project_quality > 0.6:  pros.append("High-quality original projects")
    if advanced > 0:           pros.append(f"{advanced} advanced project(s)")
    if star_vol > 0.3:         pros.append("Projects getting community recognition")
    if commit_quality > 0.7:   pros.append("Descriptive commit messages")

    if consistency < 0.3:      cons.append("Low commit consistency")
    if project_quality < 0.3:  cons.append("Mostly tutorial/homework repos")
    if activity.get("garbage_commits", 0) > activity.get("total_commits", 1) * 0.5:
        cons.append("Many low-quality commit messages")
    if n_langs <= 1:           cons.append("Limited language diversity")
    if not orig_projects:      cons.append("No clearly original projects found")

    return {
        "score":           round(final_score, 4),
        "breakdown": {
            "project_quality": round(project_quality, 3),
            "consistency":     round(consistency, 3),
            "tech_depth":      round(tech_depth, 3),
            "activity":        round(activity_score, 3),
        },
        "pros": " | ".join(pros) or "N/A",
        "cons": " | ".join(cons) or "N/A",
    }