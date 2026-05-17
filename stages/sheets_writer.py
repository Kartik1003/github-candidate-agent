import gspread, datetime
from google.oauth2.service_account import Credentials
import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def get_sheet():
    creds  = Credentials.from_service_account_file(config.SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(config.SHEET_ID)

HEADERS = [
    "Rank", "Name", "GitHub", "LinkedIn", "Portfolio", "Resume/CV",
    "Score", "Primary Domain", "Skills", "Pros", "Cons",
    "Consistency", "Project Quality", "Tech Depth", "Activity",
    "Projects Summary", "Top Languages", "Stars", "Last Updated",
]

def write_candidates(ranked: list[dict]):
    sheet = get_sheet()
    today = datetime.date.today().isoformat()

    try:
        ws = sheet.add_worksheet(title=today, rows="200", cols="25")
    except Exception:
        ws = sheet.worksheet(today)
        ws.clear()

    ws.append_row(HEADERS)

    rows = []
    for i, c in enumerate(ranked, 1):
        links    = c["links"]
        activity = c["activity"]
        cat      = c["category"]
        scoring  = c["scoring"]
        projects = c.get("projects", [])

        proj_summary = " | ".join(
            f"{p['name']} ({', '.join(p.get('languages', [])[:2])}): {p.get('description','')[:80]}"
            for p in projects
        )

        rows.append([
            i,
            c.get("name", c.get("login", "")),
            f"https://github.com/{c['login']}",
            links.get("linkedin", ""),
            links.get("portfolio", ""),
            links.get("resume", ""),
            scoring["score"],
            cat["primary_domain"],
            ", ".join(activity.get("top_languages", [])),
            scoring["pros"],
            scoring["cons"],
            scoring["breakdown"]["consistency"],
            scoring["breakdown"]["project_quality"],
            scoring["breakdown"]["tech_depth"],
            scoring["breakdown"]["activity"],
            proj_summary[:300],
            ", ".join(activity.get("top_languages", [])[:3]),
            activity.get("stars_total", 0),
            today,
        ])

    ws.append_rows(rows, value_input_option="USER_ENTERED")
    print(f"✓ Wrote {len(rows)} candidates to sheet tab '{today}'")