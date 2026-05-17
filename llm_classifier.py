"""
llm_classifier.py — Tasks 1, 3, 4: Gemini-powered classification, scoring, and link extraction.

All LLM calls use gemini-3.1-pro-preview via the Google GenAI SDK.
Every call is wrapped in try/except with strict JSON validation.
"""

import json
import re
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Gemini client (singleton)
# ---------------------------------------------------------------------------

_CLIENT = None
MODEL = "gemini-3.1-pro-preview"


def _get_client():
    global _CLIENT
    if _CLIENT is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Add it to your .env file."
            )
        _CLIENT = genai.Client(api_key=api_key)
    return _CLIENT


def _call_gemini(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """Send a prompt to Gemini and return the text response."""
    client = _get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=user_prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=0.2,
        ),
    )
    return response.text


def _extract_json(text: str) -> dict:
    """Extract and parse JSON from Gemini's response, handling markdown fences."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```json\s*", "", text)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()
    return json.loads(cleaned)


# ═══════════════════════════════════════════════════════════════════════════
# TASK 1 — LLM Classification (replaces keyword filters)
# ═══════════════════════════════════════════════════════════════════════════

_CLASSIFY_SYSTEM = "You are a precise classifier analyzing GitHub profiles. Always respond ONLY with valid JSON, no extra text."

_CLASSIFY_TEMPLATE = """You are analyzing a GitHub profile to classify the candidate.

Bio: {bio}
README excerpt: {readme}

Classify this person. Respond ONLY in JSON:
{{
  "is_indian": true/false,
  "is_student": true/false,
  "is_job_seeker": true/false,
  "confidence": {{ "indian": 0.0-1.0, "student": 0.0-1.0, "job_seeker": 0.0-1.0 }},
  "reasoning": "brief explanation"
}}"""

_EMPTY_CLASSIFICATION = {
    "is_indian": False,
    "is_student": False,
    "is_job_seeker": False,
    "confidence": {"indian": 0.0, "student": 0.0, "job_seeker": 0.0},
    "reasoning": "No bio or README content available for classification.",
}


def classify_candidate(bio: str, readme: str) -> dict:
    """
    Task 1: Use Gemini to classify a candidate as Indian / student / job-seeker.

    Returns a dict with is_indian, is_student, is_job_seeker, confidence, reasoning.
    If bio and readme are both empty, returns all-false with zero confidence.
    """
    bio = (bio or "").strip()
    readme = (readme or "").strip()

    if not bio and not readme:
        return _EMPTY_CLASSIFICATION.copy()

    prompt = _CLASSIFY_TEMPLATE.format(
        bio=bio[:500] or "(empty)",
        readme=readme[:1000] or "(empty)",
    )

    try:
        raw = _call_gemini(_CLASSIFY_SYSTEM, prompt)
        result = _extract_json(raw)

        # Validate expected keys
        for key in ("is_indian", "is_student", "is_job_seeker", "confidence"):
            if key not in result:
                raise KeyError(f"Missing key: {key}")

        return result

    except Exception as e:
        print(f"[llm_classifier] classify_candidate error: {e}")
        return _EMPTY_CLASSIFICATION.copy()


# ═══════════════════════════════════════════════════════════════════════════
# TASK 3 — LLM-Based Smart Scoring
# ═══════════════════════════════════════════════════════════════════════════

_SCORE_SYSTEM = "You are a technical recruiter. Always respond ONLY with valid JSON, no extra text."

_SCORE_TEMPLATE = """You are a technical recruiter evaluating a GitHub profile for internship/job readiness.

Candidate Profile:
- Name: {name}
- Bio: {bio}
- Repositories ({repo_count} total): {repo_names_and_descriptions}
- Commit activity (last 90 days): {commit_count}
- Top languages: {languages}
- README sample: {readme_sample}

Score this candidate out of 100. Consider:
1. Project quality and complexity (30 pts)
2. Consistency of contributions (25 pts)
3. Tech stack relevance (20 pts)
4. Communication/documentation quality (15 pts)
5. Open source involvement (10 pts)

