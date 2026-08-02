---
name: gcp-cost-diagnosis-bq-billing-export
description: Diagnose GCP daily cost spikes from the BQ billing export when the user asks "why is X service so expensive", "why did GCP cost go up", "drill into Cloud Run spend", or any per-service or per-SKU cost breakdown for a GCP project. Encodes the working pattern when `bq query` returns the misleading "Aggregations of aggregations are not allowed" error on STRUCT field aggregations - query per-line (no GROUP BY) via subprocess, aggregate in Python. Also covers the cost-floor-vs-variable distinction (Cloud Run min-instance memory vs request memory, etc.) which is the fastest way to tell whether a daily spike is a new instance-footprint problem or just a traffic spike. Verified 2026-07-17 against project `worldarchitecture-ai` billing_export.gcp_billing_export_v1_011269_D08BDB_79D8F2 (Cloud Run $14.28/day breakdown with $8.93 min-inst-mem + $3.20 min-inst-CPU = $12.13 idle floor vs $2.09 request-driven).
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [gcp, billing, bigquery, cost-optimization, cloud-run, devops]
    related_skills: [gh-actions-slow-runs, spend-alert-bridge, wa-cloud-run-deploy-failure-debug, mac-di[REDACTED_OPENAI_KEY]]
---

# GCP cost diagnosis from BQ billing export

When the user asks "why is GCP X expensive" or "drill into <service> cost" and the answer needs per-SKU granularity (not just the Cloud Console Subtotal), the BQ billing export is the source of truth. This skill encodes the **two non-obvious failure modes** that block the obvious approach and the working pattern that gets around them.

## When this skill fires

- "Why is Cloud Run so expensive" / "why did GCP cost spike" / "drill into <service> cost"
- The user shares a `[Daily GCP cost] YYYY-MM-DD — $X.XX` email (the worldarchitect daily cron template) and wants service breakdown
- The user pastes a GCP cost table screenshot and asks about a specific service line
- A spend-alert cron fires (see `spend-alert-bridge`) and the named mechanism points at a specific GCP service (Cloud Run, Cloud SQL, Cloud Storage, etc.)
- Any question that requires per-SKU or per-service breakdown of GCP spend over a specific day or trend window

**Anti-trigger:** if the user wants the **official billed figure** (for invoicing / accounting), use the Cloud Console Subtotal directly. The BQ export runs **10-30% higher** than the Subtotal for ~2-3 weeks after a day closes because GCP keeps re-loading late-arriving usage events. State this caveat once when reporting BQ numbers.

## The two failure modes

### Failure mode 1 - `bq query` returns misleading "Aggregations of aggregations are not allowed"

The billing export schema has nested STRUCT fields (`service.description`, `sku.description`, `project.name`, `usage.amount`, `usage.unit`). When you write what looks like a normal GROUP BY query against this table:

```sql
SELECT sku.description AS sku, SUM(cost) AS cost
FROM `project.billing_export.gcp_billing_export_v1_*`
WHERE service.description = 'Cloud Run'
GROUP BY sku
```

`bq query` returns:

```
Error in query string: Error processing job ...: Aggregations of aggregations are not allowed at [9:12]
```

The error message points at `SUM(cost)` but the query is syntactically valid (verified by running the SAME query via the python `google-cloud-bigquery` client - it works fine). The CLI parser hits some edge case with the heredoc / STRUCT field combination.

**The actual problem is not aggregations.** The query is fine. The CLI is misreporting.

**The workaround that always works:**

1. Drop the `GROUP BY` - select per-line items only.
2. Pipe through `bq query --format=json`.
3. Aggregate in Python (`collections.defaultdict` is fine - no `pandas` needed for thousands of rows).

**The query that works (no GROUP BY):**

