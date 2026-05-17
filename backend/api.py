import asyncio
import sys
import os
import subprocess
import json
import queue
import threading
import sqlite3
import csv
import io
from datetime import datetime, timedelta

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "candidates_cache.json"))
DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "candidates.db"))

def load_candidates():
    if not os.path.exists(CACHE_FILE):
        return []
    try:
        with open(CACHE_FILE) as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
        return data.get("enriched", [])
    except (json.JSONDecodeError, ValueError):
        return []


def _get_logins_for_date_range(start_date: str, end_date: str) -> set:
    """Query SQLite for candidate logins processed between start_date and end_date (inclusive)."""
    if not os.path.exists(DB_FILE):
        return set()
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT login FROM processed_profiles WHERE date(processed_at) BETWEEN ? AND ?",
        (start_date, end_date),
    ).fetchall()
    conn.close()
    return {r[0] for r in rows}


def _get_available_dates() -> list[str]:
    """Return all distinct processing dates from SQLite, most recent first."""
    if not os.path.exists(DB_FILE):
        return []
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT DISTINCT date(processed_at) as d FROM processed_profiles ORDER BY d DESC"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows if r[0]]


def _filter_candidates(candidates, domain=None, min_score=0.0, has_linkedin=False, has_cv=False):
    """Apply standard filters and ranking to a candidate list."""
    if domain:
        candidates = [c for c in candidates if c["category"]["primary_domain"] == domain]
    if min_score:
        candidates = [c for c in candidates if c["scoring"]["score"] >= min_score]
    if has_linkedin:
        candidates = [c for c in candidates if c["links"].get("linkedin")]
    if has_cv:
        candidates = [c for c in candidates if c["links"].get("resume")]
    candidates.sort(key=lambda x: x["scoring"]["score"], reverse=True)
    for i, c in enumerate(candidates, 1):
        c["rank"] = i
    return candidates


@app.get("/candidates")
def get_candidates(
    domain: str = None,
    min_score: float = 0.0,
    has_linkedin: bool = False,
    has_cv: bool = False,
):
    candidates = load_candidates()
    if domain:
        candidates = [c for c in candidates if c["category"]["primary_domain"] == domain]
    if min_score:
        candidates = [c for c in candidates if c["scoring"]["score"] >= min_score]
    if has_linkedin:
        candidates = [c for c in candidates if c["links"].get("linkedin")]
    if has_cv:
        candidates = [c for c in candidates if c["links"].get("resume")]
    candidates.sort(key=lambda x: x["scoring"]["score"], reverse=True)
    for i, c in enumerate(candidates, 1):
        c["rank"] = i
    return candidates


@app.get("/candidates/week/{date}")
def get_candidates_by_week(
    date: str,
    domain: str = None,
    min_score: float = 0.0,
    has_linkedin: bool = False,
    has_cv: bool = False,
):
    import sqlite3
    db = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "candidates.db"))
    if not os.path.exists(db):
        return []
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT login FROM processed_profiles WHERE date(processed_at) = ?", (date,)
    ).fetchall()
    conn.close()

    logins_for_week = {r[0] for r in rows}
    all_candidates  = load_candidates()
    candidates = [c for c in all_candidates if c["login"] in logins_for_week]

    if domain:
        candidates = [c for c in candidates if c["category"]["primary_domain"] == domain]
    if min_score:
        candidates = [c for c in candidates if c["scoring"]["score"] >= min_score]
    if has_linkedin:
        candidates = [c for c in candidates if c["links"].get("linkedin")]
    if has_cv:
        candidates = [c for c in candidates if c["links"].get("resume")]

    candidates.sort(key=lambda x: x["scoring"]["score"], reverse=True)
    for i, c in enumerate(candidates, 1):
        c["rank"] = i
    return candidates


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 1: Date-wise & Week-wise filtering
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/candidates/by-date")
def get_candidates_by_date(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    domain: str = None,
    min_score: float = 0.0,
    has_linkedin: bool = False,
    has_cv: bool = False,
):
    """Get candidates processed on a specific date."""
    logins = _get_logins_for_date_range(date, date)
    all_candidates = load_candidates()
    candidates = [c for c in all_candidates if c["login"] in logins]
    return _filter_candidates(candidates, domain, min_score, has_linkedin, has_cv)


