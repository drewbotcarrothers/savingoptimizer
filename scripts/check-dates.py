#!/usr/bin/env python3
"""Fail if a sitemap lastmod or article publish/update date is after today.

Checks:
- every <lastmod> in sitemap.xml
- article JSON-LD datePublished / dateModified
- article:published_time / article:modified_time meta tags
- the visible date in each article's article-meta line

Dates equal to today are allowed. Program deadlines and source citations in
body copy are not article dates and are ignored.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
ARTICLES = ROOT / "guides" / "articles"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

META_RE = re.compile(r'<p class="article-meta">(.*?)</p>', re.DOTALL)
VIS_RE = re.compile(
    r"(\d{1,2})\s+("
    + "|".join(sorted(MONTHS, key=len, reverse=True))
    + r")\s+(20\d{2})"
)
ISO_FIELDS = (
    (
        "article:published_time",
        re.compile(r'<meta name="article:published_time" content="(\d{4}-\d{2}-\d{2})"'),
    ),
    (
        "article:modified_time",
        re.compile(r'<meta name="article:modified_time" content="(\d{4}-\d{2}-\d{2})"'),
    ),
    (
        "datePublished",
        re.compile(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"'),
    ),
    (
        "dateModified",
        re.compile(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"'),
    ),
)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_iso(value: str) -> date:
    return date.fromisoformat(value[:10])


def check_sitemap(today: date, problems: list[str]) -> int:
    try:
        tree = ET.parse(SITEMAP)
    except ET.ParseError as exc:
        problems.append(f"sitemap.xml: invalid XML ({exc})")
        return 0

    count = 0
    for url in tree.getroot():
        if local(url.tag) != "url":
            continue
        loc = ""
        lastmod = ""
        for child in url:
            name = local(child.tag)
            if name == "loc":
                loc = (child.text or "").strip()
            elif name == "lastmod":
                lastmod = (child.text or "").strip()
        if not lastmod:
            continue
        count += 1
        try:
            parsed = parse_iso(lastmod)
        except ValueError:
            problems.append(f"sitemap.xml: unparseable lastmod {lastmod!r} for {loc}")
            continue
        if parsed > today:
            problems.append(f"sitemap.xml: {loc} lastmod {lastmod} is after {today.isoformat()}")
    if count == 0:
        problems.append("sitemap.xml: no lastmod values found")
    return count


def check_articles(today: date, problems: list[str]) -> int:
    count = 0
    pages = sorted(ARTICLES.glob("*.html"))
    if not pages:
        problems.append(f"no article HTML files under {ARTICLES}")
        return 0

    for path in pages:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        for label, pattern in ISO_FIELDS:
            found = pattern.findall(text)
            if not found:
                problems.append(f"{rel}: missing {label}")
                continue
            for raw in found:
                count += 1
                try:
                    parsed = parse_iso(raw)
                except ValueError:
                    problems.append(f"{rel}: unparseable {label} {raw!r}")
                    continue
                if parsed > today:
                    problems.append(f"{rel}: {label} {raw} is after {today.isoformat()}")

        meta = META_RE.search(text)
        if not meta:
            problems.append(f"{rel}: missing article-meta date line")
            continue
        visible = VIS_RE.findall(meta.group(1))
        if not visible:
            # Some pages say "Reviewed 2026" without a full calendar date.
            continue
        day, month, year = visible[-1]
        try:
            parsed = date(int(year), MONTHS[month], int(day))
        except ValueError:
            problems.append(f"{rel}: unparseable visible date {day} {month} {year}")
            continue
        count += 1
        if parsed > today:
            shown = f"{int(day)} {month} {year}"
            problems.append(f"{rel}: visible article date {shown} is after {today.isoformat()}")
    return count


def main() -> int:
    today = date.today()
    problems: list[str] = []
    sitemap_count = check_sitemap(today, problems)
    article_count = check_articles(today, problems)

    if problems:
        print(f"FAIL: {len(problems)} date(s) after {today.isoformat()} or unreadable")
        for line in problems:
            print(line)
        return 1

    print(
        f"OK: {sitemap_count} sitemap lastmod values and {article_count} article dates "
        f"are on or before {today.isoformat()}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
