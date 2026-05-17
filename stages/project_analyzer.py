from utils.ai_client import classify_text, summarize_text

PROJECT_QUALITY_LABELS = [
    "original project with clear purpose",
    "tutorial clone or course homework",
    "complex system with multiple components",
    "simple script or utility",
]

COMPLEXITY_LABELS = [
    "beginner level project",
    "intermediate level project",
    "advanced level project",
]

def analyze_repo(repo) -> dict:
    """Analyze a single repo and return structured project data."""
    try:
        readme = repo.get_readme().decoded_content.decode("utf-8", errors="ignore")
    except Exception:
        readme = repo.description or ""

    summary = summarize_text(readme) if len(readme) > 100 else (repo.description or "")

    quality_scores  = classify_text(readme or repo.name, PROJECT_QUALITY_LABELS)
    complex_scores  = classify_text(readme or repo.name, COMPLEXITY_LABELS)

    topics = list(repo.get_topics())
    try:
        languages = list(repo.get_languages().keys())
    except Exception:
        languages = []

    is_original = quality_scores.get("original project with clear purpose", 0) > 0.4
    complexity  = max(complex_scores, key=complex_scores.get) if complex_scores else "unknown"

    return {
        "name":        repo.name,
        "description": summary,
        "languages":   languages,
        "topics":      topics,
        "stars":       repo.stargazers_count,
        "is_original": is_original,
        "complexity":  complexity,
        "quality_score": round(quality_scores.get("original project with clear purpose", 0), 3),
    }

def analyze_projects(user) -> list[dict]:
    """Analyze top 5 original repos sorted by stars."""
    repos = sorted(
        [r for r in user.get_repos() if not r.fork],
        key=lambda r: r.stargazers_count,
        reverse=True,
    )[:5]
    return [analyze_repo(r) for r in repos]