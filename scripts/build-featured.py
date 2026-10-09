#!/usr/bin/env python3
"""Build featured (hero) image derivatives from approved masters (masters are kept off-repo).

Usage:
  python3 scripts/build-featured.py ENTRIES.json MASTERS_DIR

ENTRIES.json is a list of {"slug", "alt", "focal_y", "shot_type", "prompt", "version"}.
MASTERS_DIR holds <slug>.jpg (square, 1024 or 2048 px). For each entry this writes
  assets/featured/<slug>-hero.webp   1024x768 (4:3, cropped around focal_y), article hero
  assets/featured/<slug>-og.jpg      1200x630, og:image / twitter:image / <img> fallback (<= 120 KB)
  assets/featured/thumbs/<slug>.webp 400x300 card thumbnail for guides/index.html + hubs (<= 25 KB)
and merges the entry into assets/featured/manifest.json. Then run scripts/featured-images.py.
See BLOG-IMAGE-GUIDE.md.
"""
import importlib.util, io, json, sys
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "featured"
MANIFEST = OUT / "manifest.json"
_sp = importlib.util.spec_from_file_location("card_thumbs", ROOT / "scripts" / "card-thumbs.py")
ct = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(ct)
HERO_Q, OG_LIMIT, SOFTEN = 64, 120_000, 0.5  # light 0.5 px blur removes generator noise; ~40% smaller files


def crop(im, aw, ah, fy):
    w, h = im.size
    if w / h > aw / ah:
        nw = round(h * aw / ah); x = (w - nw) // 2
        return im.crop((x, 0, x + nw, h))
    nh = round(w * ah / aw); y = min(max(round(fy * h - nh / 2), 0), h - nh)
    return im.crop((0, y, w, y + nh))


def build(entries, masters):
    OUT.mkdir(parents=True, exist_ok=True)
    man = {e["slug"]: e for e in json.loads(MANIFEST.read_text())} if MANIFEST.exists() else {}
    for e in entries:
        slug, fy = e["slug"], float(e.get("focal_y", 0.5))
        im = Image.open(Path(masters) / f"{slug}.jpg").convert("RGB")
        hero = crop(im, 4, 3, fy).resize((1024, 768), Image.LANCZOS).filter(ImageFilter.GaussianBlur(SOFTEN))
        hero.save(OUT / f"{slug}-hero.webp", "WEBP", quality=HERO_Q, method=6)
        og = crop(im, 1200, 630, fy).resize((1200, 630), Image.LANCZOS).filter(ImageFilter.GaussianBlur(SOFTEN))
        for q in (62, 58, 54, 50, 46):
            b = io.BytesIO(); og.save(b, "JPEG", quality=q, optimize=True, progressive=True)
            if b.tell() <= OG_LIMIT: break
        (OUT / f"{slug}-og.jpg").write_bytes(b.getvalue())
        (OUT / "thumbs").mkdir(exist_ok=True)
        ct.make_thumb(OUT / f"{slug}-hero.webp", OUT / "thumbs" / f"{slug}.webp")
        man[slug] = {k: e[k] for k in ("slug", "alt", "focal_y", "shot_type", "version", "prompt") if k in e}
    MANIFEST.write_text(json.dumps(sorted(man.values(), key=lambda x: x["slug"]), indent=1, ensure_ascii=False) + "\n")
    print(f"built {len(entries)}; manifest now {len(man)}")


if __name__ == "__main__":
    build(json.loads(Path(sys.argv[1]).read_text()), sys.argv[2])
