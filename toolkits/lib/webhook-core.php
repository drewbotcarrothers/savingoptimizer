<?php
/* Saving Optimizer toolkits: Stripe webhook core. Used by toolkits/stripe-webhook.php and scripts/test-stripe-webhook.py.
 * No secrets in this file. The signing secret and any SMTP password come from a config file outside the web root
 * (see scripts/so-webhook-config.sample.php and scripts/TOOLKITS.md). */
declare(strict_types=1);

/** Verify a Stripe-Signature header (HMAC-SHA256 of "<t>.<payload>", scheme v1). Returns '' when valid, else the reason. */
function so_wh_verify(string $payload, string $header, string $secret, int $tolerance = 300, ?int $now = null): string {
    if ($secret === '') { return 'no signing secret configured'; }
    $t = null; $sigs = array();
    foreach (explode(',', $header) as $part) {
        $kv = explode('=', trim($part), 2);
        if (count($kv) !== 2) { continue; }
        if ($kv[0] === 't' && ctype_digit($kv[1])) { $t = (int) $kv[1]; }
        elseif ($kv[0] === 'v1' && $kv[1] !== '') { $sigs[] = $kv[1]; }
    }
    if ($t === null || !$sigs) { return 'malformed Stripe-Signature header'; }
    $now = $now ?? time();
    if ($tolerance > 0 && abs($now - $t) > $tolerance) { return 'timestamp outside tolerance'; }
    $expected = hash_hmac('sha256', $t . '.' . $payload, $secret);
    foreach ($sigs as $s) { if (hash_equals($expected, $s)) { return ''; } }
    return 'no matching v1 signature';
}

/** Saving Optimizer SKU for a Checkout Session, or '' for any other brand on the shared Stripe account. */
function so_wh_resolve_sku(array $session, array $D): string {
    $known = function (string $s) use ($D): bool { return isset($D['skus'][$s]) || isset($D['bundles'][$s]); };
    $pl = is_string($session['payment_link'] ?? null) ? $session['payment_link'] : '';
    if ($pl !== '' && isset($D['payment_link_ids'][$pl]) && $known((string) $D['payment_link_ids'][$pl])) {
        return (string) $D['payment_link_ids'][$pl];
    }
    $md = is_array($session['metadata'] ?? null) ? $session['metadata'] : array();
    if (($md['brand'] ?? '') === 'savingoptimizer' && is_string($md['sku'] ?? null) && $known($md['sku'])) { return $md['sku']; }
    return '';
}

/** Rows to deliver: [title, folder_url, zip_url]. A bundle lists its all-in-one zip first, then each toolkit. */
function so_wh_items(string $sku, array $D): array {
    $row = function (string $s, string $title) use ($D): array {
        return array($title, (string) ($D['downloads'][$s]['folder_url'] ?? ''), (string) ($D['downloads'][$s]['zip_url'] ?? ''));
    };
    if (isset($D['bundles'][$sku])) {
        $rows = array($row($sku, 'Everything in one zip: ' . $D['bundles'][$sku]['name']));
        foreach ($D['bundles'][$sku]['skus'] as $s) { $rows[] = $row($s, (string) $D['skus'][$s]); }
        return $rows;
    }
    return array($row($sku, (string) $D['skus'][$sku]));
}

function so_wh_product_name(string $sku, array $D): string {
    return isset($D['bundles'][$sku]) ? (string) $D['bundles'][$sku]['name'] : (string) $D['skus'][$sku];
}