@app.get("/candidates/by-week")
def get_candidates_by_week_range(
    week: str = Query(None, description="ISO week in YYYY-WNN format, e.g. 2026-W18"),
    start_date: str = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str = Query(None, description="End date YYYY-MM-DD"),
    domain: str = None,
    min_score: float = 0.0,
    has_linkedin: bool = False,
    has_cv: bool = False,
):
    """
    Get candidates for a week. Accepts either:
      - week=YYYY-WNN (ISO week, e.g. 2026-W18)
      - start_date + end_date (custom range)
    """
    if week:
        # Parse ISO week string like "2026-W18"
        try:
            # Monday of that ISO week
            monday = datetime.strptime(week + "-1", "%G-W%V-%u")
            sunday = monday + timedelta(days=6)
            sd = monday.strftime("%Y-%m-%d")
            ed = sunday.strftime("%Y-%m-%d")
        except ValueError:
            return JSONResponse(status_code=400, content={"error": f"Invalid week format: {week}. Use YYYY-WNN."})
    elif start_date and end_date:
        sd, ed = start_date, end_date
    else:
        return JSONResponse(status_code=400, content={"error": "Provide 'week' (YYYY-WNN) or 'start_date' + 'end_date'."})

    logins = _get_logins_for_date_range(sd, ed)
    all_candidates = load_candidates()
    candidates = [c for c in all_candidates if c["login"] in logins]
    return _filter_candidates(candidates, domain, min_score, has_linkedin, has_cv)


@app.get("/dates")
def get_dates():
    """Return all available processing dates for the date picker."""
    return _get_available_dates()




@app.get("/candidates/{login}")
def get_candidate(login: str):
    candidates = load_candidates()
    for c in candidates:
        if c["login"] == login:
            return c
    return JSONResponse(status_code=404, content={"error": "Not found"})


@app.get("/stats")
def get_stats():
    candidates = load_candidates()
    if not candidates:
        return {"total": 0, "avg_score": 0, "top_score": 0, "domains": {}}
    domains = {}
    for c in candidates:
        d = c["category"]["primary_domain"]
        domains[d] = domains.get(d, 0) + 1
    scores = [c["scoring"]["score"] for c in candidates]
    return {
        "total":     len(candidates),
        "avg_score": round(sum(scores) / len(scores), 3),
        "top_score": round(max(scores), 3),
        "domains":   domains,
    }


