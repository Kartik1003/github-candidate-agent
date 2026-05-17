"""
stages/code_quality.py — Multi-repo code quality analysis across ALL of a candidate's repos.

Strategy for speed (~10s target):
  - Use repo.get_git_tree(recursive=True)  → 1 API call per repo, full file listing
  - Use repo.get_languages()               → 1 API call per repo, language bytes
  - Tool/framework detection from filenames alone (no content reading)
  - Only read file content for Python complexity (top 1 repo, 5 files max)
  - Parallelize all repos with ThreadPoolExecutor (max_workers=8)

Output: aggregated score across ALL non-fork repos + full language + tool breakdown.
"""

import re
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict


# ── Grade helpers ────────────────────────────────────────────────────────────

GRADE_COLOR = {"A": "#1D9E75", "B": "#40cef3", "C": "#E6A817", "D": "#ffa44c", "E": "#E64D4D", "F": "#888"}

def _pct_to_grade(pct: float) -> str:
    if pct >= 0.80: return "A"
    if pct >= 0.60: return "B"
    if pct >= 0.40: return "C"
    if pct >= 0.20: return "D"
    return "F"


# ── Tool detection rules (filename / path patterns, no content reading) ──────

TOOL_RULES = [
    # DevOps / Infrastructure
    ("Docker",           re.compile(r"(^|/)Dockerfile$|docker-compose\.ya?ml$", re.I)),
    ("Kubernetes",       re.compile(r"(^|/)(k8s|kubernetes)/|\.ya?ml$", re.I)),
    ("Terraform",        re.compile(r"\.tf$|terraform/", re.I)),
    ("GitHub Actions",   re.compile(r"\.github/workflows/", re.I)),
    ("Jenkins",          re.compile(r"(^|/)Jenkinsfile$", re.I)),
    ("Make",             re.compile(r"(^|/)Makefile$", re.I)),
    # Testing
    ("Pytest",           re.compile(r"conftest\.py$|pytest\.ini$|pyproject\.toml$", re.I)),
    ("Jest",             re.compile(r"jest\.config\.(js|ts|json)$", re.I)),
    ("Vitest",           re.compile(r"vitest\.config\.(js|ts)$", re.I)),
    ("Mocha",            re.compile(r"\.mocharc\.(js|yml|json)$", re.I)),
    # Frontend frameworks (from config files)
    ("React",            re.compile(r"(^|/)react-.*\.js$|vite\.config\.(js|ts)$|next\.config\.(js|ts)$", re.I)),
    ("Next.js",          re.compile(r"next\.config\.(js|ts|mjs)$", re.I)),
    ("Vue",              re.compile(r"vue\.config\.(js|ts)$|\.vue$", re.I)),
    ("Svelte",           re.compile(r"svelte\.config\.(js|ts)$|\.svelte$", re.I)),
    ("Angular",          re.compile(r"angular\.json$", re.I)),
    # Python ecosystem
    ("FastAPI/Flask",    re.compile(r"(^|/)(app|main|server)\.py$", re.I)),
    ("Django",           re.compile(r"(^|/)manage\.py$|settings\.py$", re.I)),
    ("Jupyter",          re.compile(r"\.ipynb$", re.I)),
    # Packaging & config
    ("TypeScript",       re.compile(r"tsconfig(\..*)?\.json$", re.I)),
    ("ESLint",           re.compile(r"\.eslint(rc|\.config)\.(js|json|yml)$", re.I)),
    ("Prettier",         re.compile(r"\.prettierrc(\..*)?$|prettier\.config\.(js|ts)$", re.I)),
    ("dotenv",           re.compile(r"\.env\.example$|\.env\.sample$", re.I)),
    # Mobile / other
    ("Android",          re.compile(r"(^|/)AndroidManifest\.xml$", re.I)),
    ("Flutter",          re.compile(r"pubspec\.ya?ml$", re.I)),
]

