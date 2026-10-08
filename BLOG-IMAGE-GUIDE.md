# Blog Image Guide: Featured (Hero) Images, Saving Optimizer

Adapted on 8 Oct 2026 from Canadian Optimizer's `BLOG-IMAGE-GUIDE.md` (approved style, October 2026) for savingoptimizer.com, a static HTML site (`guides/articles/<slug>.html`, no build step). The look, shot mix and hard rules are the same as Canadian Optimizer's. What changes: the file paths, the cache busting, the derivative files, and two prompt lessons from the first sample batch (sections 5 and 6).

Follow this guide for every new post and any image redo.

## 1. Goals, in priority order
1. **Relevant to the post.** The image shows the post's literal subject, so a reader knows what the article is about before reading the title.
2. **Drives clicks.** It's a clear, inviting single idea that stands out at the top of the article and as a social / search preview.
3. **Trustworthy.** Rich, professional, magazine-quality, but it must look like a real photo.

## 2. Look: realistic documentary photography
- Real documentary or editorial photo, **not** AI-polished: natural light, true-to-life colour, real texture and small imperfections, ordinary everyday settings.
- **Bright** but not washed out. Avoid moody or dark grading and avoid overexposed, airy looks.
- Canadian settings and cues where natural: houses, snow, kitchens, cottages, transit, pharmacies, grocery stores, condo towers, the Rockies, maple trees.
- No glowing icons, 3D renders, clip art, illustrations or navy/abstract graphics. (Data diagrams stay in the article body as the existing SVG charts in `assets/articles/`; the hero is never a chart.)

## 3. Shot mix (across the site)
| Type | Share | Examples |
|---|---|---|
| Topic scenes, no people | ~45% | A weathered condo tower (condo fee red flags), a stack of winter tires in a garage (winter tires), an empty lake dock in September (shoulder-season travel) |
| People doing the topic | ~45% | Neighbours clearing driveways (snow removal), a shopper choosing produce (grocery savings), a pet sitter walking a dog (dog boarding), a family at Thanksgiving dinner |
| Hands or details | ~10% | Hands holding a phone and a TV remote (subscription audit), a card tapped on a terminal, coins dropped into a jar (TFSA) |

