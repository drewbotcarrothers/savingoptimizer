#!/usr/bin/env python3
"""Build the paid-toolkit pages and wiring for savingoptimizer.com.

    python3 scripts/build-toolkits.py

Reads scripts/toolkits-config.json (prices, Payment Link URLs, hubs, top posts, lead-magnet form)
and scripts/toolkits-data.json (toolkit names, contents and file lists). Writes:
  toolkits/index.html               hub of all toolkits (indexable)
  toolkits/<slug>.html              one sales page per toolkit (indexable, no ads)
  toolkits/thank-you.php            noindex download page; reads PUBLIC_TOOLKIT_* env vars
and, idempotently, adds a nav + footer link on every page, a priced CTA on matching category hubs
and top posts, and the sales URLs to sitemap.xml. Paid PDFs and buyer download URLs never live in this repo.
"""
import json, os, re, html, glob, datetime
from urllib.parse import urlencode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, 'scripts/toolkits-config.json')))
DATA = json.load(open(os.path.join(ROOT, 'scripts/toolkits-data.json')))
SITE = 'https://savingoptimizer.com'
PRICE = CFG['price_display']
EMAIL = CFG['support_email']
TODAY = datetime.date.today().isoformat()
ORDER = ['groceries', 'household', 'subscriptions', 'phone-internet', 'utilities', 'housing', 'insurance', 'transportation',
         'money-admin', 'healthcare', 'kids', 'education', 'pets', 'travel', 'activities', 'weddings']
HUBNAME = {'food-groceries': 'Food & Groceries', 'transportation': 'Transportation', 'housing': 'Housing', 'utilities': 'Utilities', 'kids': 'Kids',
           'clothing': 'Clothing', 'personal-care': 'Personal Care', 'travel': 'Travel', 'personal-finance': 'Personal Finance', 'insurance': 'Insurance',
           'healthcare': 'Healthcare', 'household-items': 'Household Items and Supplies', 'pets': 'Pets', 'subscriptions': 'Subscriptions',
           'entertainment': 'Entertainment', 'students': 'Students', 'weddings': 'Weddings', 'events': 'Events', 'education': 'Education',
           'technology': 'Technology', 'internet': 'Internet', 'sports': 'Sports'}
TOPIC = {'groceries': 'your grocery bill', 'household': 'household and personal-care shopping', 'subscriptions': 'streaming, apps and other subscriptions',
         'phone-internet': 'phone, internet and TV bills', 'utilities': 'hydro, gas and water bills', 'housing': 'rent and housing costs',
         'insurance': 'home, auto, life and travel insurance', 'transportation': 'car, transit and fuel costs', 'money-admin': 'bank fees, TFSA, RRSP and FHSA room and your credit report',
         'healthcare': 'drug, dental, vision and other health costs', 'kids': 'the costs of raising kids', 'education': 'RESPs, tuition and student costs',
         'pets': 'pet costs', 'travel': 'trips in and out of Canada', 'activities': 'tickets, passes, sports and activities', 'weddings': 'wedding costs'}
NFA = 'Education only. Not financial, tax, legal, insurance or medical advice. No savings are guaranteed; results depend on your situation.'
e = lambda s: html.escape(str(s), quote=True)
def md(s):  # **bold** only
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', e(s))
def utm(content):
    return '?' + urlencode({**CFG['utm'], 'utm_content': content})
