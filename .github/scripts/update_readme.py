"""Refresh the 'Recently active' section and the 'last updated' stamp in README.md.

Runs daily from .github/workflows/daily-readme.yml. Uses only the standard library.
"""
import datetime
import json
import os
import re
import urllib.request

USER = "emieljames"
README = "README.md"
SKIP = {USER}  # don't list the profile repo itself
MAX_REPOS = 5


def fetch_repos():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=30",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "readme-updater"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def replace_block(text, name, content):
    pattern = re.compile(rf"(<!-- {name}:START -->).*?(<!-- {name}:END -->)", re.S)
    return pattern.sub(lambda m: m.group(1) + content + m.group(2), text)


def main():
    repos = [r for r in fetch_repos() if r["name"] not in SKIP][:MAX_REPOS]
    lines = []
    for r in repos:
        pushed = r["pushed_at"][:10]
        lang = f" · `{r['language']}`" if r.get("language") else ""
        desc = f": {r['description']}" if r.get("description") else ""
        lines.append(f"- [{r['name']}]({r['html_url']}){desc}{lang} · last push {pushed}")
    recent = "\n" + "\n".join(lines) + "\n"

    # Philippine time, since the profile is based in Laguna.
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%B %d, %Y")
    updated = f"Last refreshed {today} by a daily GitHub Action"

    with open(README, encoding="utf-8") as f:
        text = f.read()
    text = replace_block(text, "RECENT", recent)
    text = replace_block(text, "UPDATED", updated)
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


if __name__ == "__main__":
    main()