/** Customer email: ['subject' => ..., 'text' => ..., 'html' => ...]. Wording matches launch/offer-brief.md. */
function so_wh_customer_email(string $sku, array $session, array $D): array {
    $e = function (string $s): string { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); };
    $support = (string) $D['support_email'];
    $days = (int) $D['refund_days'];
    $name = trim((string) ($session['customer_details']['name'] ?? ''));
    $first = $name !== '' ? preg_split('/\s+/', $name)[0] : '';
    $hi = $first !== '' ? 'Hi ' . $first . ',' : 'Hi there,';
    $product = so_wh_product_name($sku, $D);
    $page = rtrim((string) $D['site'], '/') . '/toolkits/thank-you.php?sku=' . rawurlencode($sku);
    $ref = (string) ($session['id'] ?? '');
    $refund = "{$days}-day refund: if a toolkit isn't useful to you, email {$support} within {$days} days of purchase and we'll refund you in full. No forms, and you don't need to send anything back.";
    $updates = "Free updates to the 2027 edition: you get updated files free for the life of the 2027 edition, including an update when the CRA posts the 2027 TFSA and RRSP figures. We'll email the new download link to this address.";
    $note = "Education only. Not financial, tax, legal, insurance or medical advice. No savings are guaranteed; results depend on your situation. For personal use by the purchaser; please don't share or resell the files.";
    $start = 'Start here: open the main PDF and read the Start Here page (page 2) first. It walks you through a 60-minute first pass.';

    $t = "{$hi}\n\nThanks for buying the {$product}. Your download links are below.\n\n";
    $h = '<!DOCTYPE html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>' . $e($product) . '</title></head>'
       . '<body style="margin:0;padding:0;background:#f5f7f6;font-family:Arial,Helvetica,sans-serif;color:#1d2b27;">'
       . '<div style="max-width:600px;margin:0 auto;padding:24px 16px;"><div style="background:#ffffff;border-radius:10px;padding:24px;">'
       . '<p style="margin:0 0 4px;font-size:13px;color:#4a6b61;text-transform:uppercase;letter-spacing:.04em;">Saving Optimizer</p>'
       . '<h1 style="margin:0 0 16px;font-size:22px;line-height:1.3;">Your download links</h1>'
       . '<p style="font-size:15px;line-height:1.6;">' . $e($hi) . '</p>'
       . '<p style="font-size:15px;line-height:1.6;">Thanks for buying the <strong>' . $e($product) . '</strong>. Your download links are below.</p>';
    foreach (so_wh_items($sku, $D) as [$title, $folder, $zip]) {
        $t .= "{$title}\n  Open the folder: {$folder}\n  Download the zip: {$zip}\n\n";
        $h .= '<div style="border:1px solid #d8e3df;border-radius:8px;padding:12px 14px;margin:0 0 12px;">'
            . '<p style="margin:0 0 8px;font-size:15px;font-weight:bold;">' . $e($title) . '</p>'
            . '<p style="margin:0;font-size:14px;"><a href="' . $e($folder) . '" style="color:#0f6b4f;font-weight:bold;">Open the folder</a>'
            . ' &nbsp;&middot;&nbsp; <a href="' . $e($zip) . '" style="color:#0f6b4f;font-weight:bold;">Download the zip</a></p></div>';
    }
    $t .= "{$start}\n\nYour download page (bookmark it): {$page}\n\n{$refund}\n\n{$updates}\n\nQuestions? Reply to this email or write to {$support}.\n\nAndrew\nSaving Optimizer\n\n{$note}\n" . ($ref !== '' ? "Order reference: {$ref}\n" : '');
    $h .= '<p style="font-size:15px;line-height:1.6;">' . $e($start) . '</p>'
        . '<p style="font-size:15px;line-height:1.6;">Your download page (bookmark it): <a href="' . $e($page) . '" style="color:#0f6b4f;">' . $e($page) . '</a></p>'
        . '<p style="font-size:14px;line-height:1.6;">' . $e($refund) . '</p>'
        . '<p style="font-size:14px;line-height:1.6;">' . $e($updates) . '</p>'
        . '<p style="font-size:15px;line-height:1.6;">Questions? Reply to this email or write to <a href="mailto:' . $e($support) . '" style="color:#0f6b4f;">' . $e($support) . '</a>.</p>'
        . '<p style="font-size:15px;line-height:1.6;">Andrew<br>Saving Optimizer</p></div>'
        . '<p style="font-size:12px;line-height:1.5;color:#4a6b61;padding:12px 4px 0;">' . $e($note) . ($ref !== '' ? '<br>Order reference: ' . $e($ref) : '') . '</p>'
        . '</div></body></html>';
    return array('subject' => 'Your download links: ' . $product, 'text' => $t, 'html' => $h);
}

/** Internal sale notice for the support inbox. */
function so_wh_notice_email(string $sku, array $session, array $D, string $delivery): array {
    $amt = isset($session['amount_total']) ? number_format(((int) $session['amount_total']) / 100, 2) . ' ' . strtoupper((string) ($session['currency'] ?? '')) : '?';
    $mode = !empty($session['livemode']) ? 'live' : 'TEST';
    $t = "New Saving Optimizer toolkit sale ({$mode}).\n\nProduct: " . so_wh_product_name($sku, $D) . " (sku {$sku})\nTotal: {$amt}\n"
       . 'Customer: ' . (string) ($session['customer_details']['name'] ?? '') . ' <' . (string) ($session['customer_details']['email'] ?? '') . ">\n"
       . 'Checkout Session: ' . (string) ($session['id'] ?? '') . "\nDownload-link email to the customer: {$delivery}\n";
    return array('subject' => "Toolkit sale: {$sku} ({$amt})" . ($mode === 'TEST' ? ' [test]' : ''), 'text' => $t, 'html' => null);
}

