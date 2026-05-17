import re, config
from utils.github_client import get_user

# ---------------------------------------------------------------------------
# Location / nationality heuristics
# ---------------------------------------------------------------------------

_INDIA_KEYWORDS = re.compile(
    r"\b(india|bharat|bangalore|bengaluru|mumbai|delhi|hyderabad|chennai|pune|kolkata|"
    r"ahmedabad|jaipur|lucknow|chandigarh|kochi|trivandrum|thiruvananthapuram|"
    r"bhopal|indore|nagpur|noida|gurgaon|gurugram|coimbatore|vizag|visakhapatnam|"
    r"mangalore|mysore|surat|patna|ranchi|bhubaneswar|guwahati|"
    r"kerala|karnataka|tamil\s?nadu|maharashtra|telangana|andhra\s?pradesh|"
    r"west\s?bengal|uttar\s?pradesh|madhya\s?pradesh|rajasthan|gujarat|"
    r"punjab|haryana|odisha|assam|bihar|iit|iiit|nit|bits)\b",
    re.IGNORECASE,
)


def _fields(user) -> str:
    """Concatenate all relevant text fields for keyword matching."""
    parts = []
    for attr in ("location", "bio", "company", "email"):
        val = getattr(user, attr, None)
        if val:
            parts.append(str(val))
    return " ".join(parts)


def is_indian(user) -> bool:
    fields = " ".join(filter(None, [
        user.location or "",
        user.bio or "",
        user.company or "",
        user.name or "",
    ])).lower()
    return any(kw in fields for kw in config.INDIAN_KEYWORDS)


# ---------------------------------------------------------------------------
# Student heuristics
# ---------------------------------------------------------------------------

_STUDENT_KEYWORDS = re.compile(
    r"\b(student|undergrad|undergraduate|grad\b|postgrad|freshman|sophomore|junior|senior|"
    r"b\.?tech|m\.?tech|b\.?sc|m\.?sc|b\.?e\b|m\.?e\b|ph\.?d|"
    r"university|college|institute|school of|academy|"
    r"computer\s?science\s?student|cs\s?student|engineering\s?student|"
    r"pursuing|studying|learner|campus\s?ambassador)\b",
    re.IGNORECASE,
)


def is_student(user) -> bool:
    bio = (user.bio or "").lower()
    name = (user.name or "").lower()
    text = bio + " " + name
    return any(kw in text for kw in config.STUDENT_KEYWORDS)


# ---------------------------------------------------------------------------
# Bulk filter helper (keeps backward compatibility)
# ---------------------------------------------------------------------------

def apply_filters(candidates):
    """Filter a list of user objects to only Indian students."""
    print("Filtering candidates...")
    return [c for c in candidates if is_indian(c) and is_student(c)]

def filter_candidates(logins: list) -> list:
    """
    Returns a list of PyGithub NamedUser objects that pass both filters.
    """
    valid = []
    for login in logins:
        user = get_user(login)
        if user is None:
            continue
        if is_indian(user) and is_student(user):
            valid.append(user)
            print(f"  ✓ {login} — {user.location} | {(user.bio or '')[:60]}")
    print(f"\nFiltered down to {len(valid)} Indian students.")
    return valid