- Keep desk, laptop and paperwork shots rare, about a fifth at most, and vary them.
- Few close-up portraits. When people appear, show their **faces with natural expressions**, not just backs of heads. They must be fictional and not recognizable as any real person.
- Neighbouring posts in a category (and posts that sit next to each other in a hub's `card-grid`) should not repeat the same composition.
- Compose for a crop: the subject sits in the middle band with some headroom, because the article hero (4:3) and the social card (1200×630) are crops of the square master (section 7).

## 4. Hard rules
- **Canadian currency only.** Coins must clearly read as Canadian: gold 11-sided loonies with a loon, two-tone toonies (silver ring, gold centre), and silver 5¢, 10¢ and 25¢ coins.
- **No copper pennies** (Canada stopped making them), US coins, euro coins or generic fantasy coins with fake lettering.
- **No banknotes or paper money of any kind.**
- **No text** anywhere: no titles, labels, readable screens, signs, documents, price tags, house numbers, licence plates, numbered remote buttons or fake lettering. Cards are blank, screens are blank or dark.
- No brand logos (including car badges, appliance labels, emblems on clothing), no toys, no real people.

## 5. Prompt formula
Canadian Optimizer's formula, unchanged in wording, but assembled by shot type:

> "Realistic documentary photograph of [LITERAL POST SUBJECT, as a scene / a person doing it / hands detail], [CANADIAN SETTING]. Natural daylight, bright and true-to-life colour, real texture and small imperfections, ordinary people with natural expressions (fictional). Not AI-polished, no studio look. No text, no lettering, no logos, no banknotes. Any coins are Canadian loonies, toonies and silver coins only, no pennies."

Two lessons from the 8 Oct 2026 sample batch (Grok Imagine):
1. **Only mention money when money is in the shot.** With the coin sentence in every prompt, the model added stray coins (some copper-looking) to a driveway, a garage floor, a grocery counter and a coffee table. For subjects with no money, end the prompt with "No text, no lettering, no logos." and drop the banknote and coin clauses. Keep the full clause for money subjects (TFSA jar, tip jar, coins on a counter).
2. **Only mention people when people are in the shot.** "Ordinary people with natural expressions" put hikers on a "no people" lake scene. For topic scenes, use "No people." instead.

Also add a short, specific exclusion line for the subject's known risks: "no price tags, no shelf labels" (grocery), "smooth sidewalls with no lettering, no car badges" (tires), "TV screen dark and off, remote buttons blank" (screens), "no bottles, no pictures on the walls, plain solid-colour sweaters" (dinner scenes), "no house numbers" (streets).

Settings: model `grok-imagine-image`, `aspect_ratio` 1:1, `n` 2 (pick the better one). `resolution` 2k costs the same as 1k ($0.02) and gives a 2048² master that downsizes cleanly to the 1200×630 social card.

## 6. QA before shipping
- View every new image at full size, and in a contact sheet with its category neighbours (slug labels in the sheet margin only).
- Reject and redo any image with text or fake lettering, banknotes, pennies or foreign coins, warped hands or faces, extra limbs, impossible physics (a shovel standing on its own, leaves falling indoors), or a weak link to the post topic.
- Run OCR on the batch (`tesseract <img> - --psm 11 tsv`, flag words of 3+ characters at confidence ≥ 60), then zoom into every flagged box and into small details OCR can miss: appliance displays, mailboxes, tool handles, remote buttons, shelf tags, clothing emblems.
- Tiny fake glyphs on a background detail can be fixed by a Grok Imagine edit pass ("Keep the photo exactly the same. Only change X…", $0.02 + $0.002) or a small local blur. Anything bigger means regenerating.
- Check the 4:3 hero crop and the 1200×630 social crop (contact sheet of crops) and set `focal_y` so faces and the subject survive.

## 7. Files and performance (static site), as approved 8 Oct 2026
- **Master (off-repo):** the picked Grok Imagine 2048² image, kept on the box at `/workspace/saving-optimizer/featured-masters/masters/<slug>.jpg` (raw variants in `featured-masters/raw/<slug>/`). Masters are **not** committed.
- **Committed derivatives**, built by `scripts/build-featured.py` from the master using `focal_y` (default 0.5):
  - `assets/featured/<slug>-hero.webp`: 1024×768 (4:3) article hero, WebP q64.
  - `assets/featured/<slug>-og.jpg`: 1200×630 social card (≤ 120 KB, progressive JPEG) for `og:image`, `twitter:image`, the Article JSON-LD and the `<img>` fallback inside `<picture>`.
  - Both get a 0.5 px soften before encoding (removes generator noise, ~40% smaller, invisible at display size). Budget: ~140 KB per post, ~140 MB for ~1,000 posts.
- **No category-card thumbnails** for now: hub grids and related-guide lists stay text-only.
- **Manifest:** `assets/featured/manifest.json` with one entry per post: `slug`, `alt`, `focal_y`, `shot_type`, `prompt`, `version`.
- **Markup** (inserted by `scripts/featured-images.py`, idempotent): right after the `article-meta` byline line, above `.prose` and the in-article SVG charts:
  ```html
  <figure class="article-hero">
    <picture>
      <source type="image/webp" srcset="../../assets/featured/<slug>-hero.webp?v=<version>">
      <img src="../../assets/featured/<slug>-og.jpg?v=<version>" width="1024" height="768" alt="…" fetchpriority="high" decoding="async">
    </picture>
  </figure>
  ```
  Head: `og:image` and `twitter:image` = the og jpg (absolute URL with `?v=`), plus `og:image:width` 1200, `og:image:height` 630, `og:image:alt`, `twitter:image:alt`; robots `index,follow,max-image-preview:large`; Article JSON-LD `"image": [hero.webp URL, og.jpg URL]`. CSS: `.article-hero` block in `css/styles.css` (4:3 box, rounded corners, `object-fit: cover`).
- **Cache busting:** `?v=<version>` (date stamp, e.g. `20261008`) on every featured URL. On a redo, bump that slug's `version` in the manifest and rerun both scripts, so only that post's URLs change.
- **Dates:** adding or replacing a hero does not change the article's Updated date or sitemap `lastmod`.
- Every hero needs descriptive alt text that names the post topic (one sentence: what is in the photo + "illustrating <post topic>").
- Source of truth: this file (`/workspace/saving-optimizer/content-research/BLOG-IMAGE-GUIDE.md`); the repo copy is `BLOG-IMAGE-GUIDE.md` in the site root.

## 8. Image step for every new post (do this before publishing)
1. **Spec** (in the post brief): `shot` (scene / people / hands), `scene` (literal subject, written so it also reads as the start of the alt text), `detail`, `setting` (Canadian), `extra` (specific exclusions for the subject's risks), `topic` (for the alt text), `coins: true` only if money is in the shot. Check the category's existing heroes so the composition is not a repeat of its neighbours.
2. **Generate:** add the spec line to `/workspace/saving-optimizer/featured-masters/specs/<file>.jsonl`, then from `/workspace/OpenMontage` run `python3 /workspace/saving-optimizer/featured-masters/fm.py gen <specs> --round 1` (2K, n=2, $0.04 per post; spend is tracked in `featured-masters/ledger.json`).
3. **QA** (section 6): `fm.py ocr <specs>`, `fm.py sheets <specs> <name>`; view both variants, zoom into anything flagged, pick one (`picks.json`), or fix the spec and run the next `--round`.
4. **Master:** copy the pick to `featured-masters/masters/<slug>.jpg`.
5. **Build + insert** in a fresh worktree off `origin/main`: `python3 scripts/build-featured.py entries.json /workspace/saving-optimizer/featured-masters/masters`, then `python3 scripts/featured-images.py` (the post generator `tmp-aeo/med/gen.py` also calls it when the manifest has the slug). Never publish a post with `og-default.jpg`.
6. **Validate:** `python3 scripts/featured-images.py --check`, `python3 scripts/check-dates.py`, `VROOT=$PWD python3 /workspace/tmp-aeo/validate.py`; after the deploy, confirm the live page shows the hero and `og:image`, then ping IndexNow.