def read(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def write(p, s):
    full = os.path.join(ROOT, p); os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(s)

# ---------- 1. nav + footer link on every page (idempotent) ----------
def sitewide():
    n = 0
    for f in glob.glob(os.path.join(ROOT, '**/*.html'), recursive=True):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith(('.git', 'toolkits/')) or rel == 'about/andrew-carrothers.html': continue
        s = open(f, encoding='utf-8').read(); o = s
        p = '../' * rel.count('/')
        if 'data-toolkits-nav' not in s:
            s = re.sub(r'(<nav class="site-nav"[^>]*>\s*<ul>\s*<li><a href="[^"]*">Guides</a></li>)(\s*)',
                       lambda m: m.group(1) + m.group(2) + f'<li><a href="{p}toolkits/index.html" data-toolkits-nav>Toolkits ({PRICE})</a></li>' + (m.group(2) or ''), s, count=1)
        if 'data-toolkits-footer' not in s:
            s = re.sub(r'(<li><a href="[^"]*">All guides &amp; categories</a></li>)(\s*)',
                       lambda m: m.group(1) + m.group(2) + f'<li><a href="{p}toolkits/index.html" data-toolkits-footer>Savings toolkits ({PRICE} each)</a></li>' + (m.group(2) or ''), s, count=1)
        if s != o: open(f, 'w', encoding='utf-8').write(s); n += 1
    return n

def chrome():
    a = read('about/andrew.html')
    header = a[a.index('<a class="skip-link"'):a.index('</header>') + len('</header>')]
    footer = a[a.index('<footer class="site-footer">'):a.index('</footer>') + len('</footer>')]
    return header, footer

def head(title, desc, canonical, robots='index,follow,max-image-preview:large', extra='', og_image=None):
    og = f'\n  <meta property="og:image" content="{e(og_image)}">' if og_image else ''
    return f'''<!DOCTYPE html>
<html lang="en-CA">
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-B1DYC7P4D4"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());

    gtag('config', 'G-B1DYC7P4D4');
  </script>
  <!-- No ad code on toolkit pages, on purpose. -->
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <link rel="icon" href="../favicon.ico" sizes="16x16 32x32 48x48">
  <link rel="icon" href="../assets/favicon-32.png" type="image/png" sizes="32x32">
  <link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
  <link rel="manifest" href="../site.webmanifest">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/styles.css?v=7">
  <link rel="stylesheet" href="../css/toolkits.css?v=1">
  <link rel="canonical" href="{e(canonical)}">
  <meta name="author" content="Andrew">
  <meta name="theme-color" content="#0F7A4B">
  <meta name="robots" content="{robots}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Saving Optimizer">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:url" content="{e(canonical)}">
  <meta property="og:locale" content="en_CA">{og}
{extra}</head>
<body>
'''

def signup(content):
    lm = CFG['lead_magnet']
    ready = bool(lm.get('form_action')) and bool(lm.get('sender_mailing_address'))
    hidden = '' if ready else ' hidden data-signup-not-configured="no email provider or mailing address set in scripts/toolkits-config.json"'
    addr = e(lm.get('sender_mailing_address') or '[mailing address]')
    hf = ''.join(f'<input type="hidden" name="{e(k)}" value="{e(v)}">' for k, v in lm.get('hidden_fields', {}).items())
    hf += f'<input type="hidden" name="signup_source" value="{e(content)}">'
    return f'''
    <section class="tk-signup" id="free-sample" aria-labelledby="free-sample-h"{hidden}>
      <h2 id="free-sample-h">Free sample: the 30-minute subscription audit</h2>
      <p>Get a free 12-page excerpt of the Subscriptions Savings Toolkit 2027 by email. It has Chapters 1 and 2, a worked example, a decision guide, a call script, a worksheet and the yearly calendar.</p>
      <form action="{e(lm.get('form_action', ''))}" method="{e(lm.get('method', 'post'))}">
        <label for="tk-fname-{e(content)}">First name (optional)</label>
        <input type="text" id="tk-fname-{e(content)}" name="{e(lm['name_field'])}" autocomplete="given-name">
        <label for="tk-email-{e(content)}">Email</label>
        <input type="email" id="tk-email-{e(content)}" name="{e(lm['email_field'])}" autocomplete="email" required>
        <label class="tk-consent"><input type="checkbox" name="{e(lm['consent_field'])}" value="yes" required> <span>Yes, email me the free sample, plus Saving Optimizer emails with money-saving guides and news about new toolkits. I can unsubscribe at any time.</span></label>
        {hf}
        <button class="btn btn-primary" type="submit">Email me the free sample</button>
      </form>
      <p class="tk-fine">Emails are sent by {e(lm['sender_name'])}, {e(lm['sender_email'])}, {addr}. Every email has an unsubscribe link, or you can email {e(EMAIL)} to unsubscribe; requests are processed within 10 business days. The box above is unticked until you tick it. See the <a href="../privacy.html">privacy policy</a>.</p>
    </section>'''

def faq_html(faqs):
    return '\n'.join(f'        <div class="faq-item"><h3>{e(q)}</h3><p>{md(a)}</p></div>' for q, a in faqs)
def faq_ld(faqs):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'\*\*', '', a)}} for q, a in faqs]}
def ld(obj): return f'  <script type="application/ld+json">\n{json.dumps(obj, indent=1, ensure_ascii=False)}\n  </script>\n'

