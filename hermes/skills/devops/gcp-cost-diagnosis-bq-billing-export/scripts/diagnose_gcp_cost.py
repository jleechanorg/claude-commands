#!/usr/bin/env python3
"""Diagnose GCP per-service cost breakdown for a single day.

Usage:
    python3 diagnose_gcp_cost.py --project PROJECT --dataset DATASET \
        --table TABLE --service "Cloud Run" --day 2026-07-16

The table name MUST be the full billing export table
(e.g. gcp_billing_export_v1_011269_D08BDB_79D8F2), not a wildcard.
The script queries per-line (no GROUP BY) to dodge the bq-CLI
"Aggregations of aggregations are not allowed" parser bug, then
aggregates in Python.

Prints a per-SKU table sorted by cost, plus floor vs variable summary.
"""
import argparse
import json
import subprocess
from collections import defaultdict


# SKUs that are idle-baseline (cost scales with fleet size, not traffic).
# Add your own as you encounter new services.
FLOOR_SKU_PATTERNS = [
    "Min Instance Memory",
    "Min Instance CPU",
    "Idle",
    "Always Free",
    "Standby",
    "Idle VM",
]


def is_floor(sku: str) -> bool:
    return any(pat.lower() in sku.lower() for pat in FLOOR_SKU_PATTERNS)


def run_query(project: str, table: str, service: str, day: str) -> list:
    sql = f"""
SELECT
  sku.description AS sku,
  usage.unit AS unit,
  usage.pricing_unit AS pricing_unit,
  cost,
  usage.amount AS usage_qty
FROM `{project}.{table}`
WHERE usage_start_time >= TIMESTAMP('{day} 00:00:00 UTC')
  AND usage_start_time <  TIMESTAMP('{day} 23:59:59 UTC')
  AND service.description = '{service}'
ORDER BY cost DESC
LIMIT 5000
"""
    # Source bashrc so gcloud SDK's bq can find its utils module.
    cmd = f"""bash -c 'source ~/.bashrc 2>/dev/null; bq query --use_legacy_sql=false --format=json --max_rows=5000' << 'BQEOF'
{sql}
BQEOF"""
    r = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        raise RuntimeError(f"bq query failed: {r.stderr[:500]}")
    return json.loads(r.stdout)


def aggregate(rows: list) -> dict:
    agg = defaultdict(
        lambda: {"cost": 0.0, "usage": 0.0, "unit": "", "lines": 0}
    )
    for row in rows:
        sku = row["sku"]
        agg[sku]["cost"] += float(row["cost"])
        agg[sku]["usage"] += float(row["usage_qty"])
        agg[sku]["unit"] = row.get("unit") or row.get("pricing_unit") or ""
        agg[sku]["lines"] += 1
    return agg


def render(skus: dict) -> None:
    print(f"{'SKU':<72} {'Unit':<15} {'Cost':>10} {'Bucket':>8} {'Lines':>6}")
    print("-" * 120)
    floor_cost = 0.0
    var_cost = 0.0
    total = 0.0
    for sku, v in sorted(skus.items(), key=lambda x: -x[1]["cost"]):
        bucket = "floor" if is_floor(sku) else "variable"
        if bucket == "floor":
            floor_cost += v["cost"]
        else:
            var_cost += v["cost"]
        total += v["cost"]
        print(
            f"{sku[:71]:<72} {str(v['unit'])[:14]:<15} "
            f"${v['cost']:>8.2f} {bucket:>8} {v['lines']:>6}"
        )
    print("-" * 120)
    floor_pct = (floor_cost / total * 100) if total > 0 else 0
    print(f"{'TOTAL':<72} {'':<15} ${total:>8.2f}")
    print()
    print(f"Floor:  ${floor_cost:.2f} ({floor_pct:.0f}%)")
    print(f"Variable: ${var_cost:.2f} ({100 - floor_pct:.0f}%)")
    if floor_pct > 70:
        print()
        print(
            "-> Floor dominates. Cost is STRUCTURAL (fleet size, not traffic)."
        )
        print("   Fix: right-size fleet, drop min-instances, retire excess services.")
    else:
        print()
        print("-> Variable dominates. Cost is PROPORTIONAL to traffic.")
        print("   Fix: traffic dashboards, recent deploy spikes, autoscaler tuning.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--dataset", required=True, default="billing_export")
    p.add_argument("--table", required=True, help="full billing export table name")
    p.add_argument("--service", required=True)
    p.add_argument("--day", required=True, help="YYYY-MM-DD (UTC)")
    args = p.parse_args()

    rows = run_query(args.project, f"{args.dataset}.{args.table}",
                     args.service, args.day)
    skus = aggregate(rows)
    render(skus)


if __name__ == "__main__":
    main()
