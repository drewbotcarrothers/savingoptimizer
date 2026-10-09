#!/usr/bin/env python3
"""Fail if any <text> in assets/articles/*.svg runs outside the SVG viewBox (it would be cut off on the page).

Measures each SVG in headless Chrome (Playwright, /usr/bin/google-chrome) with the fonts installed on the box
(Inter). Fix long lines by wrapping them into <tspan x=".." dy=".."> lines and moving the content below down
(grow the viewBox and the <img height> to match), or pull short labels inside.
Usage: python3 scripts/check-svg-overflow.py
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
JS = """()=>{const s=document.documentElement;const vb=s.viewBox.baseVal;s.setAttribute('width',vb.width);s.setAttribute('height',vb.height);
const R=s.getBoundingClientRect();const bad=[];
for(const t of s.querySelectorAll('text')){const r=t.getBoundingClientRect();const l=r.left-R.left+vb.x,rt=r.right-R.left+vb.x,tp=r.top-R.top+vb.y,b=r.bottom-R.top+vb.y;
 if(rt>vb.x+vb.width+0.5||l<vb.x-0.5||b>vb.y+vb.height+0.5||tp<vb.y-0.5) bad.push(t.textContent.slice(0,70));}
return bad}"""


async def main():
    files = sorted((ROOT / "assets" / "articles").glob("*.svg")); out = {}
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--disable-dev-shm-usage"])
        pg = await b.new_page()
        for f in files:
            await pg.goto(f.as_uri()); await pg.evaluate("document.fonts.ready")
            bad = await pg.evaluate(JS)
            if bad: out[f.name] = bad
        await b.close()
    print(f"{len(files)} svgs checked; {len(out)} with text outside the viewBox")
    for k, v in out.items(): print(f"  {k}: {v}")
    sys.exit(1 if out else 0)


asyncio.run(main())