@app.get("/weeks")
def get_weeks():
    import sqlite3
    db = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "candidates.db"))
    if not os.path.exists(db):
        return []
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT DISTINCT date(processed_at) as week FROM processed_profiles ORDER BY week DESC LIMIT 8"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 2: Email Report with date range
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/send-report")
async def send_report(payload: dict):
    """
    Send a candidate report email for a given date range.
    Body: { "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }
    """
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")

    if not start_date or not end_date:
        return JSONResponse(status_code=400, content={"error": "start_date and end_date are required."})

    # Fetch candidates in range
    logins = _get_logins_for_date_range(start_date, end_date)
    all_candidates = load_candidates()
    candidates = [c for c in all_candidates if c["login"] in logins]
    candidates.sort(key=lambda x: x["scoring"]["score"], reverse=True)

    if not candidates:
        return JSONResponse(status_code=404, content={"error": f"No candidates found between {start_date} and {end_date}."})

    # Build CSV attachment
    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow(["Rank", "Name", "GitHub", "LinkedIn", "Portfolio", "Score", "Domain", "Languages", "Date"])
    for i, c in enumerate(candidates, 1):
        links = c.get("links", {}) if isinstance(c.get("links"), dict) else {}
        writer.writerow([
            i,
            c.get("name", c["login"]),
            f"https://github.com/{c['login']}",
            links.get("linkedin", ""),
            links.get("portfolio", ""),
            round(c["scoring"]["score"] * 100, 1),
            c["category"]["primary_domain"].replace("_", " "),
            ", ".join(c["activity"].get("top_languages", [])[:5]),
            start_date if start_date == end_date else f"{start_date} to {end_date}",
        ])
    csv_bytes = csv_buf.getvalue().encode("utf-8")

    # Build HTML email body
    rows_html = ""
    for i, c in enumerate(candidates[:25], 1):  # top 25 in email
        links = c.get("links", {}) if isinstance(c.get("links"), dict) else {}
        score_pct = round(c["scoring"]["score"] * 100)
        score_color = "#1D9E75" if score_pct >= 60 else "#E6A817" if score_pct >= 35 else "#E64D4D"
        rows_html += f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #eee;color:#555;font-weight:600">#{i}</td>
            <td style="padding:10px;border-bottom:1px solid #eee">
                <b>{c.get('name', c['login'])}</b><br>
                <a href="https://github.com/{c['login']}" style="color:#1D9E75;font-size:13px">@{c['login']}</a>
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee">
                <span style="background:#E1F5EE;color:#085041;padding:3px 10px;border-radius:20px;font-size:12px">
                    {c['category']['primary_domain'].replace('_',' ')}
                </span>
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee;font-weight:700;color:{score_color}">{score_pct}</td>
            <td style="padding:10px;border-bottom:1px solid #eee;font-size:12px;color:#666">
                {', '.join(c['activity'].get('top_languages', [])[:3])}
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee;font-size:12px">
                {'<a href="' + links.get('linkedin','') + '" style="color:#0C447C">LinkedIn</a>' if links.get('linkedin') else ''}
                {'&nbsp;<a href="' + links.get('resume','') + '" style="color:#633806">CV</a>' if links.get('resume') else ''}
            </td>
        </tr>"""

    date_label = start_date if start_date == end_date else f"{start_date} → {end_date}"

    html_body = f"""
    <html>
    <body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;background:#f4f4f4;padding:20px">
        <div style="max-width:800px;margin:0 auto;background:#fff;padding:20px;border-radius:8px;border:1px solid #ddd">
            <div style="background-color:#1D9E75;color:white;padding:15px;border-radius:5px 5px 0 0;text-align:center">
                <h1 style="margin:0">Candidate Report</h1>
                <p style="margin:5px 0 0">{date_label} | {len(candidates)} candidates</p>
            </div>
            <div style="padding:20px">
                <table style="width:100%;border-collapse:collapse;margin-top:15px">
                    <thead>
                        <tr style="background:#f8f8f8">
                            <th style="padding:10px;border:1px solid #ddd;text-align:left">#</th>
                            <th style="padding:10px;border:1px solid #ddd;text-align:left">Candidate</th>
                            <th style="padding:10px;border:1px solid #ddd;text-align:left">Domain</th>
                            <th style="padding:10px;border:1px solid #ddd;text-align:left">Score</th>
                            <th style="padding:10px;border:1px solid #ddd;text-align:left">Languages</th>
                            <th style="padding:10px;border:1px solid #ddd;text-align:left">Links</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
                <p style="margin-top:20px;font-size:13px;color:#666">
                    * Full data for all {len(candidates)} candidates is in the attached CSV.
                </p>
            </div>
            <div style="text-align:center;font-size:12px;color:#999;margin-top:20px">
                <p>Generated by GitHub Candidate Discovery Agent</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Send the email
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from notifier import send_email
        import config
        send_email(
            subject=f"Candidate Report — {date_label}",
            html_body=html_body,
            attachments=[(f"candidates_{start_date}_to_{end_date}.csv", csv_bytes)],
            to=config.get_email_receiver(),
        )
        return {"status": "sent", "candidates": len(candidates), "date_range": date_label}
    except Exception as e:
        print(f"[send-report] Email failed: {e}")
        return JSONResponse(status_code=500, content={"error": f"Email failed: {str(e)}"})


