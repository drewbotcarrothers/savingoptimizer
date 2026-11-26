<?php
/* Saving Optimizer toolkits: Stripe webhook (checkout.session.completed -> email the buyer their download links).
 * Stripe endpoint: https://savingoptimizer.com/toolkits/stripe-webhook.php, event checkout.session.completed only.
 * Secrets live in a config file OUTSIDE the web root, never in this repo. It is looked up in this order:
 *   1. the path in the SO_WEBHOOK_CONFIG environment variable
 *   2. <parent of the document root>/.so-webhook-config.php   (recommended; one level above public_html)
 *   3. toolkits/lib/so-webhook-config.php                     (fallback; lib/.htaccess denies web access; gitignored)
 * Format: scripts/so-webhook-config.sample.php. Handling and tests: scripts/TOOLKITS.md, scripts/test-stripe-webhook.py. */
declare(strict_types=1);
header('X-Robots-Tag: noindex, nofollow');
header('Cache-Control: no-store');
header('Content-Type: text/plain; charset=utf-8');
require __DIR__ . '/lib/webhook-core.php';

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') { http_response_code(405); header('Allow: POST'); exit("POST only\n"); }
$docroot = rtrim((string) ($_SERVER['DOCUMENT_ROOT'] ?? ''), '/');
$cfgFile = '';
foreach (array((string) getenv('SO_WEBHOOK_CONFIG'), $docroot !== '' ? dirname($docroot) . '/.so-webhook-config.php' : '', __DIR__ . '/lib/so-webhook-config.php') as $f) {
    if ($f !== '' && is_readable($f)) { $cfgFile = $f; break; }
}
$cfg = $cfgFile !== '' ? require $cfgFile : null;
if (!is_array($cfg) || empty($cfg['stripe_webhook_secret'])) {
    http_response_code(500);                      // Stripe retries for up to 3 days, so configuring later still delivers
    error_log('so-webhook: config missing');
    exit("not configured\n");
}
$cfg += array('from_email' => 'contact@savingoptimizer.com', 'from_name' => 'Saving Optimizer', 'notify_email' => 'contact@savingoptimizer.com', 'transport' => 'auto');
if (empty($cfg['data_dir'])) { $cfg['data_dir'] = dirname($cfgFile) . '/.so-webhook-data'; }

$payload = (string) file_get_contents('php://input', false, null, 0, 1048576);
$D = require __DIR__ . '/lib/toolkit-data.php';
[$code, $msg] = so_wh_handle($payload, (string) ($_SERVER['HTTP_STRIPE_SIGNATURE'] ?? ''), $cfg, $D);
http_response_code($code);
echo $msg, "\n";
