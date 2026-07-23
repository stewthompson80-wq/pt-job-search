# PT Non-Clinical Job Search — Automated

This runs your job search on GitHub's servers once a day at 7:00 AM
Central — no computer of yours needs to stay on. When it finds new
listings, it emails them to you and updates a webpage you can check
anytime.

Follow the steps below in order. None of it requires coding — just some
copy/paste and clicking. Budget about 20-30 minutes the first time.

---

## Step 1 — Create a GitHub account (free)

1. Go to https://github.com/join
2. Sign up with your email, pick a username, verify your email.

## Step 2 — Create a new repository from these files

1. Once logged in, click the **+** in the top right → **New repository**.
2. Name it something like `pt-job-search`. Choose **Private** if you'd
   rather nobody else stumble across it (see the note about GitHub Pages
   in Step 6 — private repos can't use the free public webpage feature).
3. Click **Create repository**.
4. On the new repo's page, click **uploading an existing file** (or
   "Add file" → "Upload files").
5. Drag in **all the files and folders** from the package I gave you,
   preserving the folder structure (`.github/workflows/job-search.yml`,
   `scripts/job_search.py`, `data/seen_jobs.json`, `docs/index.html`,
   `README.md`). GitHub's uploader supports dragging whole folders in
   most browsers — if it flattens them, you can instead install
   [GitHub Desktop](https://desktop.github.com/) and drag the folder in,
   which is more forgiving.
6. Commit the files (there's a "Commit changes" button at the bottom).

## Step 3 — Get an Anthropic API key

1. Go to https://console.anthropic.com and sign up or log in.
2. Add a payment method under **Settings → Billing** (this is a
   pay-as-you-go API, separate from any Claude.ai subscription). Usage
   here is small — each run costs roughly $0.05-$0.15, and at once a day
   that's well under $5/month, likely closer to $2-3. I'd still recommend
   setting a monthly budget/spend limit under Billing so you can't be
   surprised.
3. Go to **API Keys** in the left sidebar → **Create Key**. Name it
   anything (e.g. "job-search"). Copy the key immediately — you won't be
   able to view it again after leaving the page.

## Step 4 — Set up an email address to send from

The simplest reliable option is a Gmail account with an **App Password**
(this is different from your normal Gmail password, and doesn't require
giving anyone your real password).

1. If you don't already use Gmail, you can either use an existing Gmail
   account or create a free one for this purpose.
2. Turn on 2-Step Verification: https://myaccount.google.com/security
3. Go to https://myaccount.google.com/apppasswords, sign in, and create
   an app password (choose "Mail" as the app). Copy the 16-character
   password it gives you.

## Step 5 — Add your secrets to the GitHub repo

These keep your API key and email password out of the code itself.

1. In your repo, go to **Settings → Secrets and variables → Actions**.
2. Click **New repository secret** and add each of these one at a time:

   | Secret name | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | the key from Step 3 |
   | `EMAIL_USERNAME` | the Gmail address sending the emails |
   | `EMAIL_PASSWORD` | the 16-character app password from Step 4 |
   | `EMAIL_TO` | the email address you want listings sent **to** — see note below |

   **On `EMAIL_TO`:** this can be *any* email address — your personal
   Gmail, a work address, whatever you actually check. It doesn't need to
   be the same as `EMAIL_USERNAME` (the Gmail account doing the sending),
   and the recipient side needs zero setup — no account, no app password,
   nothing. It's just the address the email gets delivered to, same as
   typing it in the "To:" field of any email.

## Step 6 — (Optional) Turn on the results webpage

1. In the repo, go to **Settings → Pages**.
2. Under "Build and deployment," set **Source** to "Deploy from a
   branch," branch `main`, folder `/docs`. Save.
3. GitHub will give you a URL like
   `https://yourusername.github.io/pt-job-search/` — that's your results
   page, and it updates every run.
4. Note: this free option only works if the repo is **Public**. If you
   made it Private in Step 2, you can skip this and rely on email only,
   or make the repo public later (Settings → General → Change visibility)
   — the content is just generic job listings, nothing personally
   identifying about you is published to it.

## Running a search on demand

At the top of the results webpage there's a **Run search now** button. It
works the same way as "Not interested": it opens a pre-filled GitHub
issue, you click **Submit new issue**, and a workflow runs the search
immediately, updates the page and email, and closes the issue.

This only works if you're logged into GitHub as the repo owner when you
click it — that's a deliberate restriction so a random visitor to your
public results page can't trigger runs (and rack up API charges) on your
account. If someone else tries, their issue gets closed automatically
with an explanation, nothing runs.

## Step 7 — Marking a job as "not interested"

Every listing on the results webpage (Step 6) has a **Not interested**
link. Clicking it:

1. Opens a pre-filled GitHub issue in a new tab (title already filled in
   — you don't type anything).
2. You click the green **Submit new issue** button.
3. Within a few seconds, a small automated workflow reads that issue,
   permanently removes the listing from the page and from future
   emails, and closes the issue for you. You don't need to look at the
   issue again.

This works out of the box as long as Issues are enabled on your repo
(they are by default for new repos — check **Settings → General →
Features** if you don't see the "Issues" tab). It also requires the
`.github/workflows/handle-dismiss.yml` file from this package to be
uploaded along with everything else in Step 2.

## Step 8 — Test it manually

Don't wait until tomorrow's 7 AM run to see if it works:

1. Go to the **Actions** tab in your repo.
2. Click **PT Job Search** in the left list.
3. Click **Run workflow** (dropdown on the right) → **Run workflow**.
4. Wait 1-2 minutes, refresh — you should see a green checkmark. Click
   into the run to see the logs if anything failed.
5. Check your email, and/or your GitHub Pages URL if you set it up.
6. Try clicking a "Not interested" link on the page to confirm the
   dismiss workflow runs too (Actions tab → "Handle dismiss requests").

From here it runs automatically once a day, forever, with nothing
required from you.

---

## Customizing later

- To change your profile, search focus, or how many results come back,
  edit `scripts/job_search.py` — the `PROFILE` and `SEARCH_INSTRUCTIONS`
  text near the top. Edit directly on GitHub (click the file, pencil
  icon) and commit — no local setup needed.
- The search runs once a day at 7:00 AM Central (12:00 UTC, adjusted for
  daylight saving — see the comment in the workflow file for the winter
  caveat). To change the time, edit the `cron:` line in
  `.github/workflows/job-search.yml`.
- If you ever want to pause it, go to the **Actions** tab → **PT Job
  Search** → the "..." menu → **Disable workflow**.
