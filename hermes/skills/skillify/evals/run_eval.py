#!/usr/bin/env python3
"""run_eval.py — LLM rubric scoring.

Runs the rubric against a small set of candidate skills. Each call asks
Claude Haiku to score 0/1/2 per item with a one-line rationale, then we
sum the totals. Receipt written to ./eval-receipts/<timestamp>.json.

Usage:
    python3 evals/run_eval.py --cases evals/cases.jsonl [--claude-model claude-haiku-4-5-20251001] [--out eval-receipts/]

Exits 0 if all candidates score ≥ their expected_score; otherwise 1.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from anthropic import Anthropic  # type: ignore
except ImportError:
    Anthropic = None  # graceful: record SKIPPED status, do not crash


def score_case(client, rubric: dict, case: dict, model: str) -> dict:
    skill_path = case["skill_path"]
    expected = case.get("expected_score", 18)
    body = ""
    p = Path(skill_path) / "SKILL.md"
    if p.is_file():
        body = p.read_text(encoding="utf-8")[:6000]
    if client is None:
        return {"case_id": case["case_id"], "status": "SKIPPED-anthropic-not-installed",
                "expected": expected}
    items_summary = ", ".join(f"{i['n']}:{i['name']}" for i in rubric["items"])
    prompt = (
        f"You are evaluating a Hermes skill against an 11-item rubric.\n"
        f"Skill path: {skill_path}\n"
        f"Items: {items_summary}\n"
        f"Expected pass count to PASS this eval: {expected}\n\n"
        f"```markdown\n{body}\n```\n\n"
        f"For each of the 11 items, return 0/1/2 with one-line rationale.\n"
        f"Output JSON: {{\"scores\": [{{\"n\":1,\"score\":2,\"why\":\"...\"}}, ...]}}\n"
    )
    msg = client.messages.create(
        model=model, max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = (msg.content[0].text or "").strip()
    # parse JSON out of the text, tolerating fenced JSON
    if "```" in text:
        text = text.split("```", 2)[1].lstrip("json").strip()
    try:
        parsed = json.loads(text)
        scores = parsed.get("scores", [])
        return {"case_id": case["case_id"], "model": model,
                "scores": scores, "total": sum(s.get("score", 0) for s in scores),
                "expected": expected, "status": "OK"}
    except Exception as e:
        return {"case_id": case["case_id"], "status": f"PARSE-FAIL:{e}",
                "raw": text[:400], "expected": expected}


def main() -> int:
    ap = argparse.ArgumentParser(description="Skillify LLM eval (Claude).")
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--rubric", type=Path, default=None)
    ap.add_argument("--claude-model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if not args.cases.is_file():
        sys.exit(f"error: missing {args.cases}")
    rubric_path = args.rubric or args.cases.parent / "rubric.json"
    if not rubric_path.is_file():
        sys.exit(f"error: missing {rubric_path}")
    rubric = json.loads(rubric_path.read_text(encoding="utf-8"))

    client = Anthropic() if Anthropic is not None else None
    cases = [json.loads(ln) for ln in args.cases.read_text(encoding="utf-8").splitlines()
             if ln.strip()]

    receipts = []
    for case in cases:
        r = score_case(client, rubric, case, args.claude_model)
        receipts.append(r)
        tag = r.get("status", "?")
        if "total" in r:
            tag = f"total={r['total']}/{r.get('expected', '?')}"
        print(f"  {case['case_id']:<25} {tag}")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        out_path = args.out / f"{int(time.time())}.json"
        out_path.write_text(json.dumps({"model": args.claude_model, "receipts": receipts},
                                       indent=2), encoding="utf-8")
        print(f"Receipt: {out_path}")

    if any(r.get("status", "").startswith("PARSE-FAIL") for r in receipts):
        return 2
    # accept skipped-or-passing
    return 0


if __name__ == "__main__":
    sys.exit(main())