```sql
SELECT
  sku.description AS sku,
  usage.unit AS unit,
  usage.pricing_unit AS pricing_unit,
  cost,
  usage.amount AS usage_qty
FROM `PROJECT.billing_export.gcp_billing_export_v1_BILLINGACCT_HASH`
WHERE usage_start_time >= TIMESTAMP('YYYY-MM-DD 00:00:00 UTC')
  AND usage_start_time <  TIMESTAMP('YYYY-MM-DD+1 00:00:00 UTC')
  AND service.description = 'SERVICE_NAME'
ORDER BY cost DESC
LIMIT 2000
```

Then aggregate in Python:

```python
import subprocess, json
from collections import defaultdict

r = subprocess.run(
    ['bq', 'query', '--use_legacy_sql=false', '--format=json', '--max_rows=2000'],
    input=open('/tmp/q.sql').read(), capture_output=True, text=True, timeout=60,
)
data = json.loads(r.stdout)

agg = defaultdict(lambda: {'cost': 0.0, 'usage': 0.0, 'unit': '', 'lines': 0})
for row in data:
    agg[row['sku']]['cost'] += float(row['cost'])
    agg[row['sku']]['usage'] += float(row['usage_qty'])
    agg[row['sku']]['unit'] = row.get('unit') or row.get('pricing_unit') or ''
    agg[row['sku']]['lines'] += 1

total = sum(v['cost'] for v in agg.values())
for sku, v in sorted(agg.items(), key=lambda x: -x[1]['cost']):
    print(f"{sku[:69]:<70} {str(v['unit'])[:14]:<15} ${v['cost']:>8.2f}")
print(f"TOTAL ${total:.2f}")
```

### Failure mode 2 - `bq` subprocess can't find its `utils` module when launched from a sandbox

If you call `subprocess.run(['bq', 'query', ...])` from inside an `execute_code` sandbox without sourcing `~/.bashrc`, the gcloud SDK's `utils` import fails with:

```
ImportError: cannot import name 'bq_error' from 'utils'
```

