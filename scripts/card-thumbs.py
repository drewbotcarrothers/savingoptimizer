#!/usr/bin/env python3
"""Card thumbnails for the guide listing pages (guides/index.html and the category hubs guides/<cat>.html).

Idempotent. Two steps:
  1. build: for every manifest entry, make assets/featured/thumbs/<slug>.webp (400x300, 4:3) from
     <slug>-hero.webp when it is missing (build-featured.py also writes it when a hero is (re)built).
  2. inject: every <a class="card" href="articles/<slug>.html"> on those pages gets, as its first child,
       <img class="card-thumb" src="../assets/featured/thumbs/<slug>.webp?v=<version>" width="400" height="300"
            alt="<manifest alt>" loading="lazy" decoding="async">
     or, for posts without a featured image yet, a soft-grey placeholder with the moose mark.
     A small <style id="card-thumbs-css"> block in <head> carries the layout (kept in sync from CSS below).
Usage: python3 scripts/card-thumbs.py [--check] [--force]   (--force rebuilds every thumb)
featured-images.py runs this automatically; the post generator uses card_thumb() for new cards.
"""
import html, io, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEAT = ROOT / "assets" / "featured"
THUMBS = FEAT / "thumbs"
MAN = FEAT / "manifest.json"
W, H, LIMIT = 400, 300, 25_000

CSS = ('<style id="card-thumbs-css">'
       '.card>.card-thumb{display:block;width:calc(100% + 2.7rem);max-width:none;height:auto;aspect-ratio:16/9;'
       'object-fit:cover;margin:-1.35rem -1.35rem 1rem;border-radius:11px 11px 0 0;background:#F3F4F6}'
       '.card>.card-thumb-none{display:flex;align-items:center;justify-content:center}'
       '.card>.card-thumb-none img{width:48px;height:48px;opacity:.55}'
       '</style>')

CARD_RE = re.compile(r'(<a class="card[^"]*" href="articles/([a-z0-9-]+)\.html">)(\s*)'
                     r'(?:(?:<img class="card-thumb"[^>]*>|<span class="card-thumb card-thumb-none"[^>]*>.*?</span>)\s*)?', re.S)


def manifest():
    return {e["slug"]: e for e in json.loads(MAN.read_text())} if MAN.exists() else {}


def short_alt(e):
    return re.split(r", illustrating ", e["alt"], maxsplit=1)[0].rstrip(".") + "."


def card_thumb(slug, ent=None, prefix="../"):
    """Markup for a card's thumbnail (prefix = path from the page to the site root)."""
    if ent and (THUMBS / f"{slug}.webp").exists():
        return (f'<img class="card-thumb" src="{prefix}assets/featured/thumbs/{slug}.webp?v={ent["version"]}" '
                f'width="{W}" height="{H}" alt="{html.escape(short_alt(ent), quote=True)}" loading="lazy" decoding="async">')
    return (f'<span class="card-thumb card-thumb-none" aria-hidden="true"><img src="{prefix}assets/logo-moose-64.webp" '
            f'width="48" height="48" alt="" loading="lazy" decoding="async"></span>')


def make_thumb(src, dst):
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if w * 3 != h * 4:  # centre-crop to 4:3
        nw, nh = min(w, h * 4 // 3), min(h, w * 3 // 4)
        im = im.crop(((w - nw) // 2, (h - nh) // 2, (w + nw) // 2, (h + nh) // 2))
    im = im.resize((W, H), Image.LANCZOS)
    for q in (70, 62, 55, 48, 42):  # stay under ~25 KB
        b = io.BytesIO(); im.save(b, "WEBP", quality=q, method=6)
        if b.tell() <= LIMIT: break
    Path(dst).write_bytes(b.getvalue())


def build(man, force=False):
    THUMBS.mkdir(parents=True, exist_ok=True)
    n = 0
    for s in man:
        hero, t = FEAT / f"{s}-hero.webp", THUMBS / f"{s}.webp"
        if hero.exists() and (force or not t.exists()):
            make_thumb(hero, t); n += 1
    return n


def inject(h, man):
    def rep(m):
        ws = m.group(3) if "\n" in m.group(3) else ""
        return m.group(1) + (ws or "") + card_thumb(m.group(2), man.get(m.group(2))) + (ws or "")
    h = CARD_RE.sub(rep, h)
    h = re.sub(r'[ \t]*<style id="card-thumbs-css">.*?</style>\n?', "", h, flags=re.S)
    if 'class="card-thumb' in h:
        h = h.replace("</head>", "  " + CSS + "\n</head>", 1)
    return h


def pages():
    return sorted(p for p in (ROOT / "guides").glob("*.html"))


def main():
    check, force = "--check" in sys.argv, "--force" in sys.argv
    man = manifest()
    missing = [s for s in man if (FEAT / f"{s}-hero.webp").exists() and not (THUMBS / f"{s}.webp").exists()]
    built = 0 if check else build(man, force)
    changed, cards, thumbs = [], 0, 0
    for p in pages():
        h = p.read_text(encoding="utf-8"); h2 = inject(h, man)
        cards += len(re.findall(r'<a class="card[^"]*" href="articles/', h2))
        thumbs += h2.count('<img class="card-thumb"')
        if h2 != h:
            changed.append(p.name)
            if not check: p.write_text(h2, encoding="utf-8")
    print(f"thumbs built {built}; pages {'needing update' if check else 'updated'} {len(changed)}; "
          f"cards {cards}, with thumbnail {thumbs}, placeholder {cards - thumbs}")
    if check and (changed or missing):
        print("missing thumbs:", missing[:10], "pages:", changed[:10]); sys.exit(1)


if __name__ == "__main__":
    main()
