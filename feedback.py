"""
feedback.py — Task 5: Feedback loop + ML classifier.

- mark_candidate()    — record human labels (good/bad)
- train_classifier()  — train XGBoost/LogisticRegression when labels >= 50
- ml_rank_candidate() — predict probability of "good" using saved model
"""

import os
import json
import numpy as np
import joblib

from db import get_labeled_candidates, get_label_counts, update_label, get_candidate

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_MODEL_DIR = os.path.dirname(__file__)
_MODEL_PATH = os.path.join(_MODEL_DIR, "candidate_classifier.pkl")
_MIN_LABELS = 50  # minimum labeled examples before training


# ---------------------------------------------------------------------------
# Feedback intake
# ---------------------------------------------------------------------------

def mark_candidate(username: str, label: str):
    """
    Record a human label for a candidate.

    Args:
        username: GitHub username
        label:    "good" or "bad"
    """
    if label not in ("good", "bad"):
        raise ValueError(f"Label must be 'good' or 'bad', got: {label!r}")

    update_label(username, label)
    counts = get_label_counts()
    total = sum(counts.values())
    print(f"[feedback] Labeled {username} as '{label}'. Total labels: {total}")

    if total >= _MIN_LABELS:
        print(f"[feedback] {total} labels available — consider running train_classifier().")


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def _extract_features(candidate: dict) -> np.ndarray | None:
    """
    Extract feature vector from a candidate record.

    Features: [llm_score, student_score, job_seeker_score, repo_count, commit_count]
    """
    profile = candidate.get("profile", {})
    if not profile:
        return None

    llm_score = candidate.get("llm_score", 0) or 0

    # Embedding scores from profile
    emb = profile.get("embedding_scores", {})
    student_score = emb.get("student_score", 0) or 0
    job_seeker_score = emb.get("job_seeker_score", 0) or 0

    # GitHub stats
    stats = profile.get("github_stats", {})
    repo_count = stats.get("repos", 0) or 0
    commit_count = stats.get("commits", 0) or 0

    return np.array([
        float(llm_score),
        float(student_score),
        float(job_seeker_score),
        float(repo_count),
        float(commit_count),
    ], dtype=np.float64)


# ---------------------------------------------------------------------------
# Classifier training
# ---------------------------------------------------------------------------

def train_classifier() -> dict:
    """
    Train a classifier on labeled candidates.

    Uses XGBoost if available, falls back to LogisticRegression.
    Saves model to candidate_classifier.pkl.

    Returns:
        dict with accuracy, model_type, sample_count, class_distribution
    """
    labeled = get_labeled_candidates()
    counts = get_label_counts()
    total = sum(counts.values())

    if total < _MIN_LABELS:
        return {
            "status": "insufficient_data",
            "total_labels": total,
            "required": _MIN_LABELS,
            "message": f"Need at least {_MIN_LABELS} labels. Currently have {total}.",
        }

    # Build feature matrix and label vector
    X_list, y_list = [], []
    skipped = 0

    for cand in labeled:
        features = _extract_features(cand)
        if features is None:
            skipped += 1
            continue
        X_list.append(features)
        y_list.append(1 if cand["label"] == "good" else 0)

    if len(X_list) < 10:
        return {
            "status": "insufficient_features",
            "usable_samples": len(X_list),
            "message": "Not enough candidates with extractable features.",
        }

    X = np.array(X_list)
    y = np.array(y_list)

    # Train/test split (80/20)
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None,
    )

    # Try XGBoost first, fall back to LogisticRegression
    model_type = "unknown"
    try:
        from xgboost import XGBClassifier
        model = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            eval_metric="logloss",
            use_label_encoder=False,
            random_state=42,
        )
        model_type = "XGBoost"
    except ImportError:
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight="balanced",
        )
        model_type = "LogisticRegression"

    model.fit(X_train, y_train)

    # Evaluate on holdout
    from sklearn.metrics import accuracy_score, classification_report
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Save model
    joblib.dump(model, _MODEL_PATH)
    print(f"[feedback] Trained {model_type} — accuracy: {accuracy:.3f}")
    print(f"[feedback] Model saved to {_MODEL_PATH}")
    print(f"[feedback] Classification report:\n{classification_report(y_test, y_pred)}")

    return {
        "status": "trained",
        "model_type": model_type,
        "accuracy": round(accuracy, 4),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "skipped": skipped,
        "class_distribution": counts,
    }


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def ml_rank_candidate(features: dict) -> float | None:
    """
    Predict probability of a candidate being "good" using the saved model.

    Args:
        features: dict with keys llm_score, student_score, job_seeker_score,
                  repo_count, commit_count

    Returns:
        float probability (0.0–1.0) or None if no model is available.
    """
    if not os.path.exists(_MODEL_PATH):
        return None

    try:
        model = joblib.load(_MODEL_PATH)

        feature_vec = np.array([[
            float(features.get("llm_score", 0)),
            float(features.get("student_score", 0)),
            float(features.get("job_seeker_score", 0)),
            float(features.get("repo_count", 0)),
            float(features.get("commit_count", 0)),
        ]])

        proba = model.predict_proba(feature_vec)
        # Return probability of class 1 (good)
        return float(proba[0][1])

    except Exception as e:
        print(f"[feedback] ml_rank_candidate error: {e}")
        return None


def has_trained_model() -> bool:
    """Check if a trained classifier exists."""
    return os.path.exists(_MODEL_PATH)


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Feedback system status ===")
    counts = get_label_counts()
    print(f"Label counts: {counts}")
    print(f"Trained model exists: {has_trained_model()}")

    print("\n=== ML rank test ===")
    score = ml_rank_candidate({
        "llm_score": 72,
        "student_score": 0.65,
        "job_seeker_score": 0.45,
        "repo_count": 15,
        "commit_count": 200,
    })
    print(f"ML score: {score}")
