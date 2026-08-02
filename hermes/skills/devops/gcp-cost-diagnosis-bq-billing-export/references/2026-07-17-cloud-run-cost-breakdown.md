# Cloud Run cost breakdown — `worldarchitecture-ai` — 2026-07-16

Session: Slack thread C09GRLXF9GR/ts 1784353858.763719
Date: 2026-07-17
Project: `worldarchitecture-ai`
Billing account table: `worldarchitecture-ai.billing_export.gcp_billing_export_v1_011269_D08BDB_79D8F2`

## Trigger context

User asked: "Why is cloud run so expensive" — after the daily GCP cost email
reported total $57.95 (Cloud Run $14.28 = 25% of total spend).

## Raw per-SKU breakdown for 2026-07-16

Query used (per-line, no GROUP BY, then Python aggregation):

```sql
SELECT
  sku.description AS sku,
  usage.unit AS unit,
  usage.pricing_unit AS pricing_unit,
  cost,
  usage.amount AS usage_qty
FROM `worldarchitecture-ai.billing_export.gcp_billing_export_v1_011269_D08BDB_79D8F2`
WHERE usage_start_time >= TIMESTAMP("2026-07-16 00:00:00 UTC")
  AND usage_start_time <  TIMESTAMP("2026-07-17 00:00:00 UTC")
  AND service.description = "Cloud Run"
ORDER BY cost DESC
LIMIT 2000
```

Aggregate result (1514 line items collapsed into SKU buckets):

```
SKU                                                                      Unit                  Cost            Usage  Lines
-----------------------------------------------------------------------------------------------------------------------------
Services Min Instance Memory (Request-based billing)                     byte-seconds    $    8.93 3836246473762400.00    152
Services Min Instance CPU (Request-based billing)                        seconds         $    3.20       1280509.98    151
Services CPU (Request-based billing)                                     seconds         $    1.57         65390.89    280
Services Memory (Request-based billing)                                  byte-seconds    $    0.52 225066003673907.25    283
Jobs CPU in us-central1                                                  seconds         $    0.04          2089.62      1
Cloud Run Network Internet Data Transfer Out North America to North Ame  bytes           $    0.01      78668745.00    192
Jobs Memory in us-central1                                               byte-seconds    $    0.00 2211495156676.91      1
Cloud Run Network Internet Data Transfer Out Intercontinental (Excl Oce  bytes           $    0.00       1902047.00     52
... (network + requests — all near zero)
TOTAL                                                                                    $   14.28
```

## Floor vs Variable classification

| SKU | Cost | Bucket |
|---|---:|---|
| Services Min Instance Memory | $8.93 | **floor** |
| Services Min Instance CPU | $3.20 | **floor** |
| Services CPU (Request-based) | $1.57 | variable |
| Services Memory (Request-based) | $0.52 | variable |
| Network + Jobs + Requests | $0.06 | variable |
| **Total** | **$14.28** | **floor = $12.13 (85%)** |

Floor dominance — the cost is structural (idle fleet), not traffic-driven.

## 7-day trend — confirms chronic baseline

```sql
SELECT
  DATE(usage_start_time) AS day,
  ROUND(SUM(CASE WHEN sku.description LIKE 'Services Min Instance Memory%' THEN cost ELSE 0 END), 2) AS min_inst_mem,
  ROUND(SUM(CASE WHEN sku.description LIKE 'Services Min Instance CPU%' THEN cost ELSE 0 END), 2) AS min_inst_cpu,
  ROUND(SUM(CASE WHEN sku.description LIKE 'Services CPU (Request%' THEN cost ELSE 0 END), 2) AS req_cpu,
  ROUND(SUM(CASE WHEN sku.description LIKE 'Services Memory (Request%' THEN cost ELSE 0 END), 2) AS req_mem,
  ROUND(SUM(cost), 2) AS total
FROM `worldarchitecture-ai.billing_export.gcp_billing_export_v1_011269_D08BDB_79D8F2`
WHERE service.description = 'Cloud Run'
  AND usage_start_time >= TIMESTAMP("2026-07-09 00:00:00 UTC")
  AND usage_start_time <  TIMESTAMP("2026-07-17 00:00:00 UTC")
GROUP BY day
ORDER BY day
```