_TEST_RE = re.compile(
    r"(^|/)(test_|_test\.|\.test\.|\.spec\.|__tests__/|tests?/)", re.I
)
_DOCSTRING_RE = re.compile(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', re.M)
_FUNCTION_RE  = re.compile(r"^\s*def\s+\w+", re.M)


# ── Per-repo analysis (lightweight — tree + languages only) ──────────────────

def _analyze_repo(repo) -> dict | None:
    """Analyze one repo using only git tree + language API calls."""
    try:
        lang_bytes: dict = {}
        try:
            lang_bytes = repo.get_languages()
        except Exception:
            pass

        file_paths: list[str] = []
        try:
            tree = repo.get_git_tree(repo.default_branch, recursive=True).tree
            file_paths = [f.path for f in tree if f.type == "blob"]
        except Exception:
            pass

        # Test detection
        test_files    = [p for p in file_paths if _TEST_RE.search(p)]
        has_tests     = len(test_files) > 0

        # Docs / README
        has_readme    = any("readme" in p.lower() for p in file_paths)
        has_docs      = any(("/docs/" in p.lower() or p.lower().startswith("docs/")) for p in file_paths)

        # Tool detection (filename patterns only)
        detected_tools: list[str] = []
        for tool_name, pattern in TOOL_RULES:
            if any(pattern.search(p) for p in file_paths):
                if tool_name not in detected_tools:
                    detected_tools.append(tool_name)

        # Topic-based tools (free metadata)
        for topic in (repo.topics or []):
            t = topic.lower()
            for keyword, display in [
                ("react", "React"), ("vue", "Vue"), ("angular", "Angular"),
                ("nextjs", "Next.js"), ("django", "Django"), ("flask", "Flask"),
                ("fastapi", "FastAPI"), ("docker", "Docker"), ("kubernetes", "Kubernetes"),
                ("tensorflow", "TensorFlow"), ("pytorch", "PyTorch"), ("scikit-learn", "scikit-learn"),
                ("mongodb", "MongoDB"), ("postgresql", "PostgreSQL"), ("redis", "Redis"),
                ("graphql", "GraphQL"), ("typescript", "TypeScript"),
            ]:
                if keyword in t and display not in detected_tools:
                    detected_tools.append(display)

        return {
            "name":          repo.name,
            "stars":         repo.stargazers_count,
            "language":      repo.language or "Unknown",
            "lang_bytes":    lang_bytes,
            "file_count":    len(file_paths),
            "test_count":    len(test_files),
            "has_tests":     has_tests,
            "has_readme":    has_readme,
            "has_docs":      has_docs,
            "tools":         detected_tools,
            "is_fork":       repo.fork,
        }
    except Exception:
        return None


def _get_python_complexity(user, repo_name: str) -> str | None:
    """
    Read up to 5 Python files from one repo and run radon.
    Returns a letter grade A–F, or None if radon is unavailable.
    """
    try:
        repo      = user.get_repo(repo_name)
        tree      = repo.get_git_tree(repo.default_branch, recursive=True).tree
        py_files  = [f.path for f in tree
                     if f.path.endswith(".py") and "test" not in f.path.lower()][:5]
        scores    = []
        for path in py_files:
            try:
                content = base64.b64decode(
                    repo.get_contents(path).content
                ).decode("utf-8", errors="ignore")
                from radon.complexity import cc_visit
                blocks = cc_visit(content)
                if blocks:
                    scores.append(sum(b.complexity for b in blocks) / len(blocks))
            except Exception:
                continue
        if not scores:
            return None
        avg = sum(scores) / len(scores)
        if avg <= 5:   return "A"
        if avg <= 10:  return "B"
        if avg <= 15:  return "C"
        if avg <= 20:  return "D"
        if avg <= 25:  return "E"
        return "F"
    except Exception:
        return None


# ── Main entry point ─────────────────────────────────────────────────────────

def analyze_code_quality(user, top_repo_name: str = None) -> dict:
    """
    Analyze ALL non-fork repos for a user in parallel.

    Returns a comprehensive report including:
      - overall_grade        (A–F)
      - complexity_grade     (A–F, Python only, from top repo)
      - language_breakdown   {lang: bytes, pct}  — aggregated across ALL repos
      - all_tools            [str] — frameworks/tools detected across ALL repos
      - repo_count           int
      - repos_with_tests     int
      - total_test_files     int
      - per_repo             [dict] — individual repo results
      - grade_color          str
    """
    try:
        all_repos = [r for r in user.get_repos()]
    except Exception:
        return _empty_result("Could not fetch repos")

    original_repos = [r for r in all_repos if not r.fork]

    if not original_repos:
        return _empty_result("No original repos found")

    # ── Parallel repo analysis ──────────────────────────────────────────────
    per_repo: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        future_map = {ex.submit(_analyze_repo, repo): repo.name for repo in original_repos[:20]}
        for future in as_completed(future_map):
            result = future.result()
            if result:
                per_repo.append(result)

    per_repo.sort(key=lambda r: r["stars"], reverse=True)

    # ── Aggregate language breakdown ────────────────────────────────────────
    agg_lang_bytes: dict[str, int] = defaultdict(int)
    for r in per_repo:
        for lang, nb in r["lang_bytes"].items():
            agg_lang_bytes[lang] += nb

    total_bytes = sum(agg_lang_bytes.values()) or 1
    language_breakdown = {
        lang: {
            "bytes": nb,
            "pct":   round(nb / total_bytes * 100, 1),
        }
        for lang, nb in sorted(agg_lang_bytes.items(), key=lambda x: -x[1])
    }

    # ── Aggregate tools (deduplicated) ──────────────────────────────────────
    all_tools: list[str] = []
    for r in per_repo:
        for t in r["tools"]:
            if t not in all_tools:
                all_tools.append(t)

    # ── Aggregate quality signals ───────────────────────────────────────────
    repos_with_tests = sum(1 for r in per_repo if r["has_tests"])
    total_test_files = sum(r["test_count"] for r in per_repo)
    repos_with_readme= sum(1 for r in per_repo if r["has_readme"])
    n = len(per_repo)

    # ── Python complexity (on top Python repo only) ─────────────────────────
    complexity_grade = None
    python_repos     = [r for r in per_repo if r["language"] == "Python"]
    if python_repos:
        complexity_grade = _get_python_complexity(user, python_repos[0]["name"])

    # ── Scoring ─────────────────────────────────────────────────────────────
    score     = 0.0
    max_score = 0.0

    # Tests (0–3 pts): ratio of repos with tests
    max_score += 3
    test_ratio = repos_with_tests / max(n, 1)
    if test_ratio >= 0.5:   score += 3
    elif test_ratio >= 0.25: score += 2
    elif test_ratio > 0:    score += 1

    # README coverage (0–2 pts)
    max_score += 2
    readme_ratio = repos_with_readme / max(n, 1)
    score += min(2, readme_ratio * 2)

    # Tool diversity (0–2 pts): more tools = more mature ecosystem knowledge
    max_score += 2
    score += min(2, len(all_tools) * 0.25)

    # Complexity — Python only (0–2 pts)
    if complexity_grade:
        max_score += 2
        grade_pts  = {"A": 2, "B": 1.6, "C": 1.2, "D": 0.8, "E": 0.4, "F": 0}
        score     += grade_pts.get(complexity_grade, 0)

    overall_grade = _pct_to_grade(score / max(max_score, 1))

    return {
        "overall_grade":     overall_grade,
        "grade_color":       GRADE_COLOR.get(overall_grade, "#888"),
        "complexity_grade":  complexity_grade,
        "language_breakdown": language_breakdown,
        "top_languages":     list(language_breakdown.keys())[:8],
        "all_tools":         all_tools,
        "repo_count":        n,
        "repos_with_tests":  repos_with_tests,
        "total_test_files":  total_test_files,
        "repos_with_readme": repos_with_readme,
        "per_repo":          per_repo[:10],   # top 10 by stars
        "error":             None,
    }


def _empty_result(reason: str) -> dict:
    return {
        "overall_grade": "F", "grade_color": "#888",
        "complexity_grade": None, "language_breakdown": {},
        "top_languages": [], "all_tools": [],
        "repo_count": 0, "repos_with_tests": 0,
        "total_test_files": 0, "repos_with_readme": 0,
        "per_repo": [], "error": reason,
    }
