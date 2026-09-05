#!/usr/bin/env python3
"""
Best-effort check: is there anything on your PyPI profile that isn't in
libraries.txt yet?

This is informational only — it never writes any files. Run it, read the
output, and if it finds something new, add it to libraries.txt yourself and
run sync_deps.py.

Why it's not fully automatic: https://pypi.org/user/<name>/ is served behind
Fastly's bot-challenge page for non-browser requests (curl, urllib, requests
all get an HTML/JS challenge page back, not the profile). That makes it
unsafe to scrape unattended in a script or CI job — you'd either get nothing
useful or, worse, an empty result that looks like "no packages" if the
parsing logic isn't defensive about it. This script fetches it anyway on a
best-effort basis and clearly says so when the check page is what came back,
rather than guessing.

A more reliable long-term option, if you want this fully automated: run it
from something that executes real JS (e.g. a headless-browser step in a
GitHub Action with Playwright), or maintain libraries.txt by hand — which,
realistically, is one line per new library, so it's not much of a burden.
"""

from __future__ import annotations

import pathlib
import re
import sys
import urllib.request

USERNAME = "sam3360"
PROFILE_URL = f"https://pypi.org/user/{USERNAME}/"
SELF_PACKAGE = "samall"

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIBRARIES_TXT = ROOT / "libraries.txt"

PROJECT_LINK_RE = re.compile(r'href="/project/([A-Za-z0-9][A-Za-z0-9._-]*)/"')


def read_current() -> set[str]:
    names = set()
    for line in LIBRARIES_TXT.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.add(line.lower())
    return names


def main() -> int:
    print(f"Checking {PROFILE_URL} for packages not in libraries.txt ...\n")
    req = urllib.request.Request(
        PROFILE_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; samall-checker/1.0; "
                "+https://pypi.org/project/samall/)"
            )
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"Could not reach PyPI: {exc}", file=sys.stderr)
        print("Nothing to report — check libraries.txt manually instead.")
        return 1

    if "Client Challenge" in html or "<title>Just a moment" in html:
        print(
            "PyPI returned a bot-challenge page instead of your profile "
            "(this happens for non-browser requests). Can't auto-detect "
            "right now — open the profile in an actual browser instead:\n"
            f"  {PROFILE_URL}"
        )
        return 2

    found = []
    seen = set()
    for match in PROJECT_LINK_RE.finditer(html):
        name = match.group(1)
        key = name.lower()
        if key == SELF_PACKAGE or key in seen:
            continue
        seen.add(key)
        found.append(name)

    if not found:
        print(
            "No project links found in the response. The page layout may "
            "have changed, or this was a partial/blocked response. Check "
            f"manually: {PROFILE_URL}"
        )
        return 2

    current = read_current()
    new = [n for n in found if n.lower() not in current]

    if not new:
        print(f"Up to date — all {len(found)} projects on your profile are already in libraries.txt.")
        return 0

    print("New packages on your profile not yet in libraries.txt:")
    for n in new:
        print(f"  + {n}")
    print("\nAdd them to libraries.txt, then run: python scripts/sync_deps.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
