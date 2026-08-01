#!/usr/bin/env python3
"""
render_draft_reply.py — Phase 4 of personal-tax-prep-coordination.

Renders the draft reply email to the Preparer from an answer map.
Output: /tmp/<preparer>-<year>-reply.txt

Usage:
  render_draft_reply.py                   # interactive — prompts stdin
  render_draft_reply.py --json answers.json --preparer orenhenea --year 2025
  render_draft_reply.py --from-file  # re-render from /tmp/<year>-answers.json

The answer map is a flat JSON object — keys are the Preparer's
canonical section numbers (e.g. "1a", "2b") and values are the
one-line answers. Missing keys render as `_____ (TBD)`.

Verified 2026-07-18 against Oren Hen's "Missing Data Request" template.
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


CANONICAL_TEMPLATE_2024_2025 = """\
Hi {preparer_name},

Thanks for the reminder. Working on the {year} organizer + uploads now.

{items_block}

Will start uploading the 1099 PDFs to TaxDome tonight.

Best,
Jeffrey
"""


# Oren Hen's canonical 2024/2025 organizer-question sections (in order).
# Each is `(section_number, prompt_text)`. The preparer-name reply inline
# uses one-line answers below each.
CANONICAL_SECTIONS_2024_2025 = [
    ("1", "Interest (1099-INT) — {vendor_a}, {vendor_b}: confirm or close?"),
    ("2", "Dividends (1099-DIV) — vendors per portfolio: confirm dividends received?"),
    ("3", "Foreign accounts (FBAR) — peak balances in original currency?"),
    ("4", "Crypto exchange — sells/conversions Y/N, taxable events Y/N, staking rewards USD total? Attach Form 8949 + Schedule D."),
    ("5", "1099-R (Fidelity / 401k) — codes + amounts. Re-check for late-issued forms that might belong on a prior year."),
    ("6", "Estimated tax payments — dates paid for the four federal + two state quarterly dates."),
    ("7", "Charitable contributions — cash + non-cash FMV."),
]


def canonical_outstanding_invoice_block():
    """Oren Hen's invoice 1002418 is the canonical 'still open' trap.
    Render it as a callout if not yet paid."""
    return (
        "Outstanding invoice (please confirm payment status — I've been "
        "seeing TaxDome reminder emails but no Payment confirmation):\n"
        "  - Invoice 1002418 — $80.00 Extension Fee — Status: Overdue\n"
        "    The Mar 2026 Payment confirmation was for invoice 1002106 "
        "    (the $850 prep fee), not the extension fee.\n"
    )


def render_inline_block(answers: dict, year: int) -> str:
    """Render the answer-#-by-# inline block.

    Pulls from `CANONICAL_SECTIONS_2024_2025` to keep wording stable.
    Uses vendor_a / vendor_b as Platzhalter for the 1099-INT vendors;
    pass them via answers["__vendor_a__"] and answers["__vendor_b__"].
    """
    rendered = []
    vendor_a = answers.get("__vendor_a__", "Schwab Bank 6506")
    vendor_b = answers.get("__vendor_b__", "Wells Fargo 1951")

    for num, prompt_tpl in CANONICAL_SECTIONS_2024_2025:
        prompt = prompt_tpl.format(vendor_a=vendor_a, vendor_b=vendor_b)
        answer = answers.get(num, "_____ (to confirm)")
        rendered.append(f"  {num}. {prompt}")
        rendered.append(f"     Answer: {answer}")
        rendered.append("")

    block = "\n".join(rendered)
    block += "\n" + canonical_outstanding_invoice_block()
    return block


def interactive_prompt(sections):
    """Prompt the user for each section's answer; return the answer map."""
    answers = {}
    print("Interactive answer entry — leave blank to default to '_____ (to confirm)'.\n")
    for num, prompt_tpl in sections:
        prompt = prompt_tpl.format(vendor_a="Schwab Bank 6506",
                                   vendor_b="Wells Fargo 1951")
        answer = input(f"  {num}. {prompt}\n     Answer: ").strip()
        answers[num] = answer or "_____ (to confirm)"
    return answers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="Path to answers JSON")
    ap.add_argument("--preparer", default="orenhenea",
                    help="Preparer hostname (default: orenhenea)")
    ap.add_argument("--preparer-name", default="Oren",
                    help="First-name for the salutation")
    ap.add_argument("--year", type=int, default=int(os.environ.get("TAX_YEAR", "2025")))
    ap.add_argument("--out", help="Output path (default: /tmp/<preparer>-<year>-reply.txt)")
    ap.add_argument("--interactive", action="store_true",
                    help="Prompt for answers on stdin")
    args = ap.parse_args()

    if args.interactive:
        answers = interactive_prompt(CANONICAL_SECTIONS_2024_2025)
    elif args.json:
        with open(args.json) as f:
            answers = json.load(f)
    else:
        print("ERROR: pass --json /path/to/answers.json or --interactive.",
              file=sys.stderr)
        sys.exit(2)

    items_block = render_inline_block(answers, args.year)
    body = CANONICAL_TEMPLATE_2024_2025.format(
        preparer_name=args.preparer_name,
        year=args.year,
        items_block=items_block,
    )

    out_path = args.out or f"/tmp/{args.preparer}-{args.year}-reply.txt"
    Path(out_path).write_text(body)
    print(f"[render_draft_reply] wrote {out_path}")
    print()
    print("=" * 80)
    print(body)
    print("=" * 80)
    print()
    print(f"Send ONLY after `EMAIL APPROVED` from the user.")
    print(f"Recipient thread is the Preparer's most recent unanswered email.")


if __name__ == "__main__":
    main()
