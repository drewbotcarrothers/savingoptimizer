#!/usr/bin/env python3
"""Local end-to-end test for toolkits/stripe-webhook.php and toolkits/thank-you.php.

    PHP=/path/to/php python3 scripts/test-stripe-webhook.py

Starts a fake SMTP server and `php -S` on a temp copy of toolkits/, then posts signed sample
checkout.session.completed events. The HMAC is computed here in Python, independently of the PHP code.
Uses only a throwaway test secret; no network, no real Stripe or mailbox.
"""
import hashlib, hmac, json, os, re, shutil, socket, socketserver, subprocess, sys, tempfile, threading, time, urllib.request, urllib.error, base64, quopri, email

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHP = os.environ.get('PHP', 'php')
CFG = json.load(open(os.path.join(ROOT, 'scripts/toolkits-config.json')))
SECRET = 'whsec_local_test_only_' + 'x' * 16
PL = {v: k for k, v in CFG['payment_link_ids'].items()}   # sku -> plink
MAILS, FAIL = [], {'rcpt': set()}
results = []

def check(name, cond, detail=''):
    results.append((name, bool(cond)))
    print(('PASS ' if cond else 'FAIL ') + name + (f'  [{detail}]' if detail and not cond else ''))

class SMTP(socketserver.StreamRequestHandler):
    def handle(self):
        w = lambda s: self.wfile.write((s + '\r\n').encode())
        w('220 fake.smtp ready'); frm = rcpt = None; authed = False
        while True:
            line = self.rfile.readline().decode().rstrip('\r\n')
            if not line: return
            up = line.upper()
            if up.startswith('EHLO'): w('250-fake.smtp'); w('250 AUTH LOGIN')
            elif up == 'AUTH LOGIN':
                w('334 VXNlcm5hbWU6'); u = base64.b64decode(self.rfile.readline().strip()).decode()
                w('334 UGFzc3dvcmQ6'); p = base64.b64decode(self.rfile.readline().strip()).decode()
                authed = (u, p) == ('contact@savingoptimizer.com', 'test-pass'); w('235 ok' if authed else '535 bad auth')
            elif up.startswith('MAIL FROM:'): frm = line[10:].strip('<>'); w('250 ok' if authed else '530 auth first')
            elif up.startswith('RCPT TO:'):
                rcpt = line[8:].strip('<>'); w('550 rejected' if rcpt in FAIL['rcpt'] else '250 ok')
            elif up == 'DATA':
                w('354 go'); buf = []
                while True:
                    l = self.rfile.readline().decode()
                    if l in ('.\r\n', '.\n'): break
                    buf.append(l[1:] if l.startswith('..') else l)
                MAILS.append({'from': frm, 'to': rcpt, 'raw': ''.join(buf)}); w('250 queued')
            elif up == 'QUIT': w('221 bye'); return
            else: w('500 ?')

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def body_of(raw):
    m = email.message_from_string(raw); out = {}
    for part in (m.walk() if m.is_multipart() else [m]):
        ct = part.get_content_type()
        if ct in ('text/plain', 'text/html'): out[ct] = part.get_payload(decode=True).decode('utf-8')
    out['subject'] = m['Subject']; out['from'] = m['From']; out['reply-to'] = m['Reply-To']
    return out