function so_wh_hdr(string $s): string { return preg_match('/[^\x20-\x7e]/', $s) ? '=?UTF-8?B?' . base64_encode($s) . '?=' : $s; }

/** Build a MIME message. Returns [headers-without-To/Subject, body]. */
function so_wh_mime(array $cfg, string $subject, string $text, ?string $html, string $replyTo): array {
    $from = (string) $cfg['from_email'];
    $domain = substr(strrchr($from, '@') ?: '@localhost', 1);
    $hs = array('From: ' . so_wh_hdr((string) ($cfg['from_name'] ?? 'Saving Optimizer')) . ' <' . $from . '>', 'Reply-To: ' . $replyTo,
                'Date: ' . date('r'), 'Message-ID: <' . bin2hex(random_bytes(12)) . '@' . $domain . '>', 'MIME-Version: 1.0');
    $qp = function (string $s): string { return quoted_printable_encode(str_replace(array("\r\n", "\r"), "\n", $s)); };
    if ($html === null) {
        $hs[] = 'Content-Type: text/plain; charset=UTF-8'; $hs[] = 'Content-Transfer-Encoding: quoted-printable';
        return array($hs, $qp($text));
    }
    $b = 'so_' . bin2hex(random_bytes(10));
    $hs[] = 'Content-Type: multipart/alternative; boundary="' . $b . '"';
    $body = "--{$b}\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n" . $qp($text)
          . "\r\n--{$b}\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n" . $qp($html) . "\r\n--{$b}--\r\n";
    return array($hs, $body);
}

/** Minimal SMTP client (implicit TLS on 465 or STARTTLS on 587, AUTH LOGIN). Returns '' on success, else the error. */
function so_wh_smtp(array $s, string $from, string $to, string $message): string {
    $secure = (string) ($s['secure'] ?? 'ssl');
    $ctx = stream_context_create(array('ssl' => array('verify_peer' => true, 'verify_peer_name' => true)));
    $fp = @stream_socket_client(($secure === 'ssl' ? 'ssl://' : 'tcp://') . $s['host'] . ':' . (int) $s['port'], $errno, $errstr, 15, STREAM_CLIENT_CONNECT, $ctx);
    if (!$fp) { return "SMTP connect failed: {$errstr}"; }
    stream_set_timeout($fp, 30);
    $step = function (?string $line, array $ok, string $label) use ($fp): string {
        if ($line !== null) { fwrite($fp, $line . "\r\n"); }
        $r = '';
        while (($l = fgets($fp, 2048)) !== false) { $r .= $l; if (strlen($l) < 4 || $l[3] !== '-') { break; } }
        return in_array((int) substr($r, 0, 3), $ok, true) ? '' : "SMTP {$label} failed: " . trim(substr($r, 0, 200));
    };
    $host = substr(strrchr($from, '@') ?: '@localhost', 1);
    $err = $step(null, array(220), 'greeting') ?: $step('EHLO ' . $host, array(250), 'EHLO');
    if (!$err && $secure === 'starttls') {
        $err = $step('STARTTLS', array(220), 'STARTTLS');
        if (!$err && !stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLSv1_2_CLIENT | STREAM_CRYPTO_METHOD_TLSv1_3_CLIENT)) { $err = 'SMTP TLS handshake failed'; }
        if (!$err) { $err = $step('EHLO ' . $host, array(250), 'EHLO'); }
    }
    if (!$err && (string) ($s['user'] ?? '') !== '') {
        $err = $step('AUTH LOGIN', array(334), 'AUTH') ?: $step(base64_encode((string) $s['user']), array(334), 'AUTH user')
            ?: $step(base64_encode((string) ($s['pass'] ?? '')), array(235), 'AUTH password');
    }
    if (!$err) { $err = $step('MAIL FROM:<' . $from . '>', array(250), 'MAIL FROM') ?: $step('RCPT TO:<' . $to . '>', array(250, 251), 'RCPT TO') ?: $step('DATA', array(354), 'DATA'); }
    if (!$err) {
        $data = preg_replace('/^\./m', '..', preg_replace("/\r?\n/", "\r\n", $message));
        $err = $step($data . "\r\n.", array(250), 'message');
    }
    $step('QUIT', array(221), 'QUIT');
    fclose($fp);
    return $err;
}

