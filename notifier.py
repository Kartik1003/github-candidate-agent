import smtplib, config, csv, io, json, os
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email                import encoders

CACHE_FILE = os.path.join(os.path.dirname(__file__), "candidates_cache.json")

def build_csv_attachment(top_candidates: list) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank","Name","GitHub","LinkedIn","Portfolio","Resume",
        "Score","Domain","Skills","Pros","Cons",
        "Consistency","Project Quality","Tech Depth","Activity"
    ])
    for i, c in enumerate(top_candidates, 1):
        bd = c["scoring"].get("breakdown", {})
        links = get_links(c)
        writer.writerow([
            i,
            c.get("name", c["login"]),
            f"https://github.com/{c['login']}",
            links.get("linkedin", ""),
            links.get("portfolio", ""),
            links.get("resume", ""),
            round(c["scoring"]["score"] * 100, 1),
            c["category"]["primary_domain"].replace("_", " "),
            ", ".join(c["activity"].get("top_languages", [])[:5]),
            c["scoring"]["pros"],
            c["scoring"]["cons"],
            round(bd.get("consistency", 0) * 100, 1),
            round(bd.get("project_quality", 0) * 100, 1),
            round(bd.get("tech_depth", 0) * 100, 1),
            round(bd.get("activity", 0) * 100, 1),
        ])
    return output.getvalue().encode("utf-8")


def send_email(subject: str, html_body: str, attachments: list = None, to: str = None):
    if not config.get_email_sender() or not config.get_email_password():
        print("Email not configured — skipping.")
        return

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = config.get_email_sender()
    msg["To"] = to or config.get_email_receiver()

    msg.attach(MIMEText(html_body, "html"))

    for filename, data in (attachments or []):
        part = MIMEBase("application", "octet-stream")
        part.set_payload(data)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config.get_email_sender(), config.get_email_password())
            server.sendmail(config.get_email_sender(), to or config.get_email_receiver(), msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Email failed: {e}")


def get_links(c):
    links = c.get('links', {})
    if isinstance(links, dict):
        return links
    return {}

def notify_run_complete(new: int, skipped: int, total: int, top_candidates: list):
    import datetime
    week = datetime.date.today().strftime("Week %W, %Y")

    top_rows = "".join(
        f"""<tr>
            <td style="padding:10px;border-bottom:1px solid #eee;font-weight:600;color:#555">#{i+1}</td>
            <td style="padding:10px;border-bottom:1px solid #eee">
                <b>{c.get('name', c['login'])}</b><br>
                <a href="https://github.com/{c['login']}" style="color:#1D9E75;font-size:13px">@{c['login']}</a>
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee">
                <span style="background:#E1F5EE;color:#085041;padding:3px 10px;border-radius:20px;font-size:12px">
                    {c['category']['primary_domain'].replace('_',' ')}
                </span>
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee;font-weight:600;color:#1D9E75">
                {round(c['scoring']['score'] * 100)}
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee;font-size:12px;color:#666">
                {', '.join(c['activity'].get('top_languages', [])[:3])}
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee">
                {'<a href="' + get_links(c).get('linkedin','') + '" style="color:#0C447C;font-size:12px">LinkedIn</a>' if get_links(c).get('linkedin') else ''}
                {'&nbsp;<a href="' + get_links(c).get('resume','') + '" style="color:#633806;font-size:12px">CV</a>' if get_links(c).get('resume') else ''}
            </td>
        </tr>"""
        for i, c in enumerate(top_candidates)
    )

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 800px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
            <div style="background-color: #1D9E75; color: white; padding: 15px; border-radius: 5px 5px 0 0; text-align: center;">
                <h1 style="margin: 0;">Discovery Agent: {week}</h1>
                <p style="margin: 5px 0 0;">Processed {total} candidates | {new} new matches found</p>
            </div>
            <div style="padding: 20px;">
                <h2 style="color: #1D9E75; border-bottom: 2px solid #1D9E75; padding-bottom: 5px;">Top Matches This Week</h2>
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="background-color: #f8f8f8;">
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">#</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Candidate</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Domain</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Score</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Languages</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Links</th>
                        </tr>
                    </thead>
                    <tbody>
                        {top_rows}
                    </tbody>
                </table>
                <div style="margin-top: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; font-size: 13px;">
                    <p style="margin: 0;"><strong>Run Statistics:</strong></p>
                    <ul style="margin: 5px 0;">
                        <li>Total Candidates Processed: {total}</li>
                        <li>New Candidates Discovered: {new}</li>
                        <li>Candidates Skipped (already in DB): {skipped}</li>
                    </ul>
                    <p style="margin: 10px 0 0; color: #666;">
                        * The attached CSV file contains the detailed breakdown for all top candidates.
                    </p>
                </div>
            </div>
            <div style="text-align: center; font-size: 12px; color: #999; margin-top: 20px;">
                <p>Generated by GitHub Candidate Discovery Agent</p>
            </div>
        </div>
    </body>
    </html>
    """

    csv_data = build_csv_attachment(top_candidates)
    
    send_email(
        subject=f"GitHub Candidate Report - {week}",
        html_body=html_body,
        attachments=[(f"candidates_{datetime.date.today().isoformat()}.csv", csv_data)]
    )