def main():
    tmp = tempfile.mkdtemp(prefix='so-wh-')
    try:
        home = os.path.join(tmp, 'domains', 'savingoptimizer.com'); doc = os.path.join(home, 'public_html')
        shutil.copytree(os.path.join(ROOT, 'toolkits'), os.path.join(doc, 'toolkits'), ignore=shutil.ignore_patterns('*.html'))
        smtp_port, http_port = free_port(), free_port()
        cfgfile = os.path.join(home, '.so-webhook-config.php')
        open(cfgfile, 'w').write(f"""<?php return array('stripe_webhook_secret' => '{SECRET}', 'transport' => 'auto',
          'smtp' => array('host' => '127.0.0.1', 'port' => {smtp_port}, 'secure' => 'none', 'user' => 'contact@savingoptimizer.com', 'pass' => 'test-pass'));""")
        srv = socketserver.ThreadingTCPServer(('127.0.0.1', smtp_port), SMTP); srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        php = subprocess.Popen([PHP, '-S', f'127.0.0.1:{http_port}', '-t', doc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        base = f'http://127.0.0.1:{http_port}'
        for _ in range(50):
            try: urllib.request.urlopen(base + '/toolkits/thank-you.php'); break
            except Exception: time.sleep(0.1)

        def post(event, secret=SECRET, ts=None, raw=None, header=None):
            payload = raw if raw is not None else json.dumps(event)
            ts = int(time.time()) if ts is None else ts
            sig = hmac.new(secret.encode(), f'{ts}.{payload}'.encode(), hashlib.sha256).hexdigest()
            req = urllib.request.Request(base + '/toolkits/stripe-webhook.php', data=payload.encode(), method='POST',
                                         headers={'Stripe-Signature': header or f't={ts},v1={sig}', 'Content-Type': 'application/json'})
            try: r = urllib.request.urlopen(req); return r.status, r.read().decode().strip()
            except urllib.error.HTTPError as e: return e.code, e.read().decode().strip()

        def ev(sid, sku=None, plink=None, md=None, status='paid', etype='checkout.session.completed', mail='buyer@example.com'):
            return {'id': 'evt_' + sid, 'type': etype, 'livemode': False, 'data': {'object': {
                'id': sid, 'object': 'checkout.session', 'payment_link': plink if plink is not None else PL.get(sku), 'payment_status': status,
                'amount_total': 3900 if sku == 'bundle-all' else 1500, 'currency': 'cad', 'livemode': False, 'metadata': md or {},
                'customer_details': {'email': mail, 'name': 'Sam Example'}}}}

        # 1. signature checks
        c, m = post(ev('cs_test_sig', 'pets'), secret='whsec_wrong'); check('wrong secret -> 400', c == 400 and 'no matching' in m, m)
        c, m = post(ev('cs_test_old', 'pets'), ts=int(time.time()) - 301); check('timestamp 301 s old -> 400', c == 400 and 'tolerance' in m, m)
        c, m = post(None, raw='{}', header='v1=abc'); check('malformed header -> 400', c == 400 and 'malformed' in m, m)
        good = json.dumps(ev('cs_test_tamper', 'pets')); ts = int(time.time())
        sig = hmac.new(SECRET.encode(), f'{ts}.{good}'.encode(), hashlib.sha256).hexdigest()
        c, m = post(None, raw=good.replace('"amount_total": 1500', '"amount_total": 1'), header=f't={ts},v1={sig}'); check('tampered body -> 400', c == 400 and good.count('1500') == 1, m)
        c, m = post(None, raw=good, header=f't={ts},v1={"0"*64},v1={sig}'); check('second v1 signature accepted (secret rotation)', c == 200, m)
        MAILS.clear()
        # 2. filtering
        c, m = post(ev('cs_test_other', plink='plink_OTHERBRAND', md={'brand': 'cccf', 'sku': 'pets'})); check('other brand ignored, 200', c == 200 and 'not a Saving Optimizer' in m, m)
        c, m = post(ev('cs_test_type', 'pets', etype='payment_intent.succeeded')); check('other event type ignored, 200', c == 200 and 'ignored' in m, m)
        c, m = post(ev('cs_test_unpaid', 'pets', status='unpaid')); check('unpaid session ignored, 200', c == 200 and 'payment_status' in m, m)
        check('no email for ignored events', not MAILS, len(MAILS))
        # 3. single SKU by payment_link id
        c, m = post(ev('cs_test_pets', 'pets')); check('pets by payment_link -> 200 ok: pets', c == 200 and m == 'ok: pets', m)
        check('two emails (buyer + notice)', len(MAILS) == 2 and MAILS[0]['to'] == 'buyer@example.com' and MAILS[1]['to'] == 'contact@savingoptimizer.com', [x['to'] for x in MAILS])
        b = body_of(MAILS[0]['raw']); dl = CFG['downloads']['pets']
        check('buyer email: From contact@savingoptimizer.com', 'contact@savingoptimizer.com' in (b['from'] or ''), b['from'])
        check('buyer email: subject', b['subject'] == 'Your download links: Pet Cost Toolkit 2027', b['subject'])
        for ct in ('text/plain', 'text/html'):
            t = b.get(ct, '')
            check(f'buyer email {ct}: pets folder + zip links', dl['folder_url'] in t and dl['zip_url'].replace('&', '&amp;' if ct == 'text/html' else '&') in t)
            check(f'buyer email {ct}: refund + support + updates + thank-you link', '30-day refund' in t and 'contact@savingoptimizer.com' in t and 'Free updates to the 2027 edition' in t and 'thank-you.php?sku=pets' in t)
            check(f'buyer email {ct}: no other SKU links', CFG['downloads']['kids']['folder_url'] not in t)
        n = body_of(MAILS[1]['raw']); check('notice email: sku, total, session', 'pets' in n['subject'] and '15.00 CAD' in n['text/plain'] and 'cs_test_pets' in n['text/plain'], n['subject'])
        open(os.path.join(ROOT, 'scripts', '.webhook-test-sample-email.txt'), 'w').write(b['text/plain'])
        # 4. idempotency
        MAILS.clear(); c, m = post(ev('cs_test_pets', 'pets')); check('same session again -> 200 duplicate, no email', c == 200 and 'duplicate' in m and not MAILS, m)
        # 5. bundle via metadata fallback (payment_link not in the map)
        MAILS.clear(); c, m = post(ev('cs_test_bundle', 'bundle-all', plink='', md={'brand': 'savingoptimizer', 'sku': 'bundle-all'}))
        bt = body_of(MAILS[0]['raw'])['text/plain'] if MAILS else ''
        check('bundle by metadata -> ok, all 17 folder links', c == 200 and all(CFG['downloads'][s]['folder_url'] in bt for s in CFG['downloads']), m)
        # 6. SMTP failure -> 500, claim released, retry succeeds
        FAIL['rcpt'].add('bounce@example.com'); MAILS.clear()
        c, m = post(ev('cs_test_fail', 'kids', mail='bounce@example.com')); check('SMTP reject -> 500 (Stripe retries)', c == 500, m)
        FAIL['rcpt'].clear(); c, m = post(ev('cs_test_fail', 'kids', mail='bounce@example.com')); check('retry after failure sends', c == 200 and m == 'ok: kids' and len(MAILS) == 2, m)
        log = open(os.path.join(home, '.so-webhook-data', 'webhook.log')).read()
        check('state + log written above public_html', 'cs_test_pets pets customer=sent' in log and os.path.exists(os.path.join(home, '.so-webhook-data', 'sent', 'cs_test_pets.json')))
        # 7. GET is refused; thank-you page links
        try: urllib.request.urlopen(base + '/toolkits/stripe-webhook.php'); code = 200
        except urllib.error.HTTPError as e: code = e.code
        check('GET webhook -> 405', code == 405, code)
        def page(q): return urllib.request.urlopen(base + '/toolkits/thank-you.php' + q).read().decode()
        p = page('?sku=pets'); check('thank-you pets: 2 Drive links', len(re.findall(r'href="https://drive\.google\.com', p)) == 2, len(re.findall(r'href="https://drive\.google\.com', p)))
        p = page('?sku=bundle-all'); check('thank-you bundle: 34 Drive links', len(re.findall(r'href="https://drive\.google\.com', p)) == 34)
        p = page('?sku=nope'); check('thank-you unknown sku: fallback, no links', "couldn't tell" in p and 'drive.google.com' not in p)
        php.terminate(); php.wait(5); srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [n for n, ok in results if not ok]
    print(f'\n{len(results) - len(bad)}/{len(results)} passed')
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
