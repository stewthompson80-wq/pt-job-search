"""
PT non-clinical job search — runs on a schedule via GitHub Actions.

What this does each run:
1. Calls the Anthropic API (with web search) to find current non-clinical
   PT job postings matching the profile below.
2. Compares results against data/seen_jobs.json to figure out what's NEW
   since the last run (and skips anything already marked "not interested"
   in data/dismissed_ids.json).
3. Emails you the new listings (if any).
4. Rewrites docs/index.html with the full running list, most recent first,
   each with a "Not interested" link that permanently removes it.

Edit the PROFILE and SEARCH_INSTRUCTIONS strings below any time your
situation or preferences change.
"""

import json
import os
import re
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

import common

# ---------------------------------------------------------------------------
# Configuration (from GitHub Secrets — set these in repo Settings > Secrets)
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
EMAIL_USERNAME = os.environ.get("EMAIL_USERNAME")   # the Gmail address sending mail
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")   # Gmail App Password (not your normal password)
EMAIL_TO = os.environ.get("EMAIL_TO")               # where you want listings sent
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "")  # set automatically by GitHub Actions, "owner/repo"

# ---------------------------------------------------------------------------
# Candidate profile — edit freely
# ---------------------------------------------------------------------------
PROFILE = """Candidate profile:
- Doctor of Physical Therapy (DPT), 15 years of clinical experience
- Board Certified Clinical Specialist in Geriatric Physical Therapy
- Located in the Shreveport, Louisiana area
- Actively looking to leave direct patient care for a NON-CLINICAL role
- Acceptable work arrangements, in order of flexibility: fully remote; remote with field/travel component; remote combined with field and some office days. Any in-person field or office component MUST be based in northwest Louisiana (Shreveport-Bossier City region and surrounding parishes). Do not include roles requiring in-person work outside northwest Louisiana.
- Relevant non-clinical directions for a background like this: utilization review, case management, clinical documentation/quality review, medical/legal record review, disability or workers' comp evaluation coordination, clinical liaison or account management for medical device/DME/home health/hospice companies, clinical education/training, healthcare informatics or EMR analyst, insurance/payer clinical consultant, telehealth clinical operations, geriatric care management, healthcare compliance or accreditation review. This list is illustrative, not exhaustive."""

SEARCH_INSTRUCTIONS = """Search the web right now for CURRENT, ACTUALLY OPEN non-clinical job postings matching this profile. Check general boards (Indeed, LinkedIn, ZipRecruiter, Glassdoor) and relevant employer/health-system career pages. Prioritize postings that are remote, or remote/hybrid with any field or office component located in the Shreveport-Bossier City, Louisiana area or nearby northwest Louisiana parishes.

Return 6-12 of the best matches as STRICT JSON ONLY -- no markdown fences, no commentary before or after -- as an array of objects with exactly these fields:
title, company, location_type (one of: "Remote", "Remote + Field", "Remote + Field + Office"), city (city/parish, or "Remote" if fully remote), description (1-2 plain sentences on why it fits), url (direct link to the posting), date_posted (best guess, or empty string if unknown).

If you cannot verify a real current posting, do not invent one -- return fewer results rather than fabricating."""


def call_claude() -> list:
    prompt = f"{PROFILE}\n\n{SEARCH_INSTRUCTIONS}"
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 3000,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        },
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()
    text = "\n".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    ).strip()

    cleaned = re.sub(r"^```json\s*|^```\s*|```\s*$", "", text.strip())
    start, end = cleaned.find("["), cleaned.rfind("]")
    if start != -1 and end != -1:
        cleaned = cleaned[start : end + 1]

    try:
        jobs = json.loads(cleaned)
    except Exception as e:
        print("Could not parse model output as JSON:")
        print(text)
        raise e

    return jobs if isinstance(jobs, list) else []


def send_email(subject: str, html_body: str) -> None:
    if not (EMAIL_USERNAME and EMAIL_PASSWORD and EMAIL_TO):
        print("Email secrets not configured -- skipping send. (Set EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO)")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USERNAME
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, [EMAIL_TO], msg.as_string())
    print(f"Email sent to {EMAIL_TO}")


def build_email_html(new_jobs: list, timestamp: str) -> str:
    rows = []
    for job in new_jobs:
        rows.append(f"""
        <tr>
          <td style="padding:14px 0;border-bottom:1px solid #e2e5da;">
            <div style="font-family:Georgia,serif;font-size:17px;font-weight:600;color:#16233A;">{common.escape(job.get('title',''))}</div>
            <div style="font-size:13px;color:#425066;margin:2px 0 6px;">{common.escape(job.get('company',''))} &middot; {common.escape(job.get('city','') or 'Location not specified')}</div>
            <div style="font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:#8f6a2e;margin-bottom:6px;">{common.escape(job.get('location_type',''))}</div>
            <div style="font-size:14px;color:#2c3a4f;line-height:1.5;margin-bottom:6px;">{common.escape(job.get('description',''))}</div>
            {f'<a href="{common.escape(job.get("url",""))}" style="font-size:13px;color:#8f6a2e;">View posting &rarr;</a>' if job.get('url') else ''}
          </td>
        </tr>""")
    rows_html = "\n".join(rows) if rows else "<tr><td>No new listings.</td></tr>"
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="font-family:Georgia,serif;color:#16233A;">New non-clinical PT listings</h2>
      <p style="color:#425066;font-size:13px;">Run at {timestamp}</p>
      <table width="100%" cellpadding="0" cellspacing="0">{rows_html}</table>
    </div>"""


def main():
    seen = common.load_seen()
    dismissed = common.load_dismissed()
    dismissed_set = set(dismissed)

    jobs = call_claude()
    now = datetime.now(timezone.utc).isoformat()

    new_jobs = []
    for job in jobs:
        jid = common.job_id(job)
        if jid in dismissed_set:
            continue  # already told the bot "not interested" -- never resurface it
        if jid not in seen:
            seen[jid] = {"job": job, "first_seen": now}
            new_jobs.append(job)

    common.save_seen(seen)

    timestamp = datetime.now(timezone.utc).strftime("%B %d, %Y %I:%M %p UTC")
    if new_jobs:
        print(f"{len(new_jobs)} new listing(s) found.")
        send_email(
            subject=f"{len(new_jobs)} new PT non-clinical listing(s) — {timestamp}",
            html_body=build_email_html(new_jobs, timestamp),
        )
    else:
        print("No new listings this run.")

    common.render_results_page(seen, dismissed, repo=GITHUB_REPO)


if __name__ == "__main__":
    main()