/** Send one email with the configured transport. Returns '' on success, else the error. */
function so_wh_send(array $cfg, string $to, array $mail, string $replyTo): string {
    if (!filter_var($to, FILTER_VALIDATE_EMAIL) || preg_match('/[\r\n]/', $to)) { return 'invalid recipient'; }
    [$hs, $body] = so_wh_mime($cfg, $mail['subject'], $mail['text'], $mail['html'], $replyTo);
    $from = (string) $cfg['from_email'];
    $smtp = is_array($cfg['smtp'] ?? null) ? $cfg['smtp'] : array();
    $transport = (string) ($cfg['transport'] ?? 'auto');
    if ($transport === 'auto') { $transport = ((string) ($smtp['pass'] ?? '')) !== '' ? 'smtp' : 'mail'; }
    if ($transport === 'smtp') {
        $msg = 'To: ' . $to . "\r\nSubject: " . so_wh_hdr($mail['subject']) . "\r\n" . implode("\r\n", $hs) . "\r\n\r\n" . $body;
        return so_wh_smtp($smtp + array('host' => 'smtp.hostinger.com', 'port' => 465, 'secure' => 'ssl', 'user' => $from), $from, $to, $msg);
    }
    if ($transport === 'mail') {
        return mail($to, so_wh_hdr($mail['subject']), str_replace("\r\n", "\n", $body), implode("\r\n", $hs), '-f' . $from) ? '' : 'mail() returned false';
    }
    return 'unknown transport ' . $transport;
}

function so_wh_log(string $dir, string $line): void {
    @file_put_contents($dir . '/webhook.log', gmdate('c') . ' ' . $line . "\n", FILE_APPEND | LOCK_EX);
}

/** Handle one webhook request. Returns [http_status, message]. */
function so_wh_handle(string $payload, string $sigHeader, array $cfg, array $D, ?int $now = null): array {
    $err = so_wh_verify($payload, $sigHeader, (string) ($cfg['stripe_webhook_secret'] ?? ''), (int) ($cfg['tolerance'] ?? 300), $now);
    if ($err !== '') { return array(400, 'signature: ' . $err); }
    $ev = json_decode($payload, true);
    if (!is_array($ev) || !isset($ev['type'])) { return array(400, 'bad JSON'); }
    if ($ev['type'] !== 'checkout.session.completed') { return array(200, 'ignored: event type ' . $ev['type']); }
    $s = $ev['data']['object'] ?? null;
    if (!is_array($s)) { return array(400, 'no session object'); }
    $sku = so_wh_resolve_sku($s, $D);
    if ($sku === '') { return array(200, 'ignored: not a Saving Optimizer purchase'); }

    $dir = (string) $cfg['data_dir'];
    if (!is_dir($dir . '/sent') && !@mkdir($dir . '/sent', 0700, true) && !is_dir($dir . '/sent')) { return array(500, 'data dir not writable'); }
    $sid = preg_replace('/[^A-Za-z0-9_]/', '', (string) ($s['id'] ?? ''));
    if ($sid === '') { return array(400, 'no session id'); }
    $ps = (string) ($s['payment_status'] ?? '');
    if ($ps !== 'paid' && $ps !== 'no_payment_required') { so_wh_log($dir, "{$sid} {$sku} ignored payment_status={$ps}"); return array(200, 'ignored: payment_status ' . $ps); }

    $claim = $dir . '/sent/' . $sid . '.json';
    $fh = @fopen($claim, 'x');                       // atomic: only one request per session gets past here
    if ($fh === false) { so_wh_log($dir, "{$sid} {$sku} duplicate"); return array(200, 'duplicate: already handled'); }

    $support = (string) $D['support_email'];
    $to = (string) ($s['customer_details']['email'] ?? ($s['customer_email'] ?? ''));
    $delivery = 'no customer email on the session';
    if ($to !== '') {
        $e = so_wh_send($cfg, $to, so_wh_customer_email($sku, $s, $D), $support);
        if ($e !== '') {                               // release the claim so Stripe's retry can try again
            fclose($fh); @unlink($claim);
            so_wh_log($dir, "{$sid} {$sku} customer email FAILED: {$e}");
            return array(500, 'customer email failed');
        }
        $delivery = 'sent to ' . $to;
    }
    $notify = (string) ($cfg['notify_email'] ?? '');
    $ne = $notify !== '' ? so_wh_send($cfg, $notify, so_wh_notice_email($sku, $s, $D, $delivery), $to !== '' ? $to : $support) : 'no notify_email';
    fwrite($fh, json_encode(array('sku' => $sku, 'at' => gmdate('c'), 'customer_email' => $to !== '' ? 'sent' : 'none', 'notice' => $ne === '' ? 'sent' : $ne)));
    fclose($fh);
    so_wh_log($dir, "{$sid} {$sku} customer=" . ($to !== '' ? 'sent' : 'none') . ' notice=' . ($ne === '' ? 'sent' : $ne));
    return array(200, 'ok: ' . $sku);
}