COMMON_FAQ = [
 ('Is this financial advice?', f"No. The toolkits are education only. They explain rules, give you the math and the words to use, and point to official sources. They aren't financial, tax, legal, insurance or medical advice, and they don't recommend any company or product. No savings are guaranteed."),
 ('What if it isn’t useful to me?', f"Email {EMAIL} within {CFG['refund_days']} days of purchase and you'll get a full refund. No forms."),
 ('Do I get updates?', "Yes. Buyers get free updated files for the 2027 edition, including an update when the CRA posts new yearly figures such as the 2027 TFSA and RRSP limits. The new download link goes to the email you used at checkout."),
 ('How do I get the files?', "Checkout is by Stripe. After you pay, you land on a download page with a folder link and a one-click zip. If anything goes wrong, email us and we'll send the link."),
 ('Who wrote it, and how?', "Andrew, the founder of Saving Optimizer. Each toolkit was drafted with AI assistance, then fact-checked against dated official Canadian sources listed at the back. Worked examples use example numbers and are labelled Example."),
 ('Can I share it?', "The files are for personal use by the purchaser. Please don't share or resell them."),
]

def sales_page(slug, header, footer):
    d = DATA[slug]; link = CFG['payment_links'][slug]
    url = f'{SITE}/toolkits/{slug}.html'
    hubs = CFG['hubs'][slug]
    hub_links = ', '.join(f'<a href="../guides/{h}.html">{e(HUBNAME[h])}</a>' for h in hubs)
    title = f"{d['title']}: scripts, worksheets and a calendar ({PRICE})"
    desc = f"A {d['pages']}-page Canadian toolkit for {TOPIC[slug]}: call scripts, worksheets, worked examples, a province guide and a 12-month calendar. {PRICE}, 30-day refund."
    faqs = [('Who is it for?', d['reader'][0].upper() + d['reader'][1:])] + COMMON_FAQ
    product = {'@context': 'https://schema.org', '@type': 'Product', 'name': d['title'], 'description': d['subtitle'],
               'image': f'{SITE}/assets/toolkits/{slug}-cover.webp', 'brand': {'@type': 'Brand', 'name': 'Saving Optimizer'},
               'offers': {'@type': 'Offer', 'price': CFG['price_amount'], 'priceCurrency': CFG['currency'], 'url': url, 'availability': 'https://schema.org/InStock'}}
    crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{SITE}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Toolkits', 'item': f'{SITE}/toolkits/'},
        {'@type': 'ListItem', 'position': 3, 'name': d['title'], 'item': url}]}
    buy = lambda where: f'<a class="btn btn-primary tk-buy" href="{e(link)}" rel="nofollow noopener" data-sku="{slug}" data-placement="{where}">Buy, {PRICE}</a>'
    inside = ''.join(f'<li>{md(x)}</li>' for x in d['inside'])
    chapters = ''.join(f'<li>{e(x)}</li>' for x in d['chapters'])
    files = ''.join(f'<li>{e(x)}</li>' for x in d['files'])
    body = f'''{header}

  <main id="main">
  <article class="article-wrap">
    <nav class="crumbs" aria-label="Breadcrumb">
    <ol>
      <li><a href="../index.html">Home</a></li>
      <li><a href="index.html">Toolkits</a></li>
      <li aria-current="page">{e(d['title'])}</li>
    </ol>
    </nav>
    <div class="tk-hero">
      <div>
        <p class="kicker">Savings toolkit · 2027 edition · Canada</p>
        <h1>{e(d['title'])}</h1>
        <p class="lede">{e(d['subtitle'])}</p>
        <p class="tk-price"><strong>{PRICE}</strong> one-time · PDF, Printables PDF and calendar file</p>
        <p>{buy('hero')}</p>
        <p class="tk-trust">{CFG['refund_days']}-day refund · Free updates to the 2027 edition · By <a href="../about/andrew.html" rel="author">Andrew</a></p>
      </div>
      <div><img src="../assets/toolkits/{slug}-cover.webp" width="560" height="724" alt="Cover of the {e(d['title'])}"></div>
    </div>

    <h2>What you get</h2>
    <ul class="tk-files">{files}</ul>
    <ul>{inside}</ul>

    <h2>The 10 chapters</h2>
    <ol class="tk-chapters">{chapters}</ol>
    <p><img src="../assets/toolkits/{slug}-contents.webp" width="560" height="724" alt="Contents page of the {e(d['title'])}" loading="lazy" style="max-width:420px;width:100%;height:auto;border:1px solid var(--border);border-radius:12px;"></p>

    <h2>Free guides vs the toolkit</h2>
    <div class="tk-two">
      <div class="tk-box"><h3>Free on Saving Optimizer</h3><p>Guides that explain {e(TOPIC[slug])}: what the rules are and what to look for. Start with the {hub_links} guides.</p></div>
      <div class="tk-box paid"><h3>In the toolkit ({PRICE})</h3><p>The tools to act on it: 8 call and email scripts with “if they say no” replies, 9 worksheets, 3 worked examples, 6 decision guides with the math shown, a guide for all 13 provinces and territories, a checklist and a 12-month calendar file.</p></div>
    </div>

    <h2>How it was checked</h2>
    <p>{e(d['checked'])}. The toolkit lists {d['sources']} dated sources at the back. Every worked example uses example numbers and is labelled Example. Prepared with AI assistance and fact-checked. <a href="../how-we-create-content.html">How we create content</a>.</p>

    <p>{buy('mid')}</p>
    <p class="tk-trust">{CFG['refund_days']}-day refund. Free updates to the 2027 edition, including the 2027 TFSA and RRSP figures when the CRA posts them.</p>

    <section class="article-faq" aria-labelledby="faq-heading">
      <h2 id="faq-heading">Frequently asked questions</h2>
      <div class="faq-list">
{faq_html(faqs)}
      </div>
    </section>

    <div class="article-cta"><p>{buy('bottom')} <a class="btn btn-ghost" href="index.html">See all 16 toolkits</a></p></div>
{signup('sales-' + slug)}
    <p class="author-box"><strong>About the author:</strong> <a href="../about/andrew.html">Andrew</a> is a personal finance expert, DIY investor and life optimizer based in Toronto, Canada.</p>
    <div class="disclosure"><p><strong>Note:</strong> {NFA} Saving Optimizer isn't affiliated with any company named in the toolkit.</p></div>
  </article>
  </main>
  {footer}
  <script src="../js/main.js?v=4" defer></script>
</body>
</html>
'''
    return head(title, desc, url, extra=ld(product) + ld(crumbs) + ld(faq_ld(faqs)), og_image=f'{SITE}/assets/toolkits/{slug}-cover.webp') + body

