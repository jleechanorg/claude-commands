# Compact Gmail + Calendar Digest

Use this mode when a scheduled prompt asks only for important unread email, the next 24 hours of calendar events, and actions.

## Selection

1. Query unread mail from the last day, plus Gmail `IMPORTANT` and `STARRED` signals.
2. Rank by immediate personal/financial/security impact, explicit failures, deadlines, and unusual cost—not by recency alone.
3. Collapse notification cascades into one item. Example: transfer → low-balance → overdraft is one banking incident; lead with the highest-severity state and retain the triggering transaction in **Action needed**.
4. Limit the rendered email list to three incidents, not three individual messages.
5. Fetch message/thread snippets or plain-text bodies for shortlisted items before summarizing; subjects alone may omit the amount, deadline, failure count, or security context.

## Calendar window

- Compute a true rolling `now` through `now + 24h` window client-side.
- Drop multi-day carry-forward events that began before the window; `gog calendar events --days=1` may include them.
- Include all-day events inside the window and visually surface titles containing a time.
- For private events with no visible title, say `private calendar hold`; never invent a name.
- Show local timezone once when ambiguity matters. Avoid dumping meeting links or attendee details.

## Rendering contract

Use exactly these three sections unless the caller requests another shape:

- `• Important unread emails (top 3)`
- `• Upcoming calendar events in next 24h`
- `• Action needed`

Keep each incident/event to one line. Put the most urgent action first. Do not add unrelated system status, explanatory methodology, or offers to do more work. If both lists are empty, output exactly: `No important emails/events right now.`

When the runtime says final output is automatically delivered, do not call Slack/email send tools. Return the digest as the final response and let the configured delivery target handle transport. If direct transport is explicitly required instead, run the outbound secret gate on the resolved body before sending.

## Verification checklist

- Three or fewer email incidents.
- Cascades deduplicated.
- Shortlisted emails verified beyond subject line.
- Calendar entries truly start within the next 24 hours.
- No stale carry-forward event.
- Exact caller-requested section labels.
- No duplicate direct send when automatic delivery is active.