**Fix:** source `~/.bashrc` first (which sets up the gcloud SDK env), or run `bq query` from a `terminal()` tool call (which uses the user's normal shell).

```bash
bash -c 'source ~/.bashrc 2>/dev/null; bq query --use_legacy_sql=false --format=json < /tmp/q.sql > /tmp/q.json 2>/tmp/q.err; echo exit=$?'
```

The `terminal()` tool with bash wrapping is the reliable path.

## The discovery pattern - find the table + project + billing account

Before any cost query, you need three identifiers. Get them in this order:

```bash
# 1. Project (default if not multi-project)
gcloud config get-value project

# 2. Billing dataset name (NOT always called "billing")
bq ls -d --project_id=PROJECT
# Look for: billing_export / billing / cloud_billing_export

# 3. Full billing export table name (note the long hash suffix)
bq ls DATASET
# Pick the table starting with `gcp_billing_export_v1_` (not `_resource_v1_`)

# 4. Confirm schema (column names are STRUCT - see Failure mode 1)
bq show DATASET.gcp_billing_export_v1_HASH | head -50
```

**Critical detail:** The billing export table name has a long hex suffix (`gcp_billing_export_v1_011269_D08BDB_79D8F2`). It's tied to the **billing account**, not the project. If you support multiple billing accounts (e.g. dev vs prod), each one has its own table. Don't try to wildcard with `gcp_billing_export_v1_*` - the wildcard works in some clients and fails in `bq query` heredocs.

## The diagnosis framework - cost-floor vs cost-variable

Once you have the per-SKU breakdown for a single day, classify each SKU into one of two buckets. This tells you whether the cost is structural (idle fleet) or proportional (traffic):

| Bucket | Indicator SKUs | Diagnosis direction |
|---|---|---|
| **Floor** (idle baseline) | "Min Instance Memory", "Min Instance CPU", "Idle VM time", "Always Free tier overage" | These scale with **fleet size x uptime**, not traffic. If floor > 70% of service spend, the fix is **right-size / scale-to-zero / stop running excess services** |
| **Variable** (per-request) | "CPU (Request-based billing)", "Memory (Request-based billing)", "Requests", "Network egress" | These scale with traffic. Diagnose with traffic dashboards / recent deploy spike |

**Rule of thumb:** if floor SKUs dominate, the cost is **structural** and the fix is at the service-config layer (Cloud Run min-instance, VM rightsizing, etc.). If variable SKUs dominate, the cost is **proportional** and the fix is at the application / traffic layer.

**Verified example (Cloud Run, project `worldarchitecture-ai`, 2026-07-16):**

| SKU | Cost | Bucket |
|---|---:|---|
| Services Min Instance Memory | $8.93 | **floor** |
| Services Min Instance CPU | $3.20 | **floor** |
| Services CPU (Request-based) | $1.57 | variable |
| Services Memory (Request-based) | $0.52 | variable |
| Network egress + Jobs + Requests | $0.06 | variable |
| **Total** | **$14.28** | **floor = $12.13 (85%)** |

Floor dominance means the user should look at fleet right-sizing, not traffic. For this fleet, `mvp-site-app-s1` through `s10` (10 staging slots) plus `dev`/`preview`/`stable`/`staging` (4 slots) at 4 vCPU / 16 GiB each = ~14 large slots held warm. Downsizing dev/preview/staging would drop the floor by ~50%.

## The trend query - confirm "is this new or chronic?"

If the user asks "why did X spike today" but actually the same floor has been there for weeks, you need a 7-day trend. Same query shape, but with `usage_start_time >= TIMESTAMP(YYYY-MM-DD-N 00:00:00 UTC)` for a window:

```sql
SELECT
  DATE(usage_start_time) AS day,
  ROUND(SUM(CASE WHEN sku.description LIKE 'Services Min Instance Memory%' THEN cost ELSE 0 END), 2) AS min_inst_mem,
  ROUND(SUM(CASE WHEN sku.description LIKE 'Services Min Instance CPU%' THEN cost ELSE 0 END), 2) AS min_inst_cpu,
  ROUND(SUM(CASE WHEN sku.description LIKE 'Services CPU (Request%' THEN cost ELSE 0 END), 2) AS req_cpu,
  ROUND(SUM(CASE WHEN sku.description LIKE 'Services Memory (Request%' THEN cost ELSE 0 END), 2) AS req_mem,
  ROUND(SUM(cost), 2) AS total
FROM `PROJECT.billing_export.gcp_billing_export_v1_HASH`
WHERE service.description = 'SERVICE_NAME'
  AND usage_start_time >= TIMESTAMP('YYYY-MM-DD-7 00:00:00 UTC')
  AND usage_start_time <  TIMESTAMP('YYYY-MM-DD+1 00:00:00 UTC')
GROUP BY day
ORDER BY day
```

If the trend shows the **floor** is the same every day and **variable** is what spiked, the user has a traffic anomaly to investigate. If the floor itself is rising day-over-day, they have a fleet-size drift (new services coming online, autoscaler floor creeping up, etc.).

## Per-service attribution - the labels gap

**Heads up:** Cloud Run billing export rows do NOT carry a per-service label by default. The export has `project.labels`, `labels`, and `system_labels` arrays, but they're typically empty unless someone manually tagged each Cloud Run service with `gcloud run services update SERVICE --update-labels=service_name=SERVICE`.

If labels are present, you can attribute cost per service via:

```sql
SELECT
  -- labels is REPEATED RECORD with key/value - extract via UNNEST
  l.value AS service_label,
  SUM(cost) AS cost
FROM `PROJECT.billing_export.gcp_billing_export_v1_HASH`,
     UNNEST(labels) AS l
WHERE l.key = 'service_name'
  AND service.description = 'Cloud Run'
  AND usage_start_time >= ...
GROUP BY service_label
ORDER BY cost DESC
```

If labels are NOT present (the common case), the workaround is to **cross-reference with `gcloud run services list`** and reason about which services are running with what min-instance config, then map back to the SKU breakdown by memory/CPU footprint. This is what we did in the verified example - found 14 services at 4 vCPU/16 GiB by running `gcloud run services list --format=table(...)` then explained the $8.93 min-instance-memory line as that fleet's idle footprint.

**Recipe for the gcloud inventory:**

```bash
gcloud run services list --project=PROJECT --region=REGION \
  --format="table(metadata.name,metadata.annotations['autoscaling.knative.dev/minScale'],spec.template.spec.containers[0].resources.limits)"
```

Add a `MIN_SCALE` annotation column if you want to see which services have min-instance set (vs default 0 = scale-to-zero).

## Pitfalls

### Pitfall 1: Trusting `bq query` error messages at face value

The "Aggregations of aggregations are not allowed" error is a red herring. The query is fine. The CLI parser is misreporting. Always cross-check by running the same query through the Python client or by stripping the GROUP BY. If the no-GROUP-BY version returns rows and the GROUP BY version errors with that exact message, you're hitting the CLI bug - not a real syntax error.

### Pitfall 2: Forgetting the late-arrival caveat

The BQ number runs **10-30% higher** than the Cloud Console Subtotal for 2-3 weeks after a day closes. When reporting the BQ number, state this caveat once. If the user is comparing against a Cloud Console screenshot, explain that:
- BQ = forward-looking, accumulates late events
- Cloud Console Subtotal = point-in-time, more authoritative for "what got billed today"
- Both will converge once the invoice closes

### Pitfall 3: Aggregating on `usage.unit` directly

`usage.unit` (e.g. "byte-seconds") is the raw measurement unit. `usage.pricing_unit` (e.g. "gibibyte") is the billing unit. When computing per-unit cost, use `usage.amount_in_pricing_units` (the value scaled to pricing_unit), NOT `usage.amount` (raw). Otherwise you get nonsense rates.

### Pitfall 4: Treating all Cloud Run spend as "traffic-driven"

Cloud Run's two SKU families look similar in name ("Services Memory" vs "Services Min Instance Memory") but bill completely differently. If you only see "Cloud Run is $14/day" without breaking down by SKU, you'll misdiagnose every cost-spike report. Always pull the per-SKU table before forming a hypothesis.

### Pitfall 5: Running `bq query` from a subprocess without sourcing bashrc

The gcloud SDK's `bq` command depends on a `utils` import that breaks when the env doesn't have the SDK path. Symptom: `ImportError: cannot import name 'bq_error' from 'utils'`. Always wrap in `bash -c 'source ~/.bashrc 2>/dev/null; bq query ...'`.

### Pitfall 6: Missing the cost-floor vs variable distinction when reporting

If you only report the per-SKU table without naming which SKUs are floor vs variable, the user has to do the analysis themselves. Always group SKUs into the two buckets and state the floor-share ratio. "85% floor / 15% variable" is the single most useful sentence in any Cloud Run cost-diagnosis reply.

## Reference and cross-links

- `references/2026-07-17-cloud-run-cost-breakdown.md` - session-specific evidence: full per-SKU table for `worldarchitecture-ai` Cloud Run on 2026-07-16, gcloud service inventory (14 services at 4 vCPU/16 GiB), 7-day trend showing floor dominance, and the resulting recommended fix (downsize dev/preview/s1-s10/staging).
- `~/.hermes/skills/gh-actions-slow-runs/SKILL.md` - sibling skill for GH Actions spend spikes (different export, different scope).
- `~/.hermes/skills/spend-alert-bridge/SKILL.md` - verify-alert discipline; use this skill AFTER spend-alert-bridge confirms the alert is real.
- `~/.hermes/skills/worldarchitect/wa-cloud-run-deploy-failure-debug/SKILL.md` - Cloud Run *deploy* failure diagnosis (NOT cost). Different concern, same project.
- `~/.hermes/skills/mac-di[REDACTED_OPENAI_KEY]/SKILL.md` - the di[REDACTED_OPENAI_KEY] sibling skill (different resource, same "first-use three concurrent lanes" pattern).

## One-line summary

**Query per-line (no GROUP BY) via `bq query` heredoc, aggregate in Python; classify each SKU as floor vs variable; the floor-share ratio tells you whether the cost is structural (fleet size) or proportional (traffic).**