def hub_page(header, footer):
    url = f'{SITE}/toolkits/'
    cards = ''
    for s in ORDER:
        d = DATA[s]
        cards += f'''
        <a class="tk-card" href="{s}.html">
          <img src="../assets/toolkits/{s}-cover.webp" width="560" height="724" alt="Cover of the {e(d['title'])}" loading="lazy">
          <h3>{e(d['title'])}</h3>
          <p>For {e(TOPIC[s])}. {d['pages']} pages, plus Printables and a calendar file.</p>
          <span class="tk-card-price">{PRICE} · See what's inside →</span>
        </a>'''
    faqs = COMMON_FAQ
    items = {'@context': 'https://schema.org', '@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i, 'url': f'{SITE}/toolkits/{s}.html', 'name': DATA[s]['title']} for i, s in enumerate(ORDER, 1)]}
    body = f'''{header}

  <main id="main">
    <section class="page-intro compact">
      <div class="wrap">
        <nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="../index.html">Home</a></li><li aria-current="page">Toolkits</li></ol></nav>
        <p class="eyebrow">Savings toolkits · 2027 edition</p>
        <h1>Savings toolkits for Canadian households</h1>
        <p>The free guides on Saving Optimizer explain. Each toolkit is the kit you use to act: call and email scripts with replies for when they say no, worksheets, worked Canadian examples, decision guides with the math shown, a guide for all 13 provinces and territories, and a 12-month calendar file. {PRICE} each, one-time.</p>
      </div>
    </section>
    <section class="section" style="padding-top:1.25rem;">
      <div class="wrap">
        <div class="tk-grid">{cards}
        </div>
        <h2 style="margin-top:2.5rem;">Every toolkit includes</h2>
        <ul class="tk-files">
          <li>A 41 to 44 page PDF with a Start Here page and a 60-minute first pass</li>
          <li>8 scripts, each with 3 “if they say no” replies</li>
          <li>3 worked examples and 6 decision guides, with example numbers labelled Example</li>
          <li>A province and territory guide, 9 worksheets, a checklist and a 12-month calendar</li>
          <li>A Printables PDF and an .ics calendar file for Google, Outlook or Apple Calendar</li>
          <li>Dated official sources at the back of every toolkit</li>
        </ul>
        <p class="tk-trust">{CFG['refund_days']}-day refund · Free updates to the 2027 editions, including the 2027 TFSA and RRSP figures when the CRA posts them · By <a href="../about/andrew.html" rel="author">Andrew</a></p>
        <section class="article-faq" aria-labelledby="faq-heading">
          <h2 id="faq-heading">Frequently asked questions</h2>
          <div class="faq-list">
{faq_html(faqs)}
          </div>
        </section>
{signup('toolkits-hub')}
        <div class="disclosure"><p><strong>Note:</strong> {NFA}</p></div>
      </div>
    </section>
  </main>
  {footer}
  <script src="../js/main.js?v=4" defer></script>
</body>
</html>
'''
    desc = f'16 Canadian savings toolkits for 2027: scripts, worksheets, worked examples, province guides and a calendar file. {PRICE} each, 30-day refund.'
    return head(f'Savings toolkits for Canadian households ({PRICE} each)', desc, url, extra=ld(items) + ld(faq_ld(faqs))) + body

def thank_you(header, footer):
    skus = {s: DATA[s]['title'] for s in DATA}
    bundles = {k: {'name': v['name'], 'skus': v['skus']} for k, v in CFG.get('bundles', {}).items()}
    php_arr = lambda d: 'array(' + ', '.join(f"'{k}' => '{v.replace(chr(39), chr(92) + chr(39))}'" for k, v in d.items()) + ')'
    php_bundles = 'array(' + ', '.join(f"'{k}' => array('name' => '{v['name']}', 'skus' => array(" + ', '.join(f"'{x}'" for x in v['skus']) + '))' for k, v in bundles.items()) + ')'
    hdr = header.replace('<?', '&lt;?')
    return f'''<?php
/* Saving Optimizer toolkit thank-you page. noindex, not in the sitemap.
 * Stripe Payment Link "After payment" redirect: https://savingoptimizer.com/toolkits/thank-you.php?sku=<slug>&session_id={{CHECKOUT_SESSION_ID}}
 * Download URLs are NOT in this repo. They come from environment variables, e.g.
 *   PUBLIC_TOOLKIT_PETS_FOLDER_URL, PUBLIC_TOOLKIT_PETS_ZIP_URL   (slug upper-cased, "-" -> "_")
 * set on the host, or from an INI file outside the web root: <home>/.so-toolkit-links.ini with the same keys.
 * Generated by scripts/build-toolkits.py. */
declare(strict_types=1);
header('X-Robots-Tag: noindex, nofollow');
header('Cache-Control: no-store');
$SKUS = {php_arr(skus)};
$BUNDLES = {php_bundles};
$sku = isset($_GET['sku']) && is_string($_GET['sku']) ? strtolower($_GET['sku']) : '';
$ini = array();
if (!empty($_SERVER['DOCUMENT_ROOT'])) {{
    $f = dirname(rtrim((string) $_SERVER['DOCUMENT_ROOT'], '/')) . '/.so-toolkit-links.ini';
    if (is_readable($f)) {{ $p = parse_ini_file($f); if (is_array($p)) {{ $ini = $p; }} }}
}}
function so_link(string $slug, string $kind, array $ini): string {{
    $key = 'PUBLIC_TOOLKIT_' . strtoupper(str_replace('-', '_', $slug)) . '_' . $kind . '_URL';
    $v = getenv($key);
    if ($v === false || $v === '') {{ $v = isset($ini[$key]) ? (string) $ini[$key] : ''; }}
    return preg_match('#^https://#', $v) ? $v : '';
}}
$items = array();
if (isset($SKUS[$sku])) {{ $items = array($sku); }}
elseif (isset($BUNDLES[$sku])) {{ $items = $BUNDLES[$sku]['skus']; }}
function h(string $s): string {{ return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }}
?><!DOCTYPE html>
<html lang="en-CA">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Thank you: your Saving Optimizer toolkit</title>
  <meta name="robots" content="noindex, nofollow">
  <link rel="icon" href="../favicon.ico" sizes="16x16 32x32 48x48">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/styles.css?v=7">
  <link rel="stylesheet" href="../css/toolkits.css?v=1">
</head>
<body>
{hdr}
  <main id="main">
  <article class="article-wrap">
    <p class="kicker">Thank you</p>
    <h1>Thanks for your order</h1>
<?php if (!$items): ?>
    <p>We couldn't tell which toolkit this page is for. Your download link will also come by email. If it hasn't arrived within 24 hours, email <a href="mailto:{EMAIL}">{EMAIL}</a> with the email you used at checkout.</p>
<?php else: foreach ($items as $s): $folder = so_link($s, 'FOLDER', $ini); $zip = so_link($s, 'ZIP', $ini); ?>
    <section class="tk-box paid" style="margin:1.5rem 0;">
      <h2 style="margin-top:0;"><?= h($SKUS[$s] ?? $s) ?></h2>
      <p><strong>Start here:</strong> open the main PDF and read the Start Here page (page 2) first. It walks you through a 60-minute first pass.</p>
<?php if ($folder || $zip): ?>
      <p><?php if ($folder): ?><a class="btn btn-primary" href="<?= h($folder) ?>" rel="noopener noreferrer">Open the download folder</a> <?php endif; ?><?php if ($zip): ?><a class="btn btn-ghost" href="<?= h($zip) ?>" rel="noopener noreferrer">Download the zip</a><?php endif; ?></p>
<?php else: ?>
      <p>Your download link is on its way by email. If it hasn't arrived within 24 hours, email <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
<?php endif; ?>
    </section>
<?php endforeach; endif; ?>
    <p>Bookmark this page or keep your Stripe receipt. Free updates to the 2027 edition go to the email you used at checkout.</p>
    <p>Questions, or want a refund? Email <a href="mailto:{EMAIL}">{EMAIL}</a> within {CFG['refund_days']} days of purchase for a full refund.</p>
    <div class="disclosure"><p><strong>Note:</strong> {NFA} For personal use by the purchaser; please don't share or resell the files.</p></div>
  </article>
  </main>
  {footer}
  <script src="../js/main.js?v=4" defer></script>
</body>
</html>
'''

def cta_box(slug, prefix, content, heading_tag='h2'):
    d = DATA[slug]
    return (f'<!-- toolkit-cta:start -->\n    <aside class="toolkit-cta" aria-label="Paid toolkit">\n'
            f'      <img src="{prefix}assets/toolkits/{slug}-cover.webp" width="560" height="724" alt="" loading="lazy">\n'
            f'      <div><p class="kicker">Paid toolkit · {PRICE}</p><{heading_tag}>{e(d["title"])}</{heading_tag}>\n'
            f'      <p>Ready to act on {e(TOPIC[slug])}? Get 8 scripts with replies, 9 worksheets, worked Canadian examples and a 12-month calendar file in one {d["pages"]}-page toolkit.</p>\n'
            f'      <p><a class="btn btn-primary" href="{prefix}toolkits/{slug}.html{utm(content)}">Get the toolkit, {PRICE}</a></p>\n'
            f'      <p class="toolkit-cta-note">{CFG["refund_days"]}-day refund. Education only, not financial advice.</p></div>\n    </aside>\n    <!-- toolkit-cta:end -->\n    ')

def add_css(s, prefix):
    if 'css/toolkits.css' in s: return s
    return re.sub(r'(<link rel="stylesheet" href="[./]*css/styles\.css\?v=\d+">)', lambda m: m.group(1) + f'\n  <link rel="stylesheet" href="{prefix}css/toolkits.css?v=1">', s, count=1)

def strip_cta(s): return re.sub(r'<!-- toolkit-cta:start -->.*?<!-- toolkit-cta:end -->\n    ', '', s, flags=re.S)

def wire_hubs_and_posts():
    done = []
    for slug, hubs in CFG['hubs'].items():
        for h in hubs:
            p = f'guides/{h}.html'; s = strip_cta(read(p))
            i = s.index('<section class="page-intro'); j = s.index('</section>', i) + len('</section>')
            s = s[:j] + '\n    <div class="wrap">' + cta_box(slug, '../', f'hub-{h}').rstrip() + '\n    </div>' + s[j:]
            s = s.replace('<div class="wrap"><!-- toolkit-cta:start -->', '<div class="wrap"><!-- toolkit-cta:start -->')
            write(p, add_css(s, '../')); done.append(p)
        for a in CFG['top_posts'][slug]:
            p = f'guides/articles/{a}'; s = strip_cta(read(p))
            k = s.index('<div class="article-cta">')
            s = s[:k] + cta_box(slug, '../../', 'post-' + a.replace('.html', '')) + s[k:]
            write(p, add_css(s, '../../')); done.append(p)
    return done

def strip_hub_wrappers(s):  # make hub insertion idempotent
    return re.sub(r'\n    <div class="wrap">\s*\n    </div>', '', s)

def sitemap():
    s = read('sitemap.xml')
    urls = [f'{SITE}/toolkits/'] + [f'{SITE}/toolkits/{x}.html' for x in ORDER]
    s = re.sub(r'  <url><loc>https://savingoptimizer\.com/toolkits/[^<]*</loc>.*?</url>\n', '', s)
    add = ''.join(f'  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>0.9</priority></url>\n' for u in urls)
    write('sitemap.xml', s.replace('</urlset>', add + '</urlset>'))

if __name__ == '__main__':
    n = sitewide()
    header, footer = chrome()
    write('toolkits/index.html', hub_page(header, footer))
    for s in DATA: write(f'toolkits/{s}.html', sales_page(s, header, footer))
    write('toolkits/thank-you.php', thank_you(header, footer))
    # hubs: remove any earlier wrapper before re-inserting
    for hs in CFG['hubs'].values():
        for h in hs:
            p = f'guides/{h}.html'; s = read(p)
            s = re.sub(r'\n    <div class="wrap"><!-- toolkit-cta:start -->.*?<!-- toolkit-cta:end -->\s*</div>', '', s, flags=re.S)
            write(p, s)
    wired = wire_hubs_and_posts()
    sitemap()
    print(f'nav/footer updated on {n} pages; wrote toolkits/ (hub, {len(DATA)} sales pages, thank-you.php); CTAs on {len(wired)} pages; sitemap +{len(DATA) + 1}')