@app.post("/send-emails")
async def send_bulk_emails(payload: dict):
    logins  = payload.get("logins", [])
    subject = payload.get("subject", "")
    body    = payload.get("body", "")

    if not logins or not subject or not body:
        return JSONResponse(status_code=400, content={"error": "Missing logins, subject or body"})

    all_candidates = load_candidates()
    candidate_map  = {c["login"]: c for c in all_candidates}

    sent, failed = [], []
    for login in logins:
        c = candidate_map.get(login)
        if not c:
            failed.append(login)
            continue

        name      = c.get("name", login)
        linkedin  = c["links"].get("linkedin", "")
        portfolio = c["links"].get("portfolio", "")

        personalized_body = (
            body
            .replace("{{name}}",   name)
            .replace("{{github}}", f"https://github.com/{login}")
            .replace("{{domain}}", c["category"]["primary_domain"].replace("_", " "))
            .replace("{{score}}",  str(round(c["scoring"]["score"] * 100)))
        )

        html_body = f"""
        <html><body style="font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:24px">
            {personalized_body.replace(chr(10), '<br>')}
            <br><br>
            <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
            <p style="font-size:12px;color:#aaa">
                GitHub: <a href="https://github.com/{login}">github.com/{login}</a>
                {f'&nbsp;|&nbsp; LinkedIn: <a href="{linkedin}">{linkedin}</a>' if linkedin else ''}
                {f'&nbsp;|&nbsp; Portfolio: <a href="{portfolio}">{portfolio}</a>' if portfolio else ''}
            </p>
        </body></html>
        """

        try:
            import sys
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            from notifier import send_email
            import config
            send_email(subject=subject, html_body=html_body, attachments=[], to=config.get_email_receiver())
            sent.append(login)
        except Exception as e:
            failed.append(login)
            print(f"Failed to send to {login}: {e}")

    return {"sent": len(sent), "failed": len(failed), "sent_logins": sent}


@app.websocket("/ws/run-pipeline")
async def run_pipeline(websocket: WebSocket):
    """
    WebSocket endpoint that streams pipeline output to the client.

    Production-safe: handles client disconnections gracefully,
    cleans up the subprocess, and never crashes the server.
    """
    from starlette.websockets import WebSocketState, WebSocketDisconnect

    process = None
    client_connected = True

    # -- Helper: safe send that catches disconnections ----------------------
    async def safe_send(text: str) -> bool:
        """Send text to the client. Returns False if the client is gone."""
        nonlocal client_connected
        if not client_connected:
            return False
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(text)
                return True
            else:
                client_connected = False
                return False
        except (WebSocketDisconnect, RuntimeError, Exception):
            client_connected = False
            return False

    # -- Helper: kill subprocess safely -------------------------------------
    def cleanup_process():
        """Terminate the subprocess tree if it's still running."""
        nonlocal process
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            except Exception:
                pass

    try:
        await websocket.accept()

        if not await safe_send("Starting pipeline...\n"):
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        python_exe   = sys.executable

        if not await safe_send(f"Python: {python_exe}\n"):
            return
        if not await safe_send(f"Root:   {project_root}\n\n"):
            return

        q = queue.Queue()

        process = subprocess.Popen(
            [python_exe, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=project_root,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONPATH": project_root, "PYTHONUNBUFFERED": "1"},
        )

        def read_output():
            try:
                for line in process.stdout:
                    q.put(line)
                process.wait()
                q.put(f"\nExit code: {process.returncode}\n")
            except Exception:
                pass
            finally:
                q.put(None)  # sentinel — always signals end

        thread = threading.Thread(target=read_output, daemon=True)
        thread.start()

        # -- Main loop: drain queue → send to client ------------------------
        while client_connected:
            try:
                line = q.get_nowait()
                if line is None:
                    break
                if not await safe_send(line):
                    break  # client disconnected — stop sending
            except queue.Empty:
                await asyncio.sleep(0.1)

        # -- Finished normally — close gracefully ---------------------------
        if client_connected:
            await safe_send("\n✅ Pipeline finished.")
            try:
                await websocket.close()
            except Exception:
                pass

    except WebSocketDisconnect:
        print("[ws] Client disconnected during pipeline run.")
    except Exception as e:
        print(f"[ws] Unexpected WebSocket error: {e}")
        if client_connected:
            await safe_send(f"\n❌ Server error: {e}")
    finally:
        # Always clean up the subprocess, even on disconnect
        cleanup_process()
        print("[ws] WebSocket handler cleaned up.")


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE: XGBoost ML Training
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/candidates/{login}/label")
def label_candidate(login: str, payload: dict):
    """Label a candidate as 'good' or 'bad' for ML training."""
    label = payload.get("label", "").strip().lower()
    if label not in ("good", "bad"):
        return JSONResponse(status_code=400, content={"error": "label must be 'good' or 'bad'"})
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from feedback import mark_candidate
        mark_candidate(login, label)
        return {"status": "ok", "login": login, "label": label}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/label-counts")
def get_label_counts():
    """Return counts of good/bad labels."""
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from db import get_label_counts as _get_counts
        counts = _get_counts()
        return counts
    except Exception as e:
        return {"good": 0, "bad": 0, "error": str(e)}


@app.get("/model-status")
def get_model_status():
    """Return whether a trained XGBoost model exists."""
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from feedback import has_trained_model
        exists = has_trained_model()
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "candidate_classifier.pkl"))
        return {
            "model_exists": exists,
            "model_path": model_path if exists else None,
        }
    except Exception as e:
        return {"model_exists": False, "error": str(e)}


