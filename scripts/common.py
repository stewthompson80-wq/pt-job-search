"""Shared helpers used by both job_search.py and regenerate_page.py."""

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DOCS_DIR = REPO_ROOT / "docs"
SEEN_FILE = DATA_DIR / "seen_jobs.json"
DISMISSED_FILE = DATA_DIR / "dismissed_ids.json"
RESULTS_HTML = DOCS_DIR / "index.html"

DATA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)


def job_id(job: dict) -> str:
    """Stable identifier for a job so we can tell if we've seen/dismissed it."""
    url = (job.get("url") or "").strip().lower()
    if url:
        return "url:" + url
    parts = [(job.get(k) or "").strip().lower() for k in ("title", "company", "city")]
    return "jc:" + "|".join(parts)


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return default
    return default


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2))


def load_seen() -> dict:
    return load_json(SEEN_FILE, {})


def save_seen(seen: dict) -> None:
    save_json(SEEN_FILE, seen)


def load_dismissed() -> list:
    return load_json(DISMISSED_FILE, [])


def save_dismissed(dismissed: list) -> None:
    save_json(DISMISSED_FILE, dismissed)


def escape(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def dismiss_issue_url(repo: str, jid: str) -> str:
    """Build a 'create issue' link that, once submitted, marks a job dismissed.

    repo should be 'owner/name' (GitHub provides this automatically as
    the GITHUB_REPOSITORY environment variable during Actions runs).
    """
    if not repo:
        return ""
    from urllib.parse import quote

    title = quote(f"dismiss: {jid}")
    body = quote(
        "Submitting this issue tells the job search bot you're not interested "
        "in this listing. It will remove it and close this issue automatically."
    )
    return f"https://github.com/{repo}/issues/new?title={title}&body={body}&labels=dismiss"


def run_now_issue_url(repo: str) -> str:
    """Build a 'create issue' link that, once submitted, triggers a fresh search."""
    if not repo:
        return ""
    from urllib.parse import quote

    title = quote("run: now")
    body = quote(
        "Submitting this issue tells the job search bot to run a fresh search "
        "right now, instead of waiting for the next scheduled run."
    )
    return f"https://github.com/{repo}/issues/new?title={title}&body={body}&labels=run-now"


def render_results_page(seen: dict, dismissed: list, repo: str = "") -> None:
    dismissed_set = set(dismissed)
    entries = [e for e in seen.values() if job_id(e["job"]) not in dismissed_set]
    entries.sort(key=lambda e: e.get("first_seen", ""), reverse=True)

    run_now_url = run_now_issue_url(repo)
    run_now_button = (
        f'<a class="run-now-btn" href="{run_now_url}" target="_blank" rel="noopener">Run search now</a>'
        if run_now_url
        else ""
    )

    cards = []
    for entry in entries:
        job = entry["job"]
        jid = job_id(job)
        dismiss_url = dismiss_issue_url(repo, jid)
        cards.append(f"""
        <div class="job">
          <div class="job-top">
            <div>
              <p class="job-title">{escape(job.get('title','Untitled role'))}</p>
              <p class="job-company">{escape(job.get('company',''))}</p>
            </div>
            <span class="tag">{escape(job.get('location_type','') )}</span>
          </div>
          <p class="job-desc">{escape(job.get('description',''))}</p>
          <div class="job-bottom">
            <span class="job-loc">{escape(job.get('city','Location not specified'))} &middot; first seen {escape(entry.get('first_seen','')[:10])}</span>
            <span class="job-links">
              {f'<a class="job-link" href="{escape(job.get("url",""))}" target="_blank" rel="noopener">View posting &rarr;</a>' if job.get('url') else ''}
              {f'<a class="dismiss-link" href="{dismiss_url}" target="_blank" rel="noopener">Not interested</a>' if dismiss_url else ''}
            </span>
          </div>
        </div>""")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>PT Job Search — Results</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{{--ink:#16233A;--paper:#EDEFE7;--brass-dim:#8f6a2e;--rust:#A64B2A;--line:rgba(22,35,58,0.14);--card:#F7F8F3;}}
  body{{margin:0;background:var(--paper);color:var(--ink);font-family:'Public Sans',sans-serif;}}
  .wrap{{max-width:800px;margin:0 auto;padding:40px 20px 60px;}}
  h1{{font-family:'Fraunces',serif;font-size:30px;margin-bottom:4px;}}
  .meta{{font-family:'IBM Plex Mono',monospace;font-size:12px;color:#5c6a7f;margin-bottom:28px;}}
  .job{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin-bottom:12px;}}
  .job-top{{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;}}
  .job-title{{font-family:'Fraunces',serif;font-weight:600;font-size:18px;margin:0;}}
  .job-company{{font-size:13.5px;color:#425066;margin:2px 0 0;}}
  .tag{{font-family:'IBM Plex Mono',monospace;font-size:10.5px;text-transform:uppercase;background:rgba(184,134,59,0.16);color:var(--brass-dim);border-radius:999px;padding:4px 10px;white-space:nowrap;height:fit-content;}}
  .job-desc{{font-size:14px;line-height:1.55;color:#2c3a4f;margin:10px 0 12px;}}
  .job-bottom{{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:#5c6a7f;}}
  .job-links{{display:flex;gap:14px;}}
  a.job-link{{color:var(--brass-dim);text-decoration:none;}}
  a.dismiss-link{{color:var(--rust);text-decoration:none;}}
  .header-row{{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;margin-bottom:4px;}}
  a.run-now-btn{{font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;background:var(--ink);color:var(--paper);text-decoration:none;border-radius:8px;padding:10px 16px;white-space:nowrap;height:fit-content;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header-row">
    <div>
      <h1>Non-clinical PT job search — results</h1>
      <p class="meta">Last updated {datetime.now(timezone.utc).strftime('%B %d, %Y %I:%M %p UTC')} &middot; {len(entries)} listing(s) shown</p>
    </div>
    {run_now_button}
  </div>
  {''.join(cards) if cards else '<p>No listings yet — check back after the next scheduled run.</p>'}
</div>
</body>
</html>"""
    RESULTS_HTML.write_text(html)
