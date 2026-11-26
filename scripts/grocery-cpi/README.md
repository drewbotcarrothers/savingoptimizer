# Grocery CPI refresh

The Canadian Grocery Price Tracker is built from Statistics Canada table **18-10-0004-01** (Consumer Price Index, monthly, not seasonally adjusted). The page does not contain typed-in index values. `refresh.py` downloads the official English cube and rewrites the CSV plus the generated blocks on the tracker and embed pages.

Published files:

| File | URL |
| --- | --- |
| `data/grocery-cpi.csv` | https://savingoptimizer.com/data/grocery-cpi.csv |
| `guides/data/grocery-price-tracker.html` | https://savingoptimizer.com/guides/data/grocery-price-tracker.html |
| `embed/grocery-price-tracker.html` | https://savingoptimizer.com/embed/grocery-price-tracker.html |

The embed page is `noindex` and is not listed in `sitemap.xml`. The script stops if that URL shows up in the sitemap.

## Categories

Canada only, index 2002=100:

- All-items (comparison)
- Food
- Food purchased from stores
- Meat
- Fish, seafood and other marine products
- Dairy products and eggs
- Bakery and cereal products (excluding baby food)
- Fresh fruit
- Fresh vegetables

Those are the official product labels in the cube. Bakery is the parent series that excludes baby food. Fish and seafood is the parent series “Fish, seafood and other marine products.”

Year-over-year change is `(this month / same month last year − 1) × 100`, rounded half up to one decimal. The script refuses to write a file if any of the nine series is missing the latest month, or if the 24-month chart would have a gap.

## Monthly run

From the repository root, after Statistics Canada publishes the next CPI month:

```bash
python3 scripts/grocery-cpi/refresh.py
```

That downloads `https://www150.statcan.gc.ca/n1/tbl/csv/18100004-eng.zip`. If the download fails, or a category is missing, the script exits non-zero and does not replace the published CSV or HTML.

To rebuild from a cube zip you already have (same checks, no download):

```bash
python3 scripts/grocery-cpi/refresh.py --zip /path/to/18100004-eng.zip
```

`--retrieved YYYY-MM-DD` sets the “retrieved” date on the source line. The default is the day you run the script.

Commit `data/grocery-cpi.csv` and the two HTML files together. The source line on both pages should read:

`Source: Statistics Canada, Table 18-10-0004-01, retrieved <date>.`

The October 2026 reference month was in the Statistics Canada release of 16 Nov 2026 (vector `v41690973`, release time reported by the Web Data Service).