@app.post("/train")
def train_model():
    """Trigger XGBoost training. Returns accuracy + status."""
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from feedback import train_classifier
        result = train_classifier()
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE: CSV Export
# ═══════════════════════════════════════════════════════════════════════════

from fastapi.responses import StreamingResponse

@app.get("/candidates/export/csv")
def export_candidates_csv(
    domain: str = None,
    min_score: float = 0.0,
    has_linkedin: bool = False,
    has_cv: bool = False,
):
    """Export current filtered candidates as a downloadable CSV file."""
    candidates = load_candidates()
    candidates = _filter_candidates(candidates, domain, min_score, has_linkedin, has_cv)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Rank", "Name", "GitHub", "LinkedIn", "Portfolio", "CV", "Score", "Domain", "Languages", "Followers", "Commits", "Repos"])
    for i, c in enumerate(candidates, 1):
        links = c.get("links", {}) if isinstance(c.get("links"), dict) else {}
        stats = c.get("activity", {})
        writer.writerow([
            i,
            c.get("name", c.get("login", "")),
            f"https://github.com/{c.get('login', '')}",
            links.get("linkedin", ""),
            links.get("portfolio", ""),
            links.get("resume", ""),
            round(c["scoring"]["score"] * 100, 1),
            c["category"]["primary_domain"].replace("_", " "),
            ", ".join(c["activity"].get("top_languages", [])[:5]),
            stats.get("followers", ""),
            stats.get("commit_count", ""),
            stats.get("repo_count", ""),
        ])

    buf.seek(0)
    filename = f"candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE: Enrichment Analysis (lazy, per-candidate, on-demand)
# ═══════════════════════════════════════════════════════════════════════════

ENRICHMENT_CACHE_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "enrichment_cache.json")
)

