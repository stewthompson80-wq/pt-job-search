"""
Regenerates docs/index.html from the current data files.

Used by the "Handle dismiss requests" workflow after someone clicks
"Not interested" on the results page -- no Anthropic API call needed,
just re-renders the page with the newly dismissed job filtered out.
"""

import os

import common


def main():
    seen = common.load_seen()
    dismissed = common.load_dismissed()
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    common.render_results_page(seen, dismissed, repo=repo)


if __name__ == "__main__":
    main()
