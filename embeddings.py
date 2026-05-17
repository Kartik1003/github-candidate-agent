"""
embeddings.py — Task 2: Semantic matching via sentence-transformers.

Model : sentence-transformers/all-MiniLM-L6-v2  (loaded once, reused)
Output: student_score, job_seeker_score, developer_score, top_match
"""

import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL = None

def _get_model():
    global _MODEL
    if _MODEL is None:
        print("[embeddings] Loading all-MiniLM-L6-v2 …")
        _MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("[embeddings] Model ready.")
    return _MODEL

REFERENCE_PHRASES = {
    "student": [
        "computer science student looking for internship",
        "undergraduate developer India",
        "engineering student pursuing btech",
        "college student learning to code",
        "final year student open to opportunities",
    ],
    "job_seeker": [
        "open to work software engineer",
        "actively looking for software developer roles",
        "seeking full-time opportunities in tech",
        "available for hire developer",
        "job seeker software engineering",
    ],
    "developer": [
        "senior developer not looking for jobs",
        "experienced software architect building systems",
        "open source maintainer and contributor",
        "full stack developer with years of experience",
        "professional software engineer at a tech company",
    ],
}

_REF_EMBEDDINGS = None

def _get_reference_embeddings():
    global _REF_EMBEDDINGS
    if _REF_EMBEDDINGS is None:
        model = _get_model()
        _REF_EMBEDDINGS = {}
        for cat, phrases in REFERENCE_PHRASES.items():
            _REF_EMBEDDINGS[cat] = model.encode(phrases, convert_to_numpy=True)
    return _REF_EMBEDDINGS

def _cosine_sim(a, b):
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(dot / norm) if norm else 0.0

def _avg_similarity(text_emb, ref_embs):
    return float(np.mean([_cosine_sim(text_emb, r) for r in ref_embs]))

UNCLEAR_THRESHOLD = 0.35

def encode_text(text):
    return _get_model().encode(text, convert_to_numpy=True).astype(np.float32)

def embed_and_classify(text):
    if not text or not text.strip():
        return {
            "student_score": 0.0, "job_seeker_score": 0.0,
            "developer_score": 0.0, "top_match": "unclear",
            "embedding": np.zeros(384, dtype=np.float32),
        }
    text_emb = encode_text(text)
    ref_embs = _get_reference_embeddings()
    scores = {cat: round(_avg_similarity(text_emb, refs), 4) for cat, refs in ref_embs.items()}
    max_cat = max(scores, key=scores.get)
    top = max_cat if scores[max_cat] >= UNCLEAR_THRESHOLD else "unclear"
    return {
        "student_score": scores.get("student", 0.0),
        "job_seeker_score": scores.get("job_seeker", 0.0),
        "developer_score": scores.get("developer", 0.0),
        "top_match": top, "embedding": text_emb,
    }

if __name__ == "__main__":
    for t in [
        "CS undergraduate at IIT Delhi, looking for SDE internship",
        "Senior Staff Engineer at Google, 15 years experience",
        "Open to work | Full-stack developer | React + Node.js", "",
    ]:
        r = embed_and_classify(t)
        print(f"\nText: {t!r}")
        print(f"  Student={r['student_score']:.4f}  JobSeeker={r['job_seeker_score']:.4f}  Dev={r['developer_score']:.4f}  → {r['top_match']}")
