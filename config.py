import os
from dotenv import load_dotenv

# Base configuration loading
load_dotenv()

def reload_config():
    """Reloads .env file from disk."""
    load_dotenv(override=True)

# Helper functions to get live values
def get_email_sender():
    reload_config()
    return os.getenv("EMAIL_SENDER", "")

def get_email_password():
    reload_config()
    return os.getenv("EMAIL_PASSWORD", "")

def get_email_receiver():
    reload_config()
    return os.getenv("EMAIL_RECEIVER", "")

# We keep the old variables for backward compatibility, but they will be 
# static unless the server restarts. 
# Code that wants "live" updates should use the functions above.
EMAIL_SENDER   = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")

# Static settings
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN")
HF_TOKEN       = os.getenv("HF_TOKEN")
SHEET_ID       = os.getenv("GOOGLE_SHEET_ID")
SERVICE_ACCOUNT_FILE = "credentials/service_account.json"

# Tunable constants
MAX_CANDIDATES   = 10_000
TOP_N            = 100
COMMITS_LOOKBACK = 90

SCORE_WEIGHTS = {
    "project_quality": 0.35,
    "consistency":     0.25,
    "tech_depth":      0.20,
    "activity":        0.20,
}

INDIAN_KEYWORDS = [
    "india", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
    "chennai", "pune", "kolkata", "ahmedabad", "iit", "nit", "bits",
]

STUDENT_KEYWORDS = [
    "student", "btech", "b.tech", "bca", "mca", "mtech", "m.tech",
    "undergrad", "undergraduate", "freshman", "sophomore", "junior", "senior",
    "cs undergraduate", "computer science student", "engineering student",
    "looking for internship", "open to internship", "seeking internship",
    "final year", "3rd year", "2nd year", "1st year",
]

DOMAIN_LANGUAGES = {
    "frontend":         ["JavaScript", "TypeScript", "CSS", "HTML", "Vue", "Svelte"],
    "backend":          ["Python", "Java", "Go", "Rust", "C#", "Ruby", "PHP", "Kotlin"],
    "ai_ml":            ["Jupyter Notebook", "Python"],
    "data_engineering": ["SQL", "Scala", "R"],
    "devops":           ["Dockerfile", "Shell", "HCL"],
    "mobile":           ["Swift", "Kotlin", "Dart"],
}