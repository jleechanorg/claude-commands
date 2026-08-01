# Oren Hen / TaxDome — Preparer-specific notes

User's Preparer is **Oren Hen, Enrolled Agent**, doing business as
**Oren Hen EA, Inc.**

- Mailing address: 6404 Wilshire Blvd, Suite #800, Los Angeles, CA 90048
- Office: 323-433-4363  •  Cell: 310-904-3334  •  Fax: 323-739-1670
- PTIN: P00450310  •  EIN: 47-1613168
- Firm domain (TaxDome): `orenheneainc`
- Portal URL: `https://orenheneainc.taxdome.com/login`
- Dashboard: `https://orenheneainc.taxdome.com/app/dashboard`
- Email: `oren@orenhenea.com`
- TaxDome notifications: `notifications@taxdome.com`

## How Oren Hen sends email

- Personal emails from `oren@orenhenea.com` always have a confidentiality
  footer ("This message is intended only for the designated recipient…
  IRC confidentiality protections"). Reply inline below the question —
  his parser expects that.
- TaxDome system notifications from `notifications@taxdome.com` are
  auto-generated for organizer completion, invoice payment, invoice
  overdue. Don't reply to these directly; reply to the original
  Preparer thread via gmail reply.
- He uses the exact same "Missing Data Request" numbered-section format
  every year since 2020. Treat the most recent year's questions as the
  template for the current year — diff for new entries, but keep wording.

## TaxDome invoice-numbering convention

- Invoice numbers are 7-digit (e.g. `1002106`, `1002418`).
- The Mar 2026 payment of $850 referenced invoice `1002106` — that was
  the tax-prep fee, not the extension fee.
- The May-Jun 2026 "$80 overdue" reminder chain references invoice
  `1002418` — that is the extension fee, NOT yet paid as of 2026-07-18.
- When the user says "I think I paid this" — verify the EXACT invoice
  number in a `Confirmation of invoice(s) paid` thread, not by paraphrasing.

## Tax organizer template (canonical 2024 / 2025 wording)

Oren Hen uses this numbered structure. Re-render every year from the
most recent "Missing Data Request" or "Finalize Organizer" thread:

1. Interest (1099-INT) — confirm or close per account
2. Dividends (1099-DIV) — confirm dividends per account
3. Foreign bank accounts (FBAR) — peak balance in original currency
4. Crypto exchange — sells/conversions/taxable-events Y/N, staking
   rewards USD total, attach Form 8949 + Schedule D
5. 1099-R (Fidelity / 401k) — codes + amounts, re-check for late-issued
   forms that might belong on a prior year
6. Estimated tax payments (federal + state) for the four quarterly dates
7. Charitable contributions (cash + non-cash) — receipts + FMV

Sub-organizer for business entities triggers separately per organizer.

## Always-true cross-year facts

- Filing status: Single, 1 dependent (when applicable). MFS occasionally.
- Address: 1046 Rose Ave, Venice, CA 90291 (home mortgage WF acct 7313)
- SSN: 113-96-1659 (verify each year on the 1040 page)
- FTB extension-payment portal: https://www.ftb.ca.gov/pay/index.html
- IRS extension-payment portal: https://www.irs.gov/payments
- Estimated tax schedule mailed by the Preparer every January (4 federal
  + 2 state vouchers — verify amounts before each payment).

## Sub-questions he surfaces per-year

- Wells Fargo 1951 (Clearing Services) status — sometimes closed, sometimes still open
- Charles Schwab 6506 (Bank) status — same
- Vanguard Brokerage 0410 (closed in 2024; verify)
- Morgan Stanley 40511 / 85734 — usually both still active
- Scotiabank RRSP — peak balance in CAD (foreign account)
- Gemini Exchange — peak balance in USD + staking rewards USD

## How to verify each year

Run `scripts/fetch_tax_season_history.sh` from this skill. It pulls:

- The latest Preparer "Missing Data Request" / "Finalize Organizer" thread body
- The prior-year vendor 1099 availability emails
- The most recent 1040 from Drive
- Outstanding TaxDome invoices from the latest reminders

Output: `/tmp/<year>-tax-history.json` (review) and
`/tmp/<year>-tax-history.md` (human-readable summary).
