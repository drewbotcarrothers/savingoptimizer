# Saving Optimizer — website (v1)

Static site for Saving Optimizer. Pure HTML, CSS, and a small `js/main.js`. **No Node.js, no npm, no build step** — there is intentionally no `package.json`.

## Local preview

**Option A — open a file**

1. Copy this folder to your computer.
2. Open `index.html` in a browser.

**Option B — tiny local server (recommended)**

```bash
python3 -m http.server 8080
```

Visit [http://localhost:8080](http://localhost:8080).

## Deploy to Hostinger

### Why “missing package.json”?

Hostinger’s **Node.js web app → Import Git repository** flow expects a Node project with a root `package.json`. This site is **not** that — it is ready-to-serve HTML.

Use one of the options below instead. Do **not** create an empty `package.json` just to silence that error unless you are deliberately converting to a Node build pipeline.

### Option 1 — Git sync (recommended for this repo)

Copies files from GitHub into `public_html` on every deploy. No build.

1. In hPanel open your **website** (the existing savingoptimizer.com site — PHP/static hosting).
2. Go to **Advanced → Git** (generic Git, not “Node.js web app”).
3. Connect GitHub and pick `drewbotcarrothers/savingoptimizer`.
4. Branch: `main`. Deploy directory: `public_html` (root).
5. Click **Deploy**.

After the first deploy, enable auto-deploy / webhook if offered so pushes to `main` update the live site.

### Option 2 — File Manager upload

1. hPanel → **Files → File Manager** → `public_html`.
2. Upload the **contents** of this repo (not a nested wrapper folder).
3. You want `public_html/index.html`, `public_html/css/`, `public_html/guides/`, etc.
4. Remove Hostinger’s default placeholder page if it is still there.

### Option 3 — “Deploy as static” (if shown)

If Hostinger offers **Deploy as static** when importing the repo, choose that. It serves the files as-is without looking for `package.json`.

## SEO / AI files

Also deployed from the repo root: `robots.txt`, `sitemap.xml`, `llms.txt`, `ai.txt`.

## Categories

The site uses a **locked set of 22 categories** (exact names in nav, headings, URLs, JSON-LD, `llms.txt`, and `sitemap.xml`): Food & Groceries, Transportation, Housing, Utilities, Kids, Clothing, Personal Care, Travel, Personal Finance, Insurance, Healthcare, Household Items and Supplies, Pets, Subscriptions, Entertainment, Students, Weddings, Events, Education, Technology, Internet, Sports. Slug files live under `guides/` (e.g. `food-groceries.html`, `household-items.html`).

## Edit later

- Shared look: `css/styles.css`
- Header menu + contact mailto: `js/main.js`
- Brand rules: `BRAND-KIT.md`
- New article: add HTML under `guides/articles/`, link from `guides/index.html` and the category page.

## Licence / credit

Site copy © 2026 Saving Optimizer. Inter is loaded from Google Fonts.
