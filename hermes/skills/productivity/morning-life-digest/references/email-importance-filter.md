# Email Importance Filter (Gmail)

Built for the morning life-digest cron. Goal: pick the top 3 unread emails
worth surfacing to a busy human at 9am.

## Mental model — three exclusion buckets

### 1. Self-sent system mail (always exclude)

Anything from `$USER@gmail.com` — automated cron outputs, deploy-bot
SUCCESS notices, WorldArchitect/AI Universe daily reports. Pull with:

```
-from:$USER@gmail.com
```

Concrete recurring subjects (regex-equivalent substring match):

- `[GCP Cron] ...` — pass/fail audit cron
- `[Hermes] ...-ingest` — pipeline logs
- `📊 Your Project Daily Report`
- `📊 AI Universe Daily Report`
- `[Daily GCP cost] ...`
- `✅ SUCCESS: ... Deployment`
- `❌ FAILED: ... Deployment`

### 2. Transactional digests (almost always exclude)

These arrive daily, contain no decision needed, and would crowd out real
action items:

- `Chase <no.reply.alerts@chase.com>` — daily summary, balance alerts
- `Monarch <email@email.monarch.com>` — budget updates, statement balances
- `Barclays Arrival` / `American Express` — AutoPay reminders
- `Capital One` — payment received
- `Frontier` — bill ready
- `Wise` — privacy notices (low signal)
- `PayPal` — legal agreement changes (low signal unless billing-related)
- `Indeed` — ToS updates
- `LinkedIn` — security verification prompts (low signal unless NEW device)
- `OpenRouter` — receipts (info only)
- `USPS Informed Delivery` — daily digest
- `Alibaba Cloud` — promotional

### 3. Newsletters (always exclude)

- `Mailbrew` — newsletter roundup
- `noreply@x.ai` (Grok) — newsletter
- `newsletter@info.alibabacloud.com`
- `aws-marketing-email-replies@amazon.com`
- `news@email.tripo3d.ai`
- `indeed.com` marketing
- `team@moonshot.ai` — Kimi product news (low signal for end user)
- `no-reply@contact.elevenlabs.io` — webinar promo
- `donotreply@email.schwab.com` — money check-up (informational)

## What survives (rank by action signal)

After exclusions, rank survivors:

1. **Billing overrun / budget alert** — Google Cloud Billing 444% style.
   Always #1 if present.
2. **Hard deadline** — "before Aug 1 you may need to make changes" (Bank of
   America), "your bill is past due", "subscription expiring in X days".
3. **Account security** — Google Security alert on a new device, GitHub
   repo transfer you didn't initiate.
4. **Government / safety** — LA City emergency alert, IRS notice.
5. **Money movement you initiated but not completed** — wire confirmation,
   payment bounced.
6. **HR / employment** — recruiter / employer reply on an active loop.

Skip everything else (promotions, ToS changes, "we updated our privacy
notice", generic newsletters).

## Concrete exclusion query

A single combined query (tested 2026-07-22):

```
is:unread newer_than:3d \
  -from:$USER@gmail.com \
  -from:noreply@github.com \
  -from:no.reply.alerts@chase.com \
  -from:no_reply@communications.paypal.com \
  -from:no-reply@accounts.google.com \
  -from:no-reply@indeed.com \
  -from:alerts@services.barclaysus.com \
  -from:welcome.americanexpress.com \
  -from:noreply@mailbrew.com \
  -from:noreply@x.ai \
  -from:newsletter@info.alibabacloud.com \
  -from:aws-marketing-email-replies@amazon.com \
  -from:news@email.tripo3d.ai \
  -from:uspsinformeddelivery@email.informeddelivery.usps.com \
  -from:email@email.monarch.com \
  -from:invoice+statements@openrouter.ai \
  -from:no-reply@billing.frontier.com \
  -from:capitalone@notification.capitalone.com \
  -from:noreply@wise.com \
  -from:donotreply@email.schwab.com \
  -from:communications@servicing.bankofamerica.com \
  -from:no-reply@contact.elevenlabs.io \
  -from:team@moonshot.ai
```

If fewer than 3 survive: include the next-best informational items
(bank balance alerts, account statements) labeled as "FYI" so the section
still has 3 bullets.
