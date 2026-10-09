<?php
/**
 * Saving Optimizer contact form handler.
 * Receives POSTs from /contact.html and emails them to contact@savingoptimizer.com with PHP mail().
 * No secrets live here. Works on PHP 7.2+.
 */

declare(strict_types=1);

const CF_TO          = 'contact@savingoptimizer.com';
const CF_FROM        = 'no-reply@savingoptimizer.com';
const CF_FROM_NAME   = 'Saving Optimizer website';
const CF_THANKS      = '/contact-thanks.html';
const CF_ERROR       = '/contact.html?error=1';
const CF_MIN_MS      = 3000;   // minimum time on the page before submitting
const CF_RATE_MAX    = 5;      // messages allowed per client...
const CF_RATE_WINDOW = 3600;   // ...per this many seconds
const CF_TOPICS      = [
    'General', 'Food & Groceries', 'Transportation', 'Housing', 'Utilities', 'Kids',
    'Clothing', 'Personal Care', 'Travel', 'Personal Finance', 'Insurance', 'Healthcare',
    'Household Items and Supplies', 'Pets', 'Subscriptions', 'Entertainment', 'Students',
    'Weddings', 'Events', 'Education', 'Technology', 'Internet', 'Sports',
    'Correction or update',
];

header('X-Robots-Tag: noindex, nofollow');
header('Cache-Control: no-store');

function so_redirect(string $to): void
{
    header('Location: ' . $to, true, 303);
    exit;
}

/** Remove CR, LF and other control characters so a value can never start a new mail header. */
function so_header_safe(string $v): string
{
    return trim((string) preg_replace('/[\x00-\x1F\x7F]+/u', ' ', $v));
}

function so_len(string $v): int
{
    return function_exists('mb_strlen') ? mb_strlen($v, 'UTF-8') : strlen($v);
}

function so_field(string $key): string
{
    $v = $_POST[$key] ?? '';
    return is_string($v) ? trim($v) : '';
}

/** Client IP used for the rate limit and shown in the email. */
function so_client_ip(): string
{
    $remote = $_SERVER['REMOTE_ADDR'] ?? '';
    $fwd = '';
    if (!empty($_SERVER['HTTP_X_FORWARDED_FOR']) && is_string($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $first = trim(explode(',', $_SERVER['HTTP_X_FORWARDED_FOR'])[0]);
        if (filter_var($first, FILTER_VALIDATE_IP)) {
            $fwd = $first;
        }
    }
    return $fwd !== '' && $fwd !== $remote ? $remote . ' (forwarded for ' . $fwd . ')' : $remote;
}

/** Rate-limit store: a folder next to (outside) the web root when writable, else the system temp dir. */
function so_rate_dir(): string
{
    $candidates = [];
    if (!empty($_SERVER['DOCUMENT_ROOT'])) {
        $candidates[] = dirname(rtrim((string) $_SERVER['DOCUMENT_ROOT'], '/')) . '/.so-contact-ratelimit';
    }
    $candidates[] = rtrim(sys_get_temp_dir(), '/') . '/so-contact-ratelimit';
    foreach ($candidates as $dir) {
        if (is_dir($dir) || @mkdir($dir, 0700, true)) {
            if (is_writable($dir)) {
                return $dir;
            }
        }
    }
    return '';
}

/** Returns true if this client is still under the limit, and records the attempt. */
function so_rate_ok(string $clientKey): bool
{
    $dir = so_rate_dir();
    if ($dir === '') {
        return true; // fail open rather than block real people if no folder is writable
    }
    $file = $dir . '/' . hash('sha256', $clientKey) . '.json';
    $fh = @fopen($file, 'c+');
    if ($fh === false) {
        return true;
    }
    flock($fh, LOCK_EX);
    $raw = stream_get_contents($fh);
    $now = time();
    $hits = json_decode($raw ?: '[]', true);
    $hits = is_array($hits) ? array_values(array_filter($hits, function ($t) use ($now) {
        return is_int($t) && $t > $now - CF_RATE_WINDOW;
    })) : [];
    $ok = count($hits) < CF_RATE_MAX;
    if ($ok) {
        $hits[] = $now;
    }
    ftruncate($fh, 0);
    rewind($fh);
    fwrite($fh, json_encode($hits));
    fflush($fh);
    flock($fh, LOCK_UN);
    fclose($fh);
    return $ok;
}

// ---- POST only -------------------------------------------------------------
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    header('Allow: POST');
    header('Content-Type: text/plain; charset=UTF-8');
    echo "This address only accepts the contact form. Please use https://savingoptimizer.com/contact.html\n";
    exit;
}

// ---- Bot checks ------------------------------------------------------------
// Honeypot: real people never see or fill the "website" field. Pretend it worked.
if (so_field('website') !== '') {
    so_redirect(CF_THANKS);
}
// Time on page, measured in the visitor's browser (avoids clock differences between browser and server).
$ts      = so_field('form_ts');
$elapsed = so_field('form_elapsed');
if (!ctype_digit($ts) || !ctype_digit($elapsed) || (int) $elapsed < CF_MIN_MS) {
    so_redirect(CF_ERROR);
}

// ---- Validation ------------------------------------------------------------
$name    = so_header_safe(so_field('name'));
$email   = so_field('email');
$topic   = so_field('topic');
$message = str_replace(["\r\n", "\r"], "\n", so_field('message'));

$valid = true;
if ($name === '' || so_len($name) > 100) {
    $valid = false;
}
if (strlen($email) > 254 || preg_match('/[\r\n]/', $email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    $valid = false;
}
if (!in_array($topic, CF_TOPICS, true)) {
    $valid = false;
}
$mlen = so_len($message);
if ($mlen < 10 || $mlen > 5000) {
    $valid = false;
}
if (!$valid) {
    so_redirect(CF_ERROR);
}

// ---- Rate limit ------------------------------------------------------------
$ip = so_client_ip();
if (!so_rate_ok($ip)) {
    so_redirect(CF_ERROR);
}

// ---- Send ------------------------------------------------------------------
$email = so_header_safe($email);
$topic = so_header_safe($topic);

$subjectText = 'Saving Optimizer contact: ' . $topic;
$subject = function_exists('mb_encode_mimeheader')
    ? mb_encode_mimeheader($subjectText, 'UTF-8', 'B', "\r\n")
    : '=?UTF-8?B?' . base64_encode($subjectText) . '?=';

$when = (new DateTime('now', new DateTimeZone('America/Toronto')))->format('Y-m-d H:i:s T');
$body = "New message from the savingoptimizer.com contact form\n\n"
      . "Name:    {$name}\n"
      . "Email:   {$email}\n"
      . "Topic:   {$topic}\n"
      . "Time:    {$when}\n"
      . "IP:      {$ip}\n\n"
      . "Message:\n{$message}\n";

$headers = implode("\r\n", [
    'From: ' . CF_FROM_NAME . ' <' . CF_FROM . '>',
    'Reply-To: ' . $email,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
]);

$sent = @mail(CF_TO, $subject, $body, $headers, '-f' . CF_FROM);
so_redirect($sent ? CF_THANKS : CF_ERROR);