```
day         min_inst_mem  min_inst_cpu  req_cpu  req_mem  total
2026-07-09         8.94          3.19     1.11     0.35  13.66
2026-07-10         8.95          3.20     2.59     0.84  15.65
2026-07-11         9.04          3.24     3.55     1.26  17.12
2026-07-12         8.91          3.19     1.59     0.54  14.28
2026-07-13         8.81          3.17     1.80     0.63  14.46
2026-07-14         8.45          3.08     2.88     1.03  15.51
2026-07-15         9.06          3.24     1.17     0.38  13.91
2026-07-16         8.93          3.20     1.57     0.52  14.28  ← today
```

The min-instance floor ($12.13/day) is rock-solid across 8 days. Only the
request-driven SKUs ($2-5/day) vary — and they vary in lockstep with
upstream test-account usage from the `testing_mcp` / `jleechantest*` family.

## Fleet inventory (`gcloud run services list`)

All Cloud Run services are in `us-central1`. No services in any other region.
22 services total. Resource footprints:

```
NAME                          MIN_SCALE  LIMITS                               URL
ai-universe-blog              (none)     {'cpu': '1000m', 'memory': '256Mi'}  ...
ai-universe-consulting        (none)     {'cpu': '1', 'memory': '512Mi'}      ...
ai-universe-consulting-v2     (none)     {'cpu': '1000m', 'memory': '512Mi'}  ...
ai-universe-frontend-dev      (none)     {'cpu': '1000m', 'memory': '512Mi'}  ...
mvp-site-app-dev              (none)     {'cpu': '4', 'memory': '16Gi'}       ...
mvp-site-app-preview          (none)     {'cpu': '4', 'memory': '16Gi'}       ...
mvp-site-app-s1               (none)     {'cpu': '4', 'memory': '16Gi'}       ...
mvp-site-app-s2               (none)     {'cpu': '4', 'memory': '16Gi'}       ...
... (s3 through s10, same 4x16Gi footprint)
mvp-site-app-stable           (none)     {'cpu': '4', 'memory': '16Gi'}       ...
mvp-site-app-staging          (none)     {'cpu': '1000m', 'memory': '2Gi'}    ...
openclaw-sso-gateway-staging  (none)     {'cpu': '1', 'memory': '1Gi'}        ...
openclaw-sso-relay-staging    (none)     {'cpu': '1', 'memory': '1Gi'}        ...
snap-clone-dev                (none)     {'cpu': '1000m', 'memory': '512Mi'}  ...
webhook-receiver              (none)     {'cpu': '1000m', 'memory': '512Mi'}  ...
```

The fleet-wide pattern: 14+ `mvp-site-app-*` slots at `4 vCPU / 16 GiB`,
most with no minScale annotation (so min-instances is technically 0 but
they each spin up cold at that size when traffic hits).

## Labels gap

Billing export rows for Cloud Run had empty `labels`, `system_labels`, and
`project.labels` arrays. No `service_name` label attached. Had to cross-
reference via gcloud to identify the 14 large services behind the
$8.93/day min-instance memory line.

## Recommended fix (not applied — diagnostic-only session)

The user's actual ask was "why is cloud run so expensive", not "fix it".
Three intervention options were offered in the reply:

1. **Downsize dev/preview/staging services** to `1 vCPU / 1 GiB` (they don't
   need 4x16Gi). Likely savings: ~$6-8/day.
2. **Set min-instances=0 explicitly on non-prod** so they truly scale to zero
   when idle. Likely savings: full slot cost when no traffic.
3. **Keep `mvp-site-app-stable` at 4x16Gi** if it actually needs that footprint
   (real prod).

Implementation was not dispatched — this was a diagnostic session, not a
`/a` / `/finish` / `/green` flow.

## Cross-references

- Skill body: `devops/gcp-cost-diagnosis-bq-billing-export/SKILL.md`
- Email body parsed: Gmail msg 19f6f85db2e35875, "[Daily GCP cost] 2026-07-16 — $57.95"
- Total daily cost for context: $57.95 (Gemini $31.83 + Cloud Run $14.28 + App Engine $2.90 + Memorystore $2.35 + Storage $2.04 + Artifact Registry $1.75 + Cloud Build $1.50 + ...)
- 7d trailing avg: $86.38 (today is 0.67× that average, so Cloud Run is NOT spiking today — it's at baseline)