def _load_enrichment_cache() -> dict:
    if os.path.exists(ENRICHMENT_CACHE_FILE):
        try:
            with open(ENRICHMENT_CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_enrichment_cache(cache: dict):
    try:
        with open(ENRICHMENT_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

def _get_gh_user(login: str):
    """Get PyGithub User object. Uses same token as main pipeline."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, root)
    import config
    from github import Github
    g = Github(config.GITHUB_TOKEN)
    return g.get_user(login)


@app.get("/candidates/{login}/staleness")
def get_staleness(login: str):
    """Return staleness badge for a candidate."""
    cache = _load_enrichment_cache()
    key = f"{login}__staleness"
    if key in cache:
        return cache[key]
    try:
        user = _get_gh_user(login)
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from stages.staleness import analyze_staleness
        result = analyze_staleness(user)
        cache[key] = result
        _save_enrichment_cache(cache)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/candidates/{login}/commit-pattern")
def get_commit_pattern(login: str):
    """Return commit timing archetype and heatmap data."""
    cache = _load_enrichment_cache()
    key = f"{login}__commit_pattern"
    if key in cache:
        return cache[key]
    try:
        user = _get_gh_user(login)
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from stages.commit_pattern import analyze_commit_pattern
        result = analyze_commit_pattern(user)
        cache[key] = result
        _save_enrichment_cache(cache)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/candidates/{login}/code-quality")
def get_code_quality(login: str, refresh: bool = False):
    """Return code quality grade across ALL repos for a candidate."""
    import traceback as _tb
    import importlib

    cache = _load_enrichment_cache()
    key   = f"{login}__code_quality"

    # Invalidate old single-repo cache entries (they lack the 'repo_count' field)
    cached = cache.get(key)
    if cached and not refresh and "repo_count" in cached:
        return cached
    # If cached entry is old format OR refresh requested → re-run

    try:
        root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        if root not in sys.path:
            sys.path.insert(0, root)

        if "stages.code_quality" in sys.modules:
            importlib.reload(sys.modules["stages.code_quality"])

        from stages.code_quality import analyze_code_quality
        user   = _get_gh_user(login)
        result = analyze_code_quality(user)   # no repo arg — analyzes all repos
        cache[key] = result
        _save_enrichment_cache(cache)
        return result
    except Exception as e:
        err = _tb.format_exc()
        print(f"[/code-quality ERROR for {login}]\n{err}")
        return JSONResponse(status_code=500, content={"error": str(e)})



@app.get("/candidates/{login}/live-projects")
def get_live_projects(login: str):
    """Return live/deployed projects for a candidate."""
    cache = _load_enrichment_cache()
    key = f"{login}__live_projects"
    if key in cache:
        return cache[key]
    try:
        user = _get_gh_user(login)
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from stages.live_project import detect_live_projects
        result = detect_live_projects(user)
        cache[key] = result
        _save_enrichment_cache(cache)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/candidates/{login}/enrich")
def enrich_candidate(login: str):
    """Run all enrichment analyses for a single candidate and return combined result."""
    try:
        user = _get_gh_user(login)
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from stages.staleness      import analyze_staleness
        from stages.commit_pattern import analyze_commit_pattern
        from stages.live_project   import detect_live_projects

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            f_staleness = ex.submit(analyze_staleness, user)
            f_pattern   = ex.submit(analyze_commit_pattern, user)
            f_live      = ex.submit(detect_live_projects, user)
            staleness   = f_staleness.result()
            pattern     = f_pattern.result()
            live        = f_live.result()

        # Cache individual results
        cache = _load_enrichment_cache()
        cache[f"{login}__staleness"]      = staleness
        cache[f"{login}__commit_pattern"] = pattern
        cache[f"{login}__live_projects"]  = live
        _save_enrichment_cache(cache)

        return {
            "login":      login,
            "staleness":  staleness,
            "pattern":    pattern,
            "live":       live,
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE: Duplicate Detector
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/duplicates")
def find_duplicates():
    """Find candidates in cache that are likely the same person."""
    import traceback as _tb
    import importlib

    try:
        root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        if root not in sys.path:
            sys.path.insert(0, root)

        # Force fresh import in case the module was cached before sys.path was set
        if "stages.duplicate_detector" in sys.modules:
            importlib.reload(sys.modules["stages.duplicate_detector"])

        from stages.duplicate_detector import detect_duplicates
        clusters = detect_duplicates()
        return {"clusters": clusters, "count": len(clusters)}
    except Exception as e:
        err_detail = _tb.format_exc()
        print(f"[/duplicates ERROR]\n{err_detail}")
        return JSONResponse(status_code=500, content={"error": str(e), "detail": err_detail})


# ═══════════════════════════════════════════════════════════════════════════
# CEO INTELLIGENCE FEATURES
# ═══════════════════════════════════════════════════════════════════════════

def _setup_stages_path():
    """Ensure stages/ is importable from the backend context."""
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)


@app.get("/candidates/{login}/red-flags")
def get_red_flags(login: str):
    """Detect warning signs in a candidate's profile."""
    import traceback as _tb
    cache = _load_enrichment_cache()
    key   = f"{login}__red_flags"
    if key in cache:
        return cache[key]
    try:
        _setup_stages_path()
        from stages.red_flags import detect_red_flags
        candidates  = load_candidates()
        candidate   = next((c for c in candidates if c["login"] == login), None)
        if not candidate:
            return JSONResponse(status_code=404, content={"error": "Candidate not found"})
        enrichment  = cache.get(f"{login}__code_quality")
        result      = detect_red_flags(candidate, enrichment)
        cache[key]  = result
        _save_enrichment_cache(cache)
        return result
    except Exception as e:
        print(f"[/red-flags ERROR]\n{_tb.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/candidates/{login}/collaboration")
def get_collaboration(login: str):
    """Return collaboration & community presence score."""
    import traceback as _tb
    cache = _load_enrichment_cache()
    key   = f"{login}__collaboration"
    if key in cache:
        return cache[key]
    try:
        _setup_stages_path()
        from stages.collaboration import analyze_collaboration
        user   = _get_gh_user(login)
        result = analyze_collaboration(user)
        cache[key] = result
        _save_enrichment_cache(cache)
        return result
    except Exception as e:
        print(f"[/collaboration ERROR]\n{_tb.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/candidates/{login}/growth")
def get_growth(login: str):
    """Return growth trajectory analysis."""
    import traceback as _tb
    cache = _load_enrichment_cache()
    key   = f"{login}__growth"
    if key in cache:
        return cache[key]
    try:
        _setup_stages_path()
        from stages.growth import analyze_growth
        user   = _get_gh_user(login)
        result = analyze_growth(user)
        cache[key] = result
        _save_enrichment_cache(cache)
        return result
    except Exception as e:
        print(f"[/growth ERROR]\n{_tb.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/candidates/{login}/full-profile")
def get_full_profile(login: str):
    """Run all CEO intelligence analyses in parallel for one candidate."""
    import traceback as _tb
    import concurrent.futures as cf
    try:
        _setup_stages_path()
        from stages.red_flags    import detect_red_flags
        from stages.collaboration import analyze_collaboration
        from stages.growth        import analyze_growth

        candidates = load_candidates()
        candidate  = next((c for c in candidates if c["login"] == login), None)
        if not candidate:
            return JSONResponse(status_code=404, content={"error": "Candidate not found"})

        cache      = _load_enrichment_cache()
        enrichment = cache.get(f"{login}__code_quality")

        # Red flags use only cached data — instant
        red_flags = detect_red_flags(candidate, enrichment)

        # Collaboration + growth need GitHub API — run in parallel
        user = _get_gh_user(login)
        with cf.ThreadPoolExecutor(max_workers=2) as ex:
            f_collab = ex.submit(analyze_collaboration, user)
            f_growth = ex.submit(analyze_growth, user)
            collab   = f_collab.result()
            growth   = f_growth.result()

        cache[f"{login}__red_flags"]    = red_flags
        cache[f"{login}__collaboration"]= collab
        cache[f"{login}__growth"]       = growth
        _save_enrichment_cache(cache)

        return {
            "login":       login,
            "red_flags":   red_flags,
            "collaboration": collab,
            "growth":      growth,
        }
    except Exception as e:
        print(f"[/full-profile ERROR]\n{_tb.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Role-Fit Score (POST — CEO sends role criteria) ─────────────────────────

class RoleProfile(BaseModel):
    title:            str
    required:         list[str] = []
    nice_to_have:     list[str] = []
    min_commits:      int  = 0
    min_stars:        int  = 0
    needs_tests:      bool = False
    domain:           str | None = None
    needs_live_project: bool = False
    weights:          dict[str, float] | None = None


@app.post("/role-fit")
def compute_role_fit(role: RoleProfile):
    """
    Score ALL candidates against a CEO-defined job role.
    Returns candidates sorted by match %, with breakdown per candidate.
    """
    import traceback as _tb
    try:
        _setup_stages_path()
        from stages.role_fit import score_all_candidates
        candidates       = load_candidates()
        cache            = _load_enrichment_cache()
        role_dict        = role.dict()
        scored           = score_all_candidates(candidates, role_dict, cache)
        return {
            "role":       role_dict,
            "count":      len(scored),
            "candidates": scored,
        }
    except Exception as e:
        print(f"[/role-fit ERROR]\n{_tb.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})

