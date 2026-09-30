#!/usr/bin/env python3
"""Submit Saving Optimizer URLs to IndexNow (Bing, Yandex, Seznam, Naver and others).

Run this AFTER a deploy, once the new pages are live on savingoptimizer.com.

Examples:
  python3 scripts/indexnow-ping.py --since 2026-09-30   # URLs whose sitemap lastmod is on/after that date
  python3 scripts/indexnow-ping.py --changed HEAD~1      # URLs for HTML files changed since a git ref
  python3 scripts/indexnow-ping.py --all                 # every URL in sitemap.xml
  python3 scripts/indexnow-ping.py --url https://savingoptimizer.com/guides/index.html
  add --dry-run to print the URLs without sending anything

The key file (<key>.txt) lives in the site root and must be reachable at
https://savingoptimizer.com/<key>.txt before IndexNow will accept a submission.
The script checks that first.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "savingoptimizer.com"
BASE = f"https://{HOST}/"
ENDPOINT = "https://api.indexnow.org/indexnow"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
BATCH = 10000  # IndexNow maximum URLs per request


def find_key() -> str:
    keys = [p.stem for p in ROOT.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", p.stem)
            and p.read_text(encoding="utf-8").strip() == p.stem]
    if len(keys) != 1:
        sys.exit(f"Expected exactly one IndexNow key file in {ROOT}, found {len(keys)}.")
    return keys[0]


def sitemap_entries() -> list[tuple[str, str]]:
    tree = ET.parse(ROOT / "sitemap.xml")
    out = []
    for url in tree.getroot().iter(f"{NS}url"):
        loc = (url.findtext(f"{NS}loc") or "").strip()
        lastmod = (url.findtext(f"{NS}lastmod") or "").strip()
        if loc:
            out.append((loc, lastmod))
    return out


def urls_changed_since(ref: str) -> list[str]:
    names = subprocess.run(["git", "diff", "--name-only", ref, "--", "*.html"], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.split()
    known = {loc for loc, _ in sitemap_entries()}
    urls = []
    for name in names:
        if not (ROOT / name).exists():
            continue
        url = BASE if name == "index.html" else BASE + name
        if url in known:
            urls.append(url)
    return urls


def key_is_live(key: str) -> bool:
    try:
        with urllib.request.urlopen(f"{BASE}{key}.txt", timeout=20) as resp:
            return resp.read().decode("utf-8").strip() == key
    except (urllib.error.URLError, TimeoutError):
        return False


def submit(key: str, urls: list[str]) -> None:
    for i in range(0, len(urls), BATCH):
        chunk = urls[i:i + BATCH]
        body = json.dumps({"host": HOST, "key": key, "keyLocation": f"{BASE}{key}.txt",
                           "urlList": chunk}).encode("utf-8")
        req = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                print(f"Submitted {len(chunk)} URL(s): HTTP {resp.status}")
        except urllib.error.HTTPError as exc:
            # 200/202 = accepted, 400 bad request, 403 key not valid, 422 URLs not on host, 429 too many requests
            sys.exit(f"IndexNow rejected the batch: HTTP {exc.code} {exc.read().decode('utf-8', 'replace')[:300]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true", help="submit every URL in sitemap.xml")
    g.add_argument("--since", metavar="YYYY-MM-DD", help="submit URLs whose lastmod is on or after this date")
    g.add_argument("--changed", metavar="GIT_REF", help="submit URLs for HTML files changed since GIT_REF")
    g.add_argument("--url", action="append", help="submit one URL (repeatable)")
    ap.add_argument("--dry-run", action="store_true", help="print URLs, do not submit")
    args = ap.parse_args()

    key = find_key()
    if args.all:
        urls = [loc for loc, _ in sitemap_entries()]
    elif args.since:
        urls = [loc for loc, lastmod in sitemap_entries() if lastmod[:10] >= args.since]
    elif args.changed:
        urls = urls_changed_since(args.changed)
    else:
        urls = args.url
    urls = [u for u in dict.fromkeys(urls) if u.startswith(BASE)]
    if not urls:
        print("No URLs to submit.")
        return 0
    print(f"{len(urls)} URL(s) selected.")
    if args.dry_run:
        print("\n".join(urls))
        return 0
    if not key_is_live(key):
        sys.exit(f"Key file {BASE}{key}.txt is not live yet. Deploy first, then run this again.")
    submit(key, urls)
    return 0


if __name__ == "__main__":
    sys.exit(main())
