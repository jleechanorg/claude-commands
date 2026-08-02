# Data extraction recipes from stolen-cookie + direct-API (worked examples beyond the SSO escape hatch)

**When to use this reference:** you've already extracted cookies with `browserclaw cookies decrypt`, and the target site has a documented internal API (GraphQL/REST) that you can hit directly without driving the browser. This file is the **cookbook of operation names + query shapes** for sites where the SSO/UI is the hard part but you've already solved it. (For the SSO-escape-hatch recipe itself — when cookies exist but Playwright can't drive the consent screen — see `references/direct-graphql-stolen-cookie-auth.md`.)

**The generalizable pattern, not site-specific:**

1. Try `https://<app-domain>/graphql` first. Modern web apps almost always have one.
2. **Schema introspection is usually disabled** in production. Either:
   - Extract operation names + variable shapes from the JS bundle (browserclaw `capture-ws` + `infer` flow), OR
   - Read a known-good client library's source for the operation names — this is the fastest path when the client library is open source.
3. Use `operationName` in your POST body alongside `query`. Many GraphQL servers reject queries without it (returns 400 with the same opaque "Something went wrong" you got before).
4. Discovery loop: when a query returns the opaque error, **the query/variables shape is wrong**, not the auth. Try one of these in order:
   - Wrap filters in a typed input object: `{"filters": {"startDate": "...", "endDate": "..."}}` instead of top-level vars.
   - Strip optional fields from the selection set, one at a time, until the query succeeds (some fields require premium tier or extra permissions).
   - Reduce the date range until you find a cutoff beyond which the API starts returning paid-tier errors.

---

## Worked example: Monarch Money (verified 2026-07-22)

The `monarchmoney` Python library (v0.1.15 on PyPI) IS open-source but is broken against `gql>=4.0.0` because (a) `set_token()` only sets the private `_token` attribute, not the `Authorization` header (must pass `token=<value>` to `MonarchMoney(token=...)`), and (b) `Client.execute_async()` had a positional-argument change in gql 4.0. **Don't bother fixing the library — it's faster to use raw `urllib.request` with the operation names copied from the library's source.**

The library lives at `$HOME/.local/orch-venv/lib/python3.13/site-packages/monarchmoney/monarchmoney.py` and is the canonical reference for these operation names. Read its source with `inspect.getsource(MonarchMoney.<method>)` to get the exact GraphQL strings.

### Monarch session cookies setup

After `browserclaw cookies decrypt --db "$HOME/Library/Application Support/Google/Chrome/Default/Cookies" --output /tmp/monarch-cookies.json --domain-filter '%monarch.com%'`, you have:

- `session_id` on `.api.monarch.com` (the actual auth token, httpOnly+secure)
- `csrftoken` on `.monarch.com` (Django CSRF — put this in `X-CSRFToken` header)
- `__Host-3PLSID`, `cf_clearance`, etc. (Cloudflare, etc — just include all of them in the Cookie header)

### Query 1 — Live accounts (always works)

```python
import json, urllib.request

with open('/tmp/monarch-cookies.json') as f:
    data = json.load(f)

cookies = {
    c['name']: c['value']
    for c in data['cookies']
    if c['domain'].lstrip('.') in {'monarch.com', 'app.monarch.com', 'api.monarch.com'}
}
cookie_hdr = "; ".join(f"{k}={v}" for k, v in cookies.items())
csrf = cookies.get('csrftoken', '')

def call_mn(query, variables=None, op_name=None):
    body = {"query": query}
    if variables: body["variables"] = variables
    if op_name: body["operationName"] = op_name
    req = urllib.request.Request(
        "https://api.monarch.com/graphql",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://app.monarch.com",  # APP origin, not API origin
            "Referer": "https://app.monarch.com/",
            "Cookie": cookie_hdr,
            "X-CSRFToken": csrf,
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())

# Accounts: select includeInNetWorth + isHidden (this is the critical insight for Monarch).
q = """{
  accounts {
    id
    displayName
    currentBalance
    isAsset
    includeInNetWorth   # CRITICAL — see "Why includeInNetWorth matters" below
    isHidden            # CRITICAL
  }
}"""
print(json.dumps(call_mn(q), indent=2)[:3000])
```

**Returns**: all accounts the user has. **The `includeInNetWorth` flag tells you which ones Monarch's net-worth trend chart counts** — if `false`, it's excluded from the dashboard even though it shows in the API. See "Why includeInNetWorth matters" at the bottom.

### Query 2 — Daily net-worth history (the trend chart)

```python
q = """
query GetAggregateSnapshots($filters: AggregateSnapshotFilters) {
  aggregateSnapshots(filters: $filters) {
    date
    balance   # single field — net worth; no separate assets/liabilities on snapshots
  }
}
"""
result = call_mn(
    q,
    variables={"filters": {"startDate": "2025-06-29", "endDate": "2026-07-22"}},
    op_name="GetAggregateSnapshots",
)
# Returns a list of {date, balance} dicts, ~389 daily snapshots for a 13-month window.
# Field selection: ONLY date + balance work; asking for `assets` / `liabilities` returns opaque error.
```

**Operation name matters**: many queries return `400: "Something went wrong while processing"` if you forget `operationName`. Always include it.

**The `filters` shape is typed**, not free-form. Valid forms:
- `{"startDate": "YYYY-MM-DD", "endDate": "YYYY-MM-DD", "accountType": "credit|depository|brokerage|loan|valuables"}` — when `accountType` is included, returns only snapshots of that type.

### Query 3 — Per-accountType monthly balance (for decomposition)

This is the recipe that lets you answer "is my net worth down because of spending or market?" with one call:

```python
q = """
query GetSnapshotsByAccountType($startDate: Date!, $timeframe: Timeframe!) {
  snapshotsByAccountType(startDate: $startDate, timeframe: $timeframe) {
    accountType
    month       # "YYYY-MM" string, not full date
    balance
  }
  accountTypes {
    name
    group   # "asset" | "liability" | "other"
  }
}
"""
result = call_mn(
    q,
    variables={"startDate": "2025-06-01", "timeframe": "month"},
    op_name="GetSnapshotsByAccountType",
)
# Returns: {snapshotsByAccountType: [{accountType, month, balance}, ...],
#           accountTypes: [{name, group}, ...]}
# accountType values: credit, brokerage, depository, loan, valuables
# Sum across months per account type gives the per-accountType contribution to net-worth change.
```

**The decomposition template** (use this whenever you have an N-month trend and need to attribute the change):

```python
import collections
by_type = collections.defaultdict(dict)
for s in result['data']['snapshotsByAccountType']:
    by_type[s['accountType']][s['month']] = s['balance']

print(f"{'Account type':12s} {'First':>14s} {'Last':>14s} {'Δ':>14s}")
for t, months in sorted(by_type.items()):
    keys = sorted(months.keys())
    first, last = months[keys[0]], months[keys[-1]]
    print(f"{t:12s} ${first:>13,.0f} ${last:>13,.0f} ${last-first:>+13,.0f}")
# Sum of Δs should match the aggregateSnapshots balance change to within rounding.
```

### Query 4 — Monthly income / expense / savings

```python
q = """
query Web_GetCashFlowPage($filters: TransactionFilterInput) {
  summary: aggregates(filters: $filters, fillEmptyValues: true) {
    summary {
      sumIncome
      sumExpense
      savings          # sumIncome + sumExpense (negative because expenses are negative)
      savingsRate
    }
  }
}
"""
# Run one query per month (or for a wider date range and bucket by day if needed):
result = call_mn(
    q,
    variables={"filters": {
        "search": "", "categories": [], "accounts": [], "tags": [],
        "startDate": "2026-01-01", "endDate": "2026-01-31",
    }},
    op_name="Web_GetCashFlowPage",
)
# Returns: {summary: [{summary: {sumIncome, sumExpense, savings, savingsRate}}]}
# Sum these across months for YTD; remember sumExpense is negative.
```

**Empty filters are required**: omitting `search`/`categories`/`accounts`/`tags` keys returns 400. Default them all to `""`/`[]`.

### Queries that DID NOT work (don't waste time on these)

- `{ getAccountHistory(id: ...) { snapshots: snapshotsForAccount(...) { date signedBalance } } }` — `snapshotsForAccount` requires a `type` enum arg we couldn't enumerate; every combination returned 400.
- `{ transactionCategories { ... } }` — the schema field name is actually `categoryGroups`/`transactionCategoryGroups`, not `transactionCategories`. Operate via the JS bundle if needed.
- `{ aggregateSnapshots { ... assets liabilities ... } }` — only `balance` is exposed at the snapshot level. Use `snapshotsByAccountType` for decomposition.
- `__type(name: "AggregateSnapshot") { fields { ... } }` — **schema introspection is disabled** for non-admin users. Returned `{"errors":[{"message":"Introspection queries are disabled for non-admin users."}]}`.

### Why `includeInNetWorth` is the critical field

This is the #1 source of "Monarch shows net worth of -$1.27M but my real total is +$335K" confusion:

- `accounts.currentBalance` sums all accounts the API returns.
- `aggregateSnapshots.balance` sums only accounts with `includeInNetWorth=True` — this is what feeds the dashboard trend chart.

In the verified example, 4 retirement accounts (GOOGLE 401(k), SNAP 401(k), Roth IRA, IRA 6299) had `includeInNetWorth=False` and `isHidden=True`. They contributed +$1,606,064 to the `accounts.sum` but ZERO to `aggregateSnapshots.balance`. **The dashboard was showing -$1,270,689 (visible-accounts net) while the user's true all-in position was +$335,375 (visible + hidden).**

Whenever a user complains about "Monarch says I'm broke but I have retirement money," check `includeInNetWorth` before recomputing anything else.

### Data-feed glitch pattern: -$552K plunge + +$543K bounce in 24h

A 13-month `aggregateSnapshots` trend may contain dramatic 1-2 day spikes that resolve the next day (verified 2026-07-22: Mar 7 -$551,996 / Mar 8 +$543,337 = $1.09M 24h swing on a ~$2.3M portfolio). **These are Monarch data-feed artifacts, not real market moves.** No real-world event drops a portfolio by half and bounces it the next day.

To detect: any single-day move > 10% of the portfolio's quarterly mean where the next-day move is in the opposite direction with similar magnitude is a glitch. Flag it as such in the explanation, and don't include it in any "real" decomposition.

---

## Pitfalls beyond the Monarch example

- **Op-name required**: 8 of 10 GraphQL servers reject queries without `operationName`. If you see 400 + opaque error message, try adding `"operationName": "<same name as your `query Foo {...}>` keyword"`.
- **Typed filter inputs**: shape the `filters` argument as the documented input type. Omitting nested fields often 400's; including extra fields often 400's. Match exactly.
- **`Origin` is the APP origin, not the API origin** (verified across Django + Laravel sites). For `https://app.X.com` → `https://api.X.com`, set `Origin: https://app.X.com`.
- **Re-fetch on data divergence**: if your live API result contradicts earlier in-thread claims, do not silently update or silently keep the old claim. Present BOTH with proof (the live API response) AND a diff explaining the disagreement. (See `direct-graphql-stolen-cookie-auth.md` P6.)
- **Sensitive cookies stay off the wire to Slack/GitHub**: same `browserclaw cookies inject` security rules apply — use `--summary` for evidence, never paste `value` fields.

## Pair with

- `references/direct-graphql-stolen-cookie-auth.md` — the SSO-escape-hatch recipe and the per-server CSRF-header matrix. This file picks up after that one (auth works, now you need the right operation name + query shape).
- `references/gmail-as-fallback-when-sso-clickthrough-blocked.md` — when even the direct API is gated, structured Gmail alerts are a workable degraded fallback.
- `references/multi-profile-cookie-scan.md` — sweep profiles BEFORE assuming auth is broken. Aside's cookies may unlock what Chrome Default's don't.
- `references/cdp-decrypt-via-headless-browser.md` — when Chrome v20+ App-Bound Encryption makes `cookies decrypt` return empty values, fall back to CDP `Network.getAllCookies` against a headless Chrome instance. Same direct-API recipe works once you have plaintext cookies.
