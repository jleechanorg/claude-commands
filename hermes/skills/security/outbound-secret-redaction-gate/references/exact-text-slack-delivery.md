# Exact-text Slack delivery verification — session detail

## What happened

An exact reminder was sent to `#life` with a successful `chat.postMessage` receipt. A later `chat.getPermalink` call failed with `invalid_arguments`, and a channel-wide history scan initially failed to find a prefix match because Slack canonicalized the body: the Unicode receipt emoji became `:receipt:` and the bare domain became an auto-link (`<http://...|...>`). A subsequent history read showed the message at the returned timestamp and confirmed it was present.

## Reusable verification recipe

1. Preserve the `channel` and `ts` returned by `chat.postMessage`.
2. Use a read API against that exact message or a narrowly bounded history window; do not search only for the raw Unicode prefix.
3. Normalize only known Slack transforms before comparison:
   - Unicode emoji may be represented as colon aliases such as `:receipt:`.
   - Bare URLs/domains may be represented as `<http://url|label>` or `<https://url|label>`.
   - Do not silently ignore substantive wording changes.
4. If `chat.getPermalink` returns `invalid_arguments` or `message_not_found`, do not infer that posting failed; verify using history/replies and the original receipt.
5. If a verification attempt creates a message or mutates state, record that separately. Verification must not cause duplicate reminders.

## Reporting rule

Use “Delivered” only when both conditions hold:

- transport returned `ok=true` with channel and timestamp; and
- a readback located the same message at that timestamp (with only documented canonicalization).

Otherwise report “posted but verification incomplete” or the exact blocker. Keep the report concise when the original request says “keep it short.”
