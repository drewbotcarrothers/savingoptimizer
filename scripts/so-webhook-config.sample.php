<?php
/* Sample config for toolkits/stripe-webhook.php. Copy it to ONE level above public_html as .so-webhook-config.php
 * (e.g. /home/<user>/domains/savingoptimizer.com/.so-webhook-config.php), fill it in, and set permissions to 600.
 * Never commit the filled-in copy. */
return array(
    'stripe_webhook_secret' => 'whsec_...',            // Stripe Dashboard > Developers > Webhooks > the savingoptimizer.com endpoint > Signing secret
    'from_email'   => 'contact@savingoptimizer.com',  // must be a real Hostinger mailbox on savingoptimizer.com
    'from_name'    => 'Saving Optimizer',
    'notify_email' => 'contact@savingoptimizer.com',  // gets a short notice for every sale
    'transport'    => 'auto',                         // auto = SMTP when smtp.pass is set, otherwise PHP mail()
    'smtp' => array(                                  // Hostinger Email: smtp.hostinger.com, 465, SSL (or 587 + 'starttls')
        'host' => 'smtp.hostinger.com', 'port' => 465, 'secure' => 'ssl',
        'user' => 'contact@savingoptimizer.com',
        'pass' => '',                                 // the contact@ mailbox password (hPanel > Emails). Empty = use mail()
    ),
    // 'data_dir' => '/home/<user>/domains/savingoptimizer.com/.so-webhook-data',  // default: .so-webhook-data next to this file
    // 'tolerance' => 300,                                                            // seconds, Stripe's default
);
