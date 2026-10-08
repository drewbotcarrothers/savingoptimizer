#!/usr/bin/env python3
"""Insert or refresh featured (hero) images in article pages from assets/featured/manifest.json.

Idempotent. For every manifest entry whose files exist:
  - <figure class="article-hero"> right after the article-meta line (above .prose)
  - og:image / twitter:image -> assets/featured/<slug>-og.jpg?v=<version>, plus og:image:width,
    og:image:height, og:image:alt and twitter:image:alt
  - robots meta gets max-image-preview:large
  - Article JSON-LD "image" -> [hero.webp, og.jpg]
Article dates are not touched. Usage: python3 scripts/featured-images.py [--check]
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://savingoptimizer.com"
MAN = ROOT / "assets" / "featured" / "manifest.json"


def hero_block(e):
    s, v, a = e["slug"], e["version"], html.escape(e["alt"], quote=True)
    return (
        '    <figure class="article-hero">\n'
        '      <picture>\n'
        f'        <source type="image/webp" srcset="../../assets/featured/{s}-hero.webp?v={v}">\n'
        f'        <img src="../../assets/featured/{s}-og.jpg?v={v}" width="1024" height="768" alt="{a}" fetchpriority="high" decoding="async">\n'
        '      </picture>\n'
        '    </figure>\n')


def apply(h, e):
    s, v, a = e["slug"], e["version"], html.escape(e["alt"], quote=True)
    og = f"{SITE}/assets/featured/{s}-og.jpg?v={v}"
    hero = f"{SITE}/assets/featured/{s}-hero.webp?v={v}"
    # hero figure
    h = re.sub(r'    <figure class="article-hero">.*?</figure>\n', '', h, flags=re.S)
    h, n = re.subn(r'(<p class="article-meta">.*?</p>\n)', lambda m: m.group(1) + hero_block(e), h, count=1, flags=re.S)
    if n != 1: raise ValueError("no article-meta")
    # head tags
    h = re.sub(r'\n  <meta property="og:image:(?:width|height|alt)" content="[^"]*">', '', h)
    h = re.sub(r'\n  <meta name="twitter:image:alt" content="[^"]*">', '', h)
    h, n1 = re.subn(r'<meta property="og:image" content="[^"]*">',
                    f'<meta property="og:image" content="{og}">\n  <meta property="og:image:width" content="1200">\n'
                    f'  <meta property="og:image:height" content="630">\n  <meta property="og:image:alt" content="{a}">', h, count=1)
    h, n2 = re.subn(r'<meta name="twitter:image" content="[^"]*">',
                    f'<meta name="twitter:image" content="{og}">\n  <meta name="twitter:image:alt" content="{a}">', h, count=1)
    if not (n1 and n2): raise ValueError("og/twitter image tag missing")
    h = h.replace('<meta name="robots" content="index,follow">', '<meta name="robots" content="index,follow,max-image-preview:large">')
    # Article JSON-LD image
    def fix(m):
        j = m.group(1)
        try: d = json.loads(j)
        except Exception: return m.group(0)
        if not (isinstance(d, dict) and d.get("@type") == "Article"): return m.group(0)
        j2 = re.sub(r'\n  "image": (?:\[.*?\n  \]|"[^"]*"),', '\n  "image": [\n    ' + json.dumps(hero) + ',\n    ' + json.dumps(og) + '\n  ],', j, count=1, flags=re.S)
        if json.loads(j2).get("image") != [hero, og]: raise ValueError("JSON-LD image not updated")
        return m.group(0).replace(j, j2)
    h = re.sub(r'<script type="application/ld\+json">(.*?)</script>', fix, h, flags=re.S)
    return h


def main():
    check = "--check" in sys.argv
    entries = json.loads(MAN.read_text())
    changed, bad = 0, []
    for e in entries:
        f = ROOT / "guides" / "articles" / f"{e['slug']}.html"
        files = [ROOT / "assets" / "featured" / f"{e['slug']}-{x}" for x in ("hero.webp", "og.jpg")]
        if not f.exists() or not all(p.exists() for p in files) or not e.get("alt"):
            bad.append(e["slug"]); continue
        h = f.read_text(encoding="utf-8"); h2 = apply(h, e)
        if h2 != h:
            changed += 1
            if not check: f.write_text(h2, encoding="utf-8")
    print(f"manifest {len(entries)}; {'would change' if check else 'changed'} {changed}; problems {bad}")
    if bad or (check and changed): sys.exit(1)


if __name__ == "__main__":
    main()