Respond ONLY in JSON:
{{
  "total_score": int,
  "breakdown": {{
    "project_quality": int,
    "consistency": int,
    "tech_stack": int,
    "documentation": int,
    "open_source": int
  }},
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "recruiter_summary": "2-3 sentence summary"
}}"""

_EMPTY_SCORE = {
    "total_score": 0,
    "breakdown": {
        "project_quality": 0,
        "consistency": 0,
        "tech_stack": 0,
        "documentation": 0,
        "open_source": 0,
    },
    "strengths": [],
    "weaknesses": ["Insufficient data to evaluate"],
    "recruiter_summary": "Not enough profile data for evaluation.",
}


def llm_score_candidate(profile: dict) -> dict:
    """
    Task 3: Use Gemini to evaluate and score a GitHub profile.

    profile keys: name, bio, repos (list of dicts), commit_count,
                  top_languages (list), readme_sample (str)
    """
    repos = profile.get("repos", [])
    repo_descriptions = "; ".join(
        f"{r.get('name', '?')}: {r.get('description', 'no description')}"
        for r in repos[:10]
    )

    languages = ", ".join(profile.get("top_languages", [])[:8]) or "N/A"

    prompt = _SCORE_TEMPLATE.format(
        name=profile.get("name", "Unknown"),
        bio=(profile.get("bio") or "(empty)")[:300],
        repo_count=len(repos),
        repo_names_and_descriptions=repo_descriptions[:800] or "N/A",
        commit_count=profile.get("commit_count", 0),
        languages=languages,
        readme_sample=(profile.get("readme_sample") or "(empty)")[:600],
    )

    try:
        raw = _call_gemini(_SCORE_SYSTEM, prompt, max_tokens=1024)
        result = _extract_json(raw)

        # Validate score bounds
        total = result.get("total_score", 0)
        result["total_score"] = max(0, min(100, int(total)))

        return result

    except Exception as e:
        print(f"[llm_classifier] llm_score_candidate error: {e}")
        return _EMPTY_SCORE.copy()


# ═══════════════════════════════════════════════════════════════════════════
# TASK 4 — Intelligent Link Extraction (LLM + Regex hybrid)
# ═══════════════════════════════════════════════════════════════════════════

_URL_REGEX = re.compile(r"https?://[^\s<>\"{}|\\^`\[\]]+")

_LINKS_SYSTEM = "You are a link extractor. Always respond ONLY with valid JSON, no extra text."

_LINKS_TEMPLATE = """Extract and classify all professional profile links from this text.
Text: {text}
Raw URLs found: {url_list}

Also detect unlinked mentions like "LinkedIn: john-doe" or "portfolio at mysite.com"

Respond ONLY in JSON:
{{
  "linkedin": "url or null",
  "portfolio": "url or null",
  "resume": "url or null",
  "twitter": "url or null",
  "github_pages": "url or null",
  "other": ["url", ...]
}}"""

_EMPTY_LINKS = {
    "linkedin": None,
    "portfolio": None,
    "resume": None,
    "twitter": None,
    "github_pages": None,
    "other": [],
}


def extract_links(text: str) -> dict:
    """
    Task 4: Hybrid link extraction — regex pre-pass + LLM classification.

    Returns a dict with linkedin, portfolio, resume, twitter, github_pages, other.
    """
    text = (text or "").strip()
    if not text:
        return _EMPTY_LINKS.copy()

    # Step 1 — Regex pre-pass
    raw_urls = _URL_REGEX.findall(text)
    # Clean trailing punctuation
    raw_urls = [u.rstrip(".,;:)]}") for u in raw_urls]

    # If no URLs found and text is very short, skip LLM call
    if not raw_urls and len(text) < 20:
        return _EMPTY_LINKS.copy()

    # Step 2 — LLM classification
    prompt = _LINKS_TEMPLATE.format(
        text=text[:1500],
        url_list=json.dumps(raw_urls[:20]),
    )

    try:
        raw = _call_gemini(_LINKS_SYSTEM, prompt, max_tokens=512)
        result = _extract_json(raw)

        # Ensure all expected keys
        for key in ("linkedin", "portfolio", "resume", "twitter", "github_pages"):
            if key not in result:
                result[key] = None
        if "other" not in result:
            result["other"] = []

        return result

    except Exception as e:
        print(f"[llm_classifier] extract_links error: {e}")
        # Fallback: return regex-only results
        fallback = _EMPTY_LINKS.copy()
        fallback["other"] = raw_urls[:10]
        return fallback


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Task 1: classify_candidate ===")
    r = classify_candidate(
        bio="CS undergrad at IIT Bombay | Open to SDE internships",
        readme="# Portfolio\nBuilt web apps with React and Node.js",
    )
    print(json.dumps(r, indent=2))

    print("\n=== Task 3: llm_score_candidate ===")
    r = llm_score_candidate({
        "name": "Test User",
        "bio": "Full-stack developer",
        "repos": [{"name": "my-app", "description": "A React dashboard"}],
        "commit_count": 150,
        "top_languages": ["Python", "JavaScript", "TypeScript"],
        "readme_sample": "# My App\nA full-stack dashboard built with React.",
    })
    print(json.dumps(r, indent=2))

    print("\n=== Task 4: extract_links ===")
    r = extract_links(
        "Check my portfolio at https://johndoe.dev and LinkedIn: john-doe-123. "
        "Also https://twitter.com/johndoe"
    )
    print(json.dumps(r, indent=2))
