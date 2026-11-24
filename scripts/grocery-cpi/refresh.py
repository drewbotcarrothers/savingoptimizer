#!/usr/bin/env python3
"""Refresh the Canadian grocery CPI pages from Statistics Canada table 18-10-0004-01.

Downloads the official English CSV cube (monthly, not seasonally adjusted),
keeps Canada only, and rewrites:

- data/grocery-cpi.csv
- the generated block in guides/data/grocery-price-tracker.html
- the generated block in embed/grocery-price-tracker.html

The script never invents a missing index. If the download fails, a required
category is absent, or the latest month is incomplete, it exits non-zero and
leaves the published files unchanged.

Usage (from the repository root):

    python3 scripts/grocery-cpi/refresh.py
    python3 scripts/grocery-cpi/refresh.py --zip /path/to/18100004-eng.zip
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import re
import sys
import tempfile
import urllib.request
import zipfile
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data" / "grocery-cpi.csv"
TRACKER_PATH = ROOT / "guides" / "data" / "grocery-price-tracker.html"
EMBED_PATH = ROOT / "embed" / "grocery-price-tracker.html"
SITEMAP_PATH = ROOT / "sitemap.xml"

ZIP_URL = "https://www150.statcan.gc.ca/n1/tbl/csv/18100004-eng.zip"
TABLE_URL = "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810000401"
TABLE_ID = "18-10-0004-01"
GEO = "Canada"
UOM = "2002=100"
USER_AGENT = "SavingOptimizer grocery-cpi refresh (+https://savingoptimizer.com)"

# Official "Products and product groups" labels from cube 18100004.
# expected_vector is the VECTOR published in that cube for Canada. A mismatch
# stops the refresh instead of silently following a renamed series.
SERIES = [
    {
        "product": "All-items",
        "legend": "All-items",
        "column": "All-items",
        "expected_vector": "v41690973",
        "color": "#4B5563",
        "width": 2.25,
        "dash": "6 4",
    },
    {
        "product": "Food",
        "legend": "Food",
        "column": "Food",
        "expected_vector": "v41690974",
        "color": "#0F7A4B",
        "width": 1.75,
        "dash": None,
    },
    {
        "product": "Food purchased from stores",
        "legend": "Food purchased from stores",
        "column": "Food from stores",
        "expected_vector": "v41690975",
        "color": "#111827",
        "width": 2.75,
        "dash": None,
    },
    {
        "product": "Meat",
        "legend": "Meat",
        "column": "Meat",
        "expected_vector": "v41690976",
        "color": "#C2410C",
        "width": 1.75,
        "dash": None,
    },
    {
        "product": "Fish, seafood and other marine products",
        "legend": "Fish and seafood",
        "column": "Fish and seafood",
        "expected_vector": "v41690987",
        "color": "#0369A1",
        "width": 1.75,
        "dash": None,
    },
    {
        "product": "Dairy products and eggs",
        "legend": "Dairy products and eggs",
        "column": "Dairy and eggs",
        "expected_vector": "v41690992",
        "color": "#6D28D9",
        "width": 1.75,
        "dash": None,
    },
    {
        "product": "Bakery and cereal products (excluding baby food)",
        "legend": "Bakery and cereal",
        "column": "Bakery and cereal",
        "expected_vector": "v41691000",
        "color": "#A16207",
        "width": 1.75,
        "dash": None,
    },
    {
        "product": "Fresh fruit",
        "legend": "Fresh fruit",
        "column": "Fresh fruit",
        "expected_vector": "v41691011",
        "color": "#BE185D",
        "width": 1.75,
        "dash": None,
    },
    {
        "product": "Fresh vegetables",
        "legend": "Fresh vegetables",
        "column": "Fresh vegetables",
        "expected_vector": "v41691021",
        "color": "#047857",
        "width": 1.75,
        "dash": None,
    },
]

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
MONTHS_SHORT = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

TRACKER_START = "<!-- GROCERY_CPI_BLOCK_START -->"
TRACKER_END = "<!-- GROCERY_CPI_BLOCK_END -->"
EMBED_START = "<!-- GROCERY_CPI_EMBED_START -->"
EMBED_END = "<!-- GROCERY_CPI_EMBED_END -->"


class RefreshError(Exception):
    """The published files were not changed."""


def yoy_pct(current: Decimal, previous: Decimal) -> Decimal:
    """Percent change, rounded half up to one decimal (StatCan index precision)."""
    if previous == 0:
        raise RefreshError("Cannot compute a percent change against an index of 0.")
    raw = (current / previous - Decimal(1)) * Decimal(100)
    return raw.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def format_index(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}"


def format_pct(value: Decimal) -> str:
    if value > 0:
        return f"+{value}%"
    return f"{value}%"


def format_cad(amount: Decimal) -> str:
    """Index points map 1:1 onto a basket that cost CA$100 in 2002."""
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "-" if quantized < 0 else ""
    return f"{sign}CA${abs(quantized):,.2f}"


def shift_month(ym: str, delta: int) -> str:
    year, month = (int(part) for part in ym.split("-"))
    index = year * 12 + (month - 1) + delta
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def month_long(ym: str) -> str:
    year, month = ym.split("-")
    return f"{MONTHS[int(month) - 1]} {year}"


def month_short(ym: str) -> str:
    year, month = ym.split("-")
    return f"{MONTHS_SHORT[int(month) - 1]} {year}"


def display_date(day: date) -> str:
    return f"{day.day} {MONTHS_SHORT[day.month - 1]} {day.year}"


def download_zip(destination: Path) -> None:
    request = urllib.request.Request(ZIP_URL, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = response.read()
    except Exception as exc:  # noqa: BLE001 — report any transport failure and stop
        raise RefreshError(f"Could not download {ZIP_URL}: {exc}") from exc
    if len(payload) < 1_000_000:
        raise RefreshError(
            f"Download was only {len(payload)} bytes. Refusing to treat that as the CPI cube."
        )
    destination.write_bytes(payload)


def load_series(zip_path: Path) -> tuple[dict[str, dict[str, Decimal]], dict[str, str]]:
    wanted = {item["product"]: item for item in SERIES}
    values: dict[str, dict[str, Decimal]] = {name: {} for name in wanted}
    vectors: dict[str, str] = {}
    try:
        archive = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        raise RefreshError(f"{zip_path} is not a valid zip file: {exc}") from exc
    with archive:
        members = [
            name
            for name in archive.namelist()
            if name.endswith("18100004.csv") and "MetaData" not in name
        ]
        if len(members) != 1:
            raise RefreshError(
                f"Expected one 18100004.csv in the cube zip, found {members!r}."
            )
        with archive.open(members[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
            required = {
                "REF_DATE",
                "GEO",
                "Products and product groups",
                "UOM",
                "VECTOR",
                "VALUE",
            }
            if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
                raise RefreshError(f"Unexpected CSV columns: {reader.fieldnames!r}")
            for row in reader:
                product = row["Products and product groups"]
                if product not in wanted or row["GEO"] != GEO:
                    continue
                if row["UOM"] != UOM:
                    raise RefreshError(
                        f"{product} has UOM {row['UOM']!r}, expected {UOM}."
                    )
                vector = row["VECTOR"].strip()
                if product in vectors and vectors[product] != vector:
                    raise RefreshError(f"{product} has more than one vector id.")
                vectors[product] = vector
                raw_value = row["VALUE"].strip()
                if not raw_value:
                    continue
                try:
                    values[product][row["REF_DATE"]] = Decimal(raw_value)
                except Exception as exc:  # noqa: BLE001
                    raise RefreshError(
                        f"Unreadable index for {product} {row['REF_DATE']}: {raw_value!r}"
                    ) from exc
    for item in SERIES:
        product = item["product"]
        if not values[product]:
            raise RefreshError(f"No Canada rows for {product!r} in the cube.")
        found = vectors.get(product, "")
        if found != item["expected_vector"]:
            raise RefreshError(
                f"{product} vector is {found or '(missing)'}, expected {item['expected_vector']}."
            )
    return values, vectors


def latest_complete_month(values: dict[str, dict[str, Decimal]]) -> str:
    shared = None
    for item in SERIES:
        months = set(values[item["product"]])
        shared = months if shared is None else shared & months
    if not shared:
        raise RefreshError("The nine categories have no month in common.")
    return max(shared)


def window_months(latest: str, count: int = 24) -> list[str]:
    start = shift_month(latest, -(count - 1))
    months = []
    cursor = start
    while cursor <= latest:
        months.append(cursor)
        cursor = shift_month(cursor, 1)
    if len(months) != count:
        raise RefreshError(f"Expected {count} months ending {latest}, built {len(months)}.")
    return months


def require_window(values: dict[str, dict[str, Decimal]], months: list[str]) -> None:
    missing = []
    for item in SERIES:
        product = item["product"]
        for month in months:
            if month not in values[product]:
                missing.append(f"{product} {month}")
            prior = shift_month(month, -12)
            if prior not in values[product]:
                missing.append(f"{product} {prior} (needed for year-over-year)")
    if missing:
        preview = "; ".join(missing[:8])
        raise RefreshError(f"Refusing to chart a gap in the CPI file: {preview}")


def write_csv(values: dict[str, dict[str, Decimal]], vectors: dict[str, str]) -> int:
    months = sorted({month for series in values.values() for month in series})
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = CSV_PATH.with_suffix(".csv.tmp")
    count = 0
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "ref_date",
                "geo",
                "seasonal_adjustment",
                "table_id",
                "product",
                "vector",
                "uom",
                "index_2002",
                "yoy_percent",
            ]
        )
        for month in months:
            for item in SERIES:
                product = item["product"]
                if month not in values[product]:
                    continue
                current = values[product][month]
                prior_month = shift_month(month, -12)
                yoy = ""
                if prior_month in values[product]:
                    yoy = format(yoy_pct(current, values[product][prior_month]), "f")
                writer.writerow(
                    [
                        month,
                        GEO,
                        "not seasonally adjusted",
                        TABLE_ID,
                        product,
                        vectors[product],
                        UOM,
                        format_index(current),
                        yoy,
                    ]
                )
                count += 1
    temporary.replace(CSV_PATH)
    return count


def chart_svg(values: dict[str, dict[str, Decimal]], months: list[str], *, compact: bool) -> str:
    width = 640 if compact else 720
    height = 268 if compact else 372
    left = 46
    right = 12
    top = 14
    bottom = 32
    plot_w = width - left - right
    plot_h = height - top - bottom
    flat = [
        values[item["product"]][month]
        for item in SERIES
        for month in months
    ]
    low = min(flat)
    high = max(flat)
    step = Decimal(10) if (high - low) > 40 else Decimal(5)
    y_min = (low // step) * step
    if y_min == low:
        y_min -= step
    y_max = ((high + step - Decimal("0.1")) // step) * step
    if y_max == high:
        y_max += step

    def x_at(index: int) -> float:
        if len(months) == 1:
            return left + plot_w / 2
        return left + plot_w * (index / (len(months) - 1))

    def y_at(level: Decimal) -> float:
        ratio = (level - y_min) / (y_max - y_min)
        return top + plot_h * (1 - float(ratio))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="cpi-chart-title cpi-chart-desc">',
        "<title id=\"cpi-chart-title\">"
        + html.escape(
            f"Consumer Price Index, Canada, {month_long(months[0])} to {month_long(months[-1])}"
        )
        + "</title>",
        "<desc id=\"cpi-chart-desc\">"
        + html.escape(
            "Line chart of the Consumer Price Index (2002=100), not seasonally adjusted, "
            "for all-items and eight food categories. The data table beside this chart "
            "lists every plotted index."
        )
        + "</desc>",
    ]
    tick = y_min
    while tick <= y_max:
        y = y_at(tick)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" '
            f'stroke="#E5E7EB" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-size="12" font-family="Inter, system-ui, sans-serif" fill="#6B7280">'
            f"{format_index(tick)}</text>"
        )
        tick += step
    label_every = 6 if compact else 3
    label_indexes = [
        index
        for index in range(len(months))
        if index % label_every == 0 or index == len(months) - 1
    ]
    if len(label_indexes) >= 2 and label_indexes[-1] - label_indexes[-2] < label_every:
        del label_indexes[-2]
    for index in label_indexes:
        month = months[index]
        anchor = "start" if index == 0 else "end" if index == len(months) - 1 else "middle"
        parts.append(
            f'<text x="{x_at(index):.1f}" y="{height - 8}" text-anchor="{anchor}" '
            f'font-size="12" font-family="Inter, system-ui, sans-serif" fill="#6B7280">'
            f"{html.escape(month_short(month))}</text>"
        )
    for item in SERIES:
        points = " ".join(
            f"{x_at(index):.1f},{y_at(values[item['product']][month]):.1f}"
            for index, month in enumerate(months)
        )
        dash = f' stroke-dasharray="{item["dash"]}"' if item["dash"] else ""
        parts.append(
            f'<polyline fill="none" stroke="{item["color"]}" stroke-width="{item["width"]}" '
            f'stroke-linejoin="round" stroke-linecap="round"{dash} points="{points}"/>'
        )
        last_x = x_at(len(months) - 1)
        last_y = y_at(values[item["product"]][months[-1]])
        parts.append(
            f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="3" fill="{item["color"]}"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def legend_html() -> str:
    items = []
    for item in SERIES:
        items.append(
            "<li><span class=\"cpi-swatch\" style=\"background:"
            + item["color"]
            + "\"></span>"
            + html.escape(item["legend"])
            + "</li>"
        )
    return '<ul class="cpi-legend">' + "".join(items) + "</ul>"


def latest_table(values: dict[str, dict[str, Decimal]], latest: str) -> str:
    prior = shift_month(latest, -12)
    rows = []
    for item in SERIES:
        current = values[item["product"]][latest]
        previous = values[item["product"]][prior]
        change = yoy_pct(current, previous)
        rows.append(
            "<tr><th scope=\"row\">"
            + html.escape(item["product"])
            + "</th><td>"
            + format_index(previous)
            + "</td><td>"
            + format_index(current)
            + "</td><td>"
            + format_pct(change)
            + "</td></tr>"
        )
    caption = (
        f"Canada, {month_long(latest)}. Index base 2002=100, not seasonally adjusted. "
        f"Year-over-year change is (this month ÷ {month_long(prior)} − 1), "
        "rounded half up to one decimal."
    )
    return (
        '<div class="table-wrap"><table><caption>'
        + html.escape(caption)
        + "</caption><thead><tr>"
        + '<th scope="col">Category</th>'
        + f'<th scope="col">{html.escape(month_short(prior))} index</th>'
        + f'<th scope="col">{html.escape(month_short(latest))} index</th>'
        + '<th scope="col">Year-over-year</th>'
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def history_table(values: dict[str, dict[str, Decimal]], months: list[str]) -> str:
    header = "".join(
        f'<th scope="col">{html.escape(item["column"])}</th>' for item in SERIES
    )
    body = []
    for month in months:
        cells = "".join(
            f"<td>{format_index(values[item['product']][month])}</td>" for item in SERIES
        )
        body.append(
            f'<tr><th scope="row">{html.escape(month_short(month))}</th>{cells}</tr>'
        )
    caption = (
        f"Index (2002=100), Canada, not seasonally adjusted, "
        f"{month_long(months[0])} to {month_long(months[-1])}."
    )
    return (
        '<div class="table-wrap"><table><caption>'
        + html.escape(caption)
        + '</caption><thead><tr><th scope="col">Month</th>'
        + header
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def cad_paragraph(values: dict[str, dict[str, Decimal]], latest: str) -> str:
    prior = shift_month(latest, -12)
    stores_now = values["Food purchased from stores"][latest]
    stores_then = values["Food purchased from stores"][prior]
    all_now = values["All-items"][latest]
    all_then = values["All-items"][prior]
    stores_yoy = yoy_pct(stores_now, stores_then)
    all_yoy = yoy_pct(all_now, all_then)
    text = (
        f"In Canadian dollars, using the index base of 2002=100: a store-food basket that "
        f"cost CA$100 in 2002 costs {format_cad(stores_now)} at the {month_long(latest)} "
        f"index for food purchased from stores, compared with {format_cad(stores_then)} in "
        f"{month_long(prior)}. That is {format_cad(stores_now - stores_then)} more, the same "
        f"{format_pct(stores_yoy)} year-over-year change. All-items moved from "
        f"{format_cad(all_then)} to {format_cad(all_now)}, or "
        f"{format_cad(all_now - all_then)} ({format_pct(all_yoy)}). "
        "This is the index expressed in dollars, before tax. It is not a receipt from a store."
    )
    return "<p>" + html.escape(text) + "</p>"


def source_line(retrieved: date) -> str:
    # Visible sentence, link text included: "Source: Statistics Canada, Table 18-10-0004-01, retrieved <date>."
    return (
        '<p class="cpi-source">Source: Statistics Canada, '
        f'<a href="{TABLE_URL}">Table {TABLE_ID}</a>, '
        f"retrieved {html.escape(display_date(retrieved))}.</p>"
    )


def tracker_block(values: dict[str, dict[str, Decimal]], latest: str, retrieved: date) -> str:
    prior = shift_month(latest, -12)
    months = window_months(latest, 24)
    stores = values["Food purchased from stores"][latest]
    stores_yoy = yoy_pct(stores, values["Food purchased from stores"][prior])
    all_items = values["All-items"][latest]
    all_yoy = yoy_pct(all_items, values["All-items"][prior])
    lead = (
        f"Latest month: {month_long(latest)}. Food purchased from stores is "
        f"{format_index(stores)} (2002=100), {format_pct(stores_yoy)} from {month_long(prior)}. "
        f"All-items is {format_index(all_items)}, {format_pct(all_yoy)}. "
        "Canada, not seasonally adjusted."
    )
    return "\n".join(
        [
            '<div class="takeaways"><h2>Key takeaways</h2><ul>',
            f"<li>{html.escape(lead)}</li>",
            "<li>A positive percent means that category's index rose. It is not a discount.</li>",
            "<li>Fresh fruit and fresh vegetables are not seasonally adjusted, so the line moves with the growing season as well as with price.</li>",
            "<li>The dollar figures translate the 2002=100 index. They are not shelf prices.</li>",
            "</ul></div>",
            "<h2>What the index is in Canadian dollars</h2>",
            cad_paragraph(values, latest),
            "<h2>Year-over-year change by category</h2>",
            "<p>Each row is the official Statistics Canada product name. "
            "Food purchased from stores is the grocery basket. Food also includes food bought from restaurants. "
            "All-items is the whole CPI, included so grocery inflation has a comparison.</p>",
            latest_table(values, latest),
            f"<h2>24-month index, {html.escape(month_long(months[0]))} to {html.escape(month_long(months[-1]))}</h2>",
            "<p>The darker line is food purchased from stores. The dashed line is all-items. "
            "The other lines are the food categories in the table.</p>",
            '<figure class="article-figure">',
            chart_svg(values, months, compact=False),
            "<figcaption>Consumer Price Index, Canada, 2002=100, not seasonally adjusted. "
            "Last point on each line is the latest month.</figcaption>",
            "</figure>",
            legend_html(),
            "<details><summary>Show the 24-month index values</summary>",
            history_table(values, months),
            "</details>",
            source_line(retrieved),
            '<p>The processed monthly file is <a href="/data/grocery-cpi.csv">grocery-cpi.csv</a>. '
            "It starts with every published month in the cube for these nine Canada series. "
            "Year-over-year is blank only when the same month a year earlier is not in the cube.</p>",
        ]
    )


def embed_block(values: dict[str, dict[str, Decimal]], latest: str, retrieved: date) -> str:
    prior = shift_month(latest, -12)
    months = window_months(latest, 24)
    stores = values["Food purchased from stores"][latest]
    stores_yoy = yoy_pct(stores, values["Food purchased from stores"][prior])
    all_items = values["All-items"][latest]
    all_yoy = yoy_pct(all_items, values["All-items"][prior])
    lead = (
        f"{month_long(latest)}. Food purchased from stores {format_index(stores)} "
        f"({format_pct(stores_yoy)} year over year). "
        f"All-items {format_index(all_items)} ({format_pct(all_yoy)})."
    )
    return "\n".join(
        [
            f'<p class="embed-latest"><strong>{html.escape(lead)}</strong> '
            "Canada, 2002=100, not seasonally adjusted.</p>",
            '<figure class="article-figure">',
            chart_svg(values, months, compact=True),
            f"<figcaption>CPI, {html.escape(month_short(months[0]))} to {html.escape(month_short(months[-1]))}. "
            "Dark line: food purchased from stores. Dashed line: all-items.</figcaption>",
            "</figure>",
            legend_html(),
            source_line(retrieved),
        ]
    )


def replace_block(page: str, start: str, end: str, block: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = start + "\n" + block.strip() + "\n" + end
    updated, count = pattern.subn(replacement, page, count=1)
    if count != 1:
        raise RefreshError(f"Expected exactly one {start} block.")
    return updated


def replace_dates(page: str, retrieved: date) -> str:
    iso = retrieved.isoformat()
    visible = display_date(retrieved)

    def time_repl(_match: re.Match[str]) -> str:
        return f'<time id="cpi-updated" datetime="{iso}">{visible}</time>'

    def meta_repl(_match: re.Match[str]) -> str:
        return f'<meta name="article:modified_time" content="{iso}"'

    def json_repl(_match: re.Match[str]) -> str:
        return f'"dateModified": "{iso}"'

    updated, time_count = re.subn(
        r'<time id="cpi-updated" datetime="[^"]*">[^<]*</time>',
        time_repl,
        page,
        count=1,
    )
    if time_count != 1:
        raise RefreshError('Expected one <time id="cpi-updated"> element.')
    updated, meta_count = re.subn(
        r'<meta name="article:modified_time" content="[^"]*"',
        meta_repl,
        updated,
        count=1,
    )
    updated, json_count = re.subn(
        r'"dateModified"\s*:\s*"[^"]*"',
        json_repl,
        updated,
        count=1,
    )
    if meta_count != 1 or json_count != 1:
        raise RefreshError("Expected one article:modified_time and one dateModified.")
    return updated


def write_pages(values: dict[str, dict[str, Decimal]], latest: str, retrieved: date) -> None:
    tracker = TRACKER_PATH.read_text(encoding="utf-8")
    embed = EMBED_PATH.read_text(encoding="utf-8")
    if TRACKER_START not in tracker or TRACKER_END not in tracker:
        raise RefreshError(f"Missing tracker markers in {TRACKER_PATH}.")
    if EMBED_START not in embed or EMBED_END not in embed:
        raise RefreshError(f"Missing embed markers in {EMBED_PATH}.")
    tracker = replace_block(tracker, TRACKER_START, TRACKER_END, tracker_block(values, latest, retrieved))
    tracker = replace_dates(tracker, retrieved)
    embed = replace_block(embed, EMBED_START, EMBED_END, embed_block(values, latest, retrieved))
    embed = replace_dates(embed, retrieved)
    if "noindex" not in embed:
        raise RefreshError("Embed page is missing noindex. Refusing to write it.")
    credit = 'Chart by <a href="https://savingoptimizer.com/guides/data/grocery-price-tracker.html">Saving Optimizer</a>'
    if credit not in embed:
        raise RefreshError('Embed page is missing the "Saving Optimizer" credit link.')
    sitemap = SITEMAP_PATH.read_text(encoding="utf-8")
    if "embed/grocery-price-tracker.html" in sitemap:
        raise RefreshError("Embed URL is in sitemap.xml. Remove it before refreshing.")
    TRACKER_PATH.write_text(tracker, encoding="utf-8")
    EMBED_PATH.write_text(embed, encoding="utf-8")


def _check_date_replacement() -> None:
    sample = (
        '<time id="cpi-updated" datetime="2020-01-01">1 Jan 2020</time>'
        '<meta name="article:modified_time" content="2020-01-01"'
        '"dateModified": "2020-01-01"'
    )
    updated = replace_dates(sample, date(2026, 11, 24))
    expected = '<time id="cpi-updated" datetime="2026-11-24">24 Nov 2026</time>'
    if expected not in updated:
        raise RefreshError(f"Date replacement broke the time element: {updated}")


def _check_rounding() -> None:
    checks = (
        (Decimal("170.4"), Decimal("165.3"), Decimal("3.1")),
        (Decimal("197.7"), Decimal("193.8"), Decimal("2.0")),
        (Decimal("200.6"), Decimal("199.6"), Decimal("0.5")),
        (Decimal("164.4"), Decimal("156.7"), Decimal("4.9")),
        (Decimal("178.9"), Decimal("176.8"), Decimal("1.2")),
    )
    for current, previous, expected in checks:
        got = yoy_pct(current, previous)
        if got != expected:
            raise RefreshError(f"Rounding check failed: {current}/{previous} -> {got}, expected {expected}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zip",
        type=Path,
        help="Use an already downloaded 18100004-eng.zip instead of fetching it.",
    )
    parser.add_argument(
        "--retrieved",
        help="Retrieval date (YYYY-MM-DD). Defaults to today. Used only for the source line.",
    )
    args = parser.parse_args()
    _check_rounding()
    _check_date_replacement()
    if args.retrieved:
        retrieved = date.fromisoformat(args.retrieved)
    else:
        retrieved = date.today()
    try:
        if args.zip:
            if not args.zip.is_file():
                raise RefreshError(f"Zip not found: {args.zip}")
            values, vectors = load_series(args.zip)
        else:
            with tempfile.TemporaryDirectory(prefix="grocery-cpi-") as temporary:
                zip_path = Path(temporary) / "18100004-eng.zip"
                download_zip(zip_path)
                values, vectors = load_series(zip_path)
        latest = latest_complete_month(values)
        months = window_months(latest, 24)
        require_window(values, months)
        # Build both HTML blocks before any publish, so a template error
        # cannot leave a new CSV beside stale pages.
        tracker_block(values, latest, retrieved)
        embed_block(values, latest, retrieved)
        count = write_csv(values, vectors)
        write_pages(values, latest, retrieved)
    except RefreshError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    prior = shift_month(latest, -12)
    print(f"Latest month: {latest}")
    print(f"Retrieved: {retrieved.isoformat()}")
    print(f"CSV rows: {count} -> {CSV_PATH.relative_to(ROOT)}")
    for item in SERIES:
        current = values[item["product"]][latest]
        change = yoy_pct(current, values[item["product"]][prior])
        print(f"  {item['product']}: {format_index(current)}  {format_pct(change)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
