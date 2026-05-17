import config
from utils.ai_client import classify_text

DOMAIN_LABELS = ["frontend", "backend", "AI/ML", "data engineering", "DevOps", "mobile", "full-stack"]

def categorize(activity: dict, projects: list[dict]) -> dict:
    """
    Rule-based first pass (languages) + AI fallback on project descriptions.
    Returns a dict of domain → score (0-1).
    """
    lang_hits = {d: 0 for d in config.DOMAIN_LANGUAGES}
    top_langs = set(activity.get("top_languages", []))

    for domain, langs in config.DOMAIN_LANGUAGES.items():
        for lang in langs:
            if lang in top_langs:
                lang_hits[domain] += 1

    # Normalize language scores
    max_hits = max(lang_hits.values()) or 1
    domain_scores = {d: round(v / max_hits, 2) for d, v in lang_hits.items()}

    # AI refinement using project descriptions
    all_descriptions = " ".join(p.get("description", "") for p in projects)
    if all_descriptions.strip():
        ai_scores = classify_text(all_descriptions, DOMAIN_LABELS)
        for label, score in ai_scores.items():
            key = label.lower().replace("/", "_").replace(" ", "_")
            if key in domain_scores:
                # blend language signal + AI signal
                domain_scores[key] = round((domain_scores.get(key, 0) + score) / 2, 3)

    primary = max(domain_scores, key=domain_scores.get)
    return {"domains": domain_scores, "primary_domain": primary}