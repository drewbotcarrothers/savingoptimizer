# Saving Optimizer — website (v1)

Static site for Saving Optimizer. Pure HTML, CSS, and a small `js/main.js`. No build step, no npm, no framework.

## Local preview

**Option A — open a file**

1. Unzip or copy this `site` folder to your computer.
2. Open `index.html` in a browser (double-click, or File → Open).

Pages that use relative links work from `file://` as well as from a local server.

**Option B — tiny local server (recommended)**

From inside this `site` folder:

```bash
# Python 3
python3 -m http.server 8080
```

Then visit [http://localhost:8080](http://localhost:8080).

Any other static server is fine (Hostinger file manager preview, VS Code Live Server, `npx serve`, etc.).

## Upload to Hostinger

Upload the **contents** of this `site` folder into `public_html` — not the wrapper folder itself.

You should end up with:

```
public_html/index.html
public_html/about.html
public_html/contact.html
public_html/css/styles.css
public_html/js/main.js
public_html/assets/logo-primary.png
public_html/assets/favicon.svg
public_html/guides/...
public_html/README.md          (optional on the server)
public_html/BRAND-KIT.md       (optional on the server)
```

If you upload the `site` folder as a whole, the homepage will sit at `yoursite.com/site/` instead of the domain root.

### Hostinger steps (hPanel)

1. Log in to hPanel → **Files** → **File Manager**.
2. Open `public_html`.
3. Upload the files and folders listed above (zip upload + extract is fastest).
4. Confirm `index.html` is at the root of `public_html`.
5. Visit the domain. If you still see a default Hostinger page, remove or replace the stock `index.html` / `default.php`.

Contact form uses `mailto:hello@savingoptimizer.com` (opens the visitor’s email app). There is no server-side form handler.

## Edit later

- Shared look: `css/styles.css`
- Header menu + contact mailto: `js/main.js`
- Brand rules: `BRAND-KIT.md`
- New article: add an HTML file under `guides/articles/`, then link it from `guides/index.html` and the matching category page.

## Licence / credit

Site copy © 2026 Saving Optimizer. Inter is loaded from Google Fonts